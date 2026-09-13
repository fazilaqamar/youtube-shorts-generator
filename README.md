# AI-Powered YouTube Shorts Automation System

An end-to-end AI-powered system for automating the creation of YouTube Shorts using **n8n, Gemini, Tavily, Pexels, FastAPI, Edge-TTS, Faster-Whisper, MoviePy, FFmpeg, and Docker**.

The project combines AI content generation, workflow automation, backend video processing, text-to-speech, speech-to-text, and automated video rendering into a single pipeline.

> 🚧 **Project Status: Active Development**
> Core services and processing components are implemented. The project is currently being tested and improved for reliable end-to-end video generation.

---

## 📌 Overview

Creating short-form videos manually involves several repetitive steps:

- Finding a topic
- Researching information
- Writing a script
- Finding suitable stock footage
- Generating narration
- Combining video and audio
- Formatting the video vertically
- Generating captions
- Rendering the final video

This project automates these steps through an AI-powered workflow orchestrated by n8n.

### Automated Pipeline

```
Topic
  -> AI Research
  -> Script Generation
  -> Scene Generation
  -> Stock Video Retrieval
  -> n8n Orchestration
  -> FastAPI Video Service
  -> AI Voice Generation
  -> Whisper Captions
  -> MoviePy + FFmpeg
  -> Final YouTube Short
```

---

## 🏗️ Architecture

```
                    n8n (Orchestration)
                         |
        -----------------------------------
        |                |                |
     Tavily           Gemini           Pexels
    (Research)         (LLM)           (Media)
                         |
                    FastAPI Video Service
                         |
        -----------------------------------
        |                |                |
     Edge-TTS         Whisper          MoviePy
        |                |                |
        -----------------------------------
                         |
                      FFmpeg
                         |
                  Final MP4 Short
```

---

## 🧰 Tech Stack

### AI & LLM
- Google Gemini
- LLM-based script generation
- AI scene generation
- Prompt engineering
- Faster-Whisper

### Automation
- n8n
- Webhooks
- HTTP Request nodes
- JavaScript/Code nodes
- Conditional workflow logic

### Backend
- Python 3.11
- FastAPI
- Uvicorn
- Pydantic
- Requests

### Video Processing
- MoviePy 2.1.2
- FFmpeg
- Edge-TTS
- Faster-Whisper 1.2.0

### APIs & Services
- Tavily
- Pexels
- Google Gemini

### Infrastructure
- Docker
- Docker Compose

---

## ✨ Features

### 🔎 AI-Powered Research
Tavily is used to retrieve relevant information for technology-related topics before content generation.

### 🧠 AI Script Generation
Gemini transforms research information into structured short-form video content.

The generated content can include:
- Video hook
- Narration
- Scene information
- Video requirements

### 🎬 Automated Stock Footage
Pexels is used to retrieve stock video footage for the generated scenes.

The current workflow has previously produced multiple valid video URLs for a video-generation request.

### 🎙️ AI Voice Generation
Edge-TTS converts the generated narration into an audio track.

The configured voice can be controlled through the environment configuration.

### 📝 Automatic Captions
Faster-Whisper is integrated into the video-processing service to support automatic speech transcription and caption generation.

Current Whisper setup includes:
- Faster-Whisper 1.2.0
- Whisper Tiny model
- Automatic speech transcription
- Caption processing

### 📱 Vertical Video Rendering
The video engine is designed for YouTube Shorts and other vertical short-form platforms.

Target resolution: **1080 x 1920**

MoviePy and FFmpeg are used to:
- Resize footage
- Crop footage
- Combine multiple clips
- Add narration
- Encode the final MP4

### 🐳 Dockerized Processing
The video-processing backend runs inside a Docker container containing the required Python packages and FFmpeg environment.

---

## 📂 Project Structure

```
youtube-shorts-generator/
├── n8n/
│   └── workflows/
│       └── tech_future_facts_v2.json
├── video-api/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── .env.example
├── .gitignore
└── docker-compose.yml
```

---

## ⚙️ How It Works

### 1. Workflow Orchestration
n8n coordinates the complete automation pipeline:

```
Research -> AI Generation -> Scene Processing -> Video URL Extraction -> Video API Request
```

### 2. Research
Tavily retrieves information related to the selected topic.

### 3. Content Generation
Gemini generates the short-form video script and scene information.

### 4. Media Retrieval
Pexels provides stock footage based on the generated scene requirements.

### 5. Video Processing
n8n sends the narration and video URLs to the FastAPI video service.

The internal Docker service URL is:
```
http://video-api:8000/generate-video
```

### 6. Voice Generation
Edge-TTS converts the narration into an audio file.

### 7. Video Assembly
MoviePy processes the downloaded clips and combines them with the generated narration.

### 8. Rendering
FFmpeg handles final video encoding into MP4 format.

---

## 🚀 FastAPI Video Service

The video backend exposes a health endpoint:

```http
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Generate Video

```http
POST /generate-video
```

Example request:

```json
{
  "narration": "Your narration text...",
  "video_urls": [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4"
  ]
}
```

The endpoint processes the request by:

1. Creating a unique job directory
2. Downloading the supplied video clips
3. Generating narration
4. Loading the audio
5. Calculating clip duration
6. Processing the video clips
7. Resizing footage
8. Cropping footage to 1080 x 1920
9. Concatenating clips
10. Adding narration
11. Rendering the final MP4

---

## 🐳 Docker Services

The project uses Docker Compose to manage the application services.

### n8n
- Container: `tff-n8n`
- Port: `5678`

### Video API
- Container: `tff-video-api`
- Internal Port: `8000`

The services communicate through the Docker Compose network.

---

## 🔐 Environment Variables

API keys and credentials are intentionally excluded from the repository.

Create a local `.env` file using `.env.example` as a template.

Example:

```env
TAVILY_API_KEY=your_tavily_api_key

PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key

VIDEO_API_KEY=your_long_random_api_key
TTS_VOICE=en-US-JennyNeural

GMAIL_ADDRESS=your_gmail_address
GMAIL_APP_PASSWORD=your_gmail_app_password

GOOGLE_SHEET_ID=
GOOGLE_SHEET_TAB=Sheet1
```

> ⚠️ Never commit real API keys, passwords, or credentials to GitHub.

The `.gitignore` file excludes `.env` from version control.

---

## 💻 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/fazilaqamar/youtube-shorts-generator.git
cd youtube-shorts-generator
```

### 2. Configure Environment Variables

Create a `.env` file based on `.env.example` and add your own API keys and configuration values.

### 3. Build the Docker Services

```bash
docker compose up -d --build
```

### 4. Check Running Containers

```bash
docker ps
```

### 5. Test the Video API

```bash
curl http://localhost:8000/health
```

Expected:

```json
{
  "status": "ok"
}
```

---

## 🛡️ Error Handling & Security

The FastAPI service includes exception handling around the video-generation pipeline.

When processing fails, the service:
- Logs the exception
- Cleans up temporary job files
- Returns an HTTP 500 response
- Prevents unnecessary temporary data from remaining

The API also supports authentication through the `X-API-Key` header.

Security practices used in the project include:
- Environment-based secrets
- `.env` excluded through `.gitignore`
- Placeholder credentials in `.env.example`
- API-key authentication
- No hardcoded production API keys

---

## 📊 Current Development Status

### Implemented
- [x] GitHub repository
- [x] Docker Compose configuration
- [x] FastAPI video service
- [x] Uvicorn server
- [x] `/health` endpoint
- [x] FFmpeg integration
- [x] MoviePy integration
- [x] Edge-TTS integration
- [x] Faster-Whisper integration
- [x] Whisper Tiny model
- [x] Caption functionality
- [x] n8n orchestration
- [x] AI research workflow
- [x] Gemini integration
- [x] Pexels video retrieval
- [x] Video URL extraction
- [x] Docker networking
- [x] Environment-based configuration
- [x] API authentication
- [x] Git/GitHub version control

### Currently Being Improved
- [ ] Reliable end-to-end video generation
- [ ] Long-running rendering requests
- [ ] Docker Engine stability
- [ ] Retry and fallback handling
- [ ] Production-oriented job processing

---

## 🔮 Future Improvements

### Reliability
- [ ] Retry failed API requests
- [ ] Add better timeout handling
- [ ] Add fallback media sources
- [ ] Improve long-running job handling
- [ ] Add structured logging

### Video Quality
- [ ] Smarter clip selection
- [ ] Improved caption styling
- [ ] Multiple TTS voices
- [ ] Background music
- [ ] Automatic audio ducking
- [ ] Better scene-to-footage matching

### Backend Architecture

The current video API uses a synchronous generation request. A future version can use asynchronous job processing:

```
POST /generate-video -> job_id -> Background Processing -> GET /jobs/{job_id} -> completed / failed / processing
```

This approach will make longer video-generation jobs more reliable.

### Automation
- [ ] Automatic YouTube upload
- [ ] Scheduled publishing
- [ ] Video metadata generation
- [ ] Thumbnail generation
- [ ] Multi-topic generation

### Engineering
- [ ] Unit tests
- [ ] Integration tests
- [ ] CI/CD with GitHub Actions
- [ ] Improved API documentation
- [ ] Monitoring and analytics
- [ ] Production deployment

---

## 🎯 Why This Project?

This project demonstrates practical AI engineering across multiple layers rather than focusing on a single AI model.

It combines:
- AI
- LLM Applications
- Workflow Automation
- Backend Development
- APIs
- Speech Processing
- Video Processing
- Docker

The goal is to build a complete AI-powered application where multiple services communicate and work together as one automated system.

---

## 📚 Learning Outcomes

This project provides hands-on experience with:

- AI workflow orchestration
- LLM API integration
- Prompt engineering
- Research APIs
- REST API development
- FastAPI
- Pydantic
- Text-to-speech
- Speech-to-text
- Video processing
- FFmpeg
- Docker
- Docker networking
- Environment-based configuration
- API authentication
- Error handling
- Git and GitHub

---

## 👩‍💻 Author

**Fazila Qamar**

BS Computer Science
Lahore College for Women University

### Interests
- AI Engineering
- Generative AI
- LLM Applications
- RAG
- AI Agents
- AI Automation
- Backend Development

### GitHub
https://github.com/fazilaqamar

---

## 📌 Project Status

🚧 **Active Development**

This repository is being developed incrementally with the goal of evolving the current AI automation prototype into a reliable, production-oriented AI video generation platform.
