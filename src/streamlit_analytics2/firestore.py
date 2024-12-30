import json

import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from streamlit import session_state as ss

from .state import data  # noqa: F401


def sanitize_data(data):  # noqa: F811
    if isinstance(data, dict):
        # Recursively sanitize dictionary keys
        return {str(k) if k else "": sanitize_data(v) for k, v in data.items() if k}
    elif isinstance(data, list):
        # Apply sanitization to elements in lists
        return [sanitize_data(item) for item in data]
    else:
        return data


def load(
    data,  # noqa: F811
    service_account_json,
    collection_name,
    streamlit_secrets_firestore_key,
    firestore_project_name,
    session_id=None,
):
    """Load count data from firestore into `data`."""
    firestore_data = None
    firestore_session_data = None

    if streamlit_secrets_firestore_key is not None:
        # Following along here
        # https://blog.streamlit.io/streamlit-firestore-continued/#part-4-securely-deploying-on-streamlit-sharing for deploying to Streamlit Cloud with Firestore
        key_dict = json.loads(st.secrets[streamlit_secrets_firestore_key])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=firestore_project_name)
        col = db.collection(collection_name)
        firestore_data = col.document("data").get().to_dict()
        if session_id is not None:
            firestore_session_data = col.document(session_id).get().to_dict()
    else:
        db = firestore.Client.from_service_account_json(service_account_json)
        col = db.collection(collection_name)
        firestore_data = col.document("data").get().to_dict()
        if session_id is not None:
            firestore_session_data = col.document(session_id).get().to_dict()

    if firestore_data is not None:
        for key in firestore_data:
            if key in data:
                data[key] = firestore_data[key]

    if firestore_session_data is not None:
        for key in firestore_session_data:
            if key in ss.session_data:
                ss.session_data[key] = firestore_session_data[key]

    # Log loaded data for debugging
    # logging.debug("Data loaded from Firestore: %s", firestore_data)


def save(
    data,  # noqa: F811
    service_account_json,
    collection_name,
    streamlit_secrets_firestore_key,
    firestore_project_name,
    session_id=None,
):
    """Save count data from `data` to firestore."""

    # Ensure all keys are strings and not empty
    sanitized_data = sanitize_data(data)

    if streamlit_secrets_firestore_key is not None:
        # Following along here https://blog.streamlit.io/streamlit-firestore-continued/#part-4-securely-deploying-on-streamlit-sharing for deploying to Streamlit Cloud with Firestore
        key_dict = json.loads(st.secrets[streamlit_secrets_firestore_key])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=firestore_project_name)
    else:
        db = firestore.Client.from_service_account_json(service_account_json)
    col = db.collection(collection_name)
    # TODO pass user set argument via config screen for the name of document
    # currently hard coded to be "data"

    # Log the data being saved
    # logging.debug("Data being saved to Firestore: %s", sanitized_data)

    # Attempt to save to Firestore
    col.document("data").set(sanitized_data)  # creates if doesn't exist
    if session_id is not None:
        sanitized_session_data = sanitize_data(ss.session_data)
        col.document(session_id).set(sanitized_session_data)  # creates if doesn't exist
