"""All database and storage calls live here so pages stay free of query code.

Security model: the app only ever uses the public anon key. Every table has
Row Level Security (see schema.sql), so the database itself refuses to return
or change another user's rows even if this code had a bug. The user_id filters
below are for clarity and speed, not the security boundary.
"""
import uuid

from database.supabase_client import get_client
from utils.constants import STORAGE_BUCKET
from utils.logging_config import get_logger

log = get_logger("repository")

IMAGE_CACHE_SECONDS = "31536000"  # filenames are random and never reused


def _db():
    client = get_client()
    if client is None:
        raise RuntimeError("The database is not configured.")
    return client


# ---- profile ---------------------------------------------------------------

def get_profile(user_id):
    rows = _db().table("profiles").select("*").eq("id", user_id).limit(1).execute().data or []
    return rows[0] if rows else {}


def ensure_profile(user_id, email="", full_name=""):
    """Create the profile row if the signup trigger has not already."""
    if get_profile(user_id):
        return
    _db().table("profiles").upsert(
        {"id": user_id, "email": email, "full_name": full_name},
        on_conflict="id", ignore_duplicates=True,
    ).execute()


def update_profile(user_id, fields):
    _db().table("profiles").update(fields).eq("id", user_id).execute()


# ---- wardrobe --------------------------------------------------------------

def list_items(user_id):
    return (_db().table("wardrobe").select("*").eq("user_id", user_id)
            .order("created_at", desc=True).execute().data or [])


def upload_image(user_id, jpeg_bytes):
    """Store a photo under the user's own folder and return its public URL."""
    path = f"{user_id}/{uuid.uuid4().hex}.jpg"
    bucket = _db().storage.from_(STORAGE_BUCKET)
    bucket.upload(path, jpeg_bytes, {"content-type": "image/jpeg", "cache-control": IMAGE_CACHE_SECONDS})
    return bucket.get_public_url(path)


def add_item(user_id, fields):
    row = {k: v for k, v in fields.items() if v not in (None, "")}
    row["user_id"] = user_id
    return _db().table("wardrobe").insert(row).execute().data


def update_item(item_id, fields):
    _db().table("wardrobe").update(fields).eq("id", item_id).execute()


def _storage_path(url):
    marker = f"/object/public/{STORAGE_BUCKET}/"
    if not url or marker not in url:
        return None
    return url.split(marker, 1)[1].split("?", 1)[0]


def delete_item(item):
    """Delete the row, then the photo. A failed photo delete never blocks the row."""
    _db().table("wardrobe").delete().eq("id", item["id"]).execute()
    path = _storage_path(item.get("image_url"))
    if path:
        try:
            _db().storage.from_(STORAGE_BUCKET).remove([path])
        except Exception as exc:
            log.warning("Could not remove stored photo %s: %s", path, exc)


# ---- wear log --------------------------------------------------------------

def list_wear(user_id):
    return (_db().table("wear_log").select("wardrobe_item_id,worn_on")
            .eq("user_id", user_id).execute().data or [])


def log_wear(user_id, item_ids, day):
    rows = [{"user_id": user_id, "wardrobe_item_id": i, "worn_on": str(day)} for i in item_ids]
    if rows:
        _db().table("wear_log").upsert(
            rows, on_conflict="wardrobe_item_id,worn_on", ignore_duplicates=True
        ).execute()


# ---- outfits ---------------------------------------------------------------

def list_outfits(user_id):
    rows = (_db().table("saved_outfits")
            .select("*, outfit_items(wardrobe(id,name,category,color,image_url))")
            .eq("user_id", user_id).order("created_at", desc=True).execute().data or [])
    for row in rows:
        row["items"] = [link["wardrobe"] for link in row.get("outfit_items", []) if link.get("wardrobe")]
    return rows


def create_outfit(user_id, title, notes, occasion, item_ids):
    created = _db().table("saved_outfits").insert(
        {"user_id": user_id, "title": title, "notes": notes or None, "occasion": occasion or None}
    ).execute().data
    outfit_id = created[0]["id"]
    _db().table("outfit_items").insert(
        [{"outfit_id": outfit_id, "wardrobe_item_id": i} for i in item_ids]
    ).execute()
    return outfit_id


def delete_outfit(outfit_id):
    _db().table("saved_outfits").delete().eq("id", outfit_id).execute()


def set_outfit_favorite(outfit_id, value):
    _db().table("saved_outfits").update({"favorite": bool(value)}).eq("id", outfit_id).execute()


# ---- planner ---------------------------------------------------------------

def list_plan(user_id, start, end):
    """{'2026-10-15': outfit_id} for the dates in [start, end]."""
    rows = (_db().table("planner").select("date,outfit_id").eq("user_id", user_id)
            .gte("date", str(start)).lte("date", str(end)).execute().data or [])
    return {r["date"]: r["outfit_id"] for r in rows}


def set_plan(user_id, day, outfit_id):
    _db().table("planner").upsert(
        {"user_id": user_id, "date": str(day), "outfit_id": outfit_id}, on_conflict="user_id,date"
    ).execute()


def clear_plan(user_id, day):
    _db().table("planner").delete().eq("user_id", user_id).eq("date", str(day)).execute()


# ---- chat ------------------------------------------------------------------

def list_chat(user_id, limit=50):
    """The newest `limit` messages, oldest first."""
    rows = (_db().table("chat_history").select("role,message,created_at")
            .eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute().data or [])
    return list(reversed(rows))


def add_chat(user_id, role, message):
    _db().table("chat_history").insert({"user_id": user_id, "role": role, "message": message}).execute()


def clear_chat(user_id):
    _db().table("chat_history").delete().eq("user_id", user_id).execute()
