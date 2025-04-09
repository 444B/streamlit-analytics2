import streamlit as st

import streamlit_analytics2 as streamlit_analytics

COLLECTION_NAME = "streamlit-analytics-secrets-approach"
DOCUMENT_NAME = "counts"
PROJECT_NAME = "ev-monitoring-poc"

session_id = st.text_input("Session ID", help="This is the session ID that will be used to track individual session data. If not provided, tracking only occurs at an aggregate level.")

if session_id is not None and session_id == "":
    session_id = None
st.write(f"Session ID: {session_id}")
st.write(f"{streamlit_analytics.session_data["loaded_from_firestore"]=}")

tab1, tab2 = st.tabs(["Classic", "Advanced"])


# classic firestore load
with tab1:
    st.header("Classic")

    if st.button("Test Classic"):

        with streamlit_analytics.track(
            firestore_key_file="pages/firebase-key.json",
            firestore_collection_name=COLLECTION_NAME,
            firestore_document_name=DOCUMENT_NAME,
            firestore_project_name=PROJECT_NAME,
            verbose=True,
            session_id=session_id,
        ):

            st.text_input("Write something")
            st.button("Click me")
            
            st.write("# Aggregate Stats")
            st.write(streamlit_analytics.data)
            st.write("# Session Stats")
            st.write(streamlit_analytics.session_data)
            
    if st.button("Delete session data", key="delete_classic"):
        streamlit_analytics.delete_session_data(
            session_id,
            COLLECTION_NAME,
            firestore_project_name=PROJECT_NAME,
            firestore_key_file="pages/firebase-key.json"
        )


# Advanced storing of key in secrets.toml
with tab2:
    st.header("Advanced")

    with streamlit_analytics.track(
        firestore_collection_name=COLLECTION_NAME,
        streamlit_secrets_firestore_key="firebase",
        firestore_project_name=PROJECT_NAME,
        session_id=session_id,
        verbose=False):

        st.text_input("Write something", key="text_input2")
        st.button("Click me", key="button2")

        st.write("# Aggregate Stats")
        st.write(streamlit_analytics.data)
        st.write("# Session Stats")
        st.write(streamlit_analytics.session_data)

    if st.button("Delete session data", key="delete_advanced"):
        print("Session deletion button clicked")
        streamlit_analytics.delete_session_data(
            session_id,
            COLLECTION_NAME,
            firestore_project_name=PROJECT_NAME,
            streamlit_secrets_firestore_key="firebase",
        )
