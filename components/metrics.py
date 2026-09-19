import streamlit as st


def stat_row(stats: list[tuple[str, str, str]]):
    """
    Render an even row of metric cards.
    stats: list of (label, value, icon) tuples, e.g. [("Pieces", "24", "👗")]
    """
    cols = st.columns(len(stats))
    for col, (label, value, icon) in zip(cols, stats):
        with col:
            st.metric(f"{icon} {label}", value)
