import streamlit as st

from database.supabase_client import supabase
from utils.theme import section_title, empty_state

WEATHER_OPTIONS = ["Warm & Sunny", "Mild", "Cold", "Rainy", "Mixed"]
TRIP_TYPES = ["Casual", "Business", "Beach", "City Break", "Formal Event", "Outdoor / Active"]

WEATHER_CATEGORY_HINTS = {
    "Warm & Sunny": {"season": ["Summer", "All Season"], "avoid_category": ["Outerwear"]},
    "Mild": {"season": ["Spring", "Autumn", "All Season"], "avoid_category": []},
    "Cold": {"season": ["Winter", "All Season"], "avoid_category": []},
    "Rainy": {"season": ["Autumn", "Winter", "All Season"], "avoid_category": []},
    "Mixed": {"season": ["All Season"], "avoid_category": []},
}


def _load_wardrobe(user_id: str):
    try:
        resp = supabase.table("wardrobe").select("*").eq("user_id", user_id).execute()
        return resp.data or []
    except Exception:
        return []


def _suggest_items(clothes: list, weather: str, days: int):
    hint = WEATHER_CATEGORY_HINTS.get(weather, {})
    seasons_ok = hint.get("season", [])
    avoid = hint.get("avoid_category", [])

    def fits(item):
        if item.get("category") in avoid:
            return False
        if seasons_ok and item.get("season") not in seasons_ok and item.get("season") != "All Season":
            return False
        return True

    pool = [i for i in clothes if fits(i)] or clothes

    by_cat = {}
    for item in pool:
        by_cat.setdefault(item.get("category"), []).append(item)

    outfits_needed = min(max(days, 1), 7)

    suggestion = {
        "tops": by_cat.get("Top", [])[:outfits_needed],
        "bottoms": by_cat.get("Bottom", [])[: max(2, outfits_needed // 2)],
        "dresses": by_cat.get("Dress", [])[: max(1, outfits_needed // 3)],
        "outerwear": by_cat.get("Outerwear", [])[:2],
        "shoes": by_cat.get("Shoes", [])[:2],
        "accessories": by_cat.get("Accessory", [])[:3],
    }
    return suggestion, outfits_needed


def show_packing():
    section_title("TRIP READY", "Packing Assistant", "Tell Lumi about your trip and get a packing list from your own closet.")

    user_id = str(st.session_state["user"].id)
    clothes = _load_wardrobe(user_id)

    if not clothes:
        empty_state("🧳", "Nothing to pack yet", "Add some pieces to your wardrobe first, then come back to plan your trip.")
        return

    st.markdown('<div class="lc-card">', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        destination = st.text_input("📍 Destination", placeholder="e.g. Seoul, South Korea")
        days = st.number_input("🗓️ Number of days", min_value=1, max_value=30, value=4)
    with c2:
        weather = st.selectbox("☁️ Weather", WEATHER_OPTIONS)
        trip_type = st.selectbox("🎒 Trip type", TRIP_TYPES)

    generate = st.button("✨ Suggest what to pack", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if generate:
        suggestion, outfits_needed = _suggest_items(clothes, weather, int(days))
        st.session_state["packing_suggestion"] = suggestion
        st.session_state["packing_outfits_needed"] = outfits_needed
        st.session_state["packing_context"] = {
            "destination": destination, "days": days, "weather": weather, "trip_type": trip_type,
        }
        st.session_state.setdefault("packed_ids", set())

    suggestion = st.session_state.get("packing_suggestion")

    if not suggestion:
        return

    ctx = st.session_state.get("packing_context", {})
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"#### 🧳 Packing list for {ctx.get('destination') or 'your trip'} "
        f"— {ctx.get('days')} days, {ctx.get('trip_type', '').lower()}"
    )
    st.caption(f"Roughly {st.session_state.get('packing_outfits_needed', '')} outfits suggested.")

    packed_ids = st.session_state.setdefault("packed_ids", set())

    labels = {
        "tops": "👚 Tops", "bottoms": "👖 Bottoms", "dresses": "👗 Dresses",
        "outerwear": "🧥 Outerwear", "shoes": "👟 Shoes", "accessories": "👜 Accessories",
    }

    total_suggested = sum(len(v) for v in suggestion.values())
    if total_suggested == 0:
        st.info("Not enough wardrobe variety for this weather yet — add more pieces for better suggestions.")

    for key, label in labels.items():
        items = suggestion.get(key, [])
        if not items:
            continue
        st.markdown(f"**{label}**")
        cols = st.columns(min(4, len(items)))
        for col, item in zip(cols, items):
            with col:
                st.markdown('<div class="lc-card" style="padding:8px;">', unsafe_allow_html=True)
                if item.get("image_url"):
                    st.image(item["image_url"], use_container_width=True)
                st.caption(item.get("name") or item.get("category"))
                packed = item["id"] in packed_ids
                if st.checkbox("Packed", value=packed, key=f"pack_{key}_{item['id']}"):
                    packed_ids.add(item["id"])
                else:
                    packed_ids.discard(item["id"])
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='lc-divider'></div>", unsafe_allow_html=True)
    st.markdown("**🧴 Essentials checklist**")
    essentials = ["Toiletries", "Chargers", "Travel documents", "Medication", "Sleepwear", "Underwear & socks"]
    ecols = st.columns(3)
    for i, essential in enumerate(essentials):
        with ecols[i % 3]:
            st.checkbox(essential, key=f"essential_{essential}")

    st.progress(
        len(packed_ids) / total_suggested if total_suggested else 0,
        text=f"{len(packed_ids)} of {total_suggested} clothing items packed",
    )
