"""Behavioural smoke test: run a small app through streamlit's AppTest and
check that streamlit_analytics2 counts pageviews, script runs and widget use."""

from streamlit.testing.v1 import AppTest

import streamlit_analytics2 as sa2
from streamlit_analytics2 import state

APP = """
import streamlit as st
import streamlit_analytics2 as sa2

with sa2.track():
    st.text_input("Write your name")
    st.selectbox("Select your favorite", ["cat", "dog", "flower"])
    st.checkbox("Tick me")
    st.button("Click me")
"""


def _fresh_app() -> AppTest:
    state.reset_data()
    state.data["loaded_from_firestore"] = False
    return AppTest.from_string(APP, default_timeout=30)


def test_pageview_and_script_runs_are_counted():
    at = _fresh_app()
    at.run()
    assert not at.exception
    assert sa2.data["total_pageviews"] == 1
    assert sa2.data["total_script_runs"] == 1

    at.run()
    assert sa2.data["total_pageviews"] == 1, "a rerun is not a new pageview"
    assert sa2.data["total_script_runs"] == 2


def test_widget_interactions_are_counted():
    at = _fresh_app()
    at.run()
    assert not at.exception
    assert set(sa2.data["widgets"]) >= {
        "Write your name",
        "Select your favorite",
        "Tick me",
        "Click me",
    }

    at.button[0].click().run()
    assert not at.exception
    assert sa2.data["widgets"]["Click me"] == 1

    at.text_input[0].set_value("Alfred").run()
    assert not at.exception
    assert sa2.data["widgets"]["Write your name"]["Alfred"] == 1

    at.selectbox[0].select("dog").run()
    assert not at.exception
    assert sa2.data["widgets"]["Select your favorite"]["dog"] == 1

    before = sa2.data["widgets"]["Tick me"]  # the first render already counts once
    at.checkbox[0].check().run()
    assert not at.exception
    assert sa2.data["widgets"]["Tick me"] == before + 1
