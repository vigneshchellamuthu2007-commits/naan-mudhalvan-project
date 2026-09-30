"""
ComicCraft – Image Generator Module
Generates comic-style panel images using Hugging Face Diffusers (Stable Diffusion).
Falls back gracefully to placeholder images when GPU/model is unavailable.
"""

import os
import re
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Output directory ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
PANELS_DIR = BASE_DIR / "static" / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(text: str, panel_num: int) -> str:
    """Create a safe filename from panel title + unique ID."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())[:30]
    uid = uuid.uuid4().hex[:8]
    return f"panel_{panel_num}_{slug}_{uid}.png"


def _generate_placeholder(
    panel_number: int,
    title: str,
    art_style: str,
    filename: str,
) -> str:
    """
    Generate a styled placeholder image using Pillow when SD is unavailable.
    Returns the relative static path for use in templates.
    """
    from PIL import Image, ImageDraw, ImageFont

    # Color palettes keyed by art style
    palettes = {
        "Anime":        ("#1a1a2e", "#e94560", "#0f3460", "#ffffff"),
        "Comic Book":   ("#1c1c1c", "#ff6b35", "#004e89", "#ffffff"),
        "Pixel Art":    ("#0d0221", "#ff3366", "#00ffcc", "#ffffff"),
        "Cartoon":      ("#ffecd2", "#ff6b6b", "#4ecdc4", "#2d3436"),
        "Realistic":    ("#2c3e50", "#3498db", "#ecf0f1", "#ffffff"),
        "Fantasy":      ("#2d1b69", "#a855f7", "#fbbf24", "#ffffff"),
    }

    bg_color, accent1, accent2, text_color = palettes.get(
        art_style, ("#1a1a2e", "#e94560", "#0f3460", "#ffffff")
    )

    # Canvas size: 800 x 600
    W, H = 800, 600
    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # ── Decorative gradient-like strips ────────────────────────────────
    for i in range(0, W, 40):
        draw.rectangle([(i, 0), (i + 20, H)], fill=accent2 + "22" if len(accent2) == 7 else accent2)

    # ── Outer border ───────────────────────────────────────────────────
    border_w = 8
    draw.rectangle([(border_w, border_w), (W - border_w, H - border_w)], outline=accent1, width=border_w)

    # ── Inner border ───────────────────────────────────────────────────
    draw.rectangle([(20, 20), (W - 20, H - 20)], outline=accent2, width=2)

    # ── Panel number badge ─────────────────────────────────────────────
    badge_r = 45
    draw.ellipse([(30, 30), (30 + badge_r * 2, 30 + badge_r * 2)], fill=accent1)

    # ── Comic icon (stylized speech bubble) ───────────────────────────
    # Large central placeholder icon
    cx, cy = W // 2, H // 2 - 40
    draw.ellipse([(cx - 100, cy - 70), (cx + 100, cy + 70)], fill=accent1, outline=text_color, width=3)
    draw.ellipse([(cx - 80, cy - 50), (cx + 80, cy + 50)], fill=bg_color)

    # ── Text: Panel number ─────────────────────────────────────────────
    try:
        font_large = ImageFont.truetype("arial.ttf", 28)
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 16)
        font_badge = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font_large = ImageFont.load_default()
        font_title = font_large
        font_small = font_large
        font_badge = font_large

    # Badge number
    draw.text((30 + badge_r - 8, 30 + badge_r - 14), str(panel_number), fill=text_color, font=font_badge)

    # Central label
    draw.text((cx, cy - 10), f"Panel {panel_number}", fill=accent1, font=font_large, anchor="mm")

    # Title
    # Wrap title if long
    words = title.split()
    lines, line = [], ""
    for word in words:
        test = f"{line} {word}".strip()
        if len(test) > 35:
            lines.append(line)
            line = word
        else:
            line = test
    lines.append(line)

    y_title = H // 2 + 50
    for ln in lines[:3]:
        draw.text((cx, y_title), ln, fill=text_color, font=font_title, anchor="mm")
        y_title += 30

    # Art style label
    draw.text((cx, H - 60), f"[ {art_style} Style ]", fill=accent2, font=font_small, anchor="mm")
    draw.text((cx, H - 35), "Image will appear when AI generator is active", fill=accent1, font=font_small, anchor="mm")

    # Save
    out_path = PANELS_DIR / filename
    img.save(str(out_path), "PNG")
    return f"/static/panels/{filename}"


def generate_image(
    panel_number: int,
    title: str,
    image_prompt: str,
    art_style: str,
) -> dict:
    """
    Generate a comic panel image.

    Tries:
      1. Hugging Face Inference API (if HF_API_KEY is set)
      2. Local Stable Diffusion via diffusers (if GPU/enough RAM available)
      3. Falls back to a styled Pillow placeholder

    Returns:
      {
        "path": "/static/panels/<filename>",
        "method": "hf_api" | "local_sd" | "placeholder",
        "error": None | <error string>
      }
    """
    filename = _safe_filename(title, panel_number)

    # ─── Style suffix map ──────────────────────────────────────────────
    style_suffixes = {
        "Anime":        "anime style, manga art, vibrant colors, detailed linework",
        "Comic Book":   "comic book style, bold lines, halftone dots, dramatic shading",
        "Pixel Art":    "pixel art style, 16-bit retro game art, crisp pixels",
        "Cartoon":      "cartoon style, bright colors, clean outlines, Pixar-like",
        "Realistic":    "photorealistic, cinematic lighting, ultra detailed, 8k",
        "Fantasy":      "fantasy digital art, epic illustration, magical atmosphere",
    }
    style_suffix = style_suffixes.get(art_style, "comic art style")
    full_prompt = f"{image_prompt}, {style_suffix}, high quality, detailed"
    negative_prompt = "blurry, low quality, distorted, watermark, text, ugly, deformed"

    hf_key = os.getenv("HF_API_KEY", "")

    # ─── Method 1: Hugging Face Inference API ─────────────────────────
    if hf_key and hf_key != "your_huggingface_api_key_here":
        try:
            import requests
            api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            headers = {"Authorization": f"Bearer {hf_key}"}
            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "negative_prompt": negative_prompt,
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5,
                    "width": 768,
                    "height": 512,
                },
            }
            resp = requests.post(api_url, headers=headers, json=payload, timeout=120)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                out_path = PANELS_DIR / filename
                with open(str(out_path), "wb") as f:
                    f.write(resp.content)
                return {"path": f"/static/panels/{filename}", "method": "hf_api", "error": None}
            else:
                raise RuntimeError(f"HF API returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            # Fall through to next method
            hf_error = str(e)
    else:
        hf_error = "HF_API_KEY not set"

    # ─── Method 2: Local Stable Diffusion via diffusers ───────────────
    try:
        import torch
        from diffusers import StableDiffusionPipeline

        if not torch.cuda.is_available():
            raise RuntimeError("No CUDA GPU available for local Stable Diffusion.")

        model_id = "runwayml/stable-diffusion-v1-5"
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
        )
        pipe = pipe.to("cuda")
        pipe.safety_checker = None  # Disable safety checker for comics

        image = pipe(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=25,
            guidance_scale=7.5,
            width=768,
            height=512,
        ).images[0]

        out_path = PANELS_DIR / filename
        image.save(str(out_path))
        return {"path": f"/static/panels/{filename}", "method": "local_sd", "error": None}

    except Exception as e:
        local_error = str(e)

    # ─── Method 3: Fallback – styled Pillow placeholder ───────────────
    rel_path = _generate_placeholder(panel_number, title, art_style, filename)
    return {
        "path": rel_path,
        "method": "placeholder",
        "error": f"Image generation unavailable. HF: {hf_error} | Local SD: {local_error}",
    }


def generate_all_images(panels: list[dict], art_style: str) -> list[dict]:
    """
    Generate images for all panels and attach results.

    Adds 'image_path' and 'image_method' keys to each panel dict.
    """
    for panel in panels:
        result = generate_image(
            panel_number=panel["panel_number"],
            title=panel["title"],
            image_prompt=panel["image_prompt"],
            art_style=art_style,
        )
        panel["image_path"] = result["path"]
        panel["image_method"] = result["method"]
        panel["image_error"] = result.get("error")
    return panels
