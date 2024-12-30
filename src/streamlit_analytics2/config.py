import os
from pathlib import Path

import streamlit as st
import toml

# import logging

# Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "streamlit_analytics2": {"enabled": True},
    "storage": {
        "save": False,
        "type": "json",
        "save_to_json": "path/to/file.json",
        "load_from_json": "path/to/file.json",
    },
    "logs": {"verbose": False},
    "access": {"unsafe_password": "test123"},
    "firestore": {
        "enabled": False,
        "firestore_key_file": "firebase-key.json",
        "firestore_project_name": "",
        "firestore_collection_name": "data",
        "streamlit_secrets_firestore_key": "",
    },
    "session": {"session_id": ""},
}


def ensure_streamlit_dir():
    """Ensure .streamlit directory exists"""
    Path(".streamlit").mkdir(exist_ok=True)


def load_analytics_config():
    """Load analytics configuration with fallback to defaults"""
    path = os.path.join(os.getcwd(), ".streamlit/analytics.toml")
    # logger.info(f"Loading configuration from: {path}")

    try:
        if not os.path.exists(path):
            # logger.warning("Configuration file not found. Creating with defaults.")
            ensure_streamlit_dir()
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

        with open(path, "r") as file:
            config = toml.load(file)

        # Check if file is empty or missing required sections
        if not config or "streamlit_analytics2" not in config:
            # logger.warning("Invalid configuration found. Resetting to defaults.")
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

        return config

    except Exception as e:  # noqa: F841
        # logger.error(f"Error loading configuration: {str(e)}")
        st.error("Error loading configuration. Using defaults.")
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration to file"""
    path = os.path.join(os.getcwd(), ".streamlit/analytics.toml")
    try:
        ensure_streamlit_dir()
        with open(path, "w") as file:
            toml.dump(config, file)
        new_config = config  # noqa: F841
        # logger.info("Configuration saved successfully")
    except Exception as e:  # noqa: F841
        # logger.error(f"Error saving configuration: {str(e)}")
        st.error("Failed to save configuration")
        raise


def show_config():
    """Display and manage configuration"""
    st.title("Analytics Configuration")
    st.markdown(
        """
    This config page serves as a proof of concept for all SA2 existing features
    and some that dont exist yet (like CSV)\
    The Buttons do not currently do anything - please make a PR to help
    implement them.\
    To learn how to use all these features, please visit the [Wiki](https://github.com/444B/streamlit-analytics2/wiki) which could also do with some love

    > This will create a .streamlit/analytics.toml in the directory that you ran streamlit\
    > You can edit the values in the text file directly if its easier

    """
    )

    # Load current config
    config = load_analytics_config()

    # Configuration inputs for streamlit_analytics2
    enabled = st.checkbox(
        "Enable Streamlit_Analytics2", value=config["streamlit_analytics2"]["enabled"]
    )
    st.divider()
    storage_save = st.checkbox("Store Data", value=config["storage"]["save"])
    storage_type = st.radio(
        "Storage type",
        ["json", "CSV"],
        horizontal=True,
        index=0 if config["storage"]["type"] == "json" else 1,
    )
    save_path = st.text_input("Save File Path", value=config["storage"]["save_to_json"])
    load_path = st.text_input(
        "Load File Path", value=config["storage"]["load_from_json"]
    )
    st.divider()
    verbose_logging = st.checkbox("Verbose Logging", value=config["logs"]["verbose"])
    st.divider()
    password = st.text_input(
        "Access Password", value=config["access"]["unsafe_password"], type="password"
    )
    st.divider()
    firestore_enabled = st.checkbox(
        "Enable Firestore", value=config["firestore"]["enabled"]
    )
    firestore_key_file = st.text_input(
        "Firestore Key File Path", value=config["firestore"]["firestore_key_file"]
    )
    firestore_project = st.text_input(
        "Firestore Project Name", value=config["firestore"]["firestore_project_name"]
    )
    firestore_collection = st.text_input(
        "Firestore Collection Name",
        value=config["firestore"]["firestore_collection_name"],
    )
    firestore_secret_key = st.text_input(
        "Firestore Secret Key",
        value=config["firestore"]["streamlit_secrets_firestore_key"],
        type="password",
    )
    st.divider()
    session_id = st.text_input("Session ID", value=config["session"]["session_id"])
    st.divider()

    # Create new config from inputs
    new_config = {
        "streamlit_analytics2": {"enabled": enabled},
        "storage": {
            "save": storage_save,
            "type": storage_type,
            "save_to_json": save_path,
            "load_from_json": load_path,
        },
        "logs": {"verbose": verbose_logging},
        "access": {"unsafe_password": password},
        "firestore": {
            "enabled": firestore_enabled,
            "firestore_key_file": firestore_key_file,
            "firestore_project_name": firestore_project,
            "firestore_collection_name": firestore_collection,
            "streamlit_secrets_firestore_key": firestore_secret_key,
        },
        "session": {"session_id": session_id},
    }

    st.subheader("Current Configuration")
    st.write("This is the final JSON that will get parsed to TOML")
    st.json(new_config)

    col1, col2 = st.columns(2)

    with col1:
        # Save button
        if st.button("Save Configuration", type="primary"):
            try:
                save_config(new_config)
                st.success("Configuration saved!")
            except Exception:
                st.error("Failed to save configuration. Please check logs.")

    with col2:
        # Reset to defaults button
        if st.button("↻ Reset to Defaults"):
            save_config(DEFAULT_CONFIG)
            st.success("Configuration reset to defaults!")
            new_config = DEFAULT_CONFIG
            st.rerun()
