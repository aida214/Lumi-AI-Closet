import random
from datetime import datetime

import streamlit as st

from database.supabase_client import supabase
from components.navbar import go
from components.metrics import stat_row

INSPIRATION = [
    "Try pairing a neutral top with your favourite jeans and white sneakers today.",
    "A cream cardigan over a slip dress feels effortless for a coffee run.",
    "Tuck in a fitted tee and add a belt to sharpen up wide-leg trousers.",
    "Layer a lightweight scarf over a plain outfit for instant polish.",
    "Monochrome pastels read expensive with almost zero effort.",
]


def _greeting_for_hour(hour: int) -> str:
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def show_dashboard():
    user = st.session_state.get("user")
    first_name = (getattr(user, "email", "") or "there").split("@")[0].title()

    # ---------------- Load wardrobe ----------------
    try:
        response = (
            supabase.table("wardrobe")
            .select("*")
            .eq("user_id", str(user.id))
            .order("created_at", desc=True)
            .execute()
        )
        clothes = response.data or []
    except Exception:
        clothes = []

    try:
        outfits_resp = (
            supabase.table("saved_outfits")
            .select("id, favorite")
            .eq("user_id", str(user.id))
            .execute()
        )
        outfits = outfits_resp.data or []
    except Exception:
        outfits = []

    total = len(clothes)
    favorites = sum(1 for item in clothes if item.get("favorite"))
    saved_looks = len(outfits)
    combos = total * (total - 1) // 2 if total > 1 else total

    # ---------------- Hero ----------------
    st.markdown(
        f"""
        <div class="lc-hero">
            <div class="lc-eyebrow">{_greeting_for_hour(datetime.now().hour).upper()}</div>
            <h1 style="margin:6px 0 4px 0;">{_greeting_for_hour(datetime.now().hour)}, {first_name} ♡</h1>
            <p class="lc-muted" style="font-size:1.05rem; margin:0;">
                Let's find something beautiful to wear today.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    stat_row(
        [
            ("Pieces", str(total), "👗"),
            ("Favorites", str(favorites), "❤️"),
            ("Saved Looks", str(saved_looks), "🩷"),
            ("Combinations", str(combos), "✨"),
        ]
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------- Today's outfit + weather ----------------
    left, right = st.columns([1.5, 1])

    with left:
        st.markdown('<div class="lc-card">', unsafe_allow_html=True)
        st.markdown("#### 🌤️ Today's outfit")

        if total == 0:
            st.markdown(
                "<p class='lc-muted'>Add a few pieces to your wardrobe and Lumi "
                "will start recommending outfits here.</p>",
                unsafe_allow_html=True,
            )
            if st.button("➕ Add your first piece", type="primary"):
                go("wardrobe")
        else:
            sample = random.sample(clothes, min(3, total))
            cols = st.columns(len(sample))
            for col, item in zip(cols, sample):
                with col:
                    if item.get("image_url"):
                        st.image(item["image_url"], use_container_width=True)
                    st.caption(item.get("name") or item.get("category") or "")
            st.markdown(
                "<p class='lc-muted' style='margin-top:8px;'>"
                "A soft, easy combination pulled straight from your closet."
                "</p>",
                unsafe_allow_html=True,
            )
            if st.button("🎀 Build on this in the Outfit Builder"):
                go("outfit_builder")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="lc-card">', unsafe_allow_html=True)
        st.markdown("#### ☁️ Today's weather")
        st.markdown(
            """
            <p class="lc-muted" style="margin-bottom:10px;">
                Mild and breezy, 18°C
            </p>
            <p style="margin:0;">Perfect for a light cardigan + skirt.</p>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Connect a weather source in Settings for live forecasts.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------- Quick actions ----------------
    st.markdown("#### ⚡ Quick actions")
    a1, a2, a3, a4, a5 = st.columns(5)
    with a1:
        if st.button("➕ Add to Wardrobe", use_container_width=True):
            go("wardrobe")
    with a2:
        if st.button("🎀 Create Outfit", use_container_width=True):
            go("outfit_builder")
    with a3:
        if st.button("🤖 Ask AI Stylist", use_container_width=True):
            go("stylist")
    with a4:
        if st.button("📅 Plan Outfits", use_container_width=True):
            go("planner")
    with a5:
        if st.button("🧳 Packing Assistant", use_container_width=True):
            go("packing")

    st.markdown("<div class='lc-divider'></div>", unsafe_allow_html=True)

    # ---------------- Recently added ----------------
    st.markdown("#### 🩷 Recently added")

    if not clothes:
        st.info("Upload your first clothing item to see it here!")
    else:
        cols = st.columns(min(4, len(clothes)))
        for i, item in enumerate(clothes[:4]):
            with cols[i]:
                st.markdown('<div class="lc-card" style="padding:10px;">', unsafe_allow_html=True)
                if item.get("image_url"):
                    st.image(item["image_url"], use_container_width=True)
                st.markdown(f"**{item.get('name') or item.get('category') or 'Item'}**")
                st.caption(item.get("brand") or "")
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='lc-divider'></div>", unsafe_allow_html=True)

    # ---------------- Daily inspiration ----------------
    st.markdown("#### ✨ Daily inspiration")
    st.markdown(
        f"""
        <div class="lc-card" style="background:var(--lavender-soft); border:none;">
            💡 {random.choice(INSPIRATION)}
        </div>
        """,
        unsafe_allow_html=True,
    )
