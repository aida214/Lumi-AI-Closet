"""Outfit builder: pick pieces by slot or let Lumi suggest, then save the look."""
import streamlit as st

from database import repository as repo
from utils.colors import outfit_harmony
from utils.constants import OCCASIONS, SLOTS
from utils.context import load_context
from utils.insights import wear_summary
from utils.outfit_engine import suggest_outfit
from utils.weather import feels_temp
from utils.ui import (collage, empty_state, esc, item_label, page_header, panel,
                      run_action, section_title, show_html)


def _suggest(items, ctx, wear):
    s = st.session_state
    forecast = ctx["forecast"]
    temp = feels_temp(forecast["today_max"], forecast["today_min"]) if forecast else None
    rain = forecast["rain_chance"] if forecast else None
    s["builder_seed"] = s.get("builder_seed", 0) + 1
    result = suggest_outfit(items, temp_c=temp, rain_chance=rain, occasion=s.get("b_occasion", "Everyday"),
                            seed=s["builder_seed"] * 101 + sum(ord(c) for c in ctx["uid"]),
                            preferred_styles=ctx["styles"], wear=wear, today=ctx["today"])
    if result["missing"]:
        st.toast(result["missing"])
        return
    for slot, _label, _cat in SLOTS:
        s[f"slot_{slot}"] = result["items"][slot]["id"] if slot in result["items"] else None
    s["builder_reasons"] = result["reasons"]


def _clear():
    for slot, _label, _cat in SLOTS:
        st.session_state[f"slot_{slot}"] = None
    st.session_state["builder_reasons"] = []
    st.session_state["b_title"] = ""
    st.session_state["b_notes"] = ""


def _save(uid, chosen_ids):
    s = st.session_state
    title = (s.get("b_title") or "").strip()
    if not title:
        st.toast("Give this look a name first.")
        return
    if len(chosen_ids) < 2 and not s.get("slot_dress"):
        st.toast("Pick at least two pieces, or a dress.")
        return
    if run_action(repo.create_outfit, uid, title, (s.get("b_notes") or "").strip(),
                  s.get("b_occasion"), chosen_ids, success="Look saved to your lookbook"):
        _clear()


def show_outfit_builder():
    ctx = load_context()
    uid = ctx["uid"]
    items = repo.list_items(uid)
    wear = wear_summary(repo.list_wear(uid))
    page_header("Outfit builder", "Choose a piece for each slot, or ask Lumi to suggest a look from your closet.")

    if not items:
        empty_state("Add a few pieces first", "The builder works with the photos in your wardrobe.",
                    "Go to wardrobe", "wardrobe", key="b_empty")
        return

    by_id = {i["id"]: i for i in items}
    top, mid = st.columns([2, 1], vertical_alignment="bottom")
    with top:
        st.selectbox("Occasion", OCCASIONS, key="b_occasion")
    with mid:
        st.button("Suggest a look", key="b_suggest", type="primary", width="stretch",
                  on_click=_suggest, args=(items, ctx, wear))

    for reason in st.session_state.get("builder_reasons", []):
        show_html(f'<div class="lc-note">{esc(reason)}</div>')

    section_title("Pick your pieces")
    chosen = {}
    cols = st.columns(3)
    for index, (slot, label, category) in enumerate(SLOTS):
        options = [None] + [i["id"] for i in items if i.get("category") == category]
        key = f"slot_{slot}"
        if st.session_state.get(key) not in options:  # piece was deleted elsewhere
            st.session_state[key] = None
        with cols[index % 3]:
            pick = st.selectbox(label, options, key=key,
                                format_func=lambda i: "None" if i is None else item_label(by_id[i]))
        if pick:
            chosen[slot] = by_id[pick]

    section_title("Preview")
    if not chosen:
        show_html('<div class="lc-note">Your look will appear here as you choose pieces.</div>')
        return
    left, right = st.columns([1, 1])
    with left:
        with panel("tile", "b_preview"):
            show_html(collage([p.get("image_url") for p in chosen.values()]))
    with right:
        _score, note = outfit_harmony([p.get("color") for p in chosen.values()])
        show_html("".join(f'<div class="lc-meta" style="text-align:left">{esc(item_label(p))}</div>'
                          for p in chosen.values()))
        if note:
            show_html(f'<div class="lc-note">{esc(note)}</div>')
        if "dress" in chosen and ("top" in chosen or "bottom" in chosen):
            show_html('<div class="lc-note">A dress usually replaces the top and bottom. '
                      'You can still save this combination.</div>')

    section_title("Save this look")
    st.text_input("Name", key="b_title", placeholder="Rainy campus day")
    st.text_area("Notes (optional)", key="b_notes", height=80)
    ids = [p["id"] for p in chosen.values()]
    s1, s2 = st.columns(2)
    with s1:
        st.button("Save look", key="b_save", type="primary", width="stretch",
                  on_click=_save, args=(uid, ids))
    with s2:
        st.button("Clear", key="b_clear", width="stretch", on_click=_clear)
