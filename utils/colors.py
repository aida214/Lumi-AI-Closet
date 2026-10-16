"""Colour names, colour harmony rules and dominant colour detection."""
import io
import re

import numpy as np
from PIL import Image

# name: (rgb, family)
NAMED = {
    "black": ((30, 30, 30), "neutral"),
    "white": ((245, 245, 245), "neutral"),
    "cream": ((243, 232, 208), "neutral"),
    "beige": ((222, 201, 171), "neutral"),
    "grey": ((150, 150, 150), "neutral"),
    "charcoal": ((70, 70, 72), "neutral"),
    "navy": ((28, 38, 88), "neutral"),
    "denim": ((88, 118, 160), "neutral"),
    "brown": ((105, 70, 48), "earth"),
    "tan": ((190, 150, 100), "earth"),
    "camel": ((190, 140, 80), "earth"),
    "khaki": ((190, 176, 122), "earth"),
    "olive": ((110, 115, 60), "earth"),
    "red": ((200, 38, 48), "warm"),
    "burgundy": ((112, 26, 46), "warm"),
    "orange": ((236, 130, 48), "warm"),
    "mustard": ((205, 160, 40), "warm"),
    "yellow": ((242, 212, 70), "warm"),
    "coral": ((240, 125, 110), "warm"),
    "hot pink": ((228, 60, 140), "warm"),
    "pink": ((240, 160, 190), "pastel"),
    "blush": ((240, 200, 206), "pastel"),
    "peach": ((250, 205, 170), "pastel"),
    "lavender": ((190, 172, 222), "pastel"),
    "baby blue": ((165, 205, 238), "pastel"),
    "mint": ((180, 225, 202), "pastel"),
    "sage": ((160, 182, 150), "pastel"),
    "blue": ((52, 100, 200), "cool"),
    "teal": ((38, 128, 130), "cool"),
    "green": ((60, 140, 78), "cool"),
    "purple": ((108, 60, 150), "cool"),
}

ALIASES = {
    "gray": "grey", "silver": "grey", "ivory": "cream", "off white": "cream",
    "offwhite": "cream", "nude": "beige", "sand": "beige", "taupe": "beige",
    "maroon": "burgundy", "wine": "burgundy", "rose": "pink",
    "light pink": "pink", "baby pink": "pink", "navy blue": "navy",
    "dark blue": "navy", "light blue": "baby blue", "sky blue": "baby blue",
    "royal blue": "blue", "turquoise": "teal", "lilac": "lavender",
    "violet": "purple", "magenta": "hot pink", "fuchsia": "hot pink",
    "gold": "mustard", "jeans": "denim", "light denim": "denim",
    "forest green": "green", "dark green": "green", "emerald": "green",
    "lime": "green", "chocolate": "brown", "mocha": "brown", "rust": "orange",
}

# Longest phrases first so "hot pink" wins over "pink".
_PHRASES = sorted(set(NAMED) | set(ALIASES), key=len, reverse=True)


def normalise_color(text):
    """Turn free text such as 'Light Blue striped' into a known colour name."""
    if not text:
        return None
    cleaned = re.sub(r"[^a-z ]", " ", str(text).lower().replace("-", " "))
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        return None
    for phrase in _PHRASES:
        if re.search(r"\b" + re.escape(phrase) + r"\b", cleaned):
            return ALIASES.get(phrase, phrase)
    return None


def color_family(name):
    return NAMED[name][1] if name in NAMED else None


def pair_score(a, b):
    """How well two colours sit together, from -1 (clash) to 1 (easy)."""
    a, b = normalise_color(a), normalise_color(b)
    if a is None or b is None:
        return 0.0
    fa, fb = color_family(a), color_family(b)
    if fa == "neutral" or fb == "neutral":
        return 1.0
    if a == b:
        return 0.8
    if fa == fb:
        return 0.7
    pair = {fa, fb}
    if pair == {"pastel", "earth"} or pair == {"earth", "warm"}:
        return 0.4
    if pair == {"pastel", "cool"} or pair == {"pastel", "warm"}:
        return 0.3
    if pair == {"earth", "cool"}:
        return 0.2
    if pair == {"warm", "cool"}:
        return -0.6
    return 0.0


def compatible_colors(name):
    name = normalise_color(name)
    if name is None:
        return []
    return [n for n in NAMED if n != name and pair_score(name, n) >= 0.7]


def outfit_harmony(colors):
    """Average pair score for a list of colours, plus a short plain note."""
    names = [normalise_color(c) for c in colors]
    names = [n for n in names if n]
    if len(names) < 2:
        return 0.0, ""
    scores = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            scores.append(pair_score(names[i], names[j]))
    avg = sum(scores) / len(scores)
    if all(color_family(n) == "neutral" for n in names):
        note = "All neutrals, so this palette is easy to wear."
    elif avg >= 0.7:
        note = "These colours sit well together."
    elif avg < 0:
        note = "Warm and cool tones are competing. A neutral piece would calm it down."
    else:
        note = "A workable mix. Keep the accessories simple."
    return avg, note


# ---- colour from a photo -------------------------------------------------

def _srgb_to_lab(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(c) for c in rgb)
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


_LAB = {name: _srgb_to_lab(rgb) for name, (rgb, _fam) in NAMED.items()}


def nearest_color_name(rgb):
    lab = _srgb_to_lab(tuple(float(c) for c in rgb))
    best, best_d = None, None
    for name, ref in _LAB.items():
        d = sum((a - b) ** 2 for a, b in zip(lab, ref))
        if best_d is None or d < best_d:
            best, best_d = name, d
    return best


def dominant_color_name(image_bytes):
    """Name the main colour of the garment in a photo, or None on failure."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return None
    img.thumbnail((96, 96))
    px = np.asarray(img).astype(int)
    flat = px.reshape(-1, 3)
    # Treat the median colour of the border as the background.
    border = np.concatenate([px[0, :], px[-1, :], px[:, 0], px[:, -1]])
    background = np.median(border, axis=0)
    distance = np.sqrt(((flat - background) ** 2).sum(axis=1))
    foreground = flat[distance > 40]
    if len(foreground) < 0.04 * len(flat):
        foreground = flat  # plain photo, or garment close to the background
    bins = foreground // 32
    keys = bins[:, 0] * 64 + bins[:, 1] * 8 + bins[:, 2]
    most_common = np.bincount(keys).argmax()
    members = foreground[keys == most_common]
    return nearest_color_name(members.mean(axis=0))
