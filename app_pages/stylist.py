import os
import random

import streamlit as st

from database.supabase_client import supabase
from utils.theme import section_title

SYSTEM_PROMPT = (
    "You are Lumi, a warm, encouraging AI fashion stylist inside the app "
    "'Lumi Closet'. You help with outfit ideas, colour combinations, "
    "styling advice, occasion outfits, weather-appropriate outfits, "
    "combining pieces the user already owns, packing, and capsule "
    "wardrobe suggestions. Keep replies short (2-4 sentences), specific, "
    "and encouraging, in a soft Korean-fashion-app tone. When the user's "
    "wardrobe is provided, reference actual pieces from it by name."
)

FALLBACK_TIPS = [
    "Try your cream cardigan with the black pleated skirt and white sneakers — add a small shoulder bag for a clean, effortless look.",
    "A monochrome outfit in soft neutrals instantly reads more polished than mixing five colours.",
    "Layering a light knit over a slip dress is a great transitional-weather trick.",
    "For a night out, swap your everyday sneakers for a low heel and add one statement accessory — nothing more.",
    "Capsule tip: five tops, three bottoms and two pairs of shoes gets you to roughly fifteen outfits.",
]


def _get_openai_key():
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY")


def _load_history(user_id: str):
    try:
        resp = (
            supabase.table("chat_history")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at")
            .limit(50)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def _save_message(user_id: str, role: str, message: str):
    try:
        supabase.table("chat_history").insert(
            {"user_id": user_id, "role": role, "message": message}
        ).execute()
    except Exception:
        pass  # chat still works in-session even if persistence fails


def _wardrobe_summary(user_id: str) -> str:
    try:
        resp = (
            supabase.table("wardrobe")
            .select("name, category, color, style, season")
            .eq("user_id", user_id)
            .limit(40)
            .execute()
        )
        items = resp.data or []
    except Exception:
        items = []

    if not items:
        return "The user's wardrobe is currently empty."

    lines = [
        f"- {i.get('name') or i.get('category')} ({i.get('category')}, {i.get('color')}, {i.get('style')})"
        for i in items
    ]
    return "The user's wardrobe includes:\n" + "\n".join(lines)


def _ask_ai(user_id: str, question: str, history: list) -> str:
    api_key = _get_openai_key()
    if not api_key:
        return random.choice(FALLBACK_TIPS)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append({"role": "system", "content": _wardrobe_summary(user_id)})
        for h in history[-10:]:
            role = "assistant" if h.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": h.get("message", "")})
        messages.append({"role": "user", "content": question})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=220,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()

    except Exception:
        return (
            "I couldn't reach my styling brain just now, but here's a tip "
            "in the meantime: " + random.choice(FALLBACK_TIPS)
        )


def show_stylist():
    section_title("AI STYLIST", "Ask Lumi", "Your always-on fashion assistant.")

    user_id = str(st.session_state["user"].id)

    if "stylist_history" not in st.session_state:
        st.session_state.stylist_history = _load_history(user_id)

    history = st.session_state.stylist_history

    st.markdown('<div class="lc-card" style="min-height:340px;">', unsafe_allow_html=True)

    if not history:
        st.markdown(
            "<p class='lc-muted'>Ask me anything — \"What should I wear to "
            "university tomorrow?\" or \"What goes with a lavender skirt?\"</p>",
            unsafe_allow_html=True,
        )
    else:
        for h in history:
            bubble_class = "lc-chat-bubble-user" if h.get("role") == "user" else "lc-chat-bubble-ai"
            st.markdown(
                f'<div class="{bubble_class}">{h.get("message", "")}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("stylist_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            question = st.text_input(
                "Message", placeholder="What should I wear today?",
                label_visibility="collapsed",
            )
        with c2:
            sent = st.form_submit_button("Send 💌", use_container_width=True)

    if sent and question.strip():
        history.append({"role": "user", "message": question})
        _save_message(user_id, "user", question)

        with st.spinner("Lumi is thinking..."):
            answer = _ask_ai(user_id, question, history)

        history.append({"role": "assistant", "message": answer})
        _save_message(user_id, "assistant", answer)

        st.session_state.stylist_history = history
        st.rerun()

    st.caption(
        "Try: outfit ideas · colour combinations · occasion outfits · "
        "packing · capsule wardrobe suggestions"
    )
