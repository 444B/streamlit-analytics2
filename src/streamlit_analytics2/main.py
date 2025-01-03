"""
Main API functions for the user to start and stop analytics tracking.
"""

import datetime
import json
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional, Union

import streamlit as st
from streamlit import session_state as ss

from . import display, firestore
from .utils import initialize_session_counts, replace_empty

# from streamlit_searchbox import st_searchbox


# logging.basicConfig(
#     level=logging.INFO, format="streamlit-analytics2: %(levelname)s: %(message)s"
# )
# Uncomment this during testing

# Dict that holds all analytics results. Note that this is persistent across users,
# as modules are only imported once by a streamlit app.
counts = {"loaded_from_firestore": False}

logging.info("SA2: Streamlit-analytics2 successfully imported")


def reset_counts():
    # Use yesterday as first entry to make chart look better.
    yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
    counts["total_pageviews"] = 0
    counts["total_script_runs"] = 0
    counts["total_time_seconds"] = 0
    counts["per_day"] = {"days": [str(yesterday)], "pageviews": [0], "script_runs": [0]}
    counts["widgets"] = {}
    counts["start_time"] = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")


reset_counts()

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
# _orig_searchbox = st_searchbox


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
# _orig_sidebar_searchbox = st.sidebar.st_searchbox
# new elements, testing
# _orig_sidebar_download_button = st.sidebar.download_button
# _orig_sidebar_link_button = st.sidebar.link_button
# _orig_sidebar_page_link = st.sidebar.page_link
# _orig_sidebar_toggle = st.sidebar.toggle
# _orig_sidebar_camera_input = st.sidebar.camera_input


def update_session_stats(counts_dict: Dict[str, Any]):
    """
    Update the session counts with the current state.

    Parameters
    ----------
    counts_dict : Dict[str, Any]
        Counts, be they aggregate or session-specific.

    Returns
    -------
    Dict[str, Any]
        Updated counts with the current state of time-dependent elements.
    """
    today = str(datetime.date.today())
    if counts_dict["per_day"]["days"][-1] != today:
        # TODO: Insert 0 for all days between today and last entry.
        counts_dict["per_day"]["days"].append(today)
        counts_dict["per_day"]["pageviews"].append(0)
        counts_dict["per_day"]["script_runs"].append(0)
    counts_dict["total_script_runs"] += 1
    counts_dict["per_day"]["script_runs"][-1] += 1
    now = datetime.datetime.now()
    counts_dict["total_time_seconds"] += (
        now - st.session_state.last_time
    ).total_seconds()
    st.session_state.last_time = now
    if not st.session_state.user_tracked:
        st.session_state.user_tracked = True
        counts_dict["total_pageviews"] += 1
        counts_dict["per_day"]["pageviews"][-1] += 1


def _track_user():
    """Track individual pageviews by storing user id to session state."""
    update_session_stats(counts)
    update_session_stats(ss.session_counts)


def _wrap_checkbox(func):
    """
    Wrap st.checkbox.
    """

    def new_func(label, *args, **kwargs):
        checked = func(label, *args, **kwargs)
        label = replace_empty(label)

        # Update aggregate counts
        if label not in counts["widgets"]:
            counts["widgets"][label] = 0
        if checked != st.session_state.state_dict.get(label, None):
            counts["widgets"][label] += 1

        # Update session counts
        if label not in ss.session_counts["widgets"]:
            ss.session_counts["widgets"][label] = 0
        if checked != st.session_state.state_dict.get(label, None):
            ss.session_counts["widgets"][label] += 1

        st.session_state.state_dict[label] = checked
        return checked

    return new_func


def _wrap_button(func):
    """
    Wrap st.button.
    """

    def new_func(label, *args, **kwargs):
        clicked = func(label, *args, **kwargs)
        label = replace_empty(label)

        # Update aggregate counts
        if label not in counts["widgets"]:
            counts["widgets"][label] = 0
        if clicked:
            counts["widgets"][label] += 1

        # Update session counts
        if label not in ss.session_counts["widgets"]:
            ss.session_counts["widgets"][label] = 0
        if clicked:
            ss.session_counts["widgets"][label] += 1

        st.session_state.state_dict[label] = clicked
        return clicked

    return new_func


def _wrap_file_uploader(func):
    """
    Wrap st.file_uploader.
    """

    def new_func(label, *args, **kwargs):
        uploaded_file = func(label, *args, **kwargs)
        label = replace_empty(label)

        # Update aggregate counts
        if label not in counts["widgets"]:
            counts["widgets"][label] = 0
        # TODO: Right now this doesn't track when multiple files are uploaded one after
        #   another. Maybe compare files directly (but probably not very clever to
        #   store in session state) or hash them somehow and check if a different file
        #   was uploaded.
        if uploaded_file and not st.session_state.state_dict.get(label, None):
            counts["widgets"][label] += 1

        # Update session counts
        if label not in ss.session_counts["widgets"]:
            ss.session_counts["widgets"][label] = 0
        if uploaded_file and not st.session_state.state_dict.get(label, None):
            ss.session_counts["widgets"][label] += 1

        st.session_state.state_dict[label] = bool(uploaded_file)
        return uploaded_file

    return new_func


def _wrap_select(func):
    """
    Wrap a streamlit function that returns one selected element out of multiple options,
    e.g. st.radio, st.selectbox, st.select_slider.
    """

    def new_func(label, options, *args, **kwargs):
        orig_selected = func(label, options, *args, **kwargs)
        label = replace_empty(label)
        selected = replace_empty(orig_selected)

        # Update aggregate counts
        if label not in counts["widgets"]:
            counts["widgets"][label] = {}
        for option in options:
            option = replace_empty(option)
            if option not in counts["widgets"][label]:
                counts["widgets"][label][option] = 0
        if selected != st.session_state.state_dict.get(label, None):
            counts["widgets"][label][selected] += 1

        # Update session counts
        if label not in ss.session_counts["widgets"]:
            ss.session_counts["widgets"][label] = {}
        for option in options:
            option = replace_empty(option)
            if option not in ss.session_counts["widgets"][label]:
                ss.session_counts["widgets"][label][option] = 0
        if selected != st.session_state.state_dict.get(label, None):
            ss.session_counts["widgets"][label][selected] += 1

        st.session_state.state_dict[label] = selected
        return orig_selected

    return new_func


def _wrap_multiselect(func):
    """
    Wrap a streamlit function that returns multiple selected elements out of multiple
    options, e.g. st.multiselect.
    """

    def new_func(label, options, *args, **kwargs):
        selected = func(label, options, *args, **kwargs)
        label = replace_empty(label)

        # Update aggregate counts
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

        # Update session counts
        if label not in ss.session_counts["widgets"]:
            ss.session_counts["widgets"][label] = {}
        for option in options:
            option = replace_empty(option)
            if option not in ss.session_counts["widgets"][label]:
                ss.session_counts["widgets"][label][option] = 0
        for sel in selected:
            sel = replace_empty(sel)
            if sel not in st.session_state.state_dict.get(label, []):
                ss.session_counts["widgets"][label][sel] += 1

        st.session_state.state_dict[label] = selected
        return selected

    return new_func


# def _wrap_searchbox(func):
#     """
#     Wrap st_searchbox function that returns a selected value from search suggestions.
#     """
#     def new_func(search_function, *args, **kwargs):
#         value = func(search_function, *args, **kwargs)

#         # Get label from kwargs or use default
#         label = kwargs.get('label', 'searchbox')
#         label = replace_empty(label)

#         # Update aggregate counts
#         if label not in counts["widgets"]:
#             counts["widgets"][label] = {}

#         # Update session counts
#         if label not in ss.session_counts["widgets"]:
#             ss.session_counts["widgets"][label] = {}

#         formatted_value = replace_empty(value)

#         if formatted_value not in counts["widgets"][label]:
#             counts["widgets"][label][formatted_value] = 0
#         if formatted_value not in ss.session_counts["widgets"][label]:
#             ss.session_counts["widgets"][label][formatted_value] = 0

#         if formatted_value != st.session_state.state_dict.get(label, None):
#             counts["widgets"][label][formatted_value] += 1
#             ss.session_counts["widgets"][label][formatted_value] += 1

#         st.session_state.state_dict[label] = formatted_value
#         return value

#     return new_func


def _wrap_value(func):
    """
    Wrap a streamlit function that returns a single value (str/int/float/datetime/...),
    e.g. st.slider, st.text_input, st.number_input, st.text_area, st.date_input,
    st.time_input, st.color_picker.
    """

    def new_func(label, *args, **kwargs):
        value = func(label, *args, **kwargs)

        # Update aggregate counts
        if label not in counts["widgets"]:
            counts["widgets"][label] = {}

        # Update session counts
        if label not in ss.session_counts["widgets"]:
            ss.session_counts["widgets"][label] = {}

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
        if formatted_value not in ss.session_counts["widgets"][label]:
            ss.session_counts["widgets"][label][formatted_value] = 0

        if formatted_value != st.session_state.state_dict.get(label, None):
            counts["widgets"][label][formatted_value] += 1
            ss.session_counts["widgets"][label][formatted_value] += 1

        st.session_state.state_dict[label] = formatted_value
        return value

    return new_func


def _wrap_chat_input(func):
    """
    Wrap a streamlit function that returns a single value (str/int/float/datetime/...),
    e.g. st.slider, st.text_input, st.number_input, st.text_area, st.date_input,
    st.time_input, st.color_picker.
    """

    def new_func(placeholder, *args, **kwargs):
        value = func(placeholder, *args, **kwargs)

        # Update aggregate counts
        if placeholder not in counts["widgets"]:
            counts["widgets"][placeholder] = {}

        # Update session counts
        if placeholder not in ss.session_counts["widgets"]:
            ss.session_counts["widgets"][placeholder] = {}

        formatted_value = str(value)

        if formatted_value not in counts["widgets"][placeholder]:
            counts["widgets"][placeholder][formatted_value] = 0
        if formatted_value not in ss.session_counts["widgets"][placeholder]:
            ss.session_counts["widgets"][placeholder][formatted_value] = 0

        if formatted_value != st.session_state.state_dict.get(placeholder):
            counts["widgets"][placeholder][formatted_value] += 1
            ss.session_counts["widgets"][placeholder][formatted_value] += 1

        st.session_state.state_dict[placeholder] = formatted_value
        return value

    return new_func


def start_tracking(
    verbose: bool = False,
    firestore_key_file: Optional[str] = None,
    firestore_collection_name: str = "counts",
    load_from_json: Optional[Union[str, Path]] = None,
    streamlit_secrets_firestore_key: Optional[str] = None,
    firestore_project_name: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """
    Start tracking user inputs to a streamlit app.

    If you call this function directly, you NEED to call `streamlit_analytics.
    stop_tracking()` at the end of your streamlit script. For a more convenient
    interface, wrap your streamlit calls in `with streamlit_analytics.track():`.
    """
    initialize_session_counts()

    if (
        streamlit_secrets_firestore_key is not None
        and not counts["loaded_from_firestore"]
    ):
        # Load both global and session counts in a single call
        firestore.load(
            counts=counts,
            service_account_json=None,
            collection_name=firestore_collection_name,
            streamlit_secrets_firestore_key=streamlit_secrets_firestore_key,
            firestore_project_name=firestore_project_name,
            session_id=session_id,  # This will load both global and session data
        )
        counts["loaded_from_firestore"] = True
        if verbose:
            print("Loaded count data from firestore:")
            print(counts)
            if session_id:
                print("Loaded session count data from firestore:")
                print(ss.session_counts)
            print()

    elif firestore_key_file and not counts["loaded_from_firestore"]:
        firestore.load(
            counts,
            firestore_key_file,
            firestore_collection_name,
            streamlit_secrets_firestore_key=None,
            firestore_project_name=None,
            session_id=session_id,
        )
        counts["loaded_from_firestore"] = True
        if verbose:
            print("Loaded count data from firestore:")
            print(counts)
            print()

    if load_from_json is not None:
        log_msg_prefix = "Loading counts from json: "
        try:
            # Using Path's read_text method simplifies file reading
            json_contents = Path(load_from_json).read_text()
            json_counts = json.loads(json_contents)

            # Use dict.update() for a cleaner way to merge the counts
            # This assumes you want json_counts to overwrite existing keys in counts
            counts.update({k: json_counts[k] for k in json_counts if k in counts})

            if verbose:
                logging.info(f"{log_msg_prefix}{load_from_json}")
                logging.info("SA2: Success! Loaded counts:")
                logging.info(counts)

        except FileNotFoundError:
            if verbose:
                logging.warning(
                    f"SA2: File {load_from_json} not found, proceeding with empty counts."
                )
        except Exception as e:
            # Catch-all for any other exceptions, log the error
            logging.error(f"SA2: Error loading counts from {load_from_json}: {e}")

    # Reset session state.
    if "user_tracked" not in st.session_state:
        st.session_state.user_tracked = False
    if "state_dict" not in st.session_state:
        st.session_state.state_dict = {}
    if "last_time" not in st.session_state:
        st.session_state.last_time = datetime.datetime.now()
    _track_user()

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
    # st_searchbox = _wrap_searchbox(_orig_searchbox)

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
    # st.sidebar.st_searchbox = _wrap_searchbox(_orig_sidebar_searchbox)  # type: ignore

    # new elements, testing
    # st.sidebar.download_button = _wrap_value(_orig_sidebar_download_button)
    # st.sidebar.link_button = _wrap_value(_orig_sidebar_link_button)
    # st.sidebar.page_link = _wrap_value(_orig_sidebar_page_link)
    # st.sidebar.toggle = _wrap_value(_orig_sidebar_toggle)
    # st.sidebar.camera_input = _wrap_value(_orig_sidebar_camera_input)

    # replacements = {
    #     "button": _wrap_bool,
    #     "checkbox": _wrap_bool,
    #     "radio": _wrap_select,
    #     "selectbox": _wrap_select,
    #     "multiselect": _wrap_multiselect,
    #     "slider": _wrap_value,
    #     "select_slider": _wrap_select,
    #     "text_input": _wrap_value,
    #     "number_input": _wrap_value,
    #     "text_area": _wrap_value,
    #     "date_input": _wrap_value,
    #     "time_input": _wrap_value,
    #     "file_uploader": _wrap_file_uploader,
    #     "color_picker": _wrap_value,
    # }

    if verbose:
        logging.info("\nSA2: Tracking script execution with streamlit-analytics...")


def stop_tracking(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[Union[str, Path]] = None,
    firestore_key_file: Optional[str] = None,
    firestore_collection_name: str = "counts",
    verbose: bool = False,
    load_from_json: Optional[Union[str, Path]] = None,
    streamlit_secrets_firestore_key: Optional[str] = None,
    firestore_project_name: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """
    Stop tracking user inputs to a streamlit app.

    Should be called after `streamlit-analytics.start_tracking()`. This method also
    shows the analytics results below your app if you attach `?analytics=on` to the URL.
    """

    if verbose:
        logging.info("SA2: Finished script execution. New counts:")
        logging.info(
            "%s", counts
        )  # Use %s and pass counts to logging to handle complex objects
        logging.info("%s", "-" * 80)  # For separators or multi-line messages

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
    # st.searchbox = _orig_searchbox
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
    # st.sidebar.searchbox = _orig_sidebar_searchbox
    # Save count data to firestore.
    # TODO: Maybe don't save on every iteration but on regular intervals in a background
    #   thread.
    if (
        streamlit_secrets_firestore_key is not None
        and firestore_project_name is not None
    ):
        if verbose:
            print("Saving count data to firestore:")
            print(counts)
            print("Saving session count data to firestore:")
            print(ss.session_counts)
            print()

        # Save both global and session counts in a single call
        firestore.save(
            counts=counts,
            service_account_json=None,
            collection_name=firestore_collection_name,
            streamlit_secrets_firestore_key=streamlit_secrets_firestore_key,
            firestore_project_name=firestore_project_name,
            session_id=session_id,  # This will save both global and session data
        )

    elif (
        streamlit_secrets_firestore_key is None
        and firestore_project_name is None
        and firestore_key_file
    ):
        if verbose:
            print("Saving count data to firestore:")
            print(counts)
            print()
        firestore.save(
            counts,
            firestore_key_file,
            firestore_collection_name,
            streamlit_secrets_firestore_key=None,
            firestore_project_name=None,
            session_id=session_id,
        )

    # Dump the counts to json file if `save_to_json` is set.
    # TODO: Make sure this is not locked if writing from multiple threads.

    # Assuming 'counts' is your data to be saved and 'save_to_json' is the path to your json file.
    if save_to_json is not None:
        # Create a Path object for the file
        file_path = Path(save_to_json)

        # Ensure the directory containing the file exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open the file and dump the json data
        with file_path.open("w") as f:
            json.dump(counts, f)

        if verbose:
            print("Storing results to file:", save_to_json)

    # Show analytics results in the streamlit app if `?analytics=on` is set in the URL.
    query_params = st.query_params
    if "analytics" in query_params and "on" in query_params["analytics"]:
        st.write("---")
        display.show_results(counts, reset_counts, unsafe_password)


@contextmanager
def track(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[Union[str, Path]] = None,
    firestore_key_file: Optional[str] = None,
    firestore_collection_name: str = "counts",
    verbose=False,
    load_from_json: Optional[Union[str, Path]] = None,
    streamlit_secrets_firestore_key: Optional[str] = None,
    firestore_project_name: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """
    Context manager to start and stop tracking user inputs to a streamlit app.

    To use this, wrap all calls to streamlit in `with streamlit_analytics.track():`.
    This also shows the analytics results below your app if you attach
    `?analytics=on` to the URL.
    """
    if (
        streamlit_secrets_firestore_key is not None
        and firestore_project_name is not None
    ):
        start_tracking(
            verbose=verbose,
            firestore_collection_name=firestore_collection_name,
            streamlit_secrets_firestore_key=streamlit_secrets_firestore_key,
            firestore_project_name=firestore_project_name,
            session_id=session_id,
        )

    else:
        start_tracking(
            verbose=verbose,
            firestore_key_file=firestore_key_file,
            firestore_collection_name=firestore_collection_name,
            load_from_json=load_from_json,
            session_id=session_id,
        )
    # Yield here to execute the code in the with statement. This will call the wrappers
    # above, which track all inputs.
    yield
    if (
        streamlit_secrets_firestore_key is not None
        and firestore_project_name is not None
    ):
        stop_tracking(
            unsafe_password=unsafe_password,
            firestore_collection_name=firestore_collection_name,
            streamlit_secrets_firestore_key=streamlit_secrets_firestore_key,
            firestore_project_name=firestore_project_name,
            session_id=session_id,
            verbose=verbose,
        )
    else:
        stop_tracking(
            unsafe_password=unsafe_password,
            save_to_json=save_to_json,
            firestore_key_file=firestore_key_file,
            firestore_collection_name=firestore_collection_name,
            verbose=verbose,
            session_id=session_id,
        )
