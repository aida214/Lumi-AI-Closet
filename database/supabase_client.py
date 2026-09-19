"""
Single shared Supabase client for the whole app.

Previously the project created a *second* Supabase client inline in
app.py (with the anon key, for auth) while every other page imported
this module's client (created with the service-role key, which
bypasses Row Level Security entirely). That's both a duplication bug
and a security issue: the service key should never be used from a
client-side app. This module now exposes one client, built with the
anon key, and every page/component shares it. Auth state (the logged
in user's session) therefore carries over automatically to every
query, and RLS policies (see schema.sql) do the access control that
the service key was previously bypassing.

Configuration is read from Streamlit secrets first (the recommended
place for local + Streamlit Cloud deployments), falling back to
environment variables / .env for people running things their own way.
"""

import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


def _get_setting(key: str) -> str | None:
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)


SUPABASE_URL = _get_setting("SUPABASE_URL")
SUPABASE_ANON_KEY = _get_setting("SUPABASE_ANON_KEY")

_missing = not SUPABASE_URL or not SUPABASE_ANON_KEY


@st.cache_resource(show_spinner=False)
def _build_client() -> "Client | None":
    if _missing:
        return None
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


supabase = _build_client()


def is_configured() -> bool:
    """True once SUPABASE_URL / SUPABASE_ANON_KEY are set."""
    return supabase is not None
