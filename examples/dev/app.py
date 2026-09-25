"""Dev app for streamlit-analytics2. Exercises widgets in every kind of
container, including the ones 0.10 cannot see (columns, forms, expanders),
so the difference shows as the new engine lands."""

import os
from pathlib import Path

import streamlit as st

import streamlit_analytics2 as sa2

DATA = Path(os.environ.get("SA2_DATA_DIR", ".")) / "sa2_data.json"


def main() -> None:
    st.title("streamlit-analytics2 dev app")
    st.caption(
        f"streamlit {st.__version__}, streamlit-analytics2 {sa2.__version__}. "
        "Add `?analytics=on` to the URL for the dashboard."
    )

    st.header("Plain widgets (tracked in 0.10)")
    name = st.text_input("Write your name")
    fav = st.selectbox("Select your favorite", ["cat", "dog", "flower"])
    if st.button("Click me"):
        st.write(f"Hello {name}, here's a {fav} for you")
    st.slider("Pick a number", 0, 10, 5)
    st.checkbox("Tick me")

    st.header("Containers (invisible to 0.10)")
    c1, c2 = st.columns(2)
    c1.button("Column button")
    with c2:
        st.toggle("Column toggle")
    with st.form("feedback"):
        st.text_area("Feedback")
        st.radio("Rating", ["good", "ok", "bad"], horizontal=True)
        st.form_submit_button("Send")
    with st.expander("More"):
        st.multiselect("Tags", ["a", "b", "c"])
        if st.session_state.get("show_issue_13"):
            # Crashes the 0.10 engine with KeyError ' ' (issue 13).
            st.selectbox("Optional choice", ["x", "y"], index=None)

    st.header("Same label, different key")
    st.button("Same label")
    st.button("Same label", key="second")

    st.sidebar.header("Sidebar")
    st.sidebar.checkbox("Sidebar checkbox")
    st.sidebar.selectbox("Sidebar pick", ["one", "two"])
    st.sidebar.toggle(
        "Show issue 13 widget (crashes 0.10)", key="show_issue_13"
    )


with sa2.track(save_to_json=DATA, load_from_json=DATA):
    main()
