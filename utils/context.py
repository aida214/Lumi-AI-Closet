"""Per-run context shared by pages: who is signed in, their profile, local date, weather."""
import streamlit as st

from database import repository as repo
from utils.weather import get_forecast, local_now


def current_user_id():
    return str(st.session_state["user"].id)


def first_name(profile, user):
    name = (profile.get("full_name") or "").strip()
    if name:
        return name.split()[0]
    return (user.email or "there").split("@")[0].title()


def load_context():
    user = st.session_state["user"]
    uid = str(user.id)
    profile = repo.get_profile(uid)
    city = (profile.get("city") or "").strip()
    forecast = get_forecast(city) if city else None
    now = local_now(forecast)
    styles = [s.strip() for s in (profile.get("favorite_aesthetics") or "").split(",") if s.strip()]
    return {
        "uid": uid,
        "user": user,
        "profile": profile,
        "name": first_name(profile, user),
        "city": city,
        "forecast": forecast,
        "now": now,
        "today": now.date(),
        "styles": styles,
    }
