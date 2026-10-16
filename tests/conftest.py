"""Install fake streamlit and supabase before any app module is imported.

The tests therefore run without Streamlit or a Supabase project, which keeps
CI fast. They exercise logic and page code paths, not the real browser UI.
"""
import sys
import types
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from tests import fake_streamlit

_st = fake_streamlit.build()
sys.modules["streamlit"] = _st

_supabase = types.ModuleType("supabase")
_supabase.create_client = lambda url, key: SimpleNamespace(url=url, key=key)
sys.modules["supabase"] = _supabase

try:
    import dotenv  # noqa: F401
except ImportError:
    _dotenv = types.ModuleType("dotenv")
    _dotenv.load_dotenv = lambda *a, **k: None
    sys.modules["dotenv"] = _dotenv


@pytest.fixture
def st():
    _st.session_state.clear()
    _st.calls.clear()
    _st.query_params.clear()
    _st.secrets.clear()
    return _st


def make_item(i, category, color, **extra):
    base = {"id": f"id-{i}", "name": f"{color.title()} {category}", "category": category, "color": color,
            "season": "All Season", "style": "Casual", "brand": "", "price": None, "favorite": False,
            "image_url": f"https://example.com/{i}.jpg",
            "created_at": (datetime(2026, 9, 1) + timedelta(days=i)).isoformat()}
    base.update(extra)
    return base


@pytest.fixture
def closet():
    return [
        make_item(1, "Top", "cream"), make_item(2, "Top", "red", season="Summer"),
        make_item(3, "Bottom", "navy"), make_item(4, "Bottom", "blue", season="Winter"),
        make_item(5, "Shoes", "white"), make_item(6, "Outerwear", "camel", season="Autumn"),
        make_item(7, "Accessory", "black"), make_item(8, "Dress", "pink", season="Summer", style="Coquette"),
    ]


@pytest.fixture
def signed_in(st):
    st.session_state["user"] = SimpleNamespace(id="user-1", email="aida@example.com",
                                               user_metadata={"full_name": "Aida Khan"})
    return st


TODAY = date(2026, 10, 15)
