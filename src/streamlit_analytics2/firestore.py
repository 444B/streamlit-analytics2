"""Legacy Firestore persistence of the aggregate counters.

Needs the extra: ``pip install "streamlit-analytics2[firestore]"``.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import streamlit as st
from streamlit import session_state as ss

from .state import data  # noqa: F401


def _client(
    service_account_json: Optional[str],
    streamlit_secrets_firestore_key: Optional[str],
    firestore_project_name: Optional[str],
) -> Any:
    try:
        from google.cloud import firestore
        from google.oauth2 import service_account
    except ImportError as exc:  # pragma: no cover - depends on the extra
        raise ImportError(
            "Firestore support needs the extra: "
            "pip install 'streamlit-analytics2[firestore]'"
        ) from exc
    if streamlit_secrets_firestore_key is not None:
        # https://blog.streamlit.io/streamlit-firestore-continued/#part-4-securely-deploying-on-streamlit-sharing
        key_dict = json.loads(st.secrets[streamlit_secrets_firestore_key])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        return firestore.Client(credentials=creds, project=firestore_project_name)
    return firestore.Client.from_service_account_json(service_account_json)


def sanitize_data(data: Any) -> Any:  # noqa: F811
    """Firestore keys must be non-empty strings."""
    if isinstance(data, dict):
        return {str(k): sanitize_data(v) for k, v in data.items() if k}
    if isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data


def load(
    data: Dict[str, Any],  # noqa: F811
    service_account_json: Optional[str],
    collection_name: Optional[str],
    document_name: Optional[str],
    streamlit_secrets_firestore_key: Optional[str],
    firestore_project_name: Optional[str],
    session_id: Optional[str] = None,
) -> None:
    """Load count data from firestore into `data`."""
    db = _client(
        service_account_json, streamlit_secrets_firestore_key, firestore_project_name
    )
    col = db.collection(collection_name)
    firestore_data = col.document(document_name).get().to_dict()
    if firestore_data:
        for key in firestore_data:
            if key in data:
                data[key] = firestore_data[key]
    if session_id is not None:
        session_doc = col.document(session_id).get().to_dict()
        if session_doc:
            for key in session_doc:
                if key in ss.session_data:
                    ss.session_data[key] = session_doc[key]


def save(
    data: Dict[str, Any],  # noqa: F811
    service_account_json: Optional[str],
    collection_name: Optional[str],
    document_name: Optional[str],
    streamlit_secrets_firestore_key: Optional[str],
    firestore_project_name: Optional[str],
    session_id: Optional[str] = None,
) -> None:
    """Save count data from `data` to firestore (merge keeps foreign fields)."""
    db = _client(
        service_account_json, streamlit_secrets_firestore_key, firestore_project_name
    )
    col = db.collection(collection_name)
    col.document(document_name).set(sanitize_data(data), merge=True)
    if session_id is not None:
        col.document(session_id).set(sanitize_data(ss.session_data), merge=True)
