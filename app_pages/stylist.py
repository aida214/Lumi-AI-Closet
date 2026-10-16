"""Stylist chat. Uses OpenAI when a key is configured, rules over your closet otherwise."""
import streamlit as st

from database import repository as repo
from utils import stylist
from utils.context import load_context
from utils.insights import wear_summary
from utils.logging_config import get_logger, report_error
from utils.ratelimit import session_limiter
from utils.ui import friendly_error, page_header
from utils.weather import feels_temp

log = get_logger("stylist_page")

QUICK_PROMPTS = [
    "What should I wear today?",
    "An outfit for class on campus",
    "Something for dinner tonight",
    "What goes with pink?",
]


def _queue(prompt):
    st.session_state["pending_prompt"] = prompt


def _clear(uid):
    try:
        repo.clear_chat(uid)
    except Exception as exc:
        report_error(log, "Clearing chat failed", exc)
        st.toast(friendly_error(exc))


def _answer(ctx, question, history, items, wear):
    forecast = ctx["forecast"]
    temp = feels_temp(forecast["today_max"], forecast["today_min"]) if forecast else None
    rain = forecast["rain_chance"] if forecast else None
    weather_text = ""
    if forecast:
        weather_text = f'{round(temp)} degrees C, {forecast["now_label"]}, {forecast["rain_chance"] or 0}% chance of rain'
    if stylist.ai_available():
        limiter = session_limiter(st.session_state, "ai_chat", max_calls=12, per_seconds=300)
        if not limiter.allow():
            return (f"You have asked a lot of questions quickly. Please wait about {limiter.retry_after()} "
                    "seconds. Meanwhile, here is a rule-based suggestion: " +
                    stylist.basic_reply(question, items, temp, rain, ctx["styles"], wear, today=ctx["today"]))
        reply = stylist.ask_ai(question, history, items, weather_text, ", ".join(ctx["styles"]))
        if reply:
            return reply
        prefix = "The AI service did not respond, so this answer uses simple rules instead. "
    else:
        prefix = ""
    seed = len(history) + ctx["today"].toordinal()
    return prefix + stylist.basic_reply(question, items, temp, rain, ctx["styles"], wear,
                                        seed=seed, today=ctx["today"])


def show_stylist():
    ctx = load_context()
    uid = ctx["uid"]
    items = repo.list_items(uid)
    wear = wear_summary(repo.list_wear(uid))
    page_header("Ask Lumi", "Outfit questions answered from the pieces you actually own.")

    if stylist.ai_available():
        st.caption("Connected to an AI model. Replies take your closet and today's weather into account.")
    else:
        st.caption("Basic mode: answers come from rules applied to your closet. "
                   "Add OPENAI_API_KEY to enable open-ended chat.")

    history = repo.list_chat(uid)
    cols = st.columns(len(QUICK_PROMPTS))
    for col, prompt in zip(cols, QUICK_PROMPTS):
        with col:
            st.button(prompt, key=f"qp_{prompt}", on_click=_queue, args=(prompt,), width="stretch")

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["message"])
    if not history:
        st.caption("No messages yet. Pick a question above or type your own below.")

    typed = st.chat_input("Ask about an outfit, a colour or an occasion")
    question = st.session_state.pop("pending_prompt", None) or typed
    if question:
        question = question.strip()[:500]
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking"):
                answer = _answer(ctx, question, history, items, wear)
            st.markdown(answer)
        try:
            repo.add_chat(uid, "user", question)
            repo.add_chat(uid, "assistant", answer)
        except Exception as exc:
            report_error(log, "Saving chat failed", exc)
            st.toast(friendly_error(exc))

    if history:
        st.button("Clear conversation", key="clear_chat", on_click=_clear, args=(uid,))
