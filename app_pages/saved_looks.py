from datetime import datetime

import streamlit as st

from database.supabase_client import supabase
from utils.theme import section_title, empty_state


def _load_outfits(user_id: str):
    try:
        resp = (
            supabase.table("saved_outfits")
            .select("*, outfit_items(wardrobe(id, name, image_url))")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return resp.data or []
    except Exception:
        # outfit_items join may not exist yet on older schemas -- fall back
        try:
            resp = (
                supabase.table("saved_outfits")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return resp.data or []
        except Exception:
            return []


def _format_date(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%b %d, %Y")
    except Exception:
        return ""


def show_saved_looks():
    section_title("YOUR LOOKBOOK", "Saved Looks", "Every outfit you've put together, all in one place.")

    user_id = str(st.session_state["user"].id)
    outfits = _load_outfits(user_id)

    if not outfits:
        empty_state("🩷", "No saved looks yet", "Build an outfit in the Outfit Builder and save it here.")
        return

    cols = st.columns(3, gap="large")

    for index, outfit in enumerate(outfits):
        with cols[index % 3]:
            st.markdown('<div class="lc-card">', unsafe_allow_html=True)

            items = [
                oi["wardrobe"] for oi in (outfit.get("outfit_items") or [])
                if oi.get("wardrobe")
            ]

            if items:
                thumb_cols = st.columns(min(3, len(items)))
                for tcol, it in zip(thumb_cols, items[:3]):
                    with tcol:
                        if it.get("image_url"):
                            st.image(it["image_url"], use_container_width=True)
            else:
                st.markdown(
                    "<div style='height:100px;border-radius:14px;background:var(--lavender-soft);"
                    "display:flex;align-items:center;justify-content:center;font-size:1.6rem;'>🎀</div>",
                    unsafe_allow_html=True,
                )

            st.markdown(f"**{outfit.get('title') or 'Untitled look'}**")
            if outfit.get("notes"):
                st.caption(outfit["notes"])
            st.caption(_format_date(outfit.get("created_at", "")))

            b1, b2 = st.columns(2)
            with b1:
                fav = outfit.get("favorite", False)
                if st.button(
                    "❤️" if fav else "🤍",
                    key=f"outfit_fav_{outfit['id']}",
                    use_container_width=True,
                ):
                    try:
                        supabase.table("saved_outfits").update(
                            {"favorite": not fav}
                        ).eq("id", outfit["id"]).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Couldn't update: {e}")
            with b2:
                if st.button("🗑️", key=f"outfit_del_{outfit['id']}", use_container_width=True):
                    try:
                        supabase.table("saved_outfits").delete().eq("id", outfit["id"]).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Couldn't delete: {e}")

            st.markdown("</div>", unsafe_allow_html=True)
