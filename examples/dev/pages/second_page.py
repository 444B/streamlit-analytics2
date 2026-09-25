"""Second page: today every page shares one global counter set (issue 47)."""

import os
from pathlib import Path

import streamlit as st

import streamlit_analytics2 as sa2

DATA = Path(os.environ.get("SA2_DATA_DIR", ".")) / "sa2_data.json"

with sa2.track(save_to_json=DATA, load_from_json=DATA):
    st.title("Second page")
    st.button("Second page button")
    st.selectbox("Second page choice", ["alpha", "beta"])
