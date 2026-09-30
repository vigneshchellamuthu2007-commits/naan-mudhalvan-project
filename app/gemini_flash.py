"""
ComicCraft – Gemini Flash Module
Generates a structured 5-panel comic outline from user input using Google Gemini.
"""

import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


def _configure_gemini():
    """Configure the Gemini client with the API key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is not set. Please add your Google Gemini API key to the .env file."
        )
    genai.configure(api_key=api_key)


def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
) -> list[dict]:
    """
    Generate a structured 5-panel comic outline.

    Returns a list of dicts, each containing:
      - panel_number (int)
      - title (str)
      - scene_description (str)
      - image_prompt (str)
    """

    _configure_gemini()

    system_prompt = (
        "You are a professional comic book writer and illustrator. "
        "Your task is to create a structured 5-panel comic outline. "
        "Return ONLY valid JSON – no markdown fences, no extra text."
    )

    user_prompt = f"""Create a 5-panel comic outline for the following story idea.

Story Prompt: {story_prompt}
Main Character: {character_name}
Setting: {setting}
Tone: {tone}
Art Style: {art_style}

Return a JSON array with exactly 5 objects. Each object must have:
- "panel_number": integer 1-5
- "title": a short catchy panel title
- "scene_description": 2-3 sentences describing what happens visually
- "image_prompt": a detailed, vivid image-generation prompt in the style of {art_style}, suitable for an AI image generator. Include the character name, setting details, mood, and composition.

Ensure the story has a clear beginning, rising action, climax, falling action, and resolution across the 5 panels. Keep the tone {tone.lower()} throughout.

Return ONLY the JSON array, nothing else."""

    import time
    from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError

    candidate_models = [
        os.getenv("GEMINI_MODEL", "gemini-3.7-flash"),
        "gemini-3.7-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3-flash-preview",
        "gemini-3.8-flash",
    ]
    # Deduplicate while preserving order
    seen = set()
    candidate_models = [m for m in candidate_models if not (m in seen or seen.add(m))]

    response = None
    last_error = None

    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                [system_prompt, user_prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )
            if response and response.text:
                break
        except (ResourceExhausted, GoogleAPICallError, Exception) as e:
            last_error = e
            continue

    if not response or not response.text:
        # Fallback generator if all API attempts fail so app never crashes
        return _generate_fallback_outline(story_prompt, character_name, setting, tone, art_style)

    raw_text = response.text.strip()

    # Clean markdown fences if any
    clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
    clean_text = re.sub(r"\s*```$", "", clean_text, flags=re.MULTILINE)

    # Extract JSON array using regex
    match = re.search(r"\[.*\]", clean_text, re.DOTALL)
    json_text = match.group(0) if match else clean_text

    try:
        panels = json.loads(json_text, strict=False)
    except json.JSONDecodeError:
        return _generate_fallback_outline(story_prompt, character_name, setting, tone, art_style)

    # Validate structure
    if not isinstance(panels, list) or len(panels) == 0:
        return _generate_fallback_outline(story_prompt, character_name, setting, tone, art_style)

    for i, panel in enumerate(panels):
        for key in ("panel_number", "title", "scene_description", "image_prompt"):
            if key not in panel:
                panel[key] = f"Panel {i+1}"

    return panels


def _generate_fallback_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
) -> list[dict]:
    """Graceful fallback outline when API quota is exhausted."""
    return [
        {
            "panel_number": 1,
            "title": "The Journey Begins",
            "scene_description": f"{character_name} stands in {setting}, contemplating the adventure ahead. The atmosphere is {tone.lower()} and full of anticipation.",
            "image_prompt": f"A vibrant {art_style} scene of {character_name} standing in {setting}, looking out towards the horizon, cinematic composition, detailed background.",
        },
        {
            "panel_number": 2,
            "title": "An Unexpected Discovery",
            "scene_description": f"While exploring {setting}, {character_name} uncovers something surprising that changes everything.",
            "image_prompt": f"{art_style} illustration of {character_name} discovering a glowing mysterious artifact in {setting}, dramatic lighting, close-up perspective.",
        },
        {
            "panel_number": 3,
            "title": "The Turning Point",
            "scene_description": f"The story reaches its peak as {character_name} confronts the central challenge in {setting}.",
            "image_prompt": f"High energy {art_style} comic action panel of {character_name} overcoming a major obstacle in {setting}, dynamic angles, vibrant effects.",
        },
        {
            "panel_number": 4,
            "title": "A Flash of Brilliance",
            "scene_description": f"Using quick thinking and courage, {character_name} finds the solution to resolve the challenge.",
            "image_prompt": f"{art_style} artwork of {character_name} executing a clever plan in {setting}, glowing determination, triumphant expression.",
        },
        {
            "panel_number": 5,
            "title": "The Dawn of a New Legend",
            "scene_description": f"With peace restored in {setting}, {character_name} celebrates the successful journey with a {tone.lower()} spirit.",
            "image_prompt": f"Heartwarming {art_style} final panel of {character_name} smiling warmly at sunset in {setting}, iconic comic book ending pose.",
        },
    ]

