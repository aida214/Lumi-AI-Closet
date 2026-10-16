"""Add a piece: upload a photo, review the suggested tags, save."""
import streamlit as st

from database import repository as repo
from utils.autotagger import analyse_clothing
from utils.constants import CATEGORIES, MAX_UPLOAD_MB, SEASONS, STYLES
from utils.images import ImageError, prepare_upload
from utils.logging_config import get_logger, report_error
from utils.ratelimit import session_limiter
from utils.ui import friendly_error

log = get_logger("upload")

SOURCE_NOTE = {
    "ai": "Tags were suggested by AI from your photo. Please check them.",
    "colour": "Colour was read from the photo. Fill in the rest below.",
    "none": "Fill in the details below.",
}


def _pick(options, value):
    return options.index(value) if value in options else 0


def show_upload_form(uid):
    version = st.session_state.setdefault("upload_version", 0)
    file = st.file_uploader(
        f"Photo of the piece (JPG, PNG or WebP, up to {MAX_UPLOAD_MB} MB)",
        type=["jpg", "jpeg", "png", "webp"], key=f"uploader_{version}",
        help="Photos from an iPhone saved as HEIC are not supported. Export them as JPG first.",
    )
    if file is None:
        return

    try:
        photo = prepare_upload(file.getvalue())
    except ImageError as exc:
        st.error(str(exc))
        return

    file_key = f"{version}_{file.name}_{file.size}"
    analysed = st.session_state.setdefault("analysed", {})
    if file_key not in analysed:
        limiter = session_limiter(st.session_state, "ai_tag", max_calls=15, per_seconds=600)
        if limiter.allow():
            with st.spinner("Reading your photo"):
                analysed[file_key] = analyse_clothing(photo)
        else:
            analysed[file_key] = (
                {"name": "", "category": "", "color": "", "season": "", "style": "", "brand": ""}, "none")
            st.info(f"Auto-tagging is paused for about {limiter.retry_after()} seconds. You can still fill in the tags by hand.")
    tags, source = analysed[file_key]

    preview, form = st.columns([1, 2])
    with preview:
        st.image(photo, width="stretch")
    with form:
        st.caption(SOURCE_NOTE[source])
        name = st.text_input("Name", value=tags["name"], key=f"up_name_{file_key}",
                             placeholder="Cream knit sweater")
        c1, c2 = st.columns(2)
        with c1:
            category = st.selectbox("Category", CATEGORIES, index=_pick(CATEGORIES, tags["category"]),
                                    key=f"up_cat_{file_key}")
            season = st.selectbox("Season", SEASONS, index=_pick(SEASONS, tags["season"]),
                                  key=f"up_season_{file_key}")
            brand = st.text_input("Brand (optional)", value=tags["brand"], key=f"up_brand_{file_key}")
        with c2:
            color = st.text_input("Colour", value=tags["color"], key=f"up_color_{file_key}")
            style = st.selectbox("Style", STYLES, index=_pick(STYLES, tags["style"]), key=f"up_style_{file_key}")
            price = st.number_input("Price paid (optional)", min_value=0.0, step=1.0, value=0.0,
                                    key=f"up_price_{file_key}")

        if st.button("Save to closet", type="primary", key=f"up_save_{file_key}"):
            if not name.strip():
                st.error("Give the piece a name first.")
                return
            limiter = session_limiter(st.session_state, "upload", max_calls=30, per_seconds=600)
            if not limiter.allow():
                st.error(f"You are adding pieces very quickly. Try again in about {limiter.retry_after()} seconds.")
                return
            try:
                with st.spinner("Saving"):
                    url = repo.upload_image(uid, photo)
                    repo.add_item(uid, {
                        "name": name.strip(), "category": category, "color": color.strip().lower(),
                        "season": season, "style": style, "brand": brand.strip(),
                        "price": float(price) if price else None, "image_url": url,
                    })
            except Exception as exc:
                report_error(log, "Saving a piece failed", exc)
                st.error(friendly_error(exc))
                return
            st.session_state["upload_version"] = version + 1
            analysed.pop(file_key, None)
            st.toast("Added to your closet")
            st.rerun()
