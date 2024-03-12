"""
Main API functions for the user to start and stop analytics tracking.
"""

import datetime
import json
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Union

import streamlit as st

from . import display, firestore
from .tracker import counts
from .utils import replace_empty
from .wrappers import (_wrap_button, _wrap_chat_input, _wrap_checkbox,
                       _wrap_file_uploader, _wrap_multiselect, _wrap_select,
                       _wrap_value)

logging.basicConfig(
    level=logging.INFO, format="streamlit-analytics2: %(levelname)s: %(message)s"
)

# Dict that holds all analytics results. Note that this is persistent across users,
# as modules are only imported once by a streamlit app.
# counts = {"loaded_from_firestore": False}


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

def _track_user():
    """Track individual pageviews by storing user id to session state."""
    today = str(datetime.date.today())
    if counts["per_day"]["days"][-1] != today:
        # TODO: Insert 0 for all days between today and last entry.
        counts["per_day"]["days"].append(today)
        counts["per_day"]["pageviews"].append(0)
        counts["per_day"]["script_runs"].append(0)
    counts["total_script_runs"] += 1
    counts["per_day"]["script_runs"][-1] += 1
    now = datetime.datetime.now()
    counts["total_time_seconds"] += (now - st.session_state.last_time).total_seconds()
    st.session_state.last_time = now
    if not st.session_state.user_tracked:
        st.session_state.user_tracked = True
        counts["total_pageviews"] += 1
        counts["per_day"]["pageviews"][-1] += 1
        # print("Tracked new user")


def start_tracking(
    verbose: bool = False,
    firestore_key_file: Optional[str] = None,
    firestore_collection_name: str = "counts",
    load_from_json: Optional[Union[str, Path]] = None,
):
    """
    Start tracking user inputs to a streamlit app.

    If you call this function directly, you NEED to call
    `streamlit_analytics.stop_tracking()` at the end of your streamlit script.
    For a more convenient interface, wrap your streamlit calls in
    `with streamlit_analytics.track():`.
    """

    if firestore_key_file and not counts["loaded_from_firestore"]:
        firestore.load(counts, firestore_key_file, firestore_collection_name)
        counts["loaded_from_firestore"] = True

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
                logging.info("Success! Loaded counts:")
                logging.info(counts)

        except FileNotFoundError:
            if verbose:
                logging.warning(
                    f"File {load_from_json} not found, proceeding with empty counts."
                )
        except Exception as e:
            # Catch-all for any other exceptions, log the error
            logging.error(f"Error loading counts from {load_from_json}: {e}")

    # Reset session state.
    if "user_tracked" not in st.session_state:
        st.session_state.user_tracked = False
    if "state_dic" not in st.session_state:
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
        logging.info("\nTracking script execution with streamlit-analytics...")


def stop_tracking(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[Union[str, Path]] = None,
    firestore_key_file: Optional[str] = None,
    firestore_collection_name: str = "counts",
    verbose: bool = False,
):
    """
    Stop tracking user inputs to a streamlit app.

    Should be called after `streamlit-analytics.start_tracking()`. This method also
    shows the analytics results below your app if you attach `?analytics=on` to the URL.
    """

    if verbose:
        logging.info("Finished script execution. New counts:")
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

    # Save count data to firestore.
    # TODO: Maybe don't save on every iteration but on regular intervals in a background
    #   thread.
    if firestore_key_file:
        if verbose:
            print("Saving count data to firestore:")
            print(counts)
            print()
        firestore.save(counts, firestore_key_file, firestore_collection_name)

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
):
    """
    Context manager to start and stop tracking user inputs to a streamlit app.

    To use this, wrap all calls to streamlit in `with streamlit_analytics.track():`.
    This also shows the analytics results below your app if you attach
    `?analytics=on` to the URL.
    """

    start_tracking(
        verbose=verbose,
        firestore_key_file=firestore_key_file,
        firestore_collection_name=firestore_collection_name,
        load_from_json=load_from_json,
    )

    # Yield here to execute the code in the with statement. This will call the wrappers
    # above, which track all inputs.
    yield
    stop_tracking(
        unsafe_password=unsafe_password,
        save_to_json=save_to_json,
        firestore_key_file=firestore_key_file,
        firestore_collection_name=firestore_collection_name,
        verbose=verbose,
    )
