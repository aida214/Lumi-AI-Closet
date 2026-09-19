import streamlit as st

from database.supabase_client import supabase
from components.metrics import stat_row
from utils.theme import section_title

AESTHETICS = [
    "Coquette", "Old Money", "Minimalist", "Streetwear", "Y2K",
    "Sporty", "Vintage", "Casual", "Formal",
]
CATEGORY_OPTIONS = ["Top", "Bottom", "Dress", "Outerwear", "Shoes", "Accessory"]


def _load_profile(user_id: str):
    try:
        resp = supabase.table("profiles").select("*").eq("id", user_id).execute()
        return (resp.data or [{}])[0]
    except Exception:
        return {}


def _load_stats(user_id: str):
    try:
        wardrobe = supabase.table("wardrobe").select("id, favorite").eq("user_id", user_id).execute().data or []
    except Exception:
        wardrobe = []
    try:
        outfits = supabase.table("saved_outfits").select("id").eq("user_id", user_id).execute().data or []
    except Exception:
        outfits = []

    return {
        "pieces": len(wardrobe),
        "favorites": sum(1 for w in wardrobe if w.get("favorite")),
        "outfits": len(outfits),
    }


def show_profile():
    section_title("YOU", "Profile", "Your style, your stats, your Lumi Closet.")

    user = st.session_state["user"]
    user_id = str(user.id)

    profile = _load_profile(user_id)
    stats = _load_stats(user_id)

    top = st.columns([1, 3])
    with top[0]:
        st.markdown(
            """
            <div style="width:96px;height:96px;border-radius:50%;
                background:linear-gradient(135deg, var(--blush) 0%, var(--lavender) 100%);
                display:flex;align-items:center;justify-content:center;font-size:2.2rem;">
                🌸
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top[1]:
        st.markdown(f"### {profile.get('full_name') or profile.get('username') or 'Your name'}")
        st.caption(user.email if hasattr(user, "email") else "")

    st.markdown("<br>", unsafe_allow_html=True)

    stat_row(
        [
            ("Pieces", str(stats["pieces"]), "👗"),
            ("Favorites", str(stats["favorites"]), "❤️"),
            ("Outfits Created", str(stats["outfits"]), "🎀"),
        ]
    )

    st.markdown("<div class='lc-divider'></div>", unsafe_allow_html=True)

    st.markdown("#### ✨ Style preferences")

    with st.form("profile_form"):
        full_name = st.text_input("Name", value=profile.get("full_name") or "")
        username = st.text_input("Username", value=profile.get("username") or "")

        preferred_aesthetic = st.multiselect(
            "Preferred aesthetic",
            AESTHETICS,
            default=[a for a in (profile.get("preferred_aesthetic") or []) if a in AESTHETICS],
        )
        favorite_categories = st.multiselect(
            "Favorite categories",
            CATEGORY_OPTIONS,
            default=[c for c in (profile.get("favorite_categories") or []) if c in CATEGORY_OPTIONS],
        )
        favorite_colors = st.text_input(
            "Favorite colours (comma separated)",
            value=", ".join(profile.get("favorite_colors") or []),
        )

        saved = st.form_submit_button("💾 Save profile", type="primary", use_container_width=True)

        if saved:
            try:
                supabase.table("profiles").update(
                    {
                        "full_name": full_name,
                        "username": username,
                        "preferred_aesthetic": preferred_aesthetic,
                        "favorite_categories": favorite_categories,
                        "favorite_colors": [c.strip() for c in favorite_colors.split(",") if c.strip()],
                    }
                ).eq("id", user_id).execute()
                st.success("Profile updated 🩷")
                st.rerun()
            except Exception as e:
                st.error(f"Couldn't save profile: {e}")
