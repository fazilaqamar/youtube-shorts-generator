import os
import gc
import uuid
import shutil
import asyncio
import logging
import subprocess

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel, Field
import requests
import edge_tts
from faster_whisper import WhisperModel

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("video-api")

app = FastAPI(title="Tech & Future Facts Video Engine")

BASE_DIR = "/data/jobs"
MUSIC_DIR = "/app/music"  # put 2-3 royalty-free background tracks here (.mp3)
API_KEY = os.environ.get("VIDEO_API_KEY")
TARGET_W, TARGET_H = 1080, 1920

os.makedirs(BASE_DIR, exist_ok=True)

# Load Whisper once at startup (small model = fast + accurate enough for captions)
whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

# ---- Voice map: language code -> Edge-TTS voice name ----
VOICE_MAP = {
    "en": "en-US-GuyNeural",
    "ur": "ur-PK-AsadNeural",
    "hi": "hi-IN-MadhurNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "ar": "ar-SA-HamedNeural",
}


class VideoRequest(BaseModel):
    narration: str = Field(..., min_length=5)
    video_urls: list[str] = Field(..., min_length=1)
    language: str = Field(default="en", description="Language code: en, ur, hi, es, fr, ar")
    add_captions: bool = Field(default=True)
    add_music: bool = Field(default=True)


@app.get("/health")
def health():
    return {"status": "ok"}


def check_auth(x_api_key: str | None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


def cleanup_dir(path: str):
    try:
        shutil.rmtree(path, ignore_errors=True)
        log.info(f"Cleaned up job dir {path}")
    except Exception as e:
        log.warning(f"Cleanup failed for {path}: {e}")


async def generate_voice(text: str, out_path: str, voice: str):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(out_path)


def transcribe_words(audio_path: str, language: str):
    """Returns a flat list of {word, start, end} using Whisper word-level timestamps."""
    segments, _ = whisper_model.transcribe(
        audio_path,
        language=language if language in VOICE_MAP else None,
        word_timestamps=True,
    )
    words = []
    for seg in segments:
        for w in seg.words:
            words.append({"word": w.word.strip(), "start": w.start, "end": w.end})
    return words


def build_ass_captions(words: list[dict], ass_path: str, video_w: int, video_h: int):
    """
    Builds a .ass subtitle file with word-by-word pop/highlight style —
    the 'bold word pops in yellow while spoken' look used in most viral Shorts.
    Groups words into short lines (~4 words) so text doesn't overflow.
    """
    font_size = int(video_h * 0.045)
    margin_v = int(video_h * 0.15)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_w}
PlayResY: {video_h}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,1,3,0,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def ts(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = t % 60
        return f"{h:01d}:{m:02d}:{s:05.2f}"

    lines = []
    group_size = 4
    for i in range(0, len(words), group_size):
        group = words[i:i + group_size]
        if not group:
            continue
        start = group[0]["start"]
        end = group[-1]["end"]
        text_parts = []
        for w in group:
            dur_cs = max(1, int((w["end"] - w["start"]) * 100))  # centiseconds
            clean_word = w["word"].replace("{", "").replace("}", "")
            text_parts.append(f"{{\\k{dur_cs}}}{clean_word}")
        line_text = " ".join(text_parts)
        lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Default,,0,0,0,,{line_text}")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(lines))


def pick_music_track():
    if not os.path.isdir(MUSIC_DIR):
        return None
    tracks = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith((".mp3", ".wav"))]
    if not tracks:
        return None
    import random
    return os.path.join(MUSIC_DIR, random.choice(tracks))


@app.post("/generate-video")
def generate_video(data: VideoRequest, x_api_key: str | None = Header(default=None)):
    check_auth(x_api_key)

    job_id = uuid.uuid4().hex
    job_dir = os.path.join(BASE_DIR, job_id)
    downloads_dir = os.path.join(job_dir, "downloads")
    audio_path = os.path.join(job_dir, "narration.mp3")
    raw_output_path = os.path.join(job_dir, "raw_video.mp4")
    output_path = os.path.join(job_dir, "final_video.mp4")
    ass_path = os.path.join(job_dir, "captions.ass")
    os.makedirs(downloads_dir, exist_ok=True)

    downloaded_files = []
    clips = []
    audio = None
    final_video = None

    try:
        log.info(f"[{job_id}] Job started — {len(data.video_urls)} clips, lang={data.language}")

        # ---- Download source clips ----
        for i, url in enumerate(data.video_urls, start=1):
            filename = os.path.join(downloads_dir, f"video_{i}.mp4")
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in resp.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            downloaded_files.append(filename)
        log.info(f"[{job_id}] Downloaded {len(downloaded_files)} clips")

        # ---- Voice (language-aware) ----
        voice = VOICE_MAP.get(data.language, VOICE_MAP["en"])
        asyncio.run(generate_voice(data.narration, audio_path, voice))
        audio = AudioFileClip(audio_path)
        total_duration = audio.duration
        log.info(f"[{job_id}] Narration duration: {total_duration:.1f}s (voice={voice})")

        # ---- Background music (mixed under narration, quiet) ----
        final_audio = audio
        if data.add_music:
            music_path = pick_music_track()
            if music_path:
                music = AudioFileClip(music_path).with_volume_scaled(0.12)
                music = music.subclipped(0, min(total_duration, music.duration))
                final_audio = CompositeAudioClip([music, audio])
                log.info(f"[{job_id}] Background music mixed in: {os.path.basename(music_path)}")

        # ---- Assemble clips ----
        clip_duration = total_duration / len(downloaded_files)
        for file in downloaded_files:
            clip = VideoFileClip(file)
            clip = clip.subclipped(0, min(clip_duration, clip.duration))
            scale = max(TARGET_W / clip.w, TARGET_H / clip.h)
            clip = clip.resized(scale)
            x1 = (clip.w - TARGET_W) / 2
            y1 = (clip.h - TARGET_H) / 2
            clip = clip.cropped(x1=x1, y1=y1, width=TARGET_W, height=TARGET_H)
            clips.append(clip)

        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.with_audio(final_audio)

        log.info(f"[{job_id}] Rendering base video...")
        final_video.write_videofile(
            raw_output_path,
            codec="libx264",
            audio_codec="aac",
            fps=30,
            preset="medium",
            threads=4,
            ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
            logger=None,
        )
        log.info(f"[{job_id}] Base render complete")

        # ---- Captions (Whisper transcription + burn-in) ----
        if data.add_captions:
            log.info(f"[{job_id}] Transcribing narration for captions...")
            words = transcribe_words(audio_path, data.language)
            build_ass_captions(words, ass_path, TARGET_W, TARGET_H)

            log.info(f"[{job_id}] Burning captions into video...")
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", raw_output_path,
                    "-vf", f"ass={ass_path}",
                    "-c:v", "libx264", "-c:a", "copy",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    output_path,
                ],
                check=True,
                capture_output=True,
            )
            log.info(f"[{job_id}] Captions burned in")
        else:
            shutil.copy(raw_output_path, output_path)

    except subprocess.CalledProcessError as e:
        log.exception(f"[{job_id}] FFmpeg caption burn failed: {e.stderr}")
        cleanup_dir(job_dir)
        raise HTTPException(status_code=500, detail=f"Caption burn failed: {e.stderr.decode(errors='ignore')[:500]}")
    except Exception as e:
        log.exception(f"[{job_id}] Failed")
        cleanup_dir(job_dir)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {e}")

    finally:
        try:
            if audio:
                audio.close()
            for c in clips:
                try:
                    c.close()
                except Exception:
                    pass
            if final_video:
                final_video.close()
            gc.collect()
        except Exception:
            pass

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename="final_video.mp4",
        background=BackgroundTask(cleanup_dir, job_dir),
    )