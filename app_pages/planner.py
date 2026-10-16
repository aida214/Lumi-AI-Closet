"""Weekly planner: choose a saved look for each day and mark it as worn."""
from datetime import timedelta

import streamlit as st

from database import repository as repo
from utils.context import load_context
from utils.ui import collage, empty_state, page_header, panel, run_action, show_html


def _shift(weeks):
    st.session_state["planner_week"] = st.session_state.get("planner_week", 0) + weeks


def _this_week():
    st.session_state["planner_week"] = 0


def _change(uid, day):
    outfit_id = st.session_state.get(f"plan_{day}")
    if outfit_id is None:
        run_action(repo.clear_plan, uid, day)
    else:
        run_action(repo.set_plan, uid, day, outfit_id)


def _worn(uid, outfit, day):
    run_action(repo.log_wear, uid, [i["id"] for i in outfit["items"]], day, success="Logged as worn")


def show_planner():
    ctx = load_context()
    uid, today = ctx["uid"], ctx["today"]
    outfits = repo.list_outfits(uid)
    page_header("Weekly planner", "Decide what you will wear before the morning rush.")

    if not outfits:
        empty_state("Save a look first", "The planner uses the outfits in your lookbook.",
                    "Open the builder", "outfit_builder", key="p_empty")
        return

    offset = st.session_state.get("planner_week", 0)
    start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    end = start + timedelta(days=6)
    plan = repo.list_plan(uid, start, end)
    by_id = {o["id"]: o for o in outfits}

    prev_col, label_col, next_col, now_col = st.columns([1, 3, 1, 1], vertical_alignment="center")
    with prev_col:
        st.button("Previous", key="p_prev", on_click=_shift, args=(-1,), width="stretch")
    with label_col:
        show_html(f'<div class="lc-weather" style="text-align:center">{start.strftime("%d %b")} to {end.strftime("%d %b %Y")}</div>')
    with next_col:
        st.button("Next", key="p_next", on_click=_shift, args=(1,), width="stretch")
    with now_col:
        st.button("Today", key="p_now", on_click=_this_week, width="stretch")

    options = [None] + [o["id"] for o in outfits]
    for n in range(7):
        day = start + timedelta(days=n)
        key = f"plan_{day}"
        planned = plan.get(str(day))
        # Always show what the database says, so changes made elsewhere appear here.
        st.session_state[key] = planned if planned in by_id else None
        with panel("chip", f"day-{day}"):
            info, picture, control = st.columns([1, 1, 2], vertical_alignment="center")
            with info:
                tag = " (today)" if day == today else ""
                show_html(f'<div class="lc-name" style="text-align:left;margin:0">{day.strftime("%A")}{tag}</div>'
                          f'<div class="lc-note">{day.strftime("%d %B")}</div>')
            with picture:
                if st.session_state[key]:
                    show_html(collage([i.get("image_url") for i in by_id[st.session_state[key]]["items"]]))
            with control:
                st.selectbox("Outfit", options, key=key, label_visibility="collapsed",
                             format_func=lambda i: "Nothing planned" if i is None else by_id[i]["title"],
                             on_change=_change, args=(uid, day))
                if planned in by_id and day <= today:
                    st.button("Mark as worn", key=f"worn_{day}", on_click=_worn,
                              args=(uid, by_id[planned], day))
