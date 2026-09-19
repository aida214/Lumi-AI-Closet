import datetime

import streamlit as st

from database.supabase_client import supabase
from utils.theme import section_title, empty_state

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _week_dates():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    return [monday + datetime.timedelta(days=i) for i in range(7)]


def _load_outfits(user_id: str):
    try:
        resp = (
            supabase.table("saved_outfits")
            .select("id, title")
            .eq("user_id", user_id)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def _load_plan(user_id: str, week_dates: list):
    try:
        resp = (
            supabase.table("planner")
            .select("*")
            .eq("user_id", user_id)
            .gte("date", str(week_dates[0]))
            .lte("date", str(week_dates[-1]))
            .execute()
        )
        rows = resp.data or []
        return {row["date"]: row for row in rows}
    except Exception:
        return {}


def show_planner():
    section_title("THIS WEEK", "Outfit Planner", "Plan what you'll wear, day by day.")

    user_id = str(st.session_state["user"].id)
    outfits = _load_outfits(user_id)

    if not outfits:
        empty_state("📅", "No saved outfits yet", "Save a look in the Outfit Builder, then plan it into your week here.")
        return

    week_dates = _week_dates()
    plan_by_date = _load_plan(user_id, week_dates)

    outfit_titles = {o["id"]: (o.get("title") or "Untitled look") for o in outfits}
    title_to_id = {v: k for k, v in outfit_titles.items()}
    choices = ["— Not planned —"] + list(outfit_titles.values())

    for day_name, day_date in zip(DAYS, week_dates):
        existing = plan_by_date.get(str(day_date))
        existing_title = outfit_titles.get(existing["outfit_id"]) if existing else None

        st.markdown('<div class="lc-card" style="margin-bottom:14px;">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])

        with c1:
            st.markdown(f"**{day_name}**")
            st.caption(day_date.strftime("%b %d"))

        with c2:
            choice = st.selectbox(
                f"plan_{day_name}",
                choices,
                index=choices.index(existing_title) if existing_title in choices else 0,
                label_visibility="collapsed",
                key=f"planner_{day_date}",
            )

            if choice == "— Not planned —" and existing:
                try:
                    supabase.table("planner").delete().eq("id", existing["id"]).execute()
                except Exception:
                    pass
            elif choice != "— Not planned —":
                outfit_id = title_to_id[choice]
                if not existing or existing.get("outfit_id") != outfit_id:
                    try:
                        if existing:
                            supabase.table("planner").update(
                                {"outfit_id": outfit_id}
                            ).eq("id", existing["id"]).execute()
                        else:
                            supabase.table("planner").insert(
                                {
                                    "user_id": user_id,
                                    "outfit_id": outfit_id,
                                    "date": str(day_date),
                                }
                            ).execute()
                    except Exception as e:
                        st.error(f"Couldn't save plan for {day_name}: {e}")

        st.markdown("</div>", unsafe_allow_html=True)
