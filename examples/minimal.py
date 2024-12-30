# This is the basic display page.
# It just shows basic diagnostic info and verifies that a config works
# More advanced testing should be done via examples/pages/all-features.py

import os
import platform
import sys

import streamlit as st

import streamlit_analytics2 as streamlit_analytics

# Get the directory of the current script
current_script_path = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the 'src' directory
src_directory_path = os.path.join(current_script_path, "..", "src")

# Add the 'src' directory to sys.path at the first position
sys.path.insert(0, src_directory_path)


# Get the software versions
python_version = platform.python_version()
streamlit_version = st.__version__
try:
    streamlit_analytics_version = streamlit_analytics.__version__
except AttributeError:
    streamlit_analytics_version = "Not available"

# Print the versions
st.write(f"Python version: {python_version}")
st.write(f"Streamlit version: {streamlit_version}")
st.write(f"streamlit_analytics2 version: {streamlit_analytics_version}")

st.markdown("---")

with streamlit_analytics.track():
    st.text_input("Write your name")
    st.selectbox("Select your favorite", ["cat", "dog", "flower"])
    st.button("Click me")
    streamlit_analytics.data
