# 🎨 ComicCraft – AI Comic Story Creator

> **Turn your imagination into an AI-powered 5-panel comic strip with story, dialogue, artwork, and PDF export.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?style=flat&logo=google)](https://aistudio.google.com/)

---

## 📖 Project Overview

ComicCraft is a full-stack AI-powered web application that transforms a simple story idea into a complete 5-panel comic strip. Users fill in a short form and the AI pipeline handles everything: story structure, character dialogue, panel narration, comic-style artwork, and a downloadable PDF.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 AI Story Generation | Google Gemini creates a structured 5-panel outline with narration and dialogue |
| 🖼️ AI Image Generation | Stable Diffusion generates unique comic artwork for each panel |
| 💬 Speech Bubbles | Character dialogue rendered as authentic comic speech bubbles |
| 📄 PDF Export | Professional multi-page PDF with cover page, images, and full story |
| 🎨 6 Art Styles | Anime, Comic Book, Pixel Art, Cartoon, Realistic, Fantasy |
| 🌍 6 Settings | School, Forest, City, Space, Village, Fantasy World |
| 🎭 6 Story Tones | Funny, Dramatic, Adventure, Light-hearted, Emotional, Mystery |
| 📱 Responsive Design | Works on desktop, tablet, and mobile |
| ⚡ FastAPI Backend | Async Python backend with full API documentation |
| 🛡️ Error Handling | Graceful fallbacks for all AI service failures |

---

## 🛠️ Technologies

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **Templates** | Jinja2 |
| **Story AI** | Google Gemini 1.5 Flash (outline) + Gemini 1.5 Pro (story) |
| **Image AI** | Hugging Face Diffusers / Stable Diffusion XL |
| **PDF** | FPDF |
| **Images** | Pillow |
| **Frontend** | HTML5, CSS3 (Vanilla), JavaScript (Vanilla) |
| **Fonts** | Google Fonts (Bangers, Inter, Orbitron) |
| **Config** | python-dotenv |

---

## 📂 Folder Structure

```
ComicCraft/
│
├── app/
│   ├── __init__.py          # Package init
│   ├── main.py              # FastAPI app + static files + templates
│   ├── routes.py            # All HTTP routes + generation pipeline
│   ├── gemini_flash.py      # Gemini 1.5 Flash – 5-panel outline
│   ├── gemini_pro.py        # Gemini 1.5 Pro – narration & dialogue
│   ├── image_generator.py   # Image generation (HF API / local SD / placeholder)
│   ├── layout_builder.py    # Merge all panel data for templates
│   └── exporters.py         # FPDF-based PDF generation
│
├── templates/
│   ├── index.html           # Homepage / story creation form
│   ├── comic_preview.html   # Generated comic preview page
│   └── export_success.html  # PDF export success page
│
├── static/
│   ├── css/style.css        # Full responsive stylesheet
│   ├── js/script.js         # Form validation, loading UI, animations
│   ├── panels/              # Generated panel images (auto-created)
│   └── exports/             # Generated PDF files (auto-created)
│
├── .env                     # Your API keys (never commit)
├── .env.example             # Example env file
├── .gitignore
├── requirements.txt
├── README.md
└── run.bat                  # Windows one-click start script
```

---

## 🚀 Installation

### 1. Prerequisites
- Python 3.10 or higher → [Download](https://www.python.org/downloads/)
- A Google Gemini API key → [Get one free](https://aistudio.google.com/app/apikey)
- (Optional) A Hugging Face API key → [Get one](https://huggingface.co/settings/tokens)

### 2. Navigate to the project
```bash
cd ComicCraft
```

### 3. Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

> ⚠️ **Note:** `torch` and `diffusers` are large packages. If you don't have a GPU or don't want local SD, the app still works with placeholder images. You can install the lightweight version:
> ```bash
> pip install fastapi uvicorn jinja2 python-multipart google-generativeai fpdf Pillow python-dotenv pydantic
> ```

---

## 🔑 Environment Variables

Copy the example file and add your keys:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Then open `.env` and fill in:

```env
GEMINI_API_KEY=your_actual_gemini_key_here
HF_API_KEY=your_actual_hf_key_here     # Optional
DEBUG=false
```

---

## ▶️ How to Run

### Option A – Windows (one-click)
```
Double-click run.bat
```
or in terminal:
```bat
run.bat
```

### Option B – Manual
```bash
# Activate venv first
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# Start the server
uvicorn app.main:app --reload
```

### Access the app
| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000 | Main application |
| http://127.0.0.1:8000/docs | Interactive API docs (Swagger) |
| http://127.0.0.1:8000/health | Server health check |
| http://127.0.0.1:8000/test-image | Test image generation |

---

## 🌐 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET`  | `/` | Homepage (form) |
| `POST` | `/generate` | Full comic generation pipeline (form) |
| `POST` | `/generate-comic/json` | JSON API for comic generation |
| `GET`  | `/test-image` | Developer image test |
| `GET`  | `/export-success` | Export success page |
| `GET`  | `/health` | Server health check |

### JSON API Example
```bash
curl -X POST http://127.0.0.1:8000/generate-comic/json \
  -H "Content-Type: application/json" \
  -d '{
    "story_prompt": "A young wizard discovers a hidden library in the forest",
    "character_name": "Zara",
    "setting": "Forest",
    "tone": "Adventure",
    "art_style": "Fantasy"
  }'
```

---

## 🎯 How Comic Generation Works

```
User submits form
        │
        ▼
[Validation] → Check inputs
        │
        ▼
[Gemini Flash] → generate_outline()
  Creates 5-panel structure with titles, scenes, image prompts
        │
        ▼
[Gemini Pro] → generate_story()
  Adds narration, character dialogue, captions to each panel
        │
        ▼
[Image Generator] → generate_all_images()
  1. Try Hugging Face API (if HF_API_KEY set)
  2. Try local Stable Diffusion (if CUDA GPU available)
  3. Fall back to styled Pillow placeholder
        │
        ▼
[Layout Builder] → build_comic_layout()
  Merges all data, formats dialogue as speech bubbles
        │
        ▼
[PDF Exporter] → save_pdf()
  Generates multi-page PDF with cover, images, story
        │
        ▼
[Preview Page] → Display all 5 panels
        │
        ▼
[Download PDF] → Saved to static/exports/
```

---

## 🖼️ Image Generation Modes

| Mode | Requirement | Quality |
|------|-------------|---------|
| **HF API** | `HF_API_KEY` set | ⭐⭐⭐⭐ High |
| **Local SD** | CUDA GPU + 8GB+ VRAM | ⭐⭐⭐⭐⭐ Highest |
| **Placeholder** | None (always works) | ⭐⭐ Fallback |

The app **never crashes** due to missing image generation – it always falls back gracefully.

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `GEMINI_API_KEY not set` | Add your key to `.env` |
| `Module not found` | Run `pip install -r requirements.txt` in your venv |
| `Port 8000 in use` | Run `uvicorn app.main:app --port 8001` |
| Gemini rate limit | Wait 60 seconds and try again |
| HF API model loading | Add `?wait_for_model=true` parameter or wait ~30s |
| No GPU for local SD | App will use placeholder images automatically |
| PDF download fails | Check `static/exports/` directory permissions |
| Images look wrong | Try a different art style or reword your story prompt |

---

## 📋 Requirements

See [`requirements.txt`](requirements.txt) for the full list. Key packages:

```
fastapi==0.115.0
uvicorn==0.30.6
google-generativeai==0.7.2
diffusers==0.30.3
fpdf==1.7.2
Pillow==10.4.0
python-dotenv==1.0.1
```

---

## 📄 License

This project is for educational/demonstration purposes.

---

*Made with ❤️ using FastAPI, Google Gemini, and Stable Diffusion*
