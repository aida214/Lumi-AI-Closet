"""Small helpers for building the interface safely.

Anything that comes from a user or from the database MUST go through esc()
before it is placed in HTML.
"""
import html as _html

import streamlit as st

from utils.logging_config import get_logger, report_error

log = get_logger("ui")


def esc(value):
    """HTML-escape and collapse whitespace so one value can never break the markup."""
    if value is None:
        return ""
    return _html.escape(" ".join(str(value).split()), quote=True)


def compact(markup):
    return "".join(line.strip() for line in markup.strip().splitlines())


def show_html(markup):
    st.markdown(compact(markup), unsafe_allow_html=True)


def panel(kind, key):
    """A styled container. kind: curve, sheet, tile or chip. key must be unique."""
    return st.container(key=f"panel-{kind}-{key}")


def page_header(title, subtitle=""):
    sub = f"<p>{esc(subtitle)}</p>" if subtitle else ""
    show_html(f'<div class="lc-pagehead"><h1>{esc(title)}</h1>{sub}</div>')


def section_title(title):
    show_html(f'<div class="lc-h2">{esc(title)}</div>')


def chip_row(labels, dark_first=False):
    chips = []
    for i, label in enumerate(l for l in labels if l):
        cls = "lc-chip dark" if dark_first and i == 0 else "lc-chip"
        chips.append(f'<span class="{cls}">{esc(label)}</span>')
    if chips:
        show_html(f'<div class="lc-chiprow">{"".join(chips)}</div>')


def chips_html(labels):
    chips = "".join(f'<span class="lc-chip">{esc(l)}</span>' for l in labels if l)
    return f'<div class="lc-chips">{chips}</div>' if chips else ""


def image_box(url, alt=""):
    if url:
        inner = f'<img src="{esc(url)}" alt="{esc(alt)}" loading="lazy">'
    else:
        inner = '<span class="lc-noimg">No photo</span>'
    return f'<div class="lc-img">{inner}</div>'


def collage(urls):
    urls = [u for u in urls if u][:4]
    if not urls:
        return '<div class="lc-img"><span class="lc-noimg">No photos</span></div>'
    cells = "".join(f'<div class="lc-cell"><img src="{esc(u)}" alt="" loading="lazy"></div>' for u in urls)
    return f'<div class="lc-collage n{len(urls)}">{cells}</div>'


def item_label(item):
    name = item.get("name") or item.get("category") or "Piece"
    color = item.get("color")
    return f"{name} ({color})" if color else name


def friendly_error(exc):
    """Short, plain message for the person using the app."""
    text = str(exc).lower()
    if "invalid login credentials" in text:
        return "That email and password do not match."
    if "email not confirmed" in text:
        return "Please confirm your email first, then log in."
    if "already registered" in text or "already been registered" in text:
        return "An account with that email already exists. Try logging in."
    if "rate limit" in text or "too many" in text or "429" in text:
        return "Too many attempts. Please wait a minute and try again."
    if "jwt" in text or "token" in text:
        return "Your session expired. Please log in again."
    if "row-level security" in text or "permission denied" in text:
        return "You do not have permission to do that."
    if "network" in text or "timed out" in text or "connection" in text:
        return "Could not reach the server. Check your connection and try again."
    return "Something went wrong. Please try again."


def run_action(fn, *args, success=None, **kwargs):
    """Run a database action from a button callback, report the result with a toast."""
    try:
        result = fn(*args, **kwargs)
    except Exception as exc:
        report_error(log, f"Action {getattr(fn, '__name__', 'action')} failed", exc)
        st.toast(friendly_error(exc))
        return False
    if success:
        st.toast(success)
    return result if result is not None else True


def empty_state(title, body, button_label=None, target=None, key="empty"):
    with panel("chip", key):
        show_html(f'<div class="lc-h2" style="margin-top:0">{esc(title)}</div><p>{esc(body)}</p>')
        if button_label and target:
            from components.navbar import set_page
            st.button(button_label, key=f"{key}_btn", on_click=set_page, args=(target,), type="primary")
