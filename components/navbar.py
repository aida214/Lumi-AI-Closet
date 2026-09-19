import streamlit as st
from database.supabase_client import supabase

NAV_ITEMS = [
    ("dashboard", "🏠", "Home"),
    ("wardrobe", "👗", "Wardrobe"),
    ("stylist", "🤖", "AI Stylist"),
    ("outfit_builder", "🎀", "Outfit Builder"),
    ("saved_looks", "🩷", "Saved Looks"),
    ("planner", "📅", "Planner"),
    ("packing", "🧳", "Packing"),
    ("profile", "✨", "Profile"),
]


def go(page: str):
    st.session_state["page"] = page
    st.rerun()


def render_sidebar_nav():
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding: 6px 0 18px 0;">
                <div style="font-family:'Fraunces',serif; font-size:1.5rem; color:#2B2330;">
                    🩷 Lumi Closet
                </div>
                <div class="lc-muted" style="font-size:0.78rem;">AI fashion companion</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current = st.session_state.get("page", "dashboard")

        for key, icon, label in NAV_ITEMS:
            is_active = current == key
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                go(key)

        st.markdown("<div class='lc-divider'></div>", unsafe_allow_html=True)

        user = st.session_state.get("user")
        display_name = getattr(user, "email", None) or "you"
        st.caption(f"Signed in as {display_name}")

        if st.button("🚪  Log out", use_container_width=True):
            try:
                if supabase:
                    supabase.auth.sign_out()
            except Exception:
                pass
            for k in ("logged_in", "user", "page"):
                st.session_state.pop(k, None)
            st.rerun()
