"""Packing list: choose pieces for a trip using the destination forecast."""
from datetime import timedelta

import streamlit as st

from database import repository as repo
from utils.context import load_context
from utils.insights import wear_summary
from utils.outfit_engine import PACK_TRIP_OCCASION, build_packing_list
from utils.ui import (chips_html, empty_state, esc, image_box, item_label, page_header,
                      panel, section_title, show_html)
from utils.weather import feels_temp, get_forecast, summarise_range

WEATHER_CHOICES = {"Hot (30 degrees)": (30, 10), "Warm (24 degrees)": (24, 20), "Mild (16 degrees)": (16, 30),
                   "Cool (9 degrees)": (9, 40), "Cold (2 degrees)": (2, 40), "Rainy (14 degrees)": (14, 80)}
ESSENTIALS = ["Phone charger", "Toiletries", "Underwear and socks", "Sleepwear", "Medication and documents"]
CATEGORY_TITLES = {"Top": "Tops", "Bottom": "Bottoms", "Dress": "Dresses", "Outerwear": "Outerwear",
                   "Shoes": "Shoes", "Accessory": "Accessories"}


def _build(items, ctx, wear):
    s = st.session_state
    start, days = s["pk_start"], int(s["pk_days"])
    destination = (s.get("pk_dest") or "").strip()
    weather_note, temp, rain = "", None, None
    forecast = get_forecast(destination) if destination else None
    summary = summarise_range(forecast, start, days) if forecast else None
    if summary:
        temp = feels_temp(summary["avg_high"], summary["avg_low"])
        rain = summary["max_rain"]
        weather_note = (f'Forecast for {forecast["place"]}: highs around {round(summary["avg_high"])}\u00b0, '
                        f'lows around {round(summary["avg_low"])}\u00b0, up to {round(rain)}% chance of rain '
                        f'({summary["covered_days"]} of {days} days covered).')
    else:
        temp, rain = WEATHER_CHOICES[s["pk_manual"]]
        weather_note = ("No forecast was available for those dates, so the weather you chose was used."
                        if destination else "Using the weather you chose.")
    result = build_packing_list(items, days, temp_c=temp, rain_chance=rain, trip_type=s["pk_type"],
                                preferred_styles=ctx["styles"], wear=wear, today=ctx["today"])
    s["pk_result"] = {"result": result, "weather": weather_note, "destination": destination, "days": days}


def _as_text(data):
    lines = [f'Packing list: {data["destination"] or "trip"}, {data["days"]} days']
    for category, pieces in data["result"]["packed"].items():
        if pieces:
            lines.append(f"\n{CATEGORY_TITLES[category]}")
            lines += [f"[ ] {item_label(p)}" for p in pieces]
    lines.append("\nEssentials")
    lines += [f"[ ] {e}" for e in ESSENTIALS]
    return "\n".join(lines)


def show_packing():
    ctx = load_context()
    uid, today = ctx["uid"], ctx["today"]
    items = repo.list_items(uid)
    wear = wear_summary(repo.list_wear(uid))
    page_header("Packing list", "Tell Lumi where you are going and for how long.")

    if not items:
        empty_state("Add pieces first", "Packing lists are built from your wardrobe.",
                    "Go to wardrobe", "wardrobe", key="pk_empty")
        return

    with panel("sheet", "pk_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Destination", key="pk_dest", placeholder="Lahore, Pakistan")
            st.date_input("Leaving on", value=today + timedelta(days=1), min_value=today, key="pk_start")
        with c2:
            st.selectbox("Trip type", list(PACK_TRIP_OCCASION), key="pk_type")
            st.number_input("Number of days", min_value=1, max_value=30, value=4, step=1, key="pk_days")
        st.selectbox("Weather if no forecast is available", list(WEATHER_CHOICES), index=2, key="pk_manual")
        st.button("Build my list", key="pk_build", type="primary", on_click=_build, args=(items, ctx, wear))

    data = st.session_state.get("pk_result")
    if not data:
        return

    result = data["result"]
    show_html(f'<div class="lc-note">{esc(data["weather"])}</div>')
    packed_ids = [p["id"] for pieces in result["packed"].values() for p in pieces]
    done = sum(1 for i in packed_ids if st.session_state.get(f"pack_{i}"))
    chip_total = len(packed_ids)
    st.progress(done / chip_total if chip_total else 0.0, text=f"{done} of {chip_total} pieces packed")
    show_html(chips_html([f'{result["combos"]} possible outfits from this selection']))
    for note in result["notes"]:
        st.warning(note)

    for category, pieces in result["packed"].items():
        if not pieces:
            continue
        section_title(CATEGORY_TITLES[category])
        for start in range(0, len(pieces), 4):
            cols = st.columns(4)
            for col, piece in zip(cols, pieces[start:start + 4]):
                with col:
                    with panel("tile", f'pk-{piece["id"]}'):
                        show_html(image_box(piece.get("image_url"), piece.get("name")) +
                                  f'<div class="lc-name">{esc(piece.get("name") or piece.get("category"))}</div>')
                        st.checkbox("Packed", key=f'pack_{piece["id"]}')

    section_title("Essentials")
    for essential in ESSENTIALS:
        st.checkbox(essential, key=f"ess_{essential}")
    st.download_button("Download list", data=_as_text(data), file_name="packing-list.txt", mime="text/plain")
