"""Insights: what you own, what you wear, and what sits unused."""
import pandas as pd
import streamlit as st

from database import repository as repo
from utils.context import load_context
from utils.insights import compute_insights, wear_summary
from utils.ui import chip_row, empty_state, esc, page_header, panel, section_title, show_html

INK = "#2E2829"


def _chart(title, data):
    if not data:
        return
    section_title(title)
    st.bar_chart(pd.Series(data, name="Pieces"), color=INK, height=260)


def show_insights():
    ctx = load_context()
    uid, today = ctx["uid"], ctx["today"]
    items = repo.list_items(uid)
    wear = wear_summary(repo.list_wear(uid))
    page_header("Closet insights", "Numbers about your own wardrobe. Everything here is calculated from what you log.")

    if not items:
        empty_state("Nothing to analyse yet", "Add pieces and log what you wear to see patterns.",
                    "Go to wardrobe", "wardrobe", key="i_empty")
        return

    data = compute_insights(items, wear, today)
    chip_row([f'{data["total"]} pieces', f'{data["worn_30"]} worn in the last 30 days',
              f'{data["never_worn"]} never worn', f'{data["favourites"]} favourites'])

    if data["tips"]:
        section_title("Worth a look")
        for n, tip in enumerate(data["tips"]):
            with panel("chip", f"tip-{n}"):
                show_html(f"<p style='margin:0'>{esc(tip)}</p>")

    left, right = st.columns(2)
    with left:
        _chart("By category", data["by_category"])
        _chart("By style", data["by_style"])
    with right:
        _chart("By colour", data["by_color"])

    section_title("Most worn")
    if data["most_worn"]:
        for item in data["most_worn"]:
            st.write(f'{item.get("name") or item.get("category")}: worn {wear[item["id"]]["count"]} times')
    else:
        st.caption("Use 'Wore it' on a piece to start counting.")

    section_title("Not worn in 30 days")
    if data["idle"]:
        for item, days, never in data["idle"][:10]:
            how = f"never worn, in your closet {days} days" if never else f"last worn {days} days ago"
            st.write(f'{item.get("name") or item.get("category")}: {how}')
    else:
        st.caption("Every piece has been worn in the last 30 days, or was added recently.")

    if data["cost_per_wear"]:
        section_title("Cost per wear")
        st.caption("Calculated from the price you entered, in whatever currency you used.")
        table = pd.DataFrame(
            [{"Piece": i.get("name") or i.get("category"), "Price": float(i["price"]),
              "Times worn": wear[i["id"]]["count"], "Cost per wear": round(cpw, 2)}
             for i, cpw in data["cost_per_wear"]])
        st.dataframe(table, hide_index=True, width="stretch")
