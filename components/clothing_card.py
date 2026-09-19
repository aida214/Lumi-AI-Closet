import streamlit as st
from database.supabase_client import supabase

CATEGORIES = ["Top", "Bottom", "Dress", "Outerwear", "Shoes", "Accessory"]
SEASONS = ["Spring", "Summer", "Autumn", "Winter", "All Season"]
STYLES = [
    "Casual", "Formal", "Streetwear", "Coquette", "Old Money",
    "Minimalist", "Y2K", "Sporty", "Vintage",
]


def clothing_card(item: dict, on_change=None):
    """
    Render one wardrobe item as a soft, rounded card.
    `on_change` is called after a favorite/edit/delete mutates the row,
    so the parent page can refresh its list.
    """

    name = item.get("name") or item.get("category") or "Clothing Item"
    brand = item.get("brand") or ""
    category = item.get("category") or "Unknown"
    color = item.get("color") or "Unknown"
    season = item.get("season") or "All Season"
    style = item.get("style") or "Casual"
    favorite = item.get("favorite", False)
    item_id = item["id"]

    st.markdown('<div class="lc-card" style="padding:14px;">', unsafe_allow_html=True)

    if item.get("image_url"):
        st.image(item["image_url"], use_container_width=True)
    else:
        st.markdown(
            "<div style='height:180px;border-radius:16px;background:var(--blush-soft);"
            "display:flex;align-items:center;justify-content:center;font-size:2rem;'>👗</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <h4 style="margin:12px 0 2px 0; color:var(--ink);">{name}</h4>
        <p class="lc-muted" style="margin:0 0 10px 0; font-size:0.85rem;">🏷 {brand or 'Unknown brand'}</p>
        <div>
            <span class="lc-pill">🎨 {color}</span>
            <span class="lc-pill lc-pill-lav">👗 {category}</span>
            <span class="lc-pill">🍂 {season}</span>
            <span class="lc-pill lc-pill-lav">✨ {style}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    b1, b2, b3 = st.columns(3)

    with b1:
        heart = "❤️" if favorite else "🤍"
        if st.button(heart, key=f"fav_{item_id}", use_container_width=True):
            try:
                supabase.table("wardrobe").update(
                    {"favorite": not favorite}
                ).eq("id", item_id).execute()
                if on_change:
                    on_change()
                st.rerun()
            except Exception as e:
                st.error(f"Couldn't update favorite: {e}")

    with b2:
        if st.button("✏️", key=f"edit_{item_id}", use_container_width=True):
            st.session_state[f"editing_{item_id}"] = not st.session_state.get(
                f"editing_{item_id}", False
            )

    with b3:
        if st.button("🗑️", key=f"delete_{item_id}", use_container_width=True):
            st.session_state[f"confirm_delete_{item_id}"] = True

    # ---------- Delete confirmation ----------
    if st.session_state.get(f"confirm_delete_{item_id}"):
        st.warning("Remove this piece from your wardrobe?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, delete", key=f"confirm_yes_{item_id}", use_container_width=True):
                try:
                    supabase.table("wardrobe").delete().eq("id", item_id).execute()
                    st.session_state.pop(f"confirm_delete_{item_id}", None)
                    if on_change:
                        on_change()
                    st.rerun()
                except Exception as e:
                    st.error(f"Delete failed: {e}")
        with c2:
            if st.button("Cancel", key=f"confirm_no_{item_id}", use_container_width=True):
                st.session_state.pop(f"confirm_delete_{item_id}", None)
                st.rerun()

    # ---------- Inline edit ----------
    if st.session_state.get(f"editing_{item_id}"):
        with st.form(key=f"edit_form_{item_id}"):
            new_name = st.text_input("Name", value=item.get("name") or "")
            ec1, ec2 = st.columns(2)
            with ec1:
                new_category = st.selectbox(
                    "Category", CATEGORIES,
                    index=CATEGORIES.index(category) if category in CATEGORIES else 0,
                )
                new_color = st.text_input("Colour", value=color if color != "Unknown" else "")
                new_season = st.selectbox(
                    "Season", SEASONS,
                    index=SEASONS.index(season) if season in SEASONS else 4,
                )
            with ec2:
                new_brand = st.text_input("Brand", value=brand)
                new_style = st.selectbox(
                    "Style", STYLES,
                    index=STYLES.index(style) if style in STYLES else 0,
                )

            saved = st.form_submit_button("💾 Save changes", use_container_width=True)
            if saved:
                try:
                    supabase.table("wardrobe").update(
                        {
                            "name": new_name,
                            "category": new_category,
                            "color": new_color,
                            "season": new_season,
                            "brand": new_brand,
                            "style": new_style,
                        }
                    ).eq("id", item_id).execute()
                    st.session_state[f"editing_{item_id}"] = False
                    if on_change:
                        on_change()
                    st.rerun()
                except Exception as e:
                    st.error(f"Couldn't save changes: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
