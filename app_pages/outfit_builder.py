import streamlit as st

from database.supabase_client import supabase
from utils.theme import section_title, empty_state

SLOTS = [
    ("top", "👚 Top", "Top"),
    ("bottom", "👖 Bottom", "Bottom"),
    ("dress", "👗 Dress", "Dress"),
    ("outerwear", "🧥 Outerwear", "Outerwear"),
    ("shoes", "👟 Shoes", "Shoes"),
    ("accessory", "👜 Bag / Accessory", "Accessory"),
]


def _load_wardrobe(user_id: str):
    try:
        resp = (
            supabase.table("wardrobe")
            .select("id, name, category, image_url, color")
            .eq("user_id", user_id)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def show_outfit_builder():
    section_title("CREATE A LOOK", "Outfit Builder", "Mix and match pieces from your closet.")

    user_id = str(st.session_state["user"].id)
    clothes = _load_wardrobe(user_id)

    if not clothes:
        empty_state("🎀", "Nothing to build with yet", "Add a few pieces to your wardrobe first.")
        return

    by_category = {}
    for item in clothes:
        by_category.setdefault(item.get("category"), []).append(item)

    if "outfit_selection" not in st.session_state:
        st.session_state.outfit_selection = {}

    st.markdown('<div class="lc-card">', unsafe_allow_html=True)

    for slot_key, label, category in SLOTS:
        options = by_category.get(category, [])
        choice_labels = ["None"] + [item.get("name") or f"{category} item" for item in options]

        selected_label = st.selectbox(label, choice_labels, key=f"slot_{slot_key}")

        if selected_label == "None":
            st.session_state.outfit_selection.pop(slot_key, None)
        else:
            match = next(
                (i for i in options if (i.get("name") or f"{category} item") == selected_label),
                None,
            )
            st.session_state.outfit_selection[slot_key] = match

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    chosen = [v for v in st.session_state.outfit_selection.values() if v]

    st.markdown("#### 🩷 Your outfit")

    if not chosen:
        st.markdown(
            "<p class='lc-muted'>Pick at least one piece above to preview your outfit.</p>",
            unsafe_allow_html=True,
        )
    else:
        cols = st.columns(len(chosen))
        for col, item in zip(cols, chosen):
            with col:
                st.markdown('<div class="lc-card" style="padding:10px;">', unsafe_allow_html=True)
                if item.get("image_url"):
                    st.image(item["image_url"], use_container_width=True)
                st.caption(item.get("name") or item.get("category"))
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("save_outfit_form"):
            title = st.text_input("Outfit name", placeholder="e.g. Campus Coffee Run")
            notes = st.text_area("Notes (optional)", placeholder="What's this outfit for?")
            save = st.form_submit_button("💾 Save this outfit", use_container_width=True, type="primary")

        if save:
            if not title.strip():
                st.error("Give your outfit a name first.")
            else:
                try:
                    outfit_resp = (
                        supabase.table("saved_outfits")
                        .insert({"user_id": user_id, "title": title, "notes": notes})
                        .execute()
                    )
                    outfit_id = outfit_resp.data[0]["id"]

                    rows = [
                        {"outfit_id": outfit_id, "wardrobe_item_id": item["id"]}
                        for item in chosen
                    ]
                    if rows:
                        supabase.table("outfit_items").insert(rows).execute()

                    st.success("🩷 Outfit saved! Find it under Saved Looks.")
                    st.session_state.outfit_selection = {}
                    st.balloons()
                except Exception as e:
                    st.error(f"Couldn't save outfit: {e}")
