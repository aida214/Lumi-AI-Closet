"""Settings lookup. Streamlit secrets first, then environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()


def get_setting(key, default=None):
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        # No secrets file, or Streamlit is not installed (unit tests).
        pass
    return os.getenv(key, default)
