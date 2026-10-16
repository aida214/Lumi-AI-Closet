"""Wardrobe: add pieces, search, filter, sort and manage them."""
import streamlit as st

from components.clothing_card import clothing_card
from components.upload_form import show_upload_form
from database import repository as repo
from utils.constants import CATEGORIES, SEASONS, STYLES
from utils.context import load_context
from utils.insights import parse_day, wear_summary
from utils.ui import empty_state, page_header, section_title

PAGE_SIZE = 12
SORTS = ["Newest first", "Oldest first", "Name A to Z", "Most worn", "Least worn"]


def _show_more():
    st.session_state["wardrobe_limit"] = st.session_state.get("wardrobe_limit", PAGE_SIZE) + PAGE_SIZE


def _reset_limit():
    st.session_state["wardrobe_limit"] = PAGE_SIZE


def _apply_filters(items, wear):
    s = st.session_state
    query = (s.get("w_search") or "").strip().lower()
    category = s.get("w_cat") or "All"
    season, style = s.get("w_season") or "All", s.get("w_style") or "All"
    colour = (s.get("w_color") or "").strip().lower()
    out = []
    for item in items:
        text = " ".join(str(item.get(k) or "") for k in ("name", "brand", "color", "category", "style")).lower()
        if query and query not in text:
            continue
        if category != "All" and item.get("category") != category:
            continue
        if season != "All" and item.get("season") != season:
            continue
        if style != "All" and item.get("style") != style:
            continue
        if colour and colour not in (item.get("color") or "").lower():
            continue
        if s.get("w_fav") and not item.get("favorite"):
            continue
        out.append(item)

    sort = s.get("w_sort") or SORTS[0]
    created = lambda i: str(parse_day(i.get("created_at")) or "")
    if sort == "Oldest first":
        out.sort(key=created)
    elif sort == "Name A to Z":
        out.sort(key=lambda i: (i.get("name") or "").lower())
    elif sort == "Most worn":
        out.sort(key=lambda i: -wear.get(i["id"], {}).get("count", 0))
    elif sort == "Least worn":
        out.sort(key=lambda i: wear.get(i["id"], {}).get("count", 0))
    return out


def show_wardrobe():
    ctx = load_context()
    uid, today = ctx["uid"], ctx["today"]
    items = repo.list_items(uid)
    wear = wear_summary(repo.list_wear(uid))

    page_header("My wardrobe", f"{len(items)} pieces. Add photos, tag them once, then reuse them everywhere.")

    with st.expander("Add a piece", expanded=not items):
        show_upload_form(uid)

    if not items:
        return

    st.pills("Category", ["All"] + CATEGORIES, selection_mode="single", default="All",
             key="w_cat", label_visibility="collapsed", on_change=_reset_limit)
    st.text_input("Search", key="w_search", placeholder="Search by name, brand, colour or style",
                  on_change=_reset_limit)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.selectbox("Season", ["All"] + SEASONS, key="w_season", on_change=_reset_limit)
    with c2:
        st.selectbox("Style", ["All"] + STYLES, key="w_style", on_change=_reset_limit)
    with c3:
        st.text_input("Colour contains", key="w_color", on_change=_reset_limit)
    with c4:
        st.selectbox("Sort by", SORTS, key="w_sort")
    st.toggle("Favourites only", key="w_fav", on_change=_reset_limit)

    shown = _apply_filters(items, wear)
    limit = st.session_state.get("wardrobe_limit", PAGE_SIZE)
    section_title(f"{len(shown)} of {len(items)} pieces")
    if not shown:
        empty_state("Nothing matches", "Try removing a filter or searching for something else.", key="w_none")
        return

    for start in range(0, min(limit, len(shown)), 3):
        cols = st.columns(3)
        for col, item in zip(cols, shown[start:min(start + 3, limit)]):
            with col:
                clothing_card(item, wear.get(item["id"]), uid, today)
    if len(shown) > limit:
        st.button(f"Show more ({len(shown) - limit} left)", key="w_more", on_click=_show_more)
