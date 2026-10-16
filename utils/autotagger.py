"""Suggest tags for a clothing photo.

Order of attempts:
1. Gemini (google-genai SDK) when GEMINI_API_KEY is set.
2. Dominant colour from the pixels, which needs no API at all.

The function never raises. The caller gets whatever could be worked out and
a short source label so the interface can be honest about it.
"""
import json

from utils.colors import dominant_color_name
from utils.config import get_setting
from utils.constants import CATEGORIES, SEASONS, STYLES
from utils.logging_config import get_logger

log = get_logger("autotagger")

# "gemini-flash-latest" is an alias, so the app does not break each time
# Google retires a dated model. Override with GEMINI_MODEL if you want to pin one.
DEFAULT_GEMINI_MODEL = "gemini-flash-latest"

PROMPT = (
    "You are tagging one photo of a single clothing item for a wardrobe app. "
    "Reply with JSON only, using exactly these keys: "
    '"name" (short, 2 to 5 words), '
    f'"category" (one of {CATEGORIES}), '
    '"color" (one or two plain colour words), '
    f'"season" (one of {SEASONS}), '
    f'"style" (one of {STYLES}), '
    '"brand" (only if clearly visible, otherwise an empty string).'
)


def _clean(tags):
    """Keep only values the app understands."""
    def pick(value, options):
        for option in options:
            if str(value).strip().lower() == option.lower():
                return option
        return ""

    return {
        "name": str(tags.get("name", "")).strip()[:60],
        "category": pick(tags.get("category", ""), CATEGORIES),
        "color": str(tags.get("color", "")).strip().lower()[:30],
        "season": pick(tags.get("season", ""), SEASONS),
        "style": pick(tags.get("style", ""), STYLES),
        "brand": str(tags.get("brand", "")).strip()[:40],
    }


def _ask_gemini(image_bytes):
    api_key = get_setting("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=20000),
        )
        response = client.models.generate_content(
            model=get_setting("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                PROMPT,
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        text = (response.text or "").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(text)
        if isinstance(data, list) and data:
            data = data[0]
        return _clean(data) if isinstance(data, dict) else None
    except Exception as exc:
        log.warning("Gemini tagging failed: %s", exc)
        return None


def analyse_clothing(image_bytes):
    """Return (tags, source) where source is 'ai', 'colour' or 'none'."""
    tags = _ask_gemini(image_bytes)
    if tags:
        if not tags["color"]:
            tags["color"] = dominant_color_name(image_bytes) or ""
        return tags, "ai"
    color = dominant_color_name(image_bytes)
    if color:
        return {"name": "", "category": "", "color": color, "season": "",
                "style": "", "brand": ""}, "colour"
    return {"name": "", "category": "", "color": "", "season": "",
            "style": "", "brand": ""}, "none"
