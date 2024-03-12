import datetime
import logging
import uuid

import streamlit as st

from .config import setup_logging
from .tracker import counts
from .utils import format_seconds, replace_empty

setup_logging()

# Store original streamlit functions. They will be monkey-patched with some wrappers
# in `start_tracking` (see wrapper functions below).
_orig_button = st.button
_orig_checkbox = st.checkbox
_orig_radio = st.radio
_orig_selectbox = st.selectbox
_orig_multiselect = st.multiselect
_orig_slider = st.slider
_orig_select_slider = st.select_slider
_orig_text_input = st.text_input
_orig_number_input = st.number_input
_orig_text_area = st.text_area
_orig_date_input = st.date_input
_orig_time_input = st.time_input
_orig_file_uploader = st.file_uploader
_orig_color_picker = st.color_picker
# new elements, testing
# _orig_download_button = st.download_button
# _orig_link_button = st.link_button
# _orig_page_link = st.page_link
# _orig_toggle = st.toggle
# _orig_camera_input = st.camera_input
_orig_chat_input = st.chat_input

_orig_sidebar_button = st.sidebar.button
_orig_sidebar_checkbox = st.sidebar.checkbox
_orig_sidebar_radio = st.sidebar.radio
_orig_sidebar_selectbox = st.sidebar.selectbox
_orig_sidebar_multiselect = st.sidebar.multiselect
_orig_sidebar_slider = st.sidebar.slider
_orig_sidebar_select_slider = st.sidebar.select_slider
_orig_sidebar_text_input = st.sidebar.text_input
_orig_sidebar_number_input = st.sidebar.number_input
_orig_sidebar_text_area = st.sidebar.text_area
_orig_sidebar_date_input = st.sidebar.date_input
_orig_sidebar_time_input = st.sidebar.time_input
_orig_sidebar_file_uploader = st.sidebar.file_uploader
_orig_sidebar_color_picker = st.sidebar.color_picker
# new elements, testing
# _orig_sidebar_download_button = st.sidebar.download_button
# _orig_sidebar_link_button = st.sidebar.link_button
# _orig_sidebar_page_link = st.sidebar.page_link
# _orig_sidebar_toggle = st.sidebar.toggle
# _orig_sidebar_camera_input = st.sidebar.camera_input

def monkey_patch():
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - monkey_patch - BEGIN")
    # Monkey-patch streamlit to call the wrappers above.
    st.button = _wrap_button(_orig_button)
    st.checkbox = _wrap_checkbox(_orig_checkbox)
    st.radio = _wrap_select(_orig_radio)
    st.selectbox = _wrap_select(_orig_selectbox)
    st.multiselect = _wrap_multiselect(_orig_multiselect)
    st.slider = _wrap_value(_orig_slider)
    st.select_slider = _wrap_select(_orig_select_slider)
    st.text_input = _wrap_value(_orig_text_input)
    st.number_input = _wrap_value(_orig_number_input)
    st.text_area = _wrap_value(_orig_text_area)
    st.date_input = _wrap_value(_orig_date_input)
    st.time_input = _wrap_value(_orig_time_input)
    st.file_uploader = _wrap_file_uploader(_orig_file_uploader)
    st.color_picker = _wrap_value(_orig_color_picker)
    # new elements, testing
    # st.download_button = _wrap_value(_orig_download_button)
    # st.link_button = _wrap_value(_orig_link_button)
    # st.page_link = _wrap_value(_orig_page_link)
    # st.toggle = _wrap_value(_orig_toggle)
    # st.camera_input = _wrap_value(_orig_camera_input)
    st.chat_input = _wrap_chat_input(_orig_chat_input)

    st.sidebar.button = _wrap_button(_orig_sidebar_button)  # type: ignore
    st.sidebar.checkbox = _wrap_checkbox(_orig_sidebar_checkbox)  # type: ignore
    st.sidebar.radio = _wrap_select(_orig_sidebar_radio)  # type: ignore
    st.sidebar.selectbox = _wrap_select(_orig_sidebar_selectbox)  # type: ignore
    st.sidebar.multiselect = _wrap_multiselect(_orig_sidebar_multiselect)  # type: ignore
    st.sidebar.slider = _wrap_value(_orig_sidebar_slider)  # type: ignore
    st.sidebar.select_slider = _wrap_select(_orig_sidebar_select_slider)  # type: ignore
    st.sidebar.text_input = _wrap_value(_orig_sidebar_text_input)  # type: ignore
    st.sidebar.number_input = _wrap_value(_orig_sidebar_number_input)  # type: ignore
    st.sidebar.text_area = _wrap_value(_orig_sidebar_text_area)  # type: ignore
    st.sidebar.date_input = _wrap_value(_orig_sidebar_date_input)  # type: ignore
    st.sidebar.time_input = _wrap_value(_orig_sidebar_time_input)  # type: ignore
    st.sidebar.file_uploader = _wrap_file_uploader(_orig_sidebar_file_uploader)  # type: ignore
    st.sidebar.color_picker = _wrap_value(_orig_sidebar_color_picker)  # type: ignore
    # new elements, testing
    # st.sidebar.download_button = _wrap_value(_orig_sidebar_download_button)
    # st.sidebar.link_button = _wrap_value(_orig_sidebar_link_button)
    # st.sidebar.page_link = _wrap_value(_orig_sidebar_page_link)
    # st.sidebar.toggle = _wrap_value(_orig_sidebar_toggle)
    # st.sidebar.camera_input = _wrap_value(_orig_sidebar_camera_input)

    logging.debug(f"{unique_id} - monkey_patch - END")


def unwrap_original():
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - unwrap_original - BEGIN")

    # Reset streamlit functions.
    st.button = _orig_button
    st.checkbox = _orig_checkbox
    st.radio = _orig_radio
    st.selectbox = _orig_selectbox
    st.multiselect = _orig_multiselect
    st.slider = _orig_slider
    st.select_slider = _orig_select_slider
    st.text_input = _orig_text_input
    st.number_input = _orig_number_input
    st.text_area = _orig_text_area
    st.date_input = _orig_date_input
    st.time_input = _orig_time_input
    st.file_uploader = _orig_file_uploader
    st.color_picker = _orig_color_picker
    # new elements, testing
    # st.download_button = _orig_download_button
    # st.link_button = _orig_link_button
    # st.page_link = _orig_page_link
    # st.toggle = _orig_toggle
    # st.camera_input = _orig_camera_input
    st.chat_input = _orig_chat_input

    st.sidebar.button = _orig_sidebar_button  # type: ignore
    st.sidebar.checkbox = _orig_sidebar_checkbox  # type: ignore
    st.sidebar.radio = _orig_sidebar_radio  # type: ignore
    st.sidebar.selectbox = _orig_sidebar_selectbox  # type: ignore
    st.sidebar.multiselect = _orig_sidebar_multiselect  # type: ignore
    st.sidebar.slider = _orig_sidebar_slider  # type: ignore
    st.sidebar.select_slider = _orig_sidebar_select_slider  # type: ignore
    st.sidebar.text_input = _orig_sidebar_text_input  # type: ignore
    st.sidebar.number_input = _orig_sidebar_number_input  # type: ignore
    st.sidebar.text_area = _orig_sidebar_text_area  # type: ignore
    st.sidebar.date_input = _orig_sidebar_date_input  # type: ignore
    st.sidebar.time_input = _orig_sidebar_time_input  # type: ignore
    st.sidebar.file_uploader = _orig_sidebar_file_uploader  # type: ignore
    st.sidebar.color_picker = _orig_sidebar_color_picker  # type: ignore
    # new elements, testing
    # st.sidebar.download_button = _orig_sidebar_download_button
    # st.sidebar.link_button = _orig_sidebar_link_button
    # st.sidebar.page_link = _orig_sidebar_page_link
    # st.sidebar.toggle = _orig_sidebar_toggle
    # st.sidebar.camera_input = _orig_sidebar_camera_input

    logging.debug(f"{unique_id} - unwrap_original - END")



def _wrap_checkbox(func):
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - _wrap_checkbox - BEGIN")
    """
    Wrap st.checkbox.
    """

    def new_func(label, *args, **kwargs):

        checked = func(label, *args, **kwargs)
        label = replace_empty(label)
        if label not in counts["widgets"]:
            counts["widgets"][label] = 0
        if checked != st.session_state.state_dict.get(label, None):
            counts["widgets"][label] += 1
        st.session_state.state_dict[label] = checked
        return checked
    logging.debug(f"{unique_id} - _wrap_checkbox - END")
    return new_func


def _wrap_button(func):
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - _wrap_button - BEGIN")
    """
    Wrap st.button.
    """

    def new_func(label, *args, **kwargs):
        clicked = func(label, *args, **kwargs)
        label = replace_empty(label)
        if label not in counts["widgets"]:
            counts["widgets"][label] = 0
        if clicked:
            counts["widgets"][label] += 1
        st.session_state.state_dict[label] = clicked
        return clicked
    logging.debug(f"{unique_id} - _wrap_button - END")
    return new_func


def _wrap_file_uploader(func):
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - _wrap_file_uploader - BEGIN")
    """
    Wrap st.file_uploader.
    """

    def new_func(label, *args, **kwargs):
        uploaded_file = func(label, *args, **kwargs)
        label = replace_empty(label)
        if label not in counts["widgets"]:
            counts["widgets"][label] = 0
        # TODO: Right now this doesn't track when multiple files are uploaded one after
        #   another. Maybe compare files directly (but probably not very clever to
        #   store in session state) or hash them somehow and check if a different file
        #   was uploaded.
        if uploaded_file and not st.session_state.state_dict.get(label, None):
            counts["widgets"][label] += 1
        st.session_state.state_dict[label] = bool(uploaded_file)
        return uploaded_file
    logging.debug(f"{unique_id} - _wrap_file_uploader - END")
    return new_func


def _wrap_select(func):
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - _wrap_select - BEGIN")
    """
    Wrap a streamlit function that returns one selected element out of multiple options,
    e.g. st.radio, st.selectbox, st.select_slider.
    """

    def new_func(label, options, *args, **kwargs):
        orig_selected = func(label, options, *args, **kwargs)
        label = replace_empty(label)
        selected = replace_empty(orig_selected)
        if label not in counts["widgets"]:
            counts["widgets"][label] = {}
        for option in options:
            option = replace_empty(option)
            if option not in counts["widgets"][label]:
                counts["widgets"][label][option] = 0
        if selected != st.session_state.state_dict.get(label, None):
            counts["widgets"][label][selected] += 1
        st.session_state.state_dict[label] = selected
        return orig_selected
    logging.debug(f"{unique_id} - _wrap_select - END")
    return new_func


def _wrap_multiselect(func):
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - _wrap_multiselect - BEGIN")
    """
    Wrap a streamlit function that returns multiple selected elements out of multiple
    options, e.g. st.multiselect.
    """

    def new_func(label, options, *args, **kwargs):
        selected = func(label, options, *args, **kwargs)
        label = replace_empty(label)
        if label not in counts["widgets"]:
            counts["widgets"][label] = {}
        for option in options:
            option = replace_empty(option)
            if option not in counts["widgets"][label]:
                counts["widgets"][label][option] = 0
        for sel in selected:
            sel = replace_empty(sel)
            if sel not in st.session_state.state_dict.get(label, []):
                counts["widgets"][label][sel] += 1
        st.session_state.state_dict[label] = selected
        return selected
    logging.debug(f"{unique_id} - _wrap_multiselect - END")
    return new_func


def _wrap_value(func):
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - _wrap_value - BEGIN")
    """
    Wrap a streamlit function that returns a single value (str/int/float/datetime/...),
    e.g. st.slider, st.text_input, st.number_input, st.text_area, st.date_input,
    st.time_input, st.color_picker.
    """

    def new_func(label, *args, **kwargs):
        value = func(label, *args, **kwargs)
        if label not in counts["widgets"]:
            counts["widgets"][label] = {}

        formatted_value = replace_empty(value)
        if type(value) is tuple and len(value) == 2:
            # Double-ended slider or date input with start/end, convert to str.
            formatted_value = f"{value[0]} - {value[1]}"

        # st.date_input and st.time return datetime object, convert to str
        if (
            isinstance(value, datetime.datetime)
            or isinstance(value, datetime.date)
            or isinstance(value, datetime.time)
        ):
            formatted_value = str(value)

        if formatted_value not in counts["widgets"][label]:
            counts["widgets"][label][formatted_value] = 0
        if formatted_value != st.session_state.state_dict.get(label, None):
            counts["widgets"][label][formatted_value] += 1
        st.session_state.state_dict[label] = formatted_value
        return value

    logging.debug(f"{unique_id} - _wrap_value - END")
    return new_func


def _wrap_chat_input(func):
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - _wrap_chat_input - BEGIN")
    """
    Wrap a streamlit function that returns a single value (str/int/float/datetime/...),
    e.g. st.slider, st.text_input, st.number_input, st.text_area, st.date_input,
    st.time_input, st.color_picker.
    """

    def new_func(placeholder, *args, **kwargs):
        value = func(placeholder, *args, **kwargs)
        if placeholder not in counts["widgets"]:
            counts["widgets"][placeholder] = {}

        formatted_value = str(value)

        if formatted_value not in counts["widgets"][placeholder]:
            counts["widgets"][placeholder][formatted_value] = 0

        if formatted_value != st.session_state.state_dict.get(placeholder):
            counts["widgets"][placeholder][formatted_value] += 1
        st.session_state.state_dict[placeholder] = formatted_value
        return value

    logging.debug(f"{unique_id} - _wrap_chat_input - END")
    return new_func
