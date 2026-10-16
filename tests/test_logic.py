from datetime import date

from utils import insights, outfit_engine, weather
from utils.colors import (compatible_colors, dominant_color_name, normalise_color, outfit_harmony,
                          pair_score)
from utils.ratelimit import RateLimiter, session_limiter

TODAY = date(2026, 10, 15)


# ---- colours ----------------------------------------------------------------

def test_normalise_color_handles_phrases_and_aliases():
    assert normalise_color("Light Blue striped") == "baby blue"
    assert normalise_color("Hot pink") == "hot pink"
    assert normalise_color("Navy-blue") == "navy"
    assert normalise_color("multicolour") is None
    assert normalise_color("") is None


def test_pair_scores():
    assert pair_score("cream", "red") == 1.0
    assert pair_score("pink", "lavender") == 0.7
    assert pair_score("red", "blue") < 0
    assert pair_score("mystery", "red") == 0.0


def test_harmony_notes():
    assert "neutrals" in outfit_harmony(["cream", "navy"])[1]
    assert "competing" in outfit_harmony(["red", "blue"])[1]
    assert outfit_harmony(["red"]) == (0.0, "")


def test_compatible_colors_include_neutrals():
    assert "black" in compatible_colors("pink")


def _photo(background, garment):
    import io
    from PIL import Image
    img = Image.new("RGB", (200, 200), background)
    for x in range(60, 140):
        for y in range(40, 160):
            img.putpixel((x, y), garment)
    out = io.BytesIO()
    img.save(out, "JPEG")
    return out.getvalue()


def test_dominant_color_ignores_white_background():
    assert dominant_color_name(_photo((255, 255, 255), (200, 38, 48))) == "red"
    assert dominant_color_name(_photo((250, 250, 250), (28, 38, 88))) == "navy"
    assert dominant_color_name(b"not an image") is None


# ---- outfit engine ----------------------------------------------------------

def test_cold_rainy_day_adds_outerwear(closet):
    result = outfit_engine.suggest_outfit(closet, temp_c=12, rain_chance=80, seed=1, today=TODAY)
    assert "outerwear" in result["items"]
    assert "shoes" in result["items"]


def test_hot_day_has_no_outerwear(closet):
    result = outfit_engine.suggest_outfit(closet, temp_c=32, seed=1, today=TODAY)
    assert "outerwear" not in result["items"]


def test_same_seed_gives_same_outfit(closet):
    a = outfit_engine.suggest_outfit(closet, temp_c=18, seed=5, today=TODAY)
    b = outfit_engine.suggest_outfit(list(reversed(closet)), temp_c=18, seed=5, today=TODAY)
    assert {k: v["id"] for k, v in a["items"].items()} == {k: v["id"] for k, v in b["items"].items()}


def test_empty_or_incomplete_closet_explains_what_is_missing(closet):
    assert outfit_engine.suggest_outfit([], today=TODAY)["missing"]
    assert outfit_engine.suggest_outfit([closet[0]], today=TODAY)["missing"]


def test_recently_worn_pieces_are_avoided(closet):
    wear = {"id-1": {"count": 5, "last": TODAY}, "id-2": {"count": 1, "last": date(2026, 8, 1)}}
    tops = set()
    for seed in range(10):
        result = outfit_engine.suggest_outfit(closet, temp_c=None, seed=seed, wear=wear, today=TODAY)
        if "top" in result["items"]:
            tops.add(result["items"]["top"]["id"])
    assert "id-2" in tops


def test_workout_never_picks_a_dress(closet):
    result = outfit_engine.suggest_outfit(closet, occasion="Workout", seed=2, today=TODAY)
    assert "dress" not in result["items"]


def test_packing_list_counts(closet):
    data = outfit_engine.build_packing_list(closet, days=5, temp_c=12, rain_chance=70, today=TODAY)
    assert len(data["packed"]["Top"]) == 2          # only two tops exist
    assert data["packed"]["Outerwear"]
    assert data["combos"] >= 1
    assert data["notes"]                            # tells her she owns fewer tops than needed


# ---- insights ---------------------------------------------------------------

def test_wear_summary_and_insights(closet):
    wear = insights.wear_summary([
        {"wardrobe_item_id": "id-1", "worn_on": "2026-10-14"},
        {"wardrobe_item_id": "id-1", "worn_on": "2026-09-01"},
        {"wardrobe_item_id": "id-2", "worn_on": "2026-08-01"},
        {"wardrobe_item_id": None, "worn_on": "2026-08-01"},
    ])
    assert wear["id-1"] == {"count": 2, "last": date(2026, 10, 14)}
    data = insights.compute_insights(closet, wear, TODAY)
    assert data["total"] == 8
    assert data["worn_30"] == 1
    assert data["never_worn"] == 6
    assert any("never been logged" in t for t in data["tips"])
    assert data["idle"][0][1] >= data["idle"][-1][1]


def test_cost_per_wear():
    items = [{"id": "a", "price": 100, "category": "Top"}]
    wear = {"a": {"count": 4, "last": TODAY}}
    assert insights.compute_insights(items, wear, TODAY)["cost_per_wear"][0][1] == 25.0


# ---- weather ----------------------------------------------------------------

RAW = {"utc_offset_seconds": 18000, "current": {"temperature_2m": 21.3, "weather_code": 2},
       "daily": {"time": ["2026-10-15", "2026-10-16"], "temperature_2m_max": [25, 23],
                 "temperature_2m_min": [12, 11], "precipitation_probability_max": [10, 60],
                 "weather_code": [0, 61]}}


def test_parse_forecast_and_range():
    fc = weather.parse_forecast(RAW, "Peshawar, Pakistan")
    assert fc["now_label"] == "Partly cloudy"
    assert fc["daily"][1]["label"] == "Light rain"
    summary = weather.summarise_range(fc, date(2026, 10, 15), 2)
    assert summary["max_rain"] == 60 and summary["covered_days"] == 2
    assert weather.summarise_range(fc, date(2027, 1, 1), 3) is None
    assert round(weather.feels_temp(25, 12), 1) == 20.7


def test_local_now_uses_city_offset():
    fc = weather.parse_forecast(RAW)
    assert weather.local_now(fc) is not None


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_geocode_prefers_matching_country_and_caches(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(url)
        return _FakeResponse({"results": [
            {"name": "Paris", "country": "United States", "admin1": "Texas", "latitude": 1, "longitude": 2},
            {"name": "Paris", "country": "France", "admin1": "Ile-de-France", "latitude": 48.8, "longitude": 2.3}]})

    class FakeHttpx:
        get = staticmethod(fake_get)

    weather.clear_cache()
    monkeypatch.setattr(weather, "httpx", FakeHttpx)
    assert weather.geocode("Paris, France")["place"] == "Paris, France"
    weather.geocode("Paris, France")
    assert len(calls) == 1  # second call came from the cache


def test_network_failure_returns_none(monkeypatch):
    class Boom:
        @staticmethod
        def get(*a, **k):
            raise RuntimeError("offline")

    weather.clear_cache()
    monkeypatch.setattr(weather, "httpx", Boom)
    assert weather.geocode("Nowhere") is None
    assert weather.get_forecast("Nowhere") is None


# ---- rate limiter -----------------------------------------------------------

def test_rate_limiter_window():
    limiter = RateLimiter(max_calls=2, per_seconds=10)
    assert limiter.allow(now=0) and limiter.allow(now=1)
    assert not limiter.allow(now=2)
    assert limiter.retry_after(now=2) >= 8
    assert limiter.allow(now=11)


def test_session_limiter_is_reused():
    state = {}
    assert session_limiter(state, "x", 1, 60) is session_limiter(state, "x", 1, 60)
