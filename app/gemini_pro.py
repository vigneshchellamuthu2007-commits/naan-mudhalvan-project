"""
ComicCraft – Gemini Pro Module
Generates detailed narration, dialogue, and captions for each comic panel
using Google Gemini.
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


def generate_story(
    outline: list[dict],
    character_name: str,
    setting: str,
    tone: str,
) -> list[dict]:
    """
    Take a 5-panel outline and generate rich narration, dialogue, and captions.

    Returns the same list enriched with:
      - narration (str)   – narrator voice-over for the panel
      - dialogue (str)    – character speech (with character names)
      - caption (str)     – short comic-style caption box text
    """

    _configure_gemini()

    # Build a readable outline summary for the prompt
    outline_text = ""
    for panel in outline:
        outline_text += (
            f"\nPanel {panel['panel_number']}: {panel['title']}\n"
            f"  Scene: {panel['scene_description']}\n"
        )

    system_prompt = (
        "You are a professional comic book scriptwriter. "
        "Write vivid narration, realistic dialogue, and punchy captions. "
        "Return ONLY valid JSON – no markdown fences, no extra text."
    )

    user_prompt = f"""Based on the following 5-panel comic outline, write detailed comic script elements for every panel.

Main Character: {character_name}
Setting: {setting}
Tone: {tone}

Outline:
{outline_text}

For each panel, provide:
- "panel_number": (matching the outline)
- "narration": 2-3 sentences of narrator voice-over describing the mood and action
- "dialogue": character dialogue in the format "CHARACTER: speech" (can have multiple lines separated by \\n). Use {character_name} as the main speaker.
- "caption": a short punchy caption (1 sentence max) that could appear in a caption box

Return a JSON array of 5 objects.
The story must flow consistently and keep the {tone.lower()} tone throughout.
Return ONLY the JSON array, nothing else."""

    import time
    from google.api_core.exceptions import ResourceExhausted

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    model = genai.GenerativeModel(model_name)
    
    response = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                [system_prompt, user_prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )
            break
        except ResourceExhausted:
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                raise ValueError("Google Gemini API rate limit reached (Free Tier). Please wait a few moments and try again.")
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)

    if not response:
        raise ValueError("Failed to get a response from Gemini.")

    raw_text = response.text.strip()

    # Clean markdown fences if any
    clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
    clean_text = re.sub(r"\s*```$", "", clean_text, flags=re.MULTILINE)

    # Extract JSON array using regex
    match = re.search(r"\[.*\]", clean_text, re.DOTALL)
    json_text = match.group(0) if match else clean_text

    try:
        story_data = json.loads(json_text, strict=False)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON for the story: {exc}\n\nRaw response:\n{raw_text}")

    if not isinstance(story_data, list):
        raise ValueError("Gemini story response is not a list.")

    # Merge story data into the outline
    enriched_panels = []
    for panel in outline:
        pn = panel["panel_number"]
        # Find matching story entry
        story_entry = next((s for s in story_data if s.get("panel_number") == pn), None)
        merged = {**panel}
        if story_entry:
            merged["narration"] = story_entry.get("narration", "")
            merged["dialogue"] = story_entry.get("dialogue", "")
            merged["caption"] = story_entry.get("caption", "")
        else:
            # Fallback if panel not found in story data
            merged["narration"] = f"The story of {panel['title']} unfolds..."
            merged["dialogue"] = f"{character_name}: Let's see what happens next!"
            merged["caption"] = panel["title"]
        enriched_panels.append(merged)

    return enriched_panels
