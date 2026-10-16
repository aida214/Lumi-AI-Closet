"""Supabase access.

Important: one client PER BROWSER SESSION. A client holds the logged-in
user's token, so sharing one client between visitors (for example with
st.cache_resource) would let one person's login change what another person
can read. The client is created lazily and stored in st.session_state.
"""
import streamlit as st
from supabase import create_client

from utils.config import get_setting


def is_configured():
    return bool(get_setting("SUPABASE_URL") and get_setting("SUPABASE_ANON_KEY"))


def get_client():
    if not is_configured():
        return None
    client = st.session_state.get("_sb_client")
    if client is None:
        client = create_client(get_setting("SUPABASE_URL"), get_setting("SUPABASE_ANON_KEY"))
        st.session_state["_sb_client"] = client
    return client


def session_is_valid():
    """True while the stored login is still usable (refreshes the token if needed)."""
    client = get_client()
    if client is None:
        return False
    try:
        return client.auth.get_session() is not None
    except Exception:
        return False
