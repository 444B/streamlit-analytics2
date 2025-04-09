import json
from pathlib import Path
from typing import Optional, Union

import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account

from .state import data, session_data  # noqa: F401


def sanitize_data(data):  # noqa: F811
    if isinstance(data, dict):
        # Recursively sanitize dictionary keys
        return {
            str(k) if k else "": sanitize_data(v) for k, v in data.items() if k
        }  # noqa: E501
    elif isinstance(data, list):
        # Apply sanitization to elements in lists
        return [sanitize_data(item) for item in data]
    else:
        return data


def load(
    data,  # noqa: F811
    service_account_json: Optional[Union[str, Path]] = None,
    collection_name: Optional[str] = None,
    document_name: Optional[str] = "counts",
    streamlit_secrets_firestore_key: Optional[str] = None,
    firestore_project_name: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """Load count data from firestore into `data`."""
    firestore_data = None
    firestore_session_data = None

    if streamlit_secrets_firestore_key is not None:
        # Following along here
        # https://blog.streamlit.io/streamlit-firestore-continued/#part-4-securely-deploying-on-streamlit-sharing  # noqa: E501
        # for deploying to Streamlit Cloud with Firestore
        key_dict = json.loads(st.secrets[streamlit_secrets_firestore_key])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=firestore_project_name)
        col = db.collection(collection_name)
        firestore_data = col.document(document_name).get().to_dict()
        if session_id is not None:
            firestore_session_data = col.document(session_id).get().to_dict()
    else:
        db = firestore.Client.from_service_account_json(service_account_json)
        col = db.collection(collection_name)
        firestore_data = col.document(document_name).get().to_dict()
        if session_id is not None:
            firestore_session_data = col.document(session_id).get().to_dict()

    if firestore_data is not None:
        for key in firestore_data:
            if key in data:
                data[key] = firestore_data[key]

    if firestore_session_data is not None:
        for key in firestore_session_data:
            if key in session_data:
                session_data[key] = firestore_session_data[key]

    # Log loaded data for debugging
    # logging.debug("Data loaded from Firestore: %s", firestore_data)


def save(
    data,  # noqa: F811
    service_account_json: Optional[Union[str, Path]] = None,
    collection_name: Optional[str] = None,
    document_name: Optional[str] = "counts",
    streamlit_secrets_firestore_key: Optional[str] = None,
    firestore_project_name: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """Save count data from `data` to firestore."""

    # Ensure all keys are strings and not empty
    sanitized_data = sanitize_data(data)

    if streamlit_secrets_firestore_key is not None:
        # Following along here https://blog.streamlit.io/streamlit-firestore-continued/#part-4-securely-deploying-on-streamlit-sharing  # noqa: E501
        # for deploying to Streamlit Cloud with Firestore
        key_dict = json.loads(st.secrets[streamlit_secrets_firestore_key])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=firestore_project_name)
    else:
        db = firestore.Client.from_service_account_json(service_account_json)
    col = db.collection(collection_name)
    # TODO pass user set argument via config screen for the name of document
    # currently hard coded to be "counts"

    # Attempt to save to Firestore
    # creates if doesn't exist
    col.document(document_name).set(sanitized_data, merge=True)
    if session_id is not None:
        sanitized_session_data = sanitize_data(session_data)
        col.document(session_id).set(sanitized_session_data, merge=True)


def delete(
    document_name: str,  # noqa: F811
    collection_name: str,
    service_account_json: Optional[Union[str, Path]] = None,
    streamlit_secrets_firestore_key: Optional[str] = None,
    firestore_project_name: Optional[str] = None,
):
    """Delete a document from firestore. Commonly used to delete session data when requested by a user by passing session_id as document_name."""
    if streamlit_secrets_firestore_key is not None:
        print("Using secrets to connect to firestore for deletion")
        # Following along here https://blog.streamlit.io/streamlit-firestore-continued/#part-4-securely-deploying-on-streamlit-sharing  # noqa: E501
        # for deploying to Streamlit Cloud with Firestore
        key_dict = json.loads(st.secrets[streamlit_secrets_firestore_key])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=firestore_project_name)
    else:
        db = firestore.Client.from_service_account_json(service_account_json)
    col = db.collection(collection_name)
    # TODO pass user set argument via config screen for the name of document
    # currently hard coded to be "counts"

    # Delete from firestore
    col.document(document_name).delete()
