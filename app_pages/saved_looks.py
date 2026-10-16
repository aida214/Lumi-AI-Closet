"""Lookbook: saved outfits, favourites, wear today, schedule on a date."""
import streamlit as st

from database import repository as repo
from utils.constants import OCCASIONS
from utils.context import load_context
from utils.ui import (chips_html, collage, empty_state, esc, page_header, panel,
                      run_action, show_html)


def _favourite(outfit_id, value):
    run_action(repo.set_outfit_favorite, outfit_id, value)


def _wear(uid, outfit, today):
    def action():
        repo.log_wear(uid, [i["id"] for i in outfit["items"]], today)
        repo.set_plan(uid, today, outfit["id"])
    run_action(action, success="Logged as worn and added to today's plan")


def _schedule(uid, outfit_id):
    day = st.session_state.get(f"sched_{outfit_id}")
    run_action(repo.set_plan, uid, day, outfit_id, success=f"Planned for {day}")


def _delete(outfit_id):
    run_action(repo.delete_outfit, outfit_id, success="Look deleted")


def show_saved_looks():
    ctx = load_context()
    uid, today = ctx["uid"], ctx["today"]
    outfits = repo.list_outfits(uid)
    page_header("Lookbook", f"{len(outfits)} saved looks.")

    if not outfits:
        empty_state("No saved looks yet", "Build an outfit and save it to see it here.",
                    "Open the builder", "outfit_builder", key="l_empty")
        return

    c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
    with c1:
        st.toggle("Favourites only", key="l_fav")
    with c2:
        st.selectbox("Occasion", ["All"] + OCCASIONS, key="l_occ")
    shown = [o for o in outfits
             if (not st.session_state.get("l_fav") or o.get("favorite"))
             and st.session_state.get("l_occ", "All") in ("All", o.get("occasion"))]
    if not shown:
        empty_state("Nothing matches", "Try a different filter.", key="l_none")
        return

    for start in range(0, len(shown), 3):
        cols = st.columns(3)
        for col, outfit in zip(cols, shown[start:start + 3]):
            oid = str(outfit["id"])
            fav = bool(outfit.get("favorite"))
            with col:
                with panel("tile", f"look-{oid}"):
                    show_html(collage([i.get("image_url") for i in outfit["items"]]) +
                              f'<div class="lc-name">{esc(outfit["title"])}</div>' +
                              chips_html([("Favourite" if fav else ""), outfit.get("occasion"),
                                          f'{len(outfit["items"])} pieces']))
                    if outfit.get("notes"):
                        show_html(f'<div class="lc-meta">{esc(outfit["notes"])}</div>')
                    a, b = st.columns(2)
                    with a:
                        st.button("Unfavourite" if fav else "Favourite", key=f"lf_{oid}", width="stretch",
                                  on_click=_favourite, args=(outfit["id"], not fav))
                    with b:
                        st.button("Wear today", key=f"lw_{oid}", width="stretch",
                                  on_click=_wear, args=(uid, outfit, today))
                    with st.popover("Plan or delete"):
                        st.date_input("Plan for", value=today, key=f"sched_{oid}")
                        st.button("Add to planner", key=f"ls_{oid}", type="primary", width="stretch",
                                  on_click=_schedule, args=(uid, outfit["id"]))
                        st.checkbox("I want to delete this look", key=f"ld_ok_{oid}")
                        st.button("Delete look", key=f"ld_{oid}", width="stretch",
                                  disabled=not st.session_state.get(f"ld_ok_{oid}", False),
                                  on_click=_delete, args=(outfit["id"],))
