"""Profile: name, city for weather, aesthetics, password and data export."""
import csv
import io

import streamlit as st

from database import repository as repo
from database import supabase_client
from utils.constants import STYLES
from utils.context import load_context
from utils.logging_config import get_logger, report_error
from utils.ui import chip_row, friendly_error, page_header, panel, run_action, section_title, show_html, esc
from utils.weather import geocode

log = get_logger("profile")


def _save_profile(uid):
    s = st.session_state
    run_action(repo.update_profile, uid, {
        "full_name": (s.get("pf_name") or "").strip(),
        "username": (s.get("pf_username") or "").strip() or None,
        "city": (s.get("pf_city") or "").strip() or None,
        "favorite_aesthetics": ", ".join(s.get("pf_styles") or []) or None,
    }, success="Profile saved")
    st.session_state.pop("today_look", None)


def _change_password():
    s = st.session_state
    new, again = s.get("pw_new") or "", s.get("pw_again") or ""
    if len(new) < 8:
        st.toast("Use at least 8 characters.")
        return
    if new != again:
        st.toast("The two passwords do not match.")
        return
    try:
        supabase_client.get_client().auth.update_user({"password": new})
        st.toast("Password updated")
    except Exception as exc:
        report_error(log, "Password change failed", exc)
        st.toast(friendly_error(exc))


def _safe_cell(value):
    """Stop spreadsheet apps from running text such as =SUM(...) as a formula."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def _csv(items):
    buffer = io.StringIO()
    fields = ["name", "category", "color", "season", "style", "brand", "price", "favorite", "created_at"]
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows({k: _safe_cell(v) for k, v in item.items()} for item in items)
    return buffer.getvalue()


def show_profile():
    ctx = load_context()
    uid, profile = ctx["uid"], ctx["profile"]
    items = repo.list_items(uid)
    page_header("Your profile", "These details personalise your weather and outfit suggestions.")
    chip_row([ctx["user"].email or "", f"{len(items)} pieces"])

    with panel("sheet", "pf_form"):
        with st.form("profile_form", border=False):
            st.text_input("Name", value=profile.get("full_name") or "", key="pf_name")
            st.text_input("Username (optional)", value=profile.get("username") or "", key="pf_username")
            st.text_input("City", value=profile.get("city") or "", key="pf_city",
                          placeholder="Peshawar, Pakistan",
                          help="Used to fetch the forecast. Add the country after a comma if the name is common.")
            current = [s.strip() for s in (profile.get("favorite_aesthetics") or "").split(",") if s.strip()]
            st.multiselect("Favourite aesthetics", STYLES, default=[s for s in current if s in STYLES], key="pf_styles",
                           help="Pieces in these styles get a small boost in suggestions.")
            st.form_submit_button("Save profile", type="primary", on_click=_save_profile, args=(uid,))

    city = (profile.get("city") or "").strip()
    if city:
        place = geocode(city)
        if place:
            show_html(f'<div class="lc-note">Weather location: {esc(place["place"])}</div>')
        else:
            show_html('<div class="lc-note">That city could not be found, so weather is switched off. '
                      'Try adding the country, for example "Peshawar, Pakistan".</div>')

    section_title("Security")
    with panel("sheet", "pf_password"):
        with st.form("password_form", border=False, clear_on_submit=True):
            st.text_input("New password", type="password", key="pw_new")
            st.text_input("Repeat new password", type="password", key="pw_again")
            st.form_submit_button("Change password", on_click=_change_password)

    section_title("Your data")
    st.caption("Download everything you have added as a spreadsheet-friendly CSV file.")
    st.download_button("Download wardrobe CSV", data=_csv(items), file_name="lumi-wardrobe.csv",
                       mime="text/csv", disabled=not items)
