"""
AI auto-tagging for a freshly uploaded clothing photo.

Uses Google Gemini's vision model to guess name/category/color/season/
style/brand from the image, matching the original project's behaviour
(the old debug prints referenced "GEMINI RETURNED"). If no API key is
configured, or the call fails for any reason, this returns an empty
tag dict rather than raising -- upload_form.py treats that as "AI
couldn't tag this, please fill it in yourself" and the rest of the app
keeps working.
"""

import os
import json
import streamlit as st

EMPTY_TAGS = {
    "name": "",
    "category": "",
    "color": "",
    "season": "",
    "style": "",
    "brand": "",
}


def _get_key() -> str | None:
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY")


def analyse_clothing(image_bytes: bytes) -> dict:
    """Best-effort AI tagging. Never raises -- returns EMPTY_TAGS on any failure."""

    api_key = _get_key()
    if not api_key:
        return dict(EMPTY_TAGS)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = (
            "Look at this photo of a single clothing item. Reply with ONLY a "
            "compact JSON object, no markdown fences, with these exact keys: "
            'name (short product-style name), category (one of: Top, Bottom, '
            'Dress, Outerwear, Shoes, Accessory), color (one main colour), '
            'season (one of: Spring, Summer, Autumn, Winter, All Season), '
            'style (one of: Casual, Formal, Streetwear, Coquette, Old Money, '
            'Minimalist, Y2K, Sporty, Vintage), brand (empty string if not '
            "visible). If you can't tell, use your best guess rather than "
            "leaving a field blank."
        )

        response = model.generate_content(
            [prompt, {"mime_type": "image/jpeg", "data": image_bytes}]
        )

        text = (response.text or "").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        tags = json.loads(text)
        return {**EMPTY_TAGS, **{k: v for k, v in tags.items() if k in EMPTY_TAGS}}

    except Exception:
        return dict(EMPTY_TAGS)
