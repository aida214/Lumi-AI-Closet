"""One wardrobe tile: photo, details, quick actions and an edit/remove popover."""
import streamlit as st

from database import repository as repo
from utils.constants import CATEGORIES, SEASONS, STYLES
from utils.ui import chips_html, esc, image_box, run_action, show_html, panel


def _worn_line(info, today):
    if not info:
        return "Not worn yet"
    days = (today - info["last"]).days
    when = "today" if days <= 0 else "yesterday" if days == 1 else f"{days} days ago"
    times = "time" if info["count"] == 1 else "times"
    return f"Worn {info['count']} {times}, last {when}"


def _toggle_favourite(item_id, value):
    run_action(repo.update_item, item_id, {"favorite": value})


def _wore_today(uid, item_id, day):
    run_action(repo.log_wear, uid, [item_id], day, success="Logged as worn today")


def _save_edit(item_id):
    s = st.session_state
    name = (s.get(f"e_name_{item_id}") or "").strip()
    if not name:
        st.toast("A piece needs a name.")
        return
    price = s.get(f"e_price_{item_id}") or 0
    run_action(repo.update_item, item_id, {
        "name": name,
        "category": s.get(f"e_cat_{item_id}"),
        "color": (s.get(f"e_color_{item_id}") or "").strip().lower() or None,
        "season": s.get(f"e_season_{item_id}"),
        "style": s.get(f"e_style_{item_id}"),
        "brand": (s.get(f"e_brand_{item_id}") or "").strip() or None,
        "price": float(price) if price else None,
    }, success="Changes saved")


def _remove(item):
    run_action(repo.delete_item, item, success="Piece removed")


def _index(options, value):
    return options.index(value) if value in options else 0


def clothing_card(item, info, uid, today):
    item_id = str(item["id"])
    name = item.get("name") or item.get("category") or "Untitled piece"
    sub = item.get("brand") or item.get("category") or ""
    favourite = bool(item.get("favorite"))
    labels = [item.get("category"), item.get("color"), item.get("season"), item.get("style")]
    if favourite:
        labels.insert(0, "Favourite")

    with panel("tile", item_id):
        show_html(image_box(item.get("image_url"), name))
        show_html(f'<div class="lc-name">{esc(name)}</div><div class="lc-meta">{esc(sub)}</div>'
                  f'{chips_html(labels)}<div class="lc-meta">{esc(_worn_line(info, today))}</div>')
        left, right = st.columns(2)
        with left:
            st.button("Unfavourite" if favourite else "Favourite", key=f"fav_{item_id}",
                      on_click=_toggle_favourite, args=(item_id, not favourite), width="stretch")
        with right:
            st.button("Wore it", key=f"wore_{item_id}", on_click=_wore_today,
                      args=(uid, item_id, today), width="stretch",
                      help="Log this piece as worn today")
        with st.popover("Edit or remove"):
            with st.form(f"edit_form_{item_id}", border=False):
                st.text_input("Name", value=item.get("name") or "", key=f"e_name_{item_id}")
                st.selectbox("Category", CATEGORIES, index=_index(CATEGORIES, item.get("category")),
                             key=f"e_cat_{item_id}")
                st.text_input("Colour", value=item.get("color") or "", key=f"e_color_{item_id}")
                st.selectbox("Season", SEASONS, index=_index(SEASONS, item.get("season")),
                             key=f"e_season_{item_id}")
                st.selectbox("Style", STYLES, index=_index(STYLES, item.get("style")),
                             key=f"e_style_{item_id}")
                st.text_input("Brand", value=item.get("brand") or "", key=f"e_brand_{item_id}")
                st.number_input("Price paid (optional)", min_value=0.0, step=1.0,
                                value=float(item.get("price") or 0), key=f"e_price_{item_id}")
                st.form_submit_button("Save changes", type="primary", width="stretch",
                                      on_click=_save_edit, args=(item_id,))
            st.checkbox("I want to remove this piece", key=f"rm_ok_{item_id}")
            st.button("Remove from closet", key=f"rm_{item_id}", width="stretch",
                      disabled=not st.session_state.get(f"rm_ok_{item_id}", False),
                      on_click=_remove, args=(item,))
