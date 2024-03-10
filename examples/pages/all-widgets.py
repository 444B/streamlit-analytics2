from datetime import datetime

import streamlit as st
import streamlit_analytics2 as streamlit_analytics

with streamlit_analytics.track(verbose=True):
    st.title("Test app with all widgets")
    st.checkbox("checkbox")
    st.button("button")
    st.radio("radio", ("option 1", "option 2"))
    st.selectbox("selectbox", ("option 1", "option 2", "option 3"))
    st.multiselect("multiselect", ("option 1", "option 2"))
    st.slider("slider")
    st.slider("double-ended slider", value=[0, 100])
    st.select_slider("select_slider", ("option 1", "option 2"))
    st.text_input("text_input")
    st.number_input("number_input")
    st.text_area("text_area")
    st.date_input("date_input")
    st.time_input("time_input")
    st.file_uploader("file_uploader")
    st.color_picker("color_picker")
    prompt = st.chat_input("Send a prompt to the bot")
    if prompt:
        st.write(f"User has sent the following prompt: {prompt}")

    st.sidebar.checkbox("sidebar_checkbox")
    st.sidebar.button("sidebar_button")
    st.sidebar.radio("sidebar_radio", ("option 1", "option 2"))
    st.sidebar.selectbox("sidebar_selectbox", ("option 1", "option 2", "option 3"))
    st.sidebar.multiselect("sidebar_multiselect", ("option 1", "option 2"))
    st.sidebar.slider("sidebar_slider")
    st.sidebar.slider("sidebar_double-ended slider", value=[0, 100])
    st.sidebar.select_slider("sidebar_select_slider", ("option 1", "option 2"))
    st.sidebar.text_input("sidebar_text_input")
    st.sidebar.number_input("sidebar_number_input")
    st.sidebar.text_area("sidebar_text_area")
    st.sidebar.date_input("sidebar_date_input")
    st.sidebar.time_input("sidebar_time_input")
    st.sidebar.file_uploader("sidebar_file_uploader")
    st.sidebar.color_picker("sidebar_color_picker")

    st.markdown("---")
    st.write(streamlit_analytics.counts)
    st.markdown("---")
