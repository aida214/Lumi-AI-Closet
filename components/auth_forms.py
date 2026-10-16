"""Login and sign-up screen."""
import re

import streamlit as st

from database import repository as repo
from database import supabase_client
from utils.logging_config import get_logger, report_error
from utils.ratelimit import session_limiter
from utils.ui import friendly_error, panel, show_html

log = get_logger("auth")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _start_session(response):
    user = response.user
    st.session_state["user"] = user
    full_name = (user.user_metadata or {}).get("full_name", "") if user.user_metadata else ""
    try:
        repo.ensure_profile(str(user.id), user.email or "", full_name)
    except Exception as exc:
        # The signup trigger normally creates the profile, so this is not fatal.
        log.warning("ensure_profile failed: %s", exc)
    st.rerun()


def _attempts_ok():
    limiter = session_limiter(st.session_state, "auth", max_calls=8, per_seconds=120)
    if limiter.allow():
        return True
    st.error(f"Too many attempts. Please wait about {limiter.retry_after()} seconds.")
    return False


def _login(email, password):
    if not EMAIL_RE.match(email or "") or not password:
        st.error("Enter your email and password.")
        return
    if not _attempts_ok():
        return
    try:
        response = supabase_client.get_client().auth.sign_in_with_password(
            {"email": email.strip(), "password": password})
    except Exception as exc:
        log.info("Login failed: %s", exc)
        st.error(friendly_error(exc))
        return
    _start_session(response)


def _signup(name, email, password, confirm):
    if not name.strip():
        st.error("Tell us your name so we can greet you.")
        return
    if not EMAIL_RE.match(email or ""):
        st.error("That email address does not look right.")
        return
    if len(password) < 8:
        st.error("Use a password with at least 8 characters.")
        return
    if password != confirm:
        st.error("The two passwords do not match.")
        return
    if not _attempts_ok():
        return
    try:
        response = supabase_client.get_client().auth.sign_up({
            "email": email.strip(), "password": password,
            "options": {"data": {"full_name": name.strip()}},
        })
    except Exception as exc:
        report_error(log, "Sign-up failed", exc)
        st.error(friendly_error(exc))
        return
    if response.session:
        _start_session(response)
    else:
        st.success("Account created. Check your inbox to confirm your email, then log in.")


def show_auth_screen():
    _left, middle, _right = st.columns([1, 2, 1])
    with middle:
        show_html('<div class="lc-brand" style="margin-bottom:8px"><span class="lc-brand-name" style="font-size:4.2rem">lumi</span>'
                  '<span class="lc-brand-sub">CLOSET</span></div>')
        show_html('<p class="lc-note" style="font-size:1.1rem">Photograph your clothes once. Build outfits, plan your week '
                  'and pack for trips from what you already own.</p>')
        with panel("curve", "auth"):
            login_tab, signup_tab = st.tabs(["Log in", "Create account"])
            with login_tab:
                with st.form("login_form"):
                    email = st.text_input("Email", key="login_email")
                    password = st.text_input("Password", type="password", key="login_password")
                    submitted = st.form_submit_button("Log in", type="primary", width="stretch")
                if submitted:
                    _login(email, password)
            with signup_tab:
                with st.form("signup_form"):
                    name = st.text_input("Your name", key="signup_name")
                    email = st.text_input("Email", key="signup_email")
                    password = st.text_input("Password (8 or more characters)", type="password", key="signup_password")
                    confirm = st.text_input("Repeat password", type="password", key="signup_confirm")
                    submitted = st.form_submit_button("Create account", type="primary", width="stretch")
                if submitted:
                    _signup(name, email, password, confirm)
