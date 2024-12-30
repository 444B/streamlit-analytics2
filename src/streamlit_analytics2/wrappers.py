import datetime

import streamlit as st
from streamlit import session_state as ss

from . import utils
from .state import data


def checkbox(func):
    """
    Wrap st.checkbox.
    """

    def new_func(label, *args, **kwargs):
        checked = func(label, *args, **kwargs)
        label = utils.replace_empty(label)

        # Update aggregate data
        if label not in data["widgets"]:
            data["widgets"][label] = 0
        if checked != st.session_state.state_dict.get(label, None):
            data["widgets"][label] += 1

        # Update session data
        if label not in ss.session_data["widgets"]:
            ss.session_data["widgets"][label] = 0
        if checked != st.session_state.state_dict.get(label, None):
            ss.session_data["widgets"][label] += 1

        st.session_state.state_dict[label] = checked
        return checked

    return new_func


def button(func):
    """
    Wrap st.button.
    """

    def new_func(label, *args, **kwargs):
        clicked = func(label, *args, **kwargs)
        label = utils.replace_empty(label)

        # Update aggregate data
        if label not in data["widgets"]:
            data["widgets"][label] = 0
        if clicked:
            data["widgets"][label] += 1

        # Update session data
        if label not in ss.session_data["widgets"]:
            ss.session_data["widgets"][label] = 0
        if clicked:
            ss.session_data["widgets"][label] += 1

        st.session_state.state_dict[label] = clicked
        return clicked

    return new_func


def file_uploader(func):
    """
    Wrap st.file_uploader.
    """

    def new_func(label, *args, **kwargs):
        uploaded_file = func(label, *args, **kwargs)
        label = utils.replace_empty(label)

        # Update aggregate data
        if label not in data["widgets"]:
            data["widgets"][label] = 0
        # TODO: Right now this doesn't track when multiple files are uploaded one after
        #   another. Maybe compare files directly (but probably not very clever to
        #   store in session state) or hash them somehow and check if a different file
        #   was uploaded.
        if uploaded_file and not st.session_state.state_dict.get(label, None):
            data["widgets"][label] += 1

        # Update session data
        if label not in ss.session_data["widgets"]:
            ss.session_data["widgets"][label] = 0
        if uploaded_file and not st.session_state.state_dict.get(label, None):
            ss.session_data["widgets"][label] += 1

        st.session_state.state_dict[label] = bool(uploaded_file)
        return uploaded_file

    return new_func


def select(func):
    """
    Wrap a streamlit function that returns one selected element out of multiple options,
    e.g. st.radio, st.selectbox, st.select_slider.
    """

    def new_func(label, options, *args, **kwargs):
        orig_selected = func(label, options, *args, **kwargs)
        label = utils.replace_empty(label)
        selected = utils.replace_empty(orig_selected)

        # Update aggregate data
        if label not in data["widgets"]:
            data["widgets"][label] = {}
        for option in options:
            option = utils.replace_empty(option)
            if option not in data["widgets"][label]:
                data["widgets"][label][option] = 0
        if selected != st.session_state.state_dict.get(label, None):
            data["widgets"][label][selected] += 1

        # Update session data
        if label not in ss.session_data["widgets"]:
            ss.session_data["widgets"][label] = {}
        for option in options:
            option = utils.replace_empty(option)
            if option not in ss.session_data["widgets"][label]:
                ss.session_data["widgets"][label][option] = 0
        if selected != st.session_state.state_dict.get(label, None):
            ss.session_data["widgets"][label][selected] += 1

        st.session_state.state_dict[label] = selected
        return orig_selected

    return new_func


def multiselect(func):
    """
    Wrap a streamlit function that returns multiple selected elements out of multiple
    options, e.g. st.multiselect.
    """

    def new_func(label, options, *args, **kwargs):
        selected = func(label, options, *args, **kwargs)
        label = utils.replace_empty(label)

        # Update aggregate data
        if label not in data["widgets"]:
            data["widgets"][label] = {}
        for option in options:
            option = utils.replace_empty(option)
            if option not in data["widgets"][label]:
                data["widgets"][label][option] = 0
        for sel in selected:
            sel = utils.replace_empty(sel)
            if sel not in st.session_state.state_dict.get(label, []):
                data["widgets"][label][sel] += 1

        # Update session data
        if label not in ss.session_data["widgets"]:
            ss.session_data["widgets"][label] = {}
        for option in options:
            option = utils.replace_empty(option)
            if option not in ss.session_data["widgets"][label]:
                ss.session_data["widgets"][label][option] = 0
        for sel in selected:
            sel = utils.replace_empty(sel)
            if sel not in st.session_state.state_dict.get(label, []):
                ss.session_data["widgets"][label][sel] += 1

        st.session_state.state_dict[label] = selected
        return selected

    return new_func


def value(func):
    """
    Wrap a streamlit function that returns a single value (str/int/float/datetime/...),
    e.g. st.slider, st.text_input, st.number_input, st.text_area, st.date_input,
    st.time_input, st.color_picker.
    """

    def new_func(label, *args, **kwargs):
        value = func(label, *args, **kwargs)

        # Update aggregate data
        if label not in data["widgets"]:
            data["widgets"][label] = {}

        # Update session data
        if label not in ss.session_data["widgets"]:
            ss.session_data["widgets"][label] = {}

        formatted_value = utils.replace_empty(value)
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

        if formatted_value not in data["widgets"][label]:
            data["widgets"][label][formatted_value] = 0
        if formatted_value not in ss.session_data["widgets"][label]:
            ss.session_data["widgets"][label][formatted_value] = 0

        if formatted_value != st.session_state.state_dict.get(label, None):
            data["widgets"][label][formatted_value] += 1
            ss.session_data["widgets"][label][formatted_value] += 1

        st.session_state.state_dict[label] = formatted_value
        return value

    return new_func


def chat_input(func):
    """
    Wrap a streamlit function that returns a single value (str/int/float/datetime/...),
    e.g. st.slider, st.text_input, st.number_input, st.text_area, st.date_input,
    st.time_input, st.color_picker.
    """

    def new_func(placeholder, *args, **kwargs):
        value = func(placeholder, *args, **kwargs)

        # Update aggregate data
        if placeholder not in data["widgets"]:
            data["widgets"][placeholder] = {}

        # Update session data
        if placeholder not in ss.session_data["widgets"]:
            ss.session_data["widgets"][placeholder] = {}

        formatted_value = str(value)

        if formatted_value not in data["widgets"][placeholder]:
            data["widgets"][placeholder][formatted_value] = 0
        if formatted_value not in ss.session_data["widgets"][placeholder]:
            ss.session_data["widgets"][placeholder][formatted_value] = 0

        if formatted_value != st.session_state.state_dict.get(placeholder):
            data["widgets"][placeholder][formatted_value] += 1
            ss.session_data["widgets"][placeholder][formatted_value] += 1

        st.session_state.state_dict[placeholder] = formatted_value
        return value

    return new_func
