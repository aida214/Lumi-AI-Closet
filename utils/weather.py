"""Weather from Open-Meteo (free, no API key).

Results are cached in memory for a short time so a busy app does not call the
API on every Streamlit rerun. Every function returns None instead of raising
when the network or the API fails, so the app keeps working without weather.
"""
import time
from datetime import datetime, timedelta, timezone

try:
    import httpx
except ImportError:  # httpx ships with supabase; missing only in minimal test setups
    httpx = None

from utils.logging_config import get_logger

log = get_logger("weather")

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_TTL = 30 * 60
GEOCODE_TTL = 24 * 60 * 60
FAILURE_TTL = 2 * 60

_cache = {}

WMO_LABELS = {
    0: "Clear sky", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    56: "Freezing drizzle", 57: "Freezing drizzle", 61: "Light rain", 63: "Rain",
    65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain", 71: "Light snow",
    73: "Snow", 75: "Heavy snow", 77: "Snow grains", 80: "Rain showers",
    81: "Rain showers", 82: "Heavy showers", 85: "Snow showers", 86: "Snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
}


def _cached(key, ttl, loader):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < hit[2]:
        return hit[1]
    value = loader()
    _cache[key] = (now, value, ttl if value is not None else FAILURE_TTL)
    return value


def clear_cache():
    _cache.clear()


def _geocode(city):
    name, _, qualifier = city.partition(",")
    qualifier = qualifier.strip().lower()
    if httpx is None:
        return None
    try:
        resp = httpx.get(
            GEOCODE_URL,
            params={"name": name.strip(), "count": 10, "language": "en", "format": "json"},
            timeout=8,
        )
        resp.raise_for_status()
        results = resp.json().get("results") or []
    except Exception as exc:
        log.warning("Geocoding failed for %r: %s", city, exc)
        return None
    if not results:
        return None
    chosen = results[0]
    if qualifier:
        for r in results:
            text = f"{r.get('country', '')} {r.get('admin1', '')}".lower()
            if qualifier in text:
                chosen = r
                break
    label = ", ".join(p for p in [chosen.get("name"), chosen.get("country")] if p)
    return {"place": label, "lat": chosen["latitude"], "lon": chosen["longitude"]}


def geocode(city):
    city = (city or "").strip()
    if not city:
        return None
    return _cached(("geo", city.lower()), GEOCODE_TTL, lambda: _geocode(city))


def parse_forecast(data, place=""):
    """Turn the raw Open-Meteo response into the small dict the app uses."""
    current = data.get("current") or {}
    daily = data.get("daily") or {}
    days = []
    for i, day in enumerate(daily.get("time") or []):
        def pick(field):
            values = daily.get(field) or []
            return values[i] if i < len(values) else None

        days.append({
            "date": day,
            "tmax": pick("temperature_2m_max"),
            "tmin": pick("temperature_2m_min"),
            "rain": pick("precipitation_probability_max"),
            "label": WMO_LABELS.get(pick("weather_code"), ""),
        })
    today = days[0] if days else {}
    return {
        "place": place,
        "utc_offset": data.get("utc_offset_seconds", 0) or 0,
        "now_temp": current.get("temperature_2m"),
        "now_label": WMO_LABELS.get(current.get("weather_code"), ""),
        "today_max": today.get("tmax"),
        "today_min": today.get("tmin"),
        "rain_chance": today.get("rain"),
        "daily": days,
    }


def _fetch_forecast(geo):
    if httpx is None:
        return None
    try:
        resp = httpx.get(
            FORECAST_URL,
            params={
                "latitude": geo["lat"],
                "longitude": geo["lon"],
                "current": "temperature_2m,weather_code",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": 16,
            },
            timeout=8,
        )
        resp.raise_for_status()
        return parse_forecast(resp.json(), geo["place"])
    except Exception as exc:
        log.warning("Forecast failed for %s: %s", geo.get("place"), exc)
        return None


def get_forecast(city):
    geo = geocode(city)
    if not geo:
        return None
    return _cached(("fc", geo["lat"], geo["lon"]), FORECAST_TTL, lambda: _fetch_forecast(geo))


def local_now(forecast=None):
    """Current time at the user's city when known, otherwise server time."""
    if forecast and forecast.get("utc_offset") is not None:
        return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            seconds=forecast["utc_offset"]
        )
    return datetime.now()


def feels_temp(tmax, tmin):
    """One temperature to dress for: weighted towards the daytime high."""
    if tmax is None and tmin is None:
        return None
    if tmax is None:
        return tmin
    if tmin is None:
        return tmax
    return (2 * tmax + tmin) / 3


def summarise_range(forecast, start, days):
    """Average high, low and worst rain chance for a trip starting on `start`."""
    if not forecast:
        return None
    wanted = {(start + timedelta(days=i)).isoformat() for i in range(days)}
    rows = [d for d in forecast["daily"] if d["date"] in wanted and d["tmax"] is not None]
    if not rows:
        return None
    highs = [d["tmax"] for d in rows]
    lows = [d["tmin"] for d in rows if d["tmin"] is not None] or highs
    rains = [d["rain"] for d in rows if d["rain"] is not None] or [0]
    return {
        "avg_high": sum(highs) / len(highs),
        "avg_low": sum(lows) / len(lows),
        "max_rain": max(rains),
        "covered_days": len(rows),
    }
