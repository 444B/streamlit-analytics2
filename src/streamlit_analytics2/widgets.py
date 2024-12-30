# import streamlit as st


# def copy_original():
#     # Store original streamlit functions. They will be monkey-patched with some wrappers
#     # in `start_tracking` (see wrapper functions below).
#     _orig_button = st.button
#     _orig_checkbox = st.checkbox
#     _orig_radio = st.radio
#     _orig_selectbox = st.selectbox
#     _orig_multiselect = st.multiselect
#     _orig_slider = st.slider
#     _orig_select_slider = st.select_slider
#     _orig_text_input = st.text_input
#     _orig_number_input = st.number_input
#     _orig_text_area = st.text_area
#     _orig_date_input = st.date_input
#     _orig_time_input = st.time_input
#     _orig_file_uploader = st.file_uploader
#     _orig_color_picker = st.color_picker
#     # new elements, testing
#     # _orig_download_button = st.download_button
#     # _orig_link_button = st.link_button
#     # _orig_page_link = st.page_link
#     # _orig_toggle = st.toggle
#     # _orig_camera_input = st.camera_input
#     _orig_chat_input = st.chat_input
#     # _orig_searchbox = st_searchbox

#     _orig_sidebar_button = st.sidebar.button
#     _orig_sidebar_checkbox = st.sidebar.checkbox
#     _orig_sidebar_radio = st.sidebar.radio
#     _orig_sidebar_selectbox = st.sidebar.selectbox
#     _orig_sidebar_multiselect = st.sidebar.multiselect
#     _orig_sidebar_slider = st.sidebar.slider
#     _orig_sidebar_select_slider = st.sidebar.select_slider
#     _orig_sidebar_text_input = st.sidebar.text_input
#     _orig_sidebar_number_input = st.sidebar.number_input
#     _orig_sidebar_text_area = st.sidebar.text_area
#     _orig_sidebar_date_input = st.sidebar.date_input
#     _orig_sidebar_time_input = st.sidebar.time_input
#     _orig_sidebar_file_uploader = st.sidebar.file_uploader
#     _orig_sidebar_color_picker = st.sidebar.color_picker
#     # _orig_sidebar_searchbox = st.sidebar.st_searchbox
#     # new elements, testing
#     # _orig_sidebar_download_button = st.sidebar.download_button
#     # _orig_sidebar_link_button = st.sidebar.link_button
#     # _orig_sidebar_page_link = st.sidebar.page_link
#     # _orig_sidebar_toggle = st.sidebar.toggle
#     # _orig_sidebar_camera_input = st.sidebar.camera_input


# def monkey_patch():
#     # Monkey-patch streamlit to call the wrappers above.
#     st.button = _wrap.button(_orig_button)
#     st.checkbox = _wrap.checkbox(_orig_checkbox)
#     st.radio = _wrap.select(_orig_radio)
#     st.selectbox = _wrap.select(_orig_selectbox)
#     st.multiselect = _wrap.multiselect(_orig_multiselect)
#     st.slider = _wrap.value(_orig_slider)
#     st.select_slider = _wrap.select(_orig_select_slider)
#     st.text_input = _wrap.value(_orig_text_input)
#     st.number_input = _wrap.value(_orig_number_input)
#     st.text_area = _wrap.value(_orig_text_area)
#     st.date_input = _wrap.value(_orig_date_input)
#     st.time_input = _wrap.value(_orig_time_input)
#     st.file_uploader = _wrap.file_uploader(_orig_file_uploader)
#     st.color_picker = _wrap.value(_orig_color_picker)
#     # new elements, testing
#     # st.download_button = _wrap.value(_orig_download_button)
#     # st.link_button = _wrap.value(_orig_link_button)
#     # st.page_link = _wrap.value(_orig_page_link)
#     # st.toggle = _wrap.value(_orig_toggle)
#     # st.camera_input = _wrap.value(_orig_camera_input)
#     st.chat_input = _wrap.chat_input(_orig_chat_input)
#     # st_searchbox = _wrap.searchbox(_orig_searchbox)

#     st.sidebar.button = _wrap.button(_orig_sidebar_button)  # type: ignore
#     st.sidebar.checkbox = _wrap.checkbox(_orig_sidebar_checkbox)  # type: ignore
#     st.sidebar.radio = _wrap.select(_orig_sidebar_radio)  # type: ignore
#     st.sidebar.selectbox = _wrap.select(_orig_sidebar_selectbox)  # type: ignore
#     st.sidebar.multiselect = _wrap.multiselect(_orig_sidebar_multiselect)  # type: ignore
#     st.sidebar.slider = _wrap.value(_orig_sidebar_slider)  # type: ignore
#     st.sidebar.select_slider = _wrap.select(_orig_sidebar_select_slider)  # type: ignore
#     st.sidebar.text_input = _wrap.value(_orig_sidebar_text_input)  # type: ignore
#     st.sidebar.number_input = _wrap.value(_orig_sidebar_number_input)  # type: ignore
#     st.sidebar.text_area = _wrap.value(_orig_sidebar_text_area)  # type: ignore
#     st.sidebar.date_input = _wrap.value(_orig_sidebar_date_input)  # type: ignore
#     st.sidebar.time_input = _wrap.value(_orig_sidebar_time_input)  # type: ignore
#     st.sidebar.file_uploader = _wrap.file_uploader(_orig_sidebar_file_uploader)  # type: ignore
#     st.sidebar.color_picker = _wrap.value(_orig_sidebar_color_picker)  # type: ignore
#     # st.sidebar.st_searchbox = _wrap.searchbox(_orig_sidebar_searchbox)  # type: ignore

#     # new elements, testing
#     # st.sidebar.download_button = _wrap.value(_orig_sidebar_download_button)
#     # st.sidebar.link_button = _wrap.value(_orig_sidebar_link_button)
#     # st.sidebar.page_link = _wrap.value(_orig_sidebar_page_link)
#     # st.sidebar.toggle = _wrap.value(_orig_sidebar_toggle)
#     # st.sidebar.camera_input = _wrap.value(_orig_sidebar_camera_input)

#     # replacements = {
#     #     "button": _wrap.bool,
#     #     "checkbox": _wrap.bool,
#     #     "radio": _wrap.select,
#     #     "selectbox": _wrap.select,
#     #     "multiselect": _wrap.multiselect,
#     #     "slider": _wrap.value,
#     #     "select_slider": _wrap.select,
#     #     "text_input": _wrap.value,
#     #     "number_input": _wrap.value,
#     #     "text_area": _wrap.value,
#     #     "date_input": _wrap.value,
#     #     "time_input": _wrap.value,
#     #     "file_uploader": _wrap.file_uploader,
#     #     "color_picker": _wrap.value,
#     # }


# def reset_widgets():
#     # Reset streamlit functions.
#     st.button = _orig_button
#     st.checkbox = _orig_checkbox
#     st.radio = _orig_radio
#     st.selectbox = _orig_selectbox
#     st.multiselect = _orig_multiselect
#     st.slider = _orig_slider
#     st.select_slider = _orig_select_slider
#     st.text_input = _orig_text_input
#     st.number_input = _orig_number_input
#     st.text_area = _orig_text_area
#     st.date_input = _orig_date_input
#     st.time_input = _orig_time_input
#     st.file_uploader = _orig_file_uploader
#     st.color_picker = _orig_color_picker
#     # new elements, testing
#     # st.download_button = _orig_download_button
#     # st.link_button = _orig_link_button
#     # st.page_link = _orig_page_link
#     # st.toggle = _orig_toggle
#     # st.camera_input = _orig_camera_input
#     st.chat_input = _orig_chat_input
#     # st.searchbox = _orig_searchbox
#     st.sidebar.button = _orig_sidebar_button  # type: ignore
#     st.sidebar.checkbox = _orig_sidebar_checkbox  # type: ignore
#     st.sidebar.radio = _orig_sidebar_radio  # type: ignore
#     st.sidebar.selectbox = _orig_sidebar_selectbox  # type: ignore
#     st.sidebar.multiselect = _orig_sidebar_multiselect  # type: ignore
#     st.sidebar.slider = _orig_sidebar_slider  # type: ignore
#     st.sidebar.select_slider = _orig_sidebar_select_slider  # type: ignore
#     st.sidebar.text_input = _orig_sidebar_text_input  # type: ignore
#     st.sidebar.number_input = _orig_sidebar_number_input  # type: ignore
#     st.sidebar.text_area = _orig_sidebar_text_area  # type: ignore
#     st.sidebar.date_input = _orig_sidebar_date_input  # type: ignore
#     st.sidebar.time_input = _orig_sidebar_time_input  # type: ignore
#     st.sidebar.file_uploader = _orig_sidebar_file_uploader  # type: ignore
#     st.sidebar.color_picker = _orig_sidebar_color_picker  # type: ignore
#     # new elements, testing
#     # st.sidebar.download_button = _orig_sidebar_download_button
#     # st.sidebar.link_button = _orig_sidebar_link_button
#     # st.sidebar.page_link = _orig_sidebar_page_link
#     # st.sidebar.toggle = _orig_sidebar_toggle
#     # st.sidebar.camera_input = _orig_sidebar_camera_input
#     # st.sidebar.searchbox = _orig_sidebar_searchbox
#     # Save data to firestore.
#     # TODO: Maybe don't save on every iteration but on regular intervals in a background
#     #   thread.
