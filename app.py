import streamlit as st

from database.supabase_client import supabase, is_configured
from utils.theme import inject_theme
from components.auth_forms import show_auth_screen
from components.navbar import render_sidebar_nav

from app_pages.dashboard import show_dashboard
from app_pages.wardrobe import show_wardrobe
from app_pages.stylist import show_stylist
from app_pages.outfit_builder import show_outfit_builder
from app_pages.saved_looks import show_saved_looks
from app_pages.planner import show_planner
from app_pages.packing import show_packing
from app_pages.profile import show_profile

# -----------------------------
# Page config (must be first Streamlit call)
# -----------------------------
st.set_page_config(
    page_title="Lumi Closet",
    page_icon="🩷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_theme()

# -----------------------------
# Session state
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

PAGES = {
    "dashboard": show_dashboard,
    "wardrobe": show_wardrobe,
    "stylist": show_stylist,
    "outfit_builder": show_outfit_builder,
    "saved_looks": show_saved_looks,
    "planner": show_planner,
    "packing": show_packing,
    "profile": show_profile,
}

# =====================================================
# LOGIN / SIGNUP
# =====================================================
if not st.session_state.logged_in or not st.session_state.user:
    show_auth_screen()

# =====================================================
# APP
# =====================================================
else:
    render_sidebar_nav()

    if not is_configured():
        st.error("Lumi Closet isn't connected to a database. Add your Supabase credentials to continue.")
    else:
        page_fn = PAGES.get(st.session_state.page, show_dashboard)
        try:
            page_fn()
        except Exception as e:
            st.error("Something went wrong loading this page.")
            st.caption(str(e))
            if st.button("⬅ Back to Home"):
                st.session_state.page = "dashboard"
                st.rerun()
