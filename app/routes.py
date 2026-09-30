"""
ComicCraft – FastAPI Routes
Defines all HTTP routes and the full comic-generation pipeline.
"""

import os
import traceback
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from pathlib import Path

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_all_images
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ─── Valid input options ───────────────────────────────────────────────
VALID_SETTINGS = {"School", "Forest", "City", "Space", "Village", "Fantasy World"}
VALID_TONES    = {"Funny", "Dramatic", "Adventure", "Light-hearted", "Emotional", "Mystery"}
VALID_STYLES   = {"Anime", "Comic Book", "Pixel Art", "Cartoon", "Realistic", "Fantasy"}


# ══════════════════════════════════════════════════════════════════════
# GET /  – Homepage
# ══════════════════════════════════════════════════════════════════════
@router.get("/", response_class=HTMLResponse, tags=["pages"])
async def index(request: Request):
    """Render the ComicCraft homepage with the story creation form."""
    return templates.TemplateResponse(request=request, name="index.html")


# ══════════════════════════════════════════════════════════════════════
# POST /generate  – Full comic generation pipeline (form submission)
# ══════════════════════════════════════════════════════════════════════
@router.post("/generate", response_class=HTMLResponse, tags=["comic"])
async def generate_comic(
    request: Request,
    story_prompt: str  = Form(...),
    character_name: str = Form(...),
    setting: str        = Form(...),
    tone: str           = Form(...),
    art_style: str      = Form(...),
):
    """
    Full pipeline:
      1. Validate inputs
      2. generate_outline()  → 5-panel outline
      3. generate_story()    → narration, dialogue, caption
      4. generate_all_images() → images per panel
      5. build_comic_layout() → merged layout
      6. save_pdf()          → PDF export
      7. Render comic_preview.html
    """

    # ── Input validation ──────────────────────────────────────────────
    errors = _validate_inputs(story_prompt, character_name, setting, tone, art_style)
    if errors:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "errors": errors,
                "form_data": {
                    "story_prompt": story_prompt,
                    "character_name": character_name,
                    "setting": setting,
                    "tone": tone,
                    "art_style": art_style,
                },
            },
            status_code=422,
        )

    try:
        # ── Step 1: Generate outline ───────────────────────────────────
        outline = generate_outline(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        # ── Step 2: Generate story (narration + dialogue + captions) ──
        enriched = generate_story(
            outline=outline,
            character_name=character_name,
            setting=setting,
            tone=tone,
        )

        # ── Step 3: Generate images ────────────────────────────────────
        with_images = generate_all_images(enriched, art_style=art_style)

        # ── Step 4: Build layout ───────────────────────────────────────
        layout = build_comic_layout(with_images)

        # ── Step 5: Export PDF ─────────────────────────────────────────
        story_title = f"{character_name}'s Adventure: {story_prompt[:40]}"
        pdf_path = save_pdf(layout, story_title=story_title)

        # ── Determine if any images used placeholder ───────────────────
        image_warnings = [
            p for p in layout if p.get("image_method") == "placeholder"
        ]

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "panels": layout,
                "pdf_path": pdf_path,
                "story_title": story_title,
                "character_name": character_name,
                "setting": setting,
                "tone": tone,
                "art_style": art_style,
                "image_warnings": len(image_warnings),
            },
        )

    except ValueError as ve:
        # Validation / API config errors
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "errors": [str(ve)],
                "form_data": {
                    "story_prompt": story_prompt,
                    "character_name": character_name,
                    "setting": setting,
                    "tone": tone,
                    "art_style": art_style,
                },
            },
            status_code=400,
        )
    except Exception as exc:
        # Unexpected errors
        tb = traceback.format_exc()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "errors": [
                    f"An unexpected error occurred: {exc}",
                    "Please check your API keys and try again.",
                ],
                "form_data": {
                    "story_prompt": story_prompt,
                    "character_name": character_name,
                    "setting": setting,
                    "tone": tone,
                    "art_style": art_style,
                },
                "debug_tb": tb if os.getenv("DEBUG", "false").lower() == "true" else None,
            },
            status_code=500,
        )


# ══════════════════════════════════════════════════════════════════════
# POST /generate-comic/json  – JSON API endpoint
# ══════════════════════════════════════════════════════════════════════
class ComicRequest(BaseModel):
    story_prompt:   str = Field(..., min_length=10, max_length=2000)
    character_name: str = Field(..., min_length=1, max_length=100)
    setting:        str = Field(...)
    tone:           str = Field(...)
    art_style:      str = Field(...)


@router.post("/generate-comic/json", tags=["api"])
async def generate_comic_json(payload: ComicRequest):
    """
    JSON API endpoint for comic generation.
    Returns the full panels data + PDF path as JSON.
    """
    errors = _validate_inputs(
        payload.story_prompt,
        payload.character_name,
        payload.setting,
        payload.tone,
        payload.art_style,
    )
    if errors:
        return JSONResponse({"success": False, "errors": errors}, status_code=422)

    try:
        outline   = generate_outline(payload.story_prompt, payload.character_name, payload.setting, payload.tone, payload.art_style)
        enriched  = generate_story(outline, payload.character_name, payload.setting, payload.tone)
        with_imgs = generate_all_images(enriched, payload.art_style)
        layout    = build_comic_layout(with_imgs)
        pdf_path  = save_pdf(layout, story_title=f"{payload.character_name}'s Comic")

        return JSONResponse({
            "success": True,
            "story_title": f"{payload.character_name}'s Comic",
            "panels": layout,
            "pdf_path": pdf_path,
        })

    except Exception as exc:
        return JSONResponse(
            {"success": False, "error": str(exc), "traceback": traceback.format_exc()},
            status_code=500,
        )


# ══════════════════════════════════════════════════════════════════════
# GET /test-image  – Developer test route for image generation
# ══════════════════════════════════════════════════════════════════════
@router.get("/test-image", tags=["dev"])
async def test_image():
    """Test image generation for a single panel without running the full pipeline."""
    from app.image_generator import generate_image
    result = generate_image(
        panel_number=1,
        title="Test Panel",
        image_prompt="A hero standing on a hilltop at sunset, dramatic lighting, dynamic pose",
        art_style="Comic Book",
    )
    return JSONResponse({
        "message": "Image generation test complete",
        "result": result,
    })


# ══════════════════════════════════════════════════════════════════════
# GET /export-success  – Export success page
# ══════════════════════════════════════════════════════════════════════
@router.get("/export-success", response_class=HTMLResponse, tags=["pages"])
async def export_success(request: Request, pdf: str = ""):
    """Display a success message after PDF export."""
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={"pdf_path": pdf},
    )


# ══════════════════════════════════════════════════════════════════════
# Private helpers
# ══════════════════════════════════════════════════════════════════════
def _validate_inputs(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
) -> list[str]:
    """Validate form inputs and return a list of error strings."""
    errors = []

    if not story_prompt or len(story_prompt.strip()) < 10:
        errors.append("Story Prompt must be at least 10 characters long.")
    if not character_name or len(character_name.strip()) < 1:
        errors.append("Character Name is required.")
    if setting not in VALID_SETTINGS:
        errors.append(f"Invalid setting. Choose from: {', '.join(sorted(VALID_SETTINGS))}.")
    if tone not in VALID_TONES:
        errors.append(f"Invalid tone. Choose from: {', '.join(sorted(VALID_TONES))}.")
    if art_style not in VALID_STYLES:
        errors.append(f"Invalid art style. Choose from: {', '.join(sorted(VALID_STYLES))}.")

    return errors
