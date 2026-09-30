"""
ComicCraft – Layout Builder Module
Combines all panel data (outline + story + images) into a clean
layout list ready for Jinja2 template rendering.
"""


def build_comic_layout(panels: list[dict]) -> list[dict]:
    """
    Combine panel data from outline, story generation, and image generation
    into a unified list of layout objects for the template.

    Each layout item contains:
        panel_number    : int
        title           : str
        scene_description: str
        image_prompt    : str
        image_path      : str  (relative URL e.g. /static/panels/...)
        image_method    : str  ("hf_api" | "local_sd" | "placeholder")
        image_error     : str | None
        narration       : str
        dialogue        : str
        caption         : str
    """

    layout = []

    for panel in panels:
        item = {
            "panel_number": panel.get("panel_number", 0),
            "title": panel.get("title", f"Panel {panel.get('panel_number', '?')}"),
            "scene_description": panel.get("scene_description", ""),
            "image_prompt": panel.get("image_prompt", ""),
            "image_path": panel.get("image_path", "/static/panels/placeholder.png"),
            "image_method": panel.get("image_method", "placeholder"),
            "image_error": panel.get("image_error"),
            "narration": panel.get("narration", ""),
            "dialogue": _format_dialogue(panel.get("dialogue", "")),
            "caption": panel.get("caption", ""),
        }
        layout.append(item)

    return layout


def _format_dialogue(raw_dialogue: str) -> list[dict]:
    """
    Parse dialogue string into a list of {speaker, text} dicts
    for speech-bubble rendering.

    Expected format:  "CHARACTER: speech text"
    Multiple lines separated by newline characters.
    """
    if not raw_dialogue:
        return []

    bubbles = []
    for line in raw_dialogue.split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            parts = line.split(":", 1)
            speaker = parts[0].strip().upper()
            speech = parts[1].strip()
        else:
            speaker = "NARRATOR"
            speech = line
        if speech:
            bubbles.append({"speaker": speaker, "text": speech})

    return bubbles
