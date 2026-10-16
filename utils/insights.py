"""Closet statistics. Pure functions so they are easy to test."""
from collections import Counter
from datetime import date, datetime, timedelta


def parse_day(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def wear_summary(rows):
    """{item_id: {"count": n, "last": date}} from wear_log rows."""
    summary = {}
    for row in rows or []:
        item_id = row.get("wardrobe_item_id")
        day = parse_day(row.get("worn_on"))
        if not item_id or not day:
            continue
        entry = summary.setdefault(item_id, {"count": 0, "last": day})
        entry["count"] += 1
        if day > entry["last"]:
            entry["last"] = day
    return summary


def _title(counter):
    return {str(k): v for k, v in counter.most_common() if k}


def compute_insights(items, wear, today):
    total = len(items)
    cutoff = today - timedelta(days=30)
    worn_recent = [i for i in items if wear.get(i["id"]) and wear[i["id"]]["last"] >= cutoff]
    never = [i for i in items if i["id"] not in wear]
    idle = []
    for item in items:
        info = wear.get(item["id"])
        last = info["last"] if info else parse_day(item.get("created_at"))
        if last and last < cutoff:
            idle.append((item, (today - last).days, info is None))
    idle.sort(key=lambda row: -row[1])

    most_worn = sorted(
        (i for i in items if i["id"] in wear),
        key=lambda i: (-wear[i["id"]]["count"], i.get("name") or ""),
    )[:5]

    cost_per_wear = []
    for item in items:
        price = item.get("price")
        info = wear.get(item["id"])
        if price and info and info["count"] > 0:
            cost_per_wear.append((item, float(price) / info["count"]))
    cost_per_wear.sort(key=lambda row: row[1])

    by_category = Counter(i.get("category") for i in items)
    tips = []
    tops, bottoms = by_category.get("Top", 0), by_category.get("Bottom", 0)
    if total and bottoms == 0 and by_category.get("Dress", 0) == 0:
        tips.append("You have no bottoms or dresses yet, so outfits cannot be built.")
    elif bottoms and tops / bottoms >= 3:
        tips.append(f"You own {tops} tops for {bottoms} bottoms. One or two more bottoms "
                    "would multiply your outfit options.")
    elif tops and bottoms == 0:
        tips.append("Add a few bottoms to pair with your tops.")
    if total >= 5 and by_category.get("Shoes", 0) == 0:
        tips.append("No shoes added yet. Outfit suggestions are more complete with them.")
    if total >= 8 and by_category.get("Outerwear", 0) == 0:
        tips.append("There is no outerwear in your closet, so cold or rainy days cannot be covered.")
    if total >= 5 and len(never) / total >= 0.5:
        tips.append(f"{len(never)} of your {total} pieces have never been logged as worn. "
                    "Use 'Wore it today' to start tracking.")

    return {
        "total": total,
        "favourites": sum(1 for i in items if i.get("favorite")),
        "worn_30": len(worn_recent),
        "never_worn": len(never),
        "idle": idle,
        "most_worn": most_worn,
        "cost_per_wear": cost_per_wear,
        "by_category": _title(by_category),
        "by_color": _title(Counter((i.get("color") or "").strip().lower() for i in items)),
        "by_style": _title(Counter(i.get("style") for i in items)),
        "tips": tips,
    }
