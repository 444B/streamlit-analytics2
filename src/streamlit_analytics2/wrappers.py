import datetime

import streamlit as st

from . import utils
from .state import data, session_data

dicts = [data, session_data]


def checkbox(func):
    """
    Wrap st.checkbox.
    """

    def new_func(label, *args, **kwargs):
        checked = func(label, *args, **kwargs)
        label = utils.replace_empty(label)

        for d in dicts:

            # Update aggregate data
            if label not in d["widgets"]:
                d["widgets"][label] = 0
            if label not in d["per_day"]["widgets"][-1]:
                d["per_day"]["widgets"][-1][label] = 0
            if checked != st.session_state.state_dict.get(label, None):
                d["widgets"][label] += 1
                d["per_day"]["widgets"][-1][label] += 1

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

        for d in dicts:
            # Update aggregate data
            if label not in d["widgets"]:
                d["widgets"][label] = 0
            if label not in d["per_day"]["widgets"][-1]:
                d["per_day"]["widgets"][-1][label] = 0
            if clicked:
                d["widgets"][label] += 1
                d["per_day"]["widgets"][-1][label] += 1

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

        for d in dicts:
            # Update aggregate data
            if label not in d["widgets"]:
                d["widgets"][label] = 0
            if label not in d["per_day"]["widgets"][-1]:
                d["per_day"]["widgets"][-1][label] = 0
            # TODO: Right now this doesn't track when multiple files are uploaded
            # one after another. Maybe compare files directly (but probably not
            # very clever to store in session state) or hash them somehow and check
            # if a different file was uploaded.
            if uploaded_file and not st.session_state.state_dict.get(label, None):
                d["widgets"][label] += 1
                d["per_day"]["widgets"][-1][label] += 1

        st.session_state.state_dict[label] = bool(uploaded_file)
        return uploaded_file

    return new_func


def select(func):
    """
    Wrap a streamlit function that returns one selected element out of multiple
    options
    e.g. st.radio, st.selectbox, st.select_slider.
    """

    def new_func(label, options, *args, **kwargs):
        orig_selected = func(label, options, *args, **kwargs)
        label = utils.replace_empty(label)
        selected = utils.replace_empty(orig_selected)

        for d in dicts:
            # Update aggregate data
            if label not in d["widgets"]:
                d["widgets"][label] = {}
            if label not in d["per_day"]["widgets"][-1]:
                d["per_day"]["widgets"][-1][label] = {}

            for option in options:
                option = utils.replace_empty(option)
                if option not in d["widgets"][label]:
                    d["widgets"][label][option] = 0
                if option not in d["per_day"]["widgets"][-1].get(label, {}):
                    d["per_day"]["widgets"][-1][label][option] = 0

            if selected != st.session_state.state_dict.get(label, None):
                d["widgets"][label][selected] += 1
                d["per_day"]["widgets"][-1][label][selected] = (
                    d["per_day"]["widgets"][-1][label].get(selected, 0) + 1
                )

        st.session_state.state_dict[label] = selected
        return orig_selected

    return new_func


def multiselect(func):
    """
    Wrap a streamlit function that returns multiple selected elements out of
    multiple options, e.g. st.multiselect.
    """

    def new_func(label, options, *args, **kwargs):
        selected = func(label, options, *args, **kwargs)
        label = utils.replace_empty(label)

        for d in dicts:
            if label not in d["widgets"]:
                d["widgets"][label] = {}
            if label not in d["per_day"]["widgets"][-1]:
                d["per_day"]["widgets"][-1][label] = {}

            for option in options:
                option = utils.replace_empty(option)
                if option not in d["widgets"][label]:
                    d["widgets"][label][option] = 0
                if option not in d["per_day"]["widgets"][-1].get(label, {}):
                    d["per_day"]["widgets"][-1][label][option] = 0

            for sel in selected:
                sel = utils.replace_empty(sel)
                if sel not in st.session_state.state_dict.get(label, []):
                    d["widgets"][label][sel] += 1
                    d["per_day"]["widgets"][-1][label][sel] += 1

        st.session_state.state_dict[label] = selected
        return selected

    return new_func


def value(func):
    """
    Wrap a streamlit function that returns a single value,
    e.g. st.slider, st.text_input, st.number_input, st.text_area, st.date_input,
    st.time_input, st.color_picker.
    """

    def new_func(label, *args, **kwargs):
        value = func(label, *args, **kwargs)
        label = utils.replace_empty(label)

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

        for d in dicts:
            if label not in d["widgets"]:
                d["widgets"][label] = {}
            if label not in d["per_day"]["widgets"][-1]:
                d["per_day"]["widgets"][-1][label] = {}

            if formatted_value not in d["widgets"][label]:
                d["widgets"][label][formatted_value] = 0
            if formatted_value not in d["per_day"]["widgets"][-1].get(label, {}):
                d["per_day"]["widgets"][-1][label][formatted_value] = 0

            if formatted_value != st.session_state.state_dict.get(label, None):
                d["widgets"][label][formatted_value] += 1
                d["per_day"]["widgets"][-1][label][formatted_value] += 1

        st.session_state.state_dict[label] = formatted_value
        return value

    return new_func


def chat_input(func):
    """
    Wrap a streamlit function that returns a single value,
    e.g. st.slider, st.text_input, st.number_input, st.text_area, st.date_input,
    st.time_input, st.color_picker.
    """

    def new_func(placeholder, *args, **kwargs):
        input_received = func(placeholder, *args, **kwargs)

        formatted_value = str(input_received)

        for d in dicts:
            # Update aggregate data
            if placeholder not in d["widgets"]:
                d["widgets"][placeholder] = {}
            if placeholder not in d["per_day"]["widgets"][-1]:
                d["per_day"]["widgets"][-1][placeholder] = {}

            if formatted_value not in d["widgets"][placeholder]:
                d["widgets"][placeholder][formatted_value] = 0
            if formatted_value not in d["per_day"]["widgets"][-1].get(placeholder, {}):
                d["per_day"]["widgets"][-1][placeholder][formatted_value] = 0

            if formatted_value != st.session_state.state_dict.get(placeholder):
                d["widgets"][placeholder][formatted_value] += 1
                d["per_day"]["widgets"][-1][placeholder][formatted_value] += 1

        st.session_state.state_dict[placeholder] = formatted_value
        return input_received

    return new_func
