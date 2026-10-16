"""Stylist replies: OpenAI when a key is set, rule-based otherwise."""
import re

from utils.colors import compatible_colors, normalise_color, pair_score
from utils.config import get_setting
from utils.logging_config import get_logger
from utils.outfit_engine import suggest_outfit

log = get_logger("stylist")

DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"

SYSTEM_PROMPT = (
    "You are Lumi, a practical personal stylist inside a wardrobe app. "
    "Answer in 2 to 5 short sentences. Prefer pieces from the user's own closet, "
    "named exactly as listed. Say so plainly if the closet lacks what is needed. "
    "Do not use emoji or markdown headings."
)

OCCASION_WORDS = {
    "Campus": ["campus", "class", "university", "lecture", "college"],
    "Work": ["work", "office", "interview", "meeting"],
    "Evening": ["date", "dinner", "party", "night", "evening", "wedding"],
    "Workout": ["gym", "workout", "run", "yoga", "training"],
    "Weekend": ["weekend", "brunch", "coffee", "shopping", "casual"],
}


def ai_available():
    return bool(get_setting("OPENAI_API_KEY"))


def closet_summary(items, limit=60):
    lines = []
    for item in items[:limit]:
        lines.append(
            f"- {item.get('name') or item.get('category')} "
            f"({item.get('category')}, {item.get('color') or 'colour unknown'}, "
            f"{item.get('season') or 'any season'}, {item.get('style') or 'no style'})"
        )
    return "\n".join(lines) if lines else "The closet is empty."


def ask_ai(question, history, items, weather_text="", aesthetics=""):
    """Return the model's reply, or None if the call fails."""
    api_key = get_setting("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=30)
        context = (
            f"Closet:\n{closet_summary(items)}\n\n"
            f"Weather today: {weather_text or 'unknown'}\n"
            f"Favourite aesthetics: {aesthetics or 'not set'}"
        )
        messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context}]
        for msg in history[-8:]:
            messages.append({"role": msg["role"], "content": msg["message"]})
        messages.append({"role": "user", "content": question})
        response = client.chat.completions.create(
            model=get_setting("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            messages=messages,
            max_completion_tokens=1000,
        )
        text = (response.choices[0].message.content or "").strip()
        return text or None
    except Exception as exc:
        log.warning("OpenAI request failed: %s", exc)
        return None


def _names(chosen):
    return ", ".join(f"{p.get('name') or p.get('category')} ({p.get('color') or 'no colour set'})"
                     for p in chosen.values())


def basic_reply(question, items, temp_c=None, rain_chance=None,
                preferred_styles=None, wear=None, seed=0, today=None):
    """Rule-based answer built from the user's real closet."""
    q = question.lower()

    for word in re.findall(r"[a-z]+(?: [a-z]+)?", q):
        colour = normalise_color(word)
        if colour and ("match" in q or "goes with" in q or "go with" in q or "pair" in q):
            good = compatible_colors(colour)
            owned = [i for i in items if i.get("color") and pair_score(colour, i["color"]) >= 0.7
                     and normalise_color(i["color"]) != colour]
            text = f"{colour.title()} pairs easily with {', '.join(good[:6])}."
            if owned:
                text += " From your closet: " + ", ".join(
                    i.get("name") or i.get("category") for i in owned[:5]) + "."
            return text

    if any(w in q for w in ["pack", "trip", "travel", "suitcase"]):
        return "Open the Packing page, enter your destination and dates, and Lumi will build a list from your closet."

    occasion = "Everyday"
    for name, words in OCCASION_WORDS.items():
        if any(w in q for w in words):
            occasion = name
            break

    result = suggest_outfit(items, temp_c=temp_c, rain_chance=rain_chance, occasion=occasion,
                            seed=seed, preferred_styles=preferred_styles, wear=wear, today=today)
    if result["missing"]:
        return result["missing"]
    lead = "Here is an outfit for today" if occasion == "Everyday" else f"Here is an outfit for {occasion.lower()}"
    return f"{lead}: {_names(result['items'])}. " + " ".join(result["reasons"][:3])
