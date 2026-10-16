"""Brand bar and page navigation (chips, like the filter chips in the design)."""
import streamlit as st

from database import supabase_client
from utils.ui import esc, show_html

NAV = [
    ("dashboard", "Home"),
    ("wardrobe", "Wardrobe"),
    ("outfit_builder", "Outfits"),
    ("saved_looks", "Lookbook"),
    ("planner", "Planner"),
    ("stylist", "Stylist"),
    ("packing", "Packing"),
    ("insights", "Insights"),
    ("profile", "Profile"),
]
LABELS = dict(NAV)
PAGE_KEYS = [k for k, _ in NAV]


def _apply_page(page):
    st.session_state["page"] = page
    st.session_state["nav"] = page
    st.query_params["page"] = page


def set_page(page):
    """Safe to use as a button on_click callback."""
    if page in LABELS:
        _apply_page(page)


def init_page_state():
    if "page" not in st.session_state:
        wanted = st.query_params.get("page")
        st.session_state["page"] = wanted if wanted in LABELS else "dashboard"
    st.session_state.setdefault("nav", st.session_state["page"])


def _nav_changed():
    chosen = st.session_state.get("nav")
    if chosen is None:  # clicking the active chip would otherwise deselect it
        st.session_state["nav"] = st.session_state["page"]
    else:
        _apply_page(chosen)


def logout():
    client = supabase_client.get_client()
    try:
        if client is not None:
            client.auth.sign_out()
    except Exception:
        pass
    st.session_state.clear()


def render_navbar(first_name):
    with st.container(key="topbar"):
        left, right = st.columns([3, 2], vertical_alignment="center")
        with left:
            show_html('<div class="lc-brand"><span class="lc-brand-name">lumi</span>'
                      '<span class="lc-brand-sub">CLOSET</span></div>')
        with right:
            name_col, out_col = st.columns([3, 2], vertical_alignment="center")
            with name_col:
                show_html(f'<div class="lc-note" style="text-align:right">Signed in as <b>{esc(first_name)}</b></div>')
            with out_col:
                st.button("Log out", key="logout_btn", on_click=logout, width="stretch")
    # The widget key "nav" also gives the element the CSS class st-key-nav.
    st.pills("Navigate", PAGE_KEYS, selection_mode="single", key="nav",
             format_func=LABELS.get, label_visibility="collapsed", on_change=_nav_changed)
