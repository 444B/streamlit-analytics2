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

from . import config, display, firestore, utils, widgets  # noqa: F811 F401
from . import wrappers as _wrap
from .state import data, reset_data

# from streamlit_searchbox import st_searchbox

# TODO look into https://github.com/444B/streamlit-analytics2/pull/119 to
# integrate
# logging.basicConfig(
#     level=logging.INFO, format="streamlit-analytics2: %(levelname)s: %(message)s"
# )
# Uncomment this during testing
# logging.info("SA2: Streamlit-analytics2 successfully imported")


def update_session_stats(data_dict: Dict[str, Any]):
    """
    Update the session data with the current state.

    Parameters
    ----------
    data : Dict[str, Any]
        Data, either aggregate or session-specific.

    Returns
    -------
    Dict[str, Any]
        Updated data with the current state of time-dependent elements.
    """
    today = str(datetime.date.today())
    if data_dict["per_day"]["days"][-1] != today:
        # TODO: Insert 0 for all days between today and last entry.
        data_dict["per_day"]["days"].append(today)
        data_dict["per_day"]["pageviews"].append(0)
        data_dict["per_day"]["script_runs"].append(0)
    data_dict["total_script_runs"] += 1
    data_dict["per_day"]["script_runs"][-1] += 1
    now = datetime.datetime.now()
    data_dict["total_time_seconds"] += (
        now - st.session_state.last_time
    ).total_seconds()
    st.session_state.last_time = now
    if not st.session_state.user_tracked:
        st.session_state.user_tracked = True
        data_dict["total_pageviews"] += 1
        data_dict["per_day"]["pageviews"][-1] += 1


def _track_user():
    """Track individual pageviews by storing user id to session state."""
    update_session_stats(data)
    update_session_stats(ss.session_data)


def start_tracking(
    verbose: bool = False,
    firestore_key_file: Optional[str] = None,
    firestore_collection_name: str = "data",
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
    utils.initialize_session_data()

    if (
        streamlit_secrets_firestore_key is not None
        and not data["loaded_from_firestore"]
    ):
        # Load both global and session data in a single call
        firestore.load(
            data=data,
            service_account_json=None,
            collection_name=firestore_collection_name,
            streamlit_secrets_firestore_key=streamlit_secrets_firestore_key,
            firestore_project_name=firestore_project_name,
            session_id=session_id,  # This will load both global and session data
        )
        data["loaded_from_firestore"] = True
        if verbose:
            print("Loaded count data from firestore:")
            print(data)
            if session_id:
                print("Loaded session count data from firestore:")
                print(ss.session_data)
            print()

    elif firestore_key_file and not data["loaded_from_firestore"]:
        firestore.load(
            data,
            firestore_key_file,
            firestore_collection_name,
            streamlit_secrets_firestore_key=None,
            firestore_project_name=None,
            session_id=session_id,
        )
        data["loaded_from_firestore"] = True
        if verbose:
            print("Loaded count data from firestore:")
            print(data)
            print()

    if load_from_json is not None:
        log_msg_prefix = "Loading data from json: "
        try:
            # Using Path's read_text method simplifies file reading
            json_contents = Path(load_from_json).read_text()
            json_data = json.loads(json_contents)

            # Use dict.update() for a cleaner way to merge the data
            # This assumes you want json_data to overwrite existing keys in data
            data.update({k: json_data[k] for k in json_data if k in data})

            if verbose:
                logging.info(f"{log_msg_prefix}{load_from_json}")
                logging.info("SA2: Success! Loaded data:")
                logging.info(data)

        except FileNotFoundError:
            if verbose:
                logging.warning(
                    f"SA2: File {load_from_json} not found, proceeding with empty data."
                )
        except Exception as e:
            # Catch-all for any other exceptions, log the error
            logging.error(f"SA2: Error loading data from {load_from_json}: {e}")

    # Reset session state.
    if "user_tracked" not in st.session_state:
        st.session_state.user_tracked = False
    if "state_dict" not in st.session_state:
        st.session_state.state_dict = {}
    if "last_time" not in st.session_state:
        st.session_state.last_time = datetime.datetime.now()
    _track_user()

    # widgets.monkey_patch()
    # Monkey-patch streamlit to call the wrappers above.
    st.button = _wrap.button(_orig_button)
    st.checkbox = _wrap.checkbox(_orig_checkbox)
    st.radio = _wrap.select(_orig_radio)
    st.selectbox = _wrap.select(_orig_selectbox)
    st.multiselect = _wrap.multiselect(_orig_multiselect)
    st.slider = _wrap.value(_orig_slider)
    st.select_slider = _wrap.select(_orig_select_slider)
    st.text_input = _wrap.value(_orig_text_input)
    st.number_input = _wrap.value(_orig_number_input)
    st.text_area = _wrap.value(_orig_text_area)
    st.date_input = _wrap.value(_orig_date_input)
    st.time_input = _wrap.value(_orig_time_input)
    st.file_uploader = _wrap.file_uploader(_orig_file_uploader)
    st.color_picker = _wrap.value(_orig_color_picker)
    # new elements, testing
    # st.download_button = _wrap.value(_orig_download_button)
    # st.link_button = _wrap.value(_orig_link_button)
    # st.page_link = _wrap.value(_orig_page_link)
    # st.toggle = _wrap.value(_orig_toggle)
    # st.camera_input = _wrap.value(_orig_camera_input)
    st.chat_input = _wrap.chat_input(_orig_chat_input)
    # st_searchbox = _wrap.searchbox(_orig_searchbox)

    st.sidebar.button = _wrap.button(_orig_sidebar_button)  # type: ignore
    st.sidebar.checkbox = _wrap.checkbox(_orig_sidebar_checkbox)  # type: ignore
    st.sidebar.radio = _wrap.select(_orig_sidebar_radio)  # type: ignore
    st.sidebar.selectbox = _wrap.select(_orig_sidebar_selectbox)  # type: ignore
    st.sidebar.multiselect = _wrap.multiselect(_orig_sidebar_multiselect)  # type: ignore
    st.sidebar.slider = _wrap.value(_orig_sidebar_slider)  # type: ignore
    st.sidebar.select_slider = _wrap.select(_orig_sidebar_select_slider)  # type: ignore
    st.sidebar.text_input = _wrap.value(_orig_sidebar_text_input)  # type: ignore
    st.sidebar.number_input = _wrap.value(_orig_sidebar_number_input)  # type: ignore
    st.sidebar.text_area = _wrap.value(_orig_sidebar_text_area)  # type: ignore
    st.sidebar.date_input = _wrap.value(_orig_sidebar_date_input)  # type: ignore
    st.sidebar.time_input = _wrap.value(_orig_sidebar_time_input)  # type: ignore
    st.sidebar.file_uploader = _wrap.file_uploader(_orig_sidebar_file_uploader)  # type: ignore
    st.sidebar.color_picker = _wrap.value(_orig_sidebar_color_picker)  # type: ignore
    # st.sidebar.st_searchbox = _wrap.searchbox(_orig_sidebar_searchbox)  # type: ignore

    # new elements, testing
    # st.sidebar.download_button = _wrap.value(_orig_sidebar_download_button)
    # st.sidebar.link_button = _wrap.value(_orig_sidebar_link_button)
    # st.sidebar.page_link = _wrap.value(_orig_sidebar_page_link)
    # st.sidebar.toggle = _wrap.value(_orig_sidebar_toggle)
    # st.sidebar.camera_input = _wrap.value(_orig_sidebar_camera_input)

    # replacements = {
    #     "button": _wrap.bool,
    #     "checkbox": _wrap.bool,
    #     "radio": _wrap.select,
    #     "selectbox": _wrap.select,
    #     "multiselect": _wrap.multiselect,
    #     "slider": _wrap.value,
    #     "select_slider": _wrap.select,
    #     "text_input": _wrap.value,
    #     "number_input": _wrap.value,
    #     "text_area": _wrap.value,
    #     "date_input": _wrap.value,
    #     "time_input": _wrap.value,
    #     "file_uploader": _wrap.file_uploader,
    #     "color_picker": _wrap.value,
    # }

    if verbose:
        logging.info("\nSA2: Tracking script execution with streamlit-analytics...")


def stop_tracking(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[Union[str, Path]] = None,
    firestore_key_file: Optional[str] = None,
    firestore_collection_name: str = "data",
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
        logging.info("SA2: Finished script execution. New data:")
        logging.info(
            "%s", data
        )  # Use %s and pass data to logging to handle complex objects
        logging.info("%s", "-" * 80)  # For separators or multi-line messages

    # widgets.reset_widgets()

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
            print(data)
            print("Saving session count data to firestore:")
            print(ss.session_data)
            print()

        # Save both global and session data in a single call
        firestore.save(
            data=data,
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
            print(data)
            print()
        firestore.save(
            data,
            firestore_key_file,
            firestore_collection_name,
            streamlit_secrets_firestore_key=None,
            firestore_project_name=None,
            session_id=session_id,
        )

    # Dump the data to json file if `save_to_json` is set.
    # TODO: Make sure this is not locked if writing from multiple threads.

    # Assuming 'data' is your data to be saved and 'save_to_json' is the path to your json file.
    if save_to_json is not None:
        # Create a Path object for the file
        file_path = Path(save_to_json)

        # Ensure the directory containing the file exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open the file and dump the json data
        with file_path.open("w") as f:
            json.dump(data, f)

        if verbose:
            print("Storing results to file:", save_to_json)

    # Show analytics results in the streamlit app if `?analytics=on` is set in the URL.
    query_params = st.query_params
    if "analytics" in query_params and "on" in query_params["analytics"]:

        @st.dialog("Streamlit-Analytics2", width="large")
        def show_sa2(data, reset_data, unsafe_password):

            tab1, tab2 = st.tabs(["Data", "Config"])

            with tab1:
                display.show_results(data, reset_data, unsafe_password)

            with tab2:
                config.show_config()

        show_sa2(data, reset_data, unsafe_password)


@contextmanager
def track(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[Union[str, Path]] = None,
    firestore_key_file: Optional[str] = None,
    firestore_collection_name: str = "data",
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


if __name__ == "streamlit_analytics2.main":
    reset_data()

    # widgets.copy_original()
    # TODO need to fix the scope for this function call and then we can move
    # these variable assignments to widgets.py

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
