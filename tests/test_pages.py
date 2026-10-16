"""Smoke tests: run every page against fake data and a fake Streamlit.

They prove the page code runs end to end on realistic data and that the
button callbacks do what they should. They do not prove the visual layout.
"""
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from database import repository as repo
from tests.conftest import TODAY
from utils import ui
from utils.weather import parse_forecast

FORECAST = parse_forecast({
    "utc_offset_seconds": 18000, "current": {"temperature_2m": 14.0, "weather_code": 61},
    "daily": {"time": [str(TODAY), "2026-10-16", "2026-10-17"], "temperature_2m_max": [17, 19, 21],
              "temperature_2m_min": [9, 10, 11], "precipitation_probability_max": [70, 20, 10],
              "weather_code": [61, 1, 0]}}, "Peshawar, Pakistan")


def fake_backend(monkeypatch, closet, outfits=None, plan=None, with_city=True):
    calls = []
    outfits = outfits if outfits is not None else [
        {"id": "o1", "title": "Rainy campus day", "notes": "Umbrella", "occasion": "Campus", "favorite": False,
         "items": [{"id": "id-1", "name": "Cream Top", "image_url": "https://example.com/1.jpg"},
                   {"id": "id-3", "name": "Navy Bottom", "image_url": None}]}]
    profile = {"id": "user-1", "full_name": "Aida Khan", "city": "Peshawar, Pakistan" if with_city else "",
               "favorite_aesthetics": "Casual, Minimalist"}
    wear_rows = [{"wardrobe_item_id": "id-1", "worn_on": "2026-10-14"}]
    table = {
        "get_profile": lambda uid: profile, "list_items": lambda uid: closet,
        "list_wear": lambda uid: wear_rows, "list_outfits": lambda uid: outfits,
        "list_plan": lambda uid, a, b: plan or {str(TODAY): "o1"},
        "list_chat": lambda uid, limit=50: [{"role": "user", "message": "hi"}, {"role": "assistant", "message": "hello"}],
    }
    for name, fn in table.items():
        monkeypatch.setattr(repo, name, fn)
    for name in ["add_chat", "clear_chat", "log_wear", "set_plan", "clear_plan", "update_item", "delete_item",
                 "create_outfit", "delete_outfit", "set_outfit_favorite", "update_profile"]:
        monkeypatch.setattr(repo, name, lambda *a, _n=name, **k: calls.append((_n, a)))
    import utils.context as context
    monkeypatch.setattr(context, "get_forecast", lambda city: FORECAST if city else None)
    return calls


def rendered(st):
    return " ".join(str(c) for c in st.calls)


def test_every_page_renders_with_data(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages.dashboard import show_dashboard
    from app_pages.insights import show_insights
    from app_pages.outfit_builder import show_outfit_builder
    from app_pages.packing import show_packing
    from app_pages.planner import show_planner
    from app_pages.profile import show_profile
    from app_pages.saved_looks import show_saved_looks
    from app_pages.stylist import show_stylist
    from app_pages.wardrobe import show_wardrobe
    for page in [show_dashboard, show_wardrobe, show_outfit_builder, show_saved_looks, show_planner,
                 show_stylist, show_packing, show_insights, show_profile]:
        signed_in.calls.clear()
        page()
        assert signed_in.calls, f"{page.__name__} rendered nothing"


def test_every_page_handles_an_empty_closet(signed_in, monkeypatch):
    fake_backend(monkeypatch, [], outfits=[], plan={}, with_city=False)
    from app_pages import (dashboard, insights, outfit_builder, packing, planner, profile, saved_looks,
                           stylist, wardrobe)
    for page in [dashboard.show_dashboard, wardrobe.show_wardrobe, outfit_builder.show_outfit_builder,
                 saved_looks.show_saved_looks, planner.show_planner, stylist.show_stylist,
                 packing.show_packing, insights.show_insights, profile.show_profile]:
        page()


def test_dashboard_survives_missing_forecast_values(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    import utils.context as context
    broken = dict(FORECAST, now_temp=None, today_max=None, today_min=None, rain_chance=None)
    monkeypatch.setattr(context, "get_forecast", lambda city: broken)
    from app_pages.dashboard import show_dashboard
    show_dashboard()
    assert "n/a" in rendered(signed_in)


def test_dashboard_shows_weather_and_a_complete_look(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages.dashboard import show_dashboard
    show_dashboard()
    text = rendered(signed_in)
    assert "14\u00b0C" in text and "Light rain" in text
    look = signed_in.session_state["today_look"]
    assert "top" in look["ids"] and "bottom" in look["ids"]
    assert "outerwear" in look["ids"]  # 14 degrees with 70% rain


def test_today_look_stays_stable_across_reruns(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages.dashboard import show_dashboard
    show_dashboard()
    first = dict(signed_in.session_state["today_look"]["ids"])
    show_dashboard()
    assert signed_in.session_state["today_look"]["ids"] == first


def test_shuffle_changes_the_seed(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages import dashboard
    dashboard.show_dashboard()
    dashboard._shuffle()
    dashboard.show_dashboard()
    assert signed_in.session_state["today_look"]["shuffle"] == 1


def test_wear_look_logs_every_piece(signed_in, monkeypatch, closet):
    calls = fake_backend(monkeypatch, closet)
    from app_pages import dashboard
    dashboard._wear_look("user-1", ["id-1", "id-3"], TODAY)
    assert calls == [("log_wear", ("user-1", ["id-1", "id-3"], TODAY))]


def test_open_in_builder_prefills_slots(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages import dashboard
    dashboard._open_in_builder({"top": "id-1", "bottom": "id-3"})
    s = signed_in.session_state
    assert s["slot_top"] == "id-1" and s["slot_shoes"] is None and s["page"] == "outfit_builder"


def test_builder_save_requires_a_name_and_two_pieces(signed_in, monkeypatch, closet):
    calls = fake_backend(monkeypatch, closet)
    from app_pages import outfit_builder as b
    b._save("user-1", ["id-1", "id-3"])
    assert not calls  # no title yet
    signed_in.session_state["b_title"] = "Look"
    b._save("user-1", ["id-1"])
    assert not calls  # only one piece
    b._save("user-1", ["id-1", "id-3"])
    assert calls[0][0] == "create_outfit"
    assert signed_in.session_state["b_title"] == ""  # form cleared after saving


def test_builder_suggest_fills_slots(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages import outfit_builder as b
    from utils.context import load_context
    b._suggest(closet, load_context(), {})
    assert signed_in.session_state["slot_top"] and signed_in.session_state["slot_bottom"]


def test_planner_change_sets_and_clears(signed_in, monkeypatch, closet):
    calls = fake_backend(monkeypatch, closet)
    from app_pages import planner
    signed_in.session_state[f"plan_{TODAY}"] = "o1"
    planner._change("user-1", TODAY)
    signed_in.session_state[f"plan_{TODAY}"] = None
    planner._change("user-1", TODAY)
    assert [c[0] for c in calls] == ["set_plan", "clear_plan"]


def test_planner_week_navigation(signed_in):
    from app_pages import planner
    planner._shift(1)
    planner._shift(1)
    planner._shift(-1)
    assert signed_in.session_state["planner_week"] == 1
    planner._this_week()
    assert signed_in.session_state["planner_week"] == 0


def test_clothing_card_edit_validates_and_saves(signed_in, monkeypatch, closet):
    calls = fake_backend(monkeypatch, closet)
    from components import clothing_card as card
    s = signed_in.session_state
    s.update({"e_name_x": "  ", "e_cat_x": "Top"})
    card._save_edit("x")
    assert not calls
    s.update({"e_name_x": "Silk shirt", "e_color_x": " Ivory ", "e_price_x": 0, "e_brand_x": ""})
    card._save_edit("x")
    name, args = calls[0]
    assert name == "update_item" and args[1]["color"] == "ivory" and args[1]["price"] is None


def test_clothing_card_renders_with_and_without_wear(signed_in, closet):
    from components.clothing_card import clothing_card
    clothing_card(closet[0], {"count": 3, "last": date(2026, 10, 14)}, "user-1", TODAY)
    clothing_card(closet[1], None, "user-1", TODAY)
    assert "Worn 3 times, last yesterday" in rendered(signed_in)
    assert "Not worn yet" in rendered(signed_in)


def test_wardrobe_filters_and_sorting(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages import wardrobe
    s = signed_in.session_state
    wear = {"id-1": {"count": 4, "last": TODAY}}
    s.update({"w_search": "navy"})
    assert [i["id"] for i in wardrobe._apply_filters(closet, wear)] == ["id-3"]
    s.clear()
    s.update({"w_cat": "Top", "w_sort": "Most worn"})
    assert wardrobe._apply_filters(closet, wear)[0]["id"] == "id-1"
    s.clear()
    s.update({"w_fav": True})
    assert wardrobe._apply_filters(closet, wear) == []
    s.clear()
    s.update({"w_season": "Summer", "w_color": "pi"})
    assert [i["id"] for i in wardrobe._apply_filters(closet, wear)] == ["id-8"]


def test_stylist_basic_mode_answers_from_closet(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages import stylist
    from utils.context import load_context
    answer = stylist._answer(load_context(), "outfit for class", [], closet, {})
    assert "campus" in answer.lower()
    assert "Cream Top" in answer or "Red Top" in answer


def test_stylist_ai_failure_falls_back(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages import stylist
    from utils.context import load_context
    monkeypatch.setattr(stylist.stylist, "ai_available", lambda: True)
    monkeypatch.setattr(stylist.stylist, "ask_ai", lambda *a, **k: None)
    assert "did not respond" in stylist._answer(load_context(), "what should I wear", [], closet, {})


def test_stylist_ai_is_rate_limited(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages import stylist
    from utils.context import load_context
    monkeypatch.setattr(stylist.stylist, "ai_available", lambda: True)
    monkeypatch.setattr(stylist.stylist, "ask_ai", lambda *a, **k: "AI says hi")
    ctx = load_context()
    replies = [stylist._answer(ctx, "hi", [], closet, {}) for _ in range(14)]
    assert replies[0] == "AI says hi"
    assert "wait about" in replies[-1]


def test_packing_builds_a_list_from_forecast_and_manual_weather(signed_in, monkeypatch, closet):
    fake_backend(monkeypatch, closet)
    from app_pages import packing
    from utils.context import load_context
    s = signed_in.session_state
    s.update({"pk_start": TODAY, "pk_days": 3, "pk_dest": "Peshawar", "pk_type": "Casual",
              "pk_manual": "Mild (16 degrees)"})
    monkeypatch.setattr(packing, "get_forecast", lambda city: FORECAST)
    packing._build(closet, load_context(), {})
    assert "Forecast for Peshawar" in s["pk_result"]["weather"]
    monkeypatch.setattr(packing, "get_forecast", lambda city: None)
    packing._build(closet, load_context(), {})
    assert "No forecast" in s["pk_result"]["weather"]
    assert "Packing list" in packing._as_text(s["pk_result"])


def test_profile_save_and_csv_formula_protection(signed_in, monkeypatch, closet):
    calls = fake_backend(monkeypatch, closet)
    from app_pages import profile
    s = signed_in.session_state
    s.update({"pf_name": " Aida ", "pf_username": "", "pf_city": "Peshawar", "pf_styles": ["Casual", "Y2K"]})
    profile._save_profile("user-1")
    assert calls[0][1][1] == {"full_name": "Aida", "username": None, "city": "Peshawar",
                              "favorite_aesthetics": "Casual, Y2K"}
    evil = dict(closet[0], name="=HYPERLINK(\"http://evil\")")
    assert "'=HYPERLINK" in profile._csv([evil])


def test_password_change_validation(signed_in):
    from app_pages import profile
    s = signed_in.session_state
    s.update({"pw_new": "short", "pw_again": "short"})
    profile._change_password()
    s.update({"pw_new": "longenough1", "pw_again": "different1"})
    profile._change_password()
    toasts = [c[1][0] for c in signed_in.calls if c[0] == "toast"]
    assert "Use at least 8 characters." in toasts and "The two passwords do not match." in toasts


def test_auth_signup_validation(signed_in):
    from components import auth_forms
    auth_forms._signup("", "a@b.co", "password1", "password1")
    auth_forms._signup("Aida", "not-an-email", "password1", "password1")
    auth_forms._signup("Aida", "a@b.co", "short", "short")
    auth_forms._signup("Aida", "a@b.co", "password1", "password2")
    errors = [c[1][0] for c in signed_in.calls if c[0] == "error"]
    assert len(errors) == 4


def test_login_attempts_are_rate_limited(signed_in, monkeypatch):
    from components import auth_forms
    from database import supabase_client

    class Auth:
        def sign_in_with_password(self, creds):
            raise RuntimeError("Invalid login credentials")

    monkeypatch.setattr(supabase_client, "get_client", lambda: SimpleNamespace(auth=Auth()))
    for _ in range(10):
        auth_forms._login("a@b.co", "wrongpass")
    errors = [c[1][0] for c in signed_in.calls if c[0] == "error"]
    assert "That email and password do not match." in errors
    assert any("Too many attempts" in e for e in errors)


def test_navigation_helpers(signed_in):
    from components import navbar
    navbar.init_page_state()
    assert signed_in.session_state["page"] == "dashboard"
    navbar.set_page("planner")
    assert signed_in.query_params["page"] == "planner" and signed_in.session_state["nav"] == "planner"
    navbar.set_page("not-a-page")
    assert signed_in.session_state["page"] == "planner"
    signed_in.session_state["nav"] = None
    navbar._nav_changed()
    assert signed_in.session_state["nav"] == "planner"  # clicking the active chip cannot deselect it


# ---- security and helpers --------------------------------------------------

def test_html_helpers_escape_user_content():
    hostile = '<img src=x onerror=alert(1)>"\n\'' 
    markup = ui.image_box("https://x.test/a.jpg\" onerror=\"alert(1)", hostile) + ui.chips_html([hostile])
    assert "<img src=x" not in markup
    assert 'onerror="alert' not in markup.replace("&quot;", "")
    assert "\n" not in ui.esc(hostile)


def test_run_action_reports_failures_with_a_friendly_toast(signed_in):
    def boom():
        raise RuntimeError("row-level security policy violated")

    assert ui.run_action(boom) is False
    assert any("permission" in c[1][0] for c in signed_in.calls if c[0] == "toast")
    assert ui.run_action(lambda: None, success="Saved") is True


def test_friendly_errors():
    assert "do not match" in ui.friendly_error(Exception("Invalid login credentials"))
    assert "Too many" in ui.friendly_error(Exception("429 rate limit"))
    assert ui.friendly_error(Exception("weird internal stacktrace")) == "Something went wrong. Please try again."


def test_storage_path_parsing():
    url = "https://abc.supabase.co/storage/v1/object/public/wardrobe/user-1/abc.jpg?t=1"
    assert repo._storage_path(url) == "user-1/abc.jpg"
    assert repo._storage_path(None) is None
    assert repo._storage_path("https://elsewhere.com/x.jpg") is None


def test_schema_enables_rls_on_every_table():
    sql = (Path(__file__).parent.parent / "schema.sql").read_text()
    tables = re.findall(r"create table if not exists public\.(\w+)", sql)
    assert len(tables) >= 7
    for table in tables:
        assert f"alter table public.{table} enable row level security" in sql, table
        assert f"on public.{table}" in sql.replace("\n", " "), f"{table} has no policy"
    assert "storage.foldername(name))[1] = auth.uid()" in sql
