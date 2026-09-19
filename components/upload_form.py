import streamlit as st
import uuid
import traceback

from database.supabase_client import supabase
from utils.autotagger import analyse_clothing

CATEGORIES = ["Top", "Bottom", "Dress", "Outerwear", "Shoes", "Accessory"]
SEASONS = ["Spring", "Summer", "Autumn", "Winter", "All Season"]
STYLES = [
    "Casual", "Formal", "Streetwear", "Coquette", "Old Money",
    "Minimalist", "Y2K", "Sporty", "Vintage",
]


def upload_form(on_saved=None):
    st.markdown("#### ✨ Add new clothing")
    st.caption("Upload a photo and Lumi will suggest the tags for you.")

    uploaded_file = st.file_uploader(
        "Choose an image", type=["png", "jpg", "jpeg"], label_visibility="collapsed"
    )

    if uploaded_file is None:
        return

    img_col, form_col = st.columns([1, 1.4])

    with img_col:
        st.image(uploaded_file, use_container_width=True)

    if "ai_tags" not in st.session_state:
        st.session_state.ai_tags = {}

    if "last_uploaded" not in st.session_state:
        st.session_state.last_uploaded = None

    # Only analyse once per uploaded image
    if st.session_state.last_uploaded != uploaded_file.name:
        with st.spinner("✨ Lumi is analysing your clothing..."):
            try:
                tags = analyse_clothing(uploaded_file.getvalue())
                st.session_state.ai_tags = tags
                st.session_state.last_uploaded = uploaded_file.name
                if any(tags.values()):
                    st.toast("AI tags ready — feel free to tweak them.", icon="✨")
            except Exception:
                traceback.print_exc()
                st.session_state.ai_tags = {}
                st.session_state.last_uploaded = uploaded_file.name
                st.info("AI tagging is unavailable right now — no worries, just fill it in below.")

    tags = st.session_state.ai_tags or {}

    with form_col:
        name = st.text_input("📝 Clothing name", value=tags.get("name", ""))

        c1, c2 = st.columns(2)
        with c1:
            category = st.selectbox(
                "👗 Category", CATEGORIES,
                index=CATEGORIES.index(tags["category"]) if tags.get("category") in CATEGORIES else 0,
            )
            color = st.text_input("🎨 Colour", value=tags.get("color", ""))
            season = st.selectbox(
                "🍂 Season", SEASONS,
                index=SEASONS.index(tags["season"]) if tags.get("season") in SEASONS else 4,
            )
        with c2:
            brand = st.text_input("🏷️ Brand", value=tags.get("brand", ""))
            style = st.selectbox(
                "✨ Style", STYLES,
                index=STYLES.index(tags["style"]) if tags.get("style") in STYLES else 0,
            )

        st.markdown("<div class='lc-divider'></div>", unsafe_allow_html=True)

        if st.button("💖 Save to my closet", use_container_width=True, type="primary"):
            try:
                extension = uploaded_file.name.split(".")[-1].lower()
                file_name = f"{uuid.uuid4()}.{extension}"

                supabase.storage.from_("wardrobe").upload(
                    path=file_name,
                    file=uploaded_file.getvalue(),
                    file_options={"content-type": uploaded_file.type},
                )

                image_url = supabase.storage.from_("wardrobe").get_public_url(file_name)

                supabase.table("wardrobe").insert(
                    {
                        "user_id": str(st.session_state["user"].id),
                        "image_url": image_url,
                        "name": name,
                        "category": category,
                        "color": color,
                        "brand": brand,
                        "season": season,
                        "style": style,
                    }
                ).execute()

                st.session_state.ai_tags = {}
                st.session_state.last_uploaded = None

                st.success("🩷 Added to your wardrobe!")
                st.balloons()
                if on_saved:
                    on_saved()
                st.rerun()

            except Exception as e:
                traceback.print_exc()
                st.error(f"Upload failed: {e}")
