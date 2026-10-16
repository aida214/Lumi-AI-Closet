"""Home: greeting, today's weather and look, the week ahead, recent pieces."""
from datetime import timedelta

import streamlit as st

from components.navbar import set_page
from database import repository as repo
from utils.constants import OCCASIONS, SLOTS
from utils.context import load_context
from utils.insights import compute_insights, wear_summary
from utils.outfit_engine import suggest_outfit
from utils.weather import feels_temp
from utils.ui import (chip_row, empty_state, esc, image_box, panel,
                      run_action, section_title, show_html)


def _greeting(hour):
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def _shuffle():
    st.session_state["look_shuffle"] = st.session_state.get("look_shuffle", 0) + 1


def _wear_look(uid, ids, day):
    run_action(repo.log_wear, uid, ids, day, success="Logged. Enjoy your day")


def _open_in_builder(ids_by_slot):
    for slot, _label, _cat in SLOTS:
        st.session_state[f"slot_{slot}"] = ids_by_slot.get(slot)
    set_page("outfit_builder")


def _today_look(ctx, items, wear):
    """Compute once per day, occasion and shuffle so reruns do not change the look."""
    forecast = ctx["forecast"]
    temp = feels_temp(forecast["today_max"], forecast["today_min"]) if forecast else None
    rain = forecast["rain_chance"] if forecast else None
    occasion = st.session_state.get("look_occasion", "Everyday")
    shuffle = st.session_state.get("look_shuffle", 0)
    by_id = {i["id"]: i for i in items}
    saved = st.session_state.get("today_look")
    fresh = (saved and saved["day"] == str(ctx["today"]) and saved["occasion"] == occasion
             and saved["shuffle"] == shuffle and all(i in by_id for i in saved["ids"].values()))
    if not fresh:
        seed = sum(ord(c) for c in ctx["uid"]) + ctx["today"].toordinal() * 31 + shuffle * 7919
        result = suggest_outfit(items, temp_c=temp, rain_chance=rain, occasion=occasion, seed=seed,
                                preferred_styles=ctx["styles"], wear=wear, today=ctx["today"])
        saved = {"day": str(ctx["today"]), "occasion": occasion, "shuffle": shuffle,
                 "ids": {slot: p["id"] for slot, p in result["items"].items()},
                 "reasons": result["reasons"], "missing": result["missing"]}
        st.session_state["today_look"] = saved
    return saved, by_id


def _deg(value):
    return f"{round(value)}\u00b0" if value is not None else "n/a"


def _weather_panel(ctx):
    forecast = ctx["forecast"]
    if forecast:
        show_html(
            f'<div class="lc-weather">{_deg(forecast["now_temp"])}C, {esc(forecast["now_label"])}</div>'
            f'<div class="lc-note">{esc(forecast["place"])}. High {_deg(forecast["today_max"])}, '
            f'low {_deg(forecast["today_min"])}, {esc(forecast["rain_chance"] or 0)}% chance of rain.</div>')
    elif ctx["city"]:
        show_html(f'<div class="lc-note">Weather for {esc(ctx["city"])} is not available right now. '
                  'Suggestions will ignore the temperature until it is.</div>')
    else:
        show_html('<div class="lc-note">Add your city in Profile to see today\'s weather and get '
                  'suggestions that fit it.</div>')
        st.button("Set my city", key="set_city", on_click=set_page, args=("profile",))


def show_dashboard():
    ctx = load_context()
    uid, today = ctx["uid"], ctx["today"]
    items = repo.list_items(uid)
    wear = wear_summary(repo.list_wear(uid))
    outfits = repo.list_outfits(uid)
    stats = compute_insights(items, wear, today)

    with panel("curve", "hero"):
        left, right = st.columns([3, 2], vertical_alignment="center")
        with left:
            show_html(f'<div class="lc-hello">{_greeting(ctx["now"].hour)}, {esc(ctx["name"])}.</div>')
            show_html(f'<div class="lc-note">{ctx["today"].strftime("%A, %d %B")}</div>')
        with right:
            _weather_panel(ctx)

    chip_row([f'{stats["total"]} pieces', f'{stats["favourites"]} favourites', f"{len(outfits)} saved looks",
              f'{stats["worn_30"]} worn in the last 30 days'])

    if not items:
        empty_state("Your closet is empty", "Add a few photos and Lumi can start suggesting outfits.",
                    "Add your first piece", "wardrobe", key="home_empty")
        return

    section_title("Today's look")
    st.selectbox("Occasion", OCCASIONS, key="look_occasion")
    look, by_id = _today_look(ctx, items, wear)
    if look["missing"]:
        st.info(look["missing"])
    else:
        picks = [by_id[i] for i in look["ids"].values()]
        cols = st.columns(max(len(picks), 1))
        for col, piece in zip(cols, picks):
            with col:
                with panel("tile", f'look-{piece["id"]}'):
                    show_html(image_box(piece.get("image_url"), piece.get("name")) +
                              f'<div class="lc-name">{esc(piece.get("name") or piece.get("category"))}</div>'
                              f'<div class="lc-meta">{esc(piece.get("category"))}</div>')
        for reason in look["reasons"]:
            show_html(f'<div class="lc-note">{esc(reason)}</div>')
        b1, b2, b3 = st.columns(3)
        with b1:
            st.button("Show me another", key="shuffle_look", on_click=_shuffle, width="stretch")
        with b2:
            st.button("I am wearing this", key="wear_look", type="primary", width="stretch",
                      on_click=_wear_look, args=(uid, list(look["ids"].values()), today))
        with b3:
            st.button("Open in builder", key="look_to_builder", width="stretch",
                      on_click=_open_in_builder, args=(dict(look["ids"]),))

    section_title("This week")
    start = today - timedelta(days=today.weekday())
    plan = repo.list_plan(uid, start, start + timedelta(days=6))
    titles = {o["id"]: o["title"] for o in outfits}
    cells = []
    for offset in range(7):
        day = start + timedelta(days=offset)
        title = titles.get(plan.get(str(day)), "Free")
        cls = "lc-day today" if day == today else "lc-day"
        cells.append(f'<div class="{cls}"><div class="dow">{day.strftime("%a")}</div>'
                     f'<div class="num">{day.day}</div><div class="plan">{esc(title)}</div></div>')
    show_html(f'<div class="lc-week">{"".join(cells)}</div>')
    st.button("Open planner", key="to_planner", on_click=set_page, args=("planner",))

    section_title("Recently added")
    recent = items[:4]
    cols = st.columns(4)
    for col, piece in zip(cols, recent):
        with col:
            with panel("tile", f'recent-{piece["id"]}'):
                show_html(image_box(piece.get("image_url"), piece.get("name")) +
                          f'<div class="lc-name">{esc(piece.get("name") or piece.get("category"))}</div>'
                          f'<div class="lc-meta">{esc(piece.get("brand") or piece.get("category"))}</div>')
