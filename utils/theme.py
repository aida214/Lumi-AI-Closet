"""
Lumi Closet design system.

One place that defines the whole visual language (color tokens, type,
components) and injects it as CSS. Every page calls `inject_theme()`
once, then uses the small helper components below (`card_open/close`,
`section_title`, `pill`, `empty_state`) to stay visually consistent
without repeating raw HTML everywhere.
"""

import streamlit as st

# ---------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------
# Color   — blush / rosewood / lavender / cream, soft dark plum ink
# Type    — "Fraunces" (serif, editorial, a little warmth) for display
#           headlines, "Plus Jakarta Sans" for everything functional
# Shape   — 20-28px radii, pill buttons, hairline borders, soft shadow

TOKENS = {
    "bg": "#FBF6F8",
    "surface": "#FFFFFF",
    "glass": "rgba(255,255,255,0.68)",
    "blush": "#F8D9E4",
    "blush_soft": "#FCE9EF",
    "lavender": "#E7E0F6",
    "lavender_soft": "#F1EDFA",
    "cream": "#FFF8F1",
    "primary": "#C4688F",
    "primary_dark": "#A44D74",
    "primary_light": "#E7A9C0",
    "ink": "#2B2330",
    "ink_soft": "#6F6574",
    "ink_faint": "#B3A9B6",
    "line": "#F0E1E8",
    "success": "#7FAE8B",
    "shadow": "0 12px 32px rgba(196,104,143,0.14)",
    "shadow_sm": "0 4px 14px rgba(43,35,48,0.06)",
}


def inject_theme():
    t = TOKENS
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,500&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">

        <style>
        :root {{
            --bg: {t['bg']};
            --surface: {t['surface']};
            --glass: {t['glass']};
            --blush: {t['blush']};
            --blush-soft: {t['blush_soft']};
            --lavender: {t['lavender']};
            --lavender-soft: {t['lavender_soft']};
            --cream: {t['cream']};
            --primary: {t['primary']};
            --primary-dark: {t['primary_dark']};
            --primary-light: {t['primary_light']};
            --ink: {t['ink']};
            --ink-soft: {t['ink_soft']};
            --ink-faint: {t['ink_faint']};
            --line: {t['line']};
            --success: {t['success']};
            --shadow: {t['shadow']};
            --shadow-sm: {t['shadow_sm']};
        }}

        /* ---------- base ---------- */
        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            color: var(--ink);
        }}
        .stApp {{
            background:
                radial-gradient(circle at 12% 0%, var(--blush-soft) 0%, transparent 45%),
                radial-gradient(circle at 100% 15%, var(--lavender-soft) 0%, transparent 40%),
                var(--bg);
        }}
        h1, h2, h3, h4 {{
            font-family: 'Fraunces', serif;
            color: var(--ink);
            letter-spacing: -0.01em;
        }}
        p, span, label, div {{
            letter-spacing: 0.01em;
        }}
        a {{ color: var(--primary-dark); }}

        /* ---------- hide default streamlit chrome ---------- */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header[data-testid="stHeader"] {{
            background: transparent;
        }}
        div[data-testid="stDecoration"] {{ display: none; }}
        div[data-testid="stToolbar"] {{ display: none; }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1160px;
        }}

        /* ---------- sidebar ---------- */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, var(--blush-soft) 130%);
            border-right: 1px solid var(--line);
        }}
        section[data-testid="stSidebar"] .block-container {{
            padding-top: 1.5rem;
        }}

        /* ---------- buttons: soft pill everywhere ---------- */
        .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
            border-radius: 999px !important;
            border: 1px solid var(--line) !important;
            background: var(--surface) !important;
            color: var(--ink) !important;
            font-weight: 600 !important;
            padding: 0.55rem 1.4rem !important;
            transition: all 0.18s ease !important;
            box-shadow: var(--shadow-sm) !important;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            transform: translateY(-1px);
            border-color: var(--primary-light) !important;
            color: var(--primary-dark) !important;
            box-shadow: var(--shadow) !important;
        }}
        .stButton > button:active {{ transform: translateY(0px); }}

        /* primary buttons: type=primary */
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            filter: brightness(1.06);
            color: #FFFFFF !important;
        }}

        /* ---------- inputs ---------- */
        .stTextInput input, .stTextArea textarea, .stNumberInput input,
        .stDateInput input {{
            border-radius: 16px !important;
            border: 1px solid var(--line) !important;
            background: var(--surface) !important;
            padding: 0.6rem 0.9rem !important;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus {{
            border-color: var(--primary-light) !important;
            box-shadow: 0 0 0 3px rgba(196,104,143,0.12) !important;
        }}
        div[data-baseweb="select"] > div {{
            border-radius: 16px !important;
            border: 1px solid var(--line) !important;
            background: var(--surface) !important;
        }}

        /* radio rendered as pill tabs */
        div[role="radiogroup"] {{
            gap: 0.4rem;
        }}
        div[role="radiogroup"] label {{
            border: 1px solid var(--line);
            padding: 0.35rem 1rem;
            border-radius: 999px;
            background: var(--surface);
        }}

        /* ---------- metrics ---------- */
        div[data-testid="stMetric"] {{
            background: var(--glass);
            backdrop-filter: blur(6px);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 14px 18px;
            box-shadow: var(--shadow-sm);
        }}
        div[data-testid="stMetricLabel"] {{ color: var(--ink-soft); }}
        div[data-testid="stMetricValue"] {{
            color: var(--primary-dark);
            font-family: 'Fraunces', serif;
        }}

        /* ---------- expander as soft card ---------- */
        div[data-testid="stExpander"] {{
            border: 1px solid var(--line) !important;
            border-radius: 20px !important;
            background: var(--surface) !important;
            box-shadow: var(--shadow-sm);
            overflow: hidden;
        }}

        /* ---------- tabs ---------- */
        button[data-baseweb="tab"] {{
            font-weight: 600;
            color: var(--ink-soft);
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: var(--primary-dark);
        }}
        div[data-baseweb="tab-highlight"] {{
            background-color: var(--primary) !important;
        }}

        /* ---------- misc ---------- */
        hr {{ border-color: var(--line) !important; }}
        div[data-testid="stImage"] img {{
            border-radius: 18px;
        }}
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-thumb {{ background: var(--blush); border-radius: 8px; }}

        /* ---------- custom component classes (used via st.markdown) ---------- */
        .lc-card {{
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 22px 24px;
            box-shadow: var(--shadow-sm);
            transition: box-shadow 0.2s ease, transform 0.2s ease;
        }}
        .lc-card:hover {{
            box-shadow: var(--shadow);
        }}
        .lc-hero {{
            background: linear-gradient(135deg, var(--blush) 0%, var(--cream) 65%, #FFFFFF 100%);
            border-radius: 28px;
            padding: 34px 38px;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }}
        .lc-eyebrow {{
            color: var(--primary-dark);
            font-weight: 600;
            font-size: 0.82rem;
        }}
        .lc-pill {{
            display: inline-block;
            background: var(--blush-soft);
            color: var(--primary-dark);
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            margin: 3px 4px 3px 0;
        }}
        .lc-pill-lav {{
            background: var(--lavender-soft);
            color: #6B5FA8;
        }}
        .lc-muted {{ color: var(--ink-soft); }}
        .lc-divider {{
            height: 1px;
            background: var(--line);
            margin: 20px 0;
            border: none;
        }}
        .lc-empty {{
            text-align:center;
            padding: 46px 24px;
            border: 1px dashed var(--line);
            border-radius: 24px;
            background: var(--glass);
        }}
        .lc-chat-bubble-user {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: #fff;
            padding: 12px 16px;
            border-radius: 18px 18px 4px 18px;
            margin: 6px 0;
            max-width: 78%;
            margin-left: auto;
        }}
        .lc-chat-bubble-ai {{
            background: var(--surface);
            border: 1px solid var(--line);
            color: var(--ink);
            padding: 12px 16px;
            border-radius: 18px 18px 18px 4px;
            margin: 6px 0;
            max-width: 78%;
            box-shadow: var(--shadow-sm);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_title(eyebrow: str, title: str, subtitle: str = ""):
    sub = f'<p class="lc-muted" style="margin-top:2px;">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div style="margin-bottom:18px;">
            <div class="lc-eyebrow">{eyebrow}</div>
            <h2 style="margin:2px 0 0 0;">{title}</h2>
            {sub}
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(emoji: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="lc-empty">
            <div style="font-size:2.2rem;">{emoji}</div>
            <h4 style="margin:10px 0 4px 0;">{title}</h4>
            <p class="lc-muted" style="margin:0;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
