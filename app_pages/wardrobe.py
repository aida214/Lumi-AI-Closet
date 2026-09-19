import streamlit as st

from database.supabase_client import supabase
from components.upload_form import upload_form
from components.clothing_card import clothing_card
from components.metrics import stat_row
from utils.theme import section_title, empty_state

CATEGORIES = ["All", "Top", "Bottom", "Dress", "Outerwear", "Shoes", "Accessory"]
STYLES = [
    "All", "Casual", "Formal", "Streetwear", "Coquette", "Old Money",
    "Minimalist", "Y2K", "Sporty", "Vintage",
]
SEASONS = ["All", "Spring", "Summer", "Autumn", "Winter", "All Season"]


@st.cache_data(ttl=30, show_spinner=False)
def _load_wardrobe(user_id: str):
    response = (
        supabase.table("wardrobe")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def show_wardrobe():
    section_title("YOUR CLOSET", "My Wardrobe", "Every piece you own, beautifully organized.")

    user_id = str(st.session_state["user"].id)

    try:
        clothes = _load_wardrobe(user_id)
    except Exception as e:
        st.error(f"Could not load wardrobe: {e}")
        return

    def refresh():
        _load_wardrobe.clear()

    # ---------------- Statistics ----------------
    total_items = len(clothes)
    favorites = sum(1 for item in clothes if item.get("favorite", False))
    tops = sum(1 for item in clothes if item.get("category") == "Top")
    bottoms = sum(1 for item in clothes if item.get("category") == "Bottom")

    stat_row(
        [
            ("Items", str(total_items), "👗"),
            ("Favorites", str(favorites), "❤️"),
            ("Tops", str(tops), "👚"),
            ("Bottoms", str(bottoms), "👖"),
        ]
    )

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("➕ Add new clothing", expanded=False):
        upload_form(on_saved=refresh)

    st.markdown("<div class='lc-divider'></div>", unsafe_allow_html=True)

    if total_items == 0:
        empty_state("🩷", "Your wardrobe is empty", "Upload your first clothing item to start building your digital closet.")
        return

    # ---------------- Search + filters ----------------
    search = st.text_input(
        "🔍 Search", placeholder="Name, brand, colour, style...", label_visibility="collapsed"
    )

    colors_available = sorted({item.get("color") for item in clothes if item.get("color")})

    c1, c2, c3 = st.columns(3)
    with c1:
        category_filter = st.selectbox("Category", CATEGORIES)
    with c2:
        style_filter = st.selectbox("Style", STYLES)
    with c3:
        color_filter = st.selectbox("Colour", ["All"] + colors_available)

    season_filter = st.selectbox("Season", SEASONS)

    filtered = clothes

    if search:
        s = search.lower()
        filtered = [
            item for item in filtered
            if s in (item.get("name") or "").lower()
            or s in (item.get("brand") or "").lower()
            or s in (item.get("color") or "").lower()
            or s in (item.get("style") or "").lower()
            or s in (item.get("category") or "").lower()
        ]

    if category_filter != "All":
        filtered = [item for item in filtered if item.get("category") == category_filter]

    if style_filter != "All":
        filtered = [item for item in filtered if item.get("style") == style_filter]

    if color_filter != "All":
        filtered = [item for item in filtered if item.get("color") == color_filter]

    if season_filter != "All":
        filtered = [item for item in filtered if item.get("season") == season_filter]

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"#### 🩷 My closet ({len(filtered)})")

    if len(filtered) == 0:
        empty_state("🔍", "No matches", "Try adjusting your search or filters.")
        return

    left, right = st.columns(2, gap="large")
    for index, item in enumerate(filtered):
        with (left if index % 2 == 0 else right):
            clothing_card(item, on_change=refresh)

    st.markdown("<br><br>", unsafe_allow_html=True)
