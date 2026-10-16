"""Lumi Closet: entry point.

Flow on every run: theme, configuration check, sign-in check, header and
navigation, then the selected page inside an error boundary.
"""
from pathlib import Path

import streamlit as st
from PIL import Image

from utils.config import get_setting
from utils.logging_config import get_logger, report_error, setup_logging

setup_logging()
log = get_logger("app")


def _favicon():
    try:
        return Image.open(Path(__file__).parent / "assets" / "favicon.png")
    except Exception:
        return None


# Must be the first Streamlit call.
st.set_page_config(page_title="Lumi Closet", page_icon=_favicon(), layout="wide",
                   initial_sidebar_state="collapsed")

from app_pages.dashboard import show_dashboard  # noqa: E402
from app_pages.insights import show_insights  # noqa: E402
from app_pages.outfit_builder import show_outfit_builder  # noqa: E402
from app_pages.packing import show_packing  # noqa: E402
from app_pages.planner import show_planner  # noqa: E402
from app_pages.profile import show_profile  # noqa: E402
from app_pages.saved_looks import show_saved_looks  # noqa: E402
from app_pages.stylist import show_stylist  # noqa: E402
from app_pages.wardrobe import show_wardrobe  # noqa: E402
from components.auth_forms import show_auth_screen  # noqa: E402
from components.navbar import init_page_state, render_navbar, set_page  # noqa: E402
from database.supabase_client import is_configured, session_is_valid  # noqa: E402
from utils.theme import inject_theme  # noqa: E402
from utils.ui import page_header  # noqa: E402

PAGES = {
    "dashboard": show_dashboard,
    "wardrobe": show_wardrobe,
    "outfit_builder": show_outfit_builder,
    "saved_looks": show_saved_looks,
    "planner": show_planner,
    "stylist": show_stylist,
    "packing": show_packing,
    "insights": show_insights,
    "profile": show_profile,
}


def show_setup_screen():
    page_header("Almost ready", "Lumi Closet needs a Supabase project before it can start.")
    st.write("Add these two values to `.streamlit/secrets.toml` (or to your host's secrets settings), then reload:")
    st.code('SUPABASE_URL = "https://your-project.supabase.co"\nSUPABASE_ANON_KEY = "your-anon-public-key"', language="toml")
    st.write("Then run `schema.sql` once in the Supabase SQL editor. The README has the full steps.")


def display_name(user):
    meta = getattr(user, "user_metadata", None) or {}
    return meta.get("full_name") or (user.email or "you").split("@")[0]


def main():
    inject_theme()
    if not is_configured():
        show_setup_screen()
        return

    if "user" not in st.session_state:
        notice = st.session_state.pop("notice", None)
        if notice:
            st.info(notice)
        show_auth_screen()
        return

    if not session_is_valid():
        st.session_state.clear()
        st.session_state["notice"] = "Your session expired. Please log in again."
        st.rerun()

    init_page_state()
    render_navbar(display_name(st.session_state["user"]))
    page = st.session_state["page"]
    try:
        PAGES[page]()
    except Exception as exc:  # st.rerun and st.stop are not Exceptions, so they pass through
        report_error(log, f"Page '{page}' failed", exc)
        st.error("This page ran into a problem. The error has been logged.")
        st.button("Back to home", on_click=set_page, args=("dashboard",))
        if get_setting("APP_ENV") == "development":
            with st.expander("Technical details"):
                st.code(f"{type(exc).__name__}: {exc}")


main()
