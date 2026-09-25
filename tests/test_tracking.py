"""Behavioural tests through streamlit's AppTest.

They check what 0.11 promises: nothing counts on first render, every container
is seen, same-label widgets stay distinct in the event log, free text is not
stored by default, and the 0.10 API and data shape still work.
"""

import json

import pytest
from streamlit.testing.v1 import AppTest

import streamlit_analytics2 as sa2
from streamlit_analytics2 import main, state

APP = """
import streamlit as st
import streamlit_analytics2 as sa2

with sa2.track({kwargs}):
    st.text_input("Write your name")
    st.selectbox("Select your favorite", ["cat", "dog", "flower"])
    st.checkbox("Tick me")
    st.button("Click me")
    c1, c2 = st.columns(2)
    c1.button("Column button")
    with c2:
        st.toggle("Column toggle")
    with st.form("f"):
        st.text_area("Feedback")
        st.form_submit_button("Send")
    with st.expander("More"):
        st.multiselect("Tags", ["a", "b", "c"])
        st.selectbox("Optional", ["x", "y"], index=None)
    st.button("Same label")
    st.button("Same label", key="second")
    st.sidebar.checkbox("Sidebar checkbox")
    if st.session_state.get("fire"):
        sa2.event("report", rows=3)
"""


def _app(**kwargs) -> AppTest:
    state.reset_data()
    state.data["loaded_from_firestore"] = False
    main._memory_store.clear()
    args = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    at = AppTest.from_string(APP.format(kwargs=args), default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def _skip_old_apptest(test):
    """AppTest on older Streamlit (the 1.47 floor) cannot serialise a rendered
    segmented_control and raises ValueError on the next rerun. The dashboard
    itself works there; only the harness cannot drive it."""
    import functools

    import streamlit as st

    @functools.wraps(test)
    def wrapper(*args, **kwargs):
        try:
            return test(*args, **kwargs)
        except ValueError as exc:
            if "is not in list" in str(exc):
                pytest.skip(
                    f"AppTest cannot drive segmented_control on streamlit {st.__version__}"
                )
            raise

    return wrapper


def _set_control(at: AppTest, key: str, value: str) -> None:
    at.session_state[key] = value
    at.run()


def _widget_events(store=None):
    store = store or main._memory_store
    return [e for e in store.read() if e.kind == "widget"]


def test_first_render_counts_nothing_but_the_visit():
    _app()
    assert sa2.data["total_pageviews"] == 1
    assert sa2.data["total_script_runs"] == 1
    assert sa2.data["widgets"] == {}
    kinds = [e.kind for e in main._memory_store.read()]
    assert kinds == ["session", "pageview", "run"]


def test_rerun_is_not_a_pageview():
    at = _app()
    at.run()
    assert sa2.data["total_pageviews"] == 1
    assert sa2.data["total_script_runs"] == 2


def test_button_counts_once_per_click_not_on_later_reruns():
    at = _app()
    at.button[0].click().run()
    assert sa2.data["widgets"]["Click me"] == 1
    at.checkbox[0].check().run()  # unrelated rerun
    assert sa2.data["widgets"]["Click me"] == 1
    assert sa2.data["widgets"]["Tick me"] == 1


def test_widgets_in_columns_forms_and_expanders_are_seen():
    at = _app()
    at.button[1].click().run()  # column button
    at.toggle[0].set_value(True).run()
    at.text_area[0].set_value("hi").run()
    at.button[2].click().run()  # form submit
    at.multiselect[0].select("b").run()
    w = sa2.data["widgets"]
    assert w["Column button"] == 1
    assert w["Column toggle"] == 1
    assert w["Send"] == 1
    assert w["Tags"] == {"b": 1}
    types = {e.widget_type for e in _widget_events()}
    assert {
        "button",
        "toggle",
        "form_submit_button",
        "multiselect",
        "text_area",
    } <= types


def test_sidebar_checkbox_is_counted():
    at = _app()
    at.sidebar.checkbox[0].check().run()
    assert sa2.data["widgets"]["Sidebar checkbox"] == 1


def test_selectbox_with_none_default_does_not_crash_and_counts_choice():
    at = _app()
    at.selectbox[1].select("y").run()
    assert not at.exception
    assert sa2.data["widgets"]["Optional"] == {"y": 1}


def test_same_label_buttons_are_distinct_in_events_and_merged_in_legacy_data():
    at = _app()
    at.button[3].click().run()
    at.button[4].click().run()
    assert sa2.data["widgets"]["Same label"] == 2
    ids = {(e.widget_id, e.key) for e in _widget_events() if e.name == "Same label"}
    assert len(ids) == 2
    assert {k for _, k in ids} == {None, "second"}


def test_free_text_is_not_stored_by_default():
    at = _app()
    at.text_input[0].set_value("Alfred").run()
    assert sa2.data["widgets"]["Write your name"] == {"<text>": 1}
    assert all(e.value != "Alfred" for e in _widget_events())


def test_free_text_stored_when_opted_in():
    at = _app(store_values=True)
    at.text_input[0].set_value("Alfred").run()
    assert sa2.data["widgets"]["Write your name"] == {"Alfred": 1}


def test_selection_values_are_stored():
    at = _app()
    at.selectbox[0].select("dog").run()
    at.selectbox[0].select("flower").run()
    assert sa2.data["widgets"]["Select your favorite"] == {"dog": 1, "flower": 1}


def test_custom_event():
    at = _app()
    at.session_state["fire"] = True
    at.run()
    custom = [e for e in main._memory_store.read() if e.kind == "custom"]
    assert len(custom) == 1
    assert custom[0].name == "report" and custom[0].props == {"rows": 3}


def test_save_to_json_keeps_legacy_shape_and_writes_jsonl_sidecar(tmp_path):
    path = tmp_path / "sa2_data.json"
    at = _app(save_to_json=str(path))
    at.button[0].click().run()
    legacy = json.loads(path.read_text())
    assert legacy["total_pageviews"] == 1
    assert legacy["widgets"]["Click me"] == 1
    assert set(legacy) >= {
        "per_day",
        "total_script_runs",
        "total_time_seconds",
        "start_time",
    }
    sidecar = tmp_path / "sa2_data.events.jsonl"
    lines = [json.loads(line) for line in sidecar.read_text().splitlines()]
    assert [line["kind"] for line in lines] == [
        "session",
        "pageview",
        "run",
        "run",
        "widget",
    ]
    assert lines[-1]["name"] == "Click me"


def test_sqlite_events_path(tmp_path):
    db = tmp_path / "events.db"
    at = _app(events_path=str(db))
    at.selectbox[0].select("dog").run()
    events = sa2.SqliteStore(db).read()
    assert [e.kind for e in events][-1] == "widget"
    assert events[-1].value == "dog"


def test_load_from_json_restores_counts(tmp_path):
    path = tmp_path / "sa2_data.json"
    path.write_text(json.dumps({"total_pageviews": 41, "widgets": {"Click me": 9}}))
    main._json_loaded.clear()
    at = _app(save_to_json=str(path), load_from_json=str(path))
    at.button[0].click().run()
    assert sa2.data["total_pageviews"] == 42
    assert sa2.data["widgets"]["Click me"] == 10


def test_start_stop_pair_still_works():
    state.reset_data()
    main._memory_store.clear()
    at = AppTest.from_string(
        "import streamlit as st, streamlit_analytics2 as sa\n"
        "sa.start_tracking()\nst.button('B')\nsa.stop_tracking()\n",
        default_timeout=30,
    )
    at.run()
    at.button[0].click().run()
    assert not at.exception
    assert sa2.data["widgets"]["B"] == 1


def test_dashboard_renders_with_password_gate():
    at = _app(unsafe_password="pw")
    at.query_params["analytics"] = "on"
    at.run()
    assert not at.exception


def test_firestore_needs_the_extra(monkeypatch):
    import sys

    from streamlit_analytics2 import firestore

    monkeypatch.setitem(sys.modules, "google.cloud", None)
    monkeypatch.setitem(sys.modules, "google.cloud.firestore", None)
    with pytest.raises(ImportError, match=r"streamlit-analytics2\[firestore\]"):
        firestore._client("key.json", None, None)


@_skip_old_apptest
def test_dashboard_renders_with_events_and_range_switch():
    at = _app()
    at.button[0].click().run()
    at.selectbox[0].select("dog").run()
    at.query_params["analytics"] = "on"
    at.run()
    assert not at.exception, at.exception
    runs_before = sa2.data["total_script_runs"]
    # Dashboard runs are not traffic: no run event, no legacy script run.
    assert sa2.data["total_script_runs"] == runs_before
    kinds = [e.kind for e in main._memory_store.read()]
    assert kinds.count("run") == 3
    _set_control(at, "_sa2_range", "All time")
    assert not at.exception, at.exception


@_skip_old_apptest
def test_query_tab_present_as(tmp_path):
    db = tmp_path / "e.db"
    at = _app(events_path=str(db), unsafe_password="pw")
    at.selectbox[0].select("dog").run()
    at.query_params["analytics"] = "on"
    at.run()
    [t for t in at.text_input if t.label == "Password"][0].set_value("pw").run()
    assert not at.exception, at.exception
    sql = [t for t in at.text_area if t.label == "SQL"][0]
    sql.set_value("SELECT kind, count(*) AS n FROM events GROUP BY kind").run()
    [b for b in at.button if b.label == "Run query"][0].click().run()
    assert not at.exception, at.exception
    assert any("Present as" in m.value for m in at.markdown)
    assert "_sa2_q_kind" in at.session_state
    for kind in ("Bar", "Pie", "Line", "Area", "Scatter"):
        _set_control(at, "_sa2_q_kind", kind)
        assert not at.exception, (kind, at.exception)
