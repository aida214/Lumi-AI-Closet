"""Rule-based outfit and packing suggestions.

No machine learning here on purpose: the rules are easy to explain and test.
Each piece gets a score from season fit, occasion fit, the user's favourite
aesthetics, how recently it was worn and a little randomness. The best top and
bottom (or dress) are then matched using simple colour rules.
"""
import math
import random
from datetime import date

from utils.colors import outfit_harmony, pair_score
from utils.constants import CATEGORIES

OCCASION_STYLES = {
    "Everyday": None,
    "Campus": ["Casual", "Minimalist", "Streetwear", "Sporty", "Vintage", "Y2K", "Coquette"],
    "Work": ["Formal", "Minimalist", "Old Money"],
    "Evening": ["Formal", "Coquette", "Old Money", "Y2K", "Vintage", "Minimalist"],
    "Weekend": ["Casual", "Streetwear", "Vintage", "Y2K", "Coquette", "Sporty", "Minimalist"],
    "Workout": ["Sporty"],
}


def preferred_seasons(temp_c):
    if temp_c is None:
        return []
    if temp_c >= 26:
        return ["Summer"]
    if temp_c >= 20:
        return ["Summer", "Spring"]
    if temp_c >= 12:
        return ["Spring", "Autumn"]
    if temp_c >= 5:
        return ["Autumn", "Winter"]
    return ["Winter"]


def needs_outerwear(temp_c, rain_chance):
    if temp_c is None or temp_c >= 24:
        return False
    return temp_c <= 17 or (rain_chance or 0) >= 60


def score_item(item, temp_c, occasion, preferred_styles, wear, today, rng):
    score = 0.0
    season = item.get("season") or "All Season"
    if temp_c is not None:
        if season == "All Season":
            score += 0.5
        elif season in preferred_seasons(temp_c):
            score += 2.0
        else:
            score -= 2.5
    allowed = OCCASION_STYLES.get(occasion)
    style = item.get("style")
    if allowed and style:
        score += 2.0 if style in allowed else -2.5
    if preferred_styles and style in preferred_styles:
        score += 1.0
    if item.get("favorite"):
        score += 0.5
    info = (wear or {}).get(item["id"])
    last = info.get("last") if info else None
    if last is None:
        score += 1.5
    else:
        days = (today - last).days
        score += min(max(days, 0), 30) / 30 * 1.5
        if days <= 1:
            score -= 1.5
    return score + rng.uniform(0, 1.0)


def _avg_harmony(item, others):
    colors = [o.get("color") for o in others if o and o.get("color")]
    if not item.get("color") or not colors:
        return 0.0
    return sum(pair_score(item["color"], c) for c in colors) / len(colors)


def _rank(items, **ctx):
    ranked = [(score_item(i, **ctx), i) for i in items]
    return sorted(ranked, key=lambda pair: -pair[0])


def suggest_outfit(items, temp_c=None, rain_chance=None, occasion="Everyday",
                   seed=0, preferred_styles=None, wear=None, today=None):
    """Return {"items": {slot: item}, "reasons": [str], "missing": str}."""
    today = today or date.today()
    rng = random.Random(seed)
    items = sorted(items, key=lambda i: str(i["id"]))
    ctx = dict(temp_c=temp_c, occasion=occasion, preferred_styles=preferred_styles,
               wear=wear, today=today, rng=rng)
    ranked = {cat: _rank([i for i in items if i.get("category") == cat], **ctx)
              for cat in CATEGORIES}

    best_pair = None
    for s_top, top in ranked["Top"][:8]:
        for s_bottom, bottom in ranked["Bottom"][:8]:
            value = (s_top + s_bottom) / 2 + pair_score(top.get("color"), bottom.get("color"))
            if best_pair is None or value > best_pair[0]:
                best_pair = (value, top, bottom)
    best_dress = ranked["Dress"][0] if ranked["Dress"] and occasion != "Workout" else None

    if best_pair is None and best_dress is None:
        return {"items": {}, "reasons": [],
                "missing": "Add at least one top and one bottom, or a dress, and Lumi can suggest outfits."}

    chosen = {}
    if best_dress and (best_pair is None or best_dress[0] + 0.5 > best_pair[0]):
        chosen["dress"] = best_dress[1]
    else:
        chosen["top"], chosen["bottom"] = best_pair[1], best_pair[2]
    base = list(chosen.values())

    def add(slot, category):
        pool = ranked[category]
        if not pool:
            return
        best = max(pool[:10], key=lambda p: p[0] + _avg_harmony(p[1], base))
        chosen[slot] = best[1]

    add("shoes", "Shoes")
    outer_needed = needs_outerwear(temp_c, rain_chance)
    if outer_needed:
        add("outerwear", "Outerwear")
    add("accessory", "Accessory")

    reasons = []
    if temp_c is not None:
        reasons.append(f"Chosen for about {round(temp_c)}\u00b0C.")
    if outer_needed:
        reasons.append("Added a layer for the cool or wet weather."
                       if "outerwear" in chosen else
                       "It is cool or wet today and there is no outerwear in your closet yet.")
    if occasion != "Everyday":
        reasons.append(f"Leaning towards styles that suit {occasion.lower()}.")
    _avg, note = outfit_harmony([p.get("color") for p in chosen.values()])
    if note:
        reasons.append(note)
    fresh = [p for p in chosen.values()
             if not (wear or {}).get(p["id"]) or (today - wear[p["id"]]["last"]).days >= 14]
    if fresh:
        reasons.append("Includes pieces you have not worn in a while.")
    return {"items": chosen, "reasons": reasons, "missing": ""}


PACK_TRIP_OCCASION = {
    "Casual": "Everyday", "City break": "Everyday", "Business": "Work",
    "Beach": "Weekend", "Formal event": "Evening", "Active": "Workout",
}


def build_packing_list(items, days, temp_c=None, rain_chance=None,
                       trip_type="Casual", seed=0, preferred_styles=None,
                       wear=None, today=None):
    """Pick how many of each category to pack, then the best-scoring pieces."""
    today = today or date.today()
    occasion = PACK_TRIP_OCCASION.get(trip_type, "Everyday")
    rng = random.Random(seed)
    items = sorted(items, key=lambda i: str(i["id"]))
    ctx = dict(temp_c=temp_c, occasion=occasion, preferred_styles=preferred_styles,
               wear=wear, today=today, rng=rng)

    outer_needed = needs_outerwear(temp_c, rain_chance)
    counts = {
        "Top": min(7, max(2, math.ceil(days * 0.75))),
        "Bottom": min(4, max(1, math.ceil(days / 3))),
        "Dress": 0 if occasion == "Workout" else min(3, days // 3),
        "Outerwear": (2 if days > 7 else 1) if outer_needed else 0,
        "Shoes": 3 if days > 7 else 2,
        "Accessory": min(3, max(1, days // 3)),
    }
    packed, notes = {}, []
    for category, want in counts.items():
        pool = _rank([i for i in items if i.get("category") == category], **ctx)
        packed[category] = [item for _score, item in pool[:want]]
        if want and len(pool) < want:
            notes.append(f"You have {len(pool)} {category.lower()} item(s) in your closet but "
                         f"about {want} would suit this trip.")
    if outer_needed and not packed["Outerwear"]:
        notes.append("Expect cool or wet weather. Consider adding a jacket to your closet.")
    combos = len(packed["Top"]) * len(packed["Bottom"]) + len(packed["Dress"])
    return {"packed": packed, "notes": notes, "combos": combos}
