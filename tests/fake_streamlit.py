"""A tiny stand-in for Streamlit so page code can run in tests without a browser.

It records what pages try to render and returns sensible default widget values.
It is NOT a replacement for trying the app in a browser. It catches typos,
wrong names, bad data handling and broken callbacks.
"""
import types
from datetime import date


class Rerun(BaseException):
    """Mirrors Streamlit, where st.rerun is not an ordinary Exception."""


class State(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def build(secrets=None):
    st = types.ModuleType("streamlit")
    st.session_state = State()
    st.query_params = {}
    st.secrets = secrets or {}
    st.calls = []

    def record(name):
        def fn(*args, **kwargs):
            st.calls.append((name, args, kwargs))
        return fn

    for name in ["markdown", "caption", "write", "info", "error", "warning", "success", "toast", "image",
                 "dataframe", "bar_chart", "progress", "code", "set_page_config"]:
        setattr(st, name, record(name))

    def widget(default):
        def fn(label, *args, **kwargs):
            key = kwargs.get("key")
            if key is not None and key in st.session_state:
                return st.session_state[key]
            value = default(label, args, kwargs)
            if key is not None:
                st.session_state[key] = value
            st.calls.append(("widget", (label,), kwargs))
            return value
        return fn

    def first_option(label, args, kwargs):
        options = list(args[0]) if args else list(kwargs.get("options", []))
        index = kwargs.get("index", 0)
        return options[index] if options and index is not None else None

    st.selectbox = widget(first_option)
    st.pills = widget(lambda l, a, k: k.get("default"))
    st.multiselect = widget(lambda l, a, k: k.get("default", []))
    st.text_input = widget(lambda l, a, k: k.get("value", ""))
    st.text_area = widget(lambda l, a, k: k.get("value", ""))
    st.number_input = widget(lambda l, a, k: k.get("value", 0))
    st.date_input = widget(lambda l, a, k: k.get("value", date.today()))
    st.toggle = widget(lambda l, a, k: False)
    st.checkbox = widget(lambda l, a, k: False)
    st.file_uploader = widget(lambda l, a, k: None)
    st.chat_input = widget(lambda l, a, k: None)
    st.button = widget(lambda l, a, k: False)
    st.download_button = widget(lambda l, a, k: False)
    st.form_submit_button = widget(lambda l, a, k: False)

    st.columns = lambda spec, **kw: [Ctx() for _ in range(spec if isinstance(spec, int) else len(spec))]
    st.tabs = lambda labels: [Ctx() for _ in labels]
    for name in ["container", "expander", "popover", "form", "spinner", "chat_message"]:
        setattr(st, name, lambda *a, **k: Ctx())

    def rerun():
        raise Rerun()

    st.rerun = rerun
    return st
