"""
ComicCraft - AI Comic Story Creator
Main FastAPI Application Entry Point

Configures the FastAPI app, Jinja2 templates, static files, and routes.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─── Base paths ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"

# ─── Ensure output directories exist ─────────────────────────────────
PANELS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Create the FastAPI application ──────────────────────────────────
app = FastAPI(
    title="ComicCraft – AI Comic Story Creator",
    description="Turn your imagination into an AI-powered comic with story, dialogue, images, and PDF export.",
    version="1.0.0",
)

# ─── Mount static files ──────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ─── Configure Jinja2 templates ──────────────────────────────────────
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ─── Register routes ─────────────────────────────────────────────────
from app.routes import router
app.include_router(router)


# ─── Health-check endpoint ───────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check():
    """Quick health-check to verify the server is running."""
    return {
        "status": "ok",
        "app": "ComicCraft",
        "gemini_key_set": bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here"),
        "hf_key_set": bool(os.getenv("HF_API_KEY") and os.getenv("HF_API_KEY") != "your_huggingface_api_key_here"),
    }
