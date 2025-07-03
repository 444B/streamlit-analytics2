"""
Main API functions for streamlit-analytics2 with backward compatibility
and automatic setup handling
"""

import datetime
import json
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional, Union

import streamlit as st
from streamlit import session_state as ss

from . import firestore, utils, widgets
from . import wrappers as _wrap
from .state import data, reset_data

# Import display module properly
try:
    from . import display
except ImportError:
    import display

# Import new modules with fallback for backward compatibility
try:
    from .storage import save_to_csv, save_to_json as save_to_json_func, load_from_csv
except ImportError:
    # Fallback implementations for backward compatibility
    def save_to_csv(data, filepath, verbose=False):
        """Fallback CSV save - converts to JSON"""
        save_to_json_func(data, filepath.replace('.csv', '.json'), verbose)
    
    def load_from_csv(filepath, verbose=False):
        """Fallback CSV load - loads from JSON"""
        json_path = filepath.replace('.csv', '.json')
        with open(json_path, 'r') as f:
            return json.load(f)
    
    def save_to_json_func(data, filepath, verbose=False):
        """Basic JSON save"""
        filepath = Path(filepath)
        # Ensure we're saving in sa2_data directory
        if not str(filepath).startswith('sa2_data'):
            filepath = Path('sa2_data') / filepath.name
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        if verbose:
            logger.info(f"Saved data to JSON: {filepath}")

try:
    from .config import load_analytics_config, save_config, is_first_run, show_config
except ImportError:
    # Fallback if config module has issues
    def load_analytics_config():
        return DEFAULT_CONFIG.copy()
    
    def save_config(config):
        pass
    
    def is_first_run():
        return not Path(".streamlit/analytics.toml").exists()
    
    def show_config():
        st.write("Config module not available")

try:
    from .session_tracking import SessionManager
except ImportError:
    # Fallback if session tracking not available
    class SessionManager:
        def __init__(self, data):
            self.data = data
        
        def get_or_create_session(self):
            return "default-session"

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - streamlit-analytics2 - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default configuration - simplified
DEFAULT_CONFIG = {
    "streamlit_analytics2": {
        "enabled": True
    },
    "storage": {
        "save": True,
        "type": "json",
        "path": "sa2_data/analytics_data.json"
    },
    "access": {
        "password_hash": "",
        "require_auth": False
    },
    "setup": {
        "completed": False,
        "version": "0.11.0"
    }
}


def update_session_stats(data_dict: Dict[str, Any]):
    """Update the session data with the current state."""
    today = str(datetime.date.today())
    if data_dict["per_day"]["days"][-1] != today:
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
    # Initialize session data if not exists
    if 'session_data' not in ss:
        ss.session_data = {
            "total_pageviews": 0,
            "total_script_runs": 0,
            "total_time_seconds": 0,
            "start_time": str(datetime.datetime.now()),
            "per_day": {
                "days": [str(datetime.date.today())],
                "pageviews": [0],
                "script_runs": [0]
            },
            "widgets": {}
        }
    
    # Only update once per script run to avoid double counting
    if 'stats_updated' not in st.session_state:
        update_session_stats(data)
        update_session_stats(ss.session_data)
        st.session_state.stats_updated = True
    
    # Initialize session manager if enabled
    config = load_analytics_config()
    if config.get('session', {}).get('enabled', True):
        if '_sa2_session_manager' not in st.session_state:
            st.session_state._sa2_session_manager = SessionManager(data)
        
        session_manager = st.session_state._sa2_session_manager
        session_manager.get_or_create_session()


def _check_and_handle_first_run():
    """Check if first run and handle setup automatically"""
    if is_first_run():
        # Show setup in a dialog instead of stopping the app
        @st.dialog("Welcome to Streamlit Analytics2!", width="large")
        def initial_setup():
            from .config import show_initial_setup
            show_initial_setup()
        
        # Only show if not already shown in this session
        if 'sa2_setup_shown' not in st.session_state:
            st.session_state.sa2_setup_shown = True
            initial_setup()


def start_tracking(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[Union[str, Path]] = None,
    load_from_json: Optional[Union[str, Path]] = None,
    firestore_project_name: Optional[str] = None,
    firestore_collection_name: Optional[str] = None,
    firestore_document_name: Optional[str] = "counts",
    firestore_key_file: Optional[str] = None,
    streamlit_secrets_firestore_key: Optional[str] = None,
    session_id: Optional[str] = None,
    verbose=False,
):
    """
    Start tracking user inputs to a streamlit app.
    
    Maintains backward compatibility while adding new features.
    """
    # Handle first run setup automatically
    _check_and_handle_first_run()
    
    # Load configuration
    config = load_analytics_config()
    
    # Override config with function parameters for backward compatibility
    if unsafe_password is not None:
        # Convert to hash for security
        config['access']['password_hash'] = hashlib.sha256(unsafe_password.encode()).hexdigest()
        config['access']['require_auth'] = True
    
    # Apply verbose logging if specified
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load existing data if specified
    if load_from_json is not None:
        try:
            load_path = Path(load_from_json)
            # Check in sa2_data directory first
            sa2_path = Path('sa2_data') / load_path.name
            if sa2_path.exists():
                load_path = sa2_path
            
            if config.get('storage', {}).get('type') == 'csv':
                # Try CSV first if configured
                csv_path = str(load_path).replace('.json', '.csv')
                if Path(csv_path).exists():
                    loaded_data = load_from_csv(csv_path, verbose)
                    data.update(loaded_data)
                else:
                    # Fall back to JSON
                    with open(load_path, "r") as f:
                        data.update(json.load(f))
            else:
                # Default to JSON
                with open(load_path, "r") as f:
                    data.update(json.load(f))
                    
            if verbose:
                logger.info(f"Loaded data from {load_path}")
                
        except FileNotFoundError:
            if verbose:
                logger.warning(f"File {load_from_json} not found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading data: {e}")

    # Reset session state for tracking
    if "user_tracked" not in st.session_state:
        st.session_state.user_tracked = False
    if "state_dict" not in st.session_state:
        st.session_state.state_dict = {}
    if "last_time" not in st.session_state:
        st.session_state.last_time = datetime.datetime.now()
    
    # Clear the stats_updated flag when starting tracking
    if 'stats_updated' in st.session_state:
        del st.session_state.stats_updated
    
    _track_user()

    # Monkey-patch streamlit widgets (keeping all original functionality)
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
    st.chat_input = _wrap.chat_input(_orig_chat_input)

    # Sidebar widgets
    st.sidebar.button = _wrap.button(_orig_sidebar_button)
    st.sidebar.checkbox = _wrap.checkbox(_orig_sidebar_checkbox)
    st.sidebar.radio = _wrap.select(_orig_sidebar_radio)
    st.sidebar.selectbox = _wrap.select(_orig_sidebar_selectbox)
    st.sidebar.multiselect = _wrap.multiselect(_orig_sidebar_multiselect)
    st.sidebar.slider = _wrap.value(_orig_sidebar_slider)
    st.sidebar.select_slider = _wrap.select(_orig_sidebar_select_slider)
    st.sidebar.text_input = _wrap.value(_orig_sidebar_text_input)
    st.sidebar.number_input = _wrap.value(_orig_sidebar_number_input)
    st.sidebar.text_area = _wrap.value(_orig_sidebar_text_area)
    st.sidebar.date_input = _wrap.value(_orig_sidebar_date_input)
    st.sidebar.time_input = _wrap.value(_orig_sidebar_time_input)
    st.sidebar.file_uploader = _wrap.file_uploader(_orig_sidebar_file_uploader)
    st.sidebar.color_picker = _wrap.value(_orig_sidebar_color_picker)


def stop_tracking(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[Union[str, Path]] = None,
    firestore_key_file: Optional[str] = None,
    firestore_collection_name: Optional[str] = None,
    firestore_document_name: Optional[str] = "counts",
    streamlit_secrets_firestore_key: Optional[str] = None,
    firestore_project_name: Optional[str] = None,
    session_id: Optional[str] = None,
    verbose=False,
):
    """
    Stop tracking and save data.
    
    Maintains backward compatibility while supporting new storage options.
    """
    # Load configuration
    config = load_analytics_config()
    
    # Track one more time to get the latest state
    _track_user()
    
    # Handle Firestore saving (backward compatibility)
    if (streamlit_secrets_firestore_key is not None and 
        firestore_project_name is not None):
        if verbose:
            logger.info("Saving to Firestore")
        firestore.save(
            data=data,
            service_account_json=None,
            collection_name=firestore_collection_name,
            document_name=firestore_document_name,
            streamlit_secrets_firestore_key=streamlit_secrets_firestore_key,
            firestore_project_name=firestore_project_name,
            session_id=session_id,
        )
    elif firestore_key_file:
        if verbose:
            logger.info("Saving to Firestore with key file")
        firestore.save(
            data,
            firestore_key_file,
            firestore_collection_name,
            firestore_document_name,
            streamlit_secrets_firestore_key=None,
            firestore_project_name=None,
            session_id=session_id,
        )
    
    # Handle file saving based on config or parameters
    save_path = None
    if save_to_json is not None:
        # Explicit save path provided (backward compatibility)
        save_path = save_to_json
    elif config.get('storage', {}).get('save', False):
        # Use config settings
        save_path = config['storage'].get('save_to_json', 'analytics.json')
    
    if save_path:
        # Ensure sa2_data directory exists
        from pathlib import Path
        sa2_dir = Path("sa2_data")
        sa2_dir.mkdir(exist_ok=True)
        
        # Adjust path to be inside sa2_data
        save_path = sa2_dir / Path(save_path).name
        
        storage_type = config.get('storage', {}).get('type', 'json')
        if storage_type == 'csv':
            csv_path = str(save_path).replace('.json', '.csv')
            save_to_csv(data, csv_path, verbose)
        else:
            save_to_json_func(data, str(save_path), verbose)

    # Show analytics results if ?analytics=on
    query_params = st.query_params
    if "analytics" in query_params and "on" in query_params["analytics"]:
        # Handle authentication
        show_dashboard = True
        
        if config.get('access', {}).get('require_auth', True):
            # Check for password in config
            password_hash = config.get('access', {}).get('password_hash', '')
            legacy_password = config.get('access', {}).get('unsafe_password', '') or unsafe_password
            
            if password_hash or legacy_password:
                if 'sa2_authenticated' not in st.session_state:
                    st.session_state.sa2_authenticated = False
                
                show_dashboard = st.session_state.sa2_authenticated
        
        if show_dashboard:
            @st.dialog("Streamlit Analytics2", width="large")
            def show_sa2():
                tab1, tab2 = st.tabs(["📊 Analytics", "⚙️ Config"])
                
                with tab1:
                    # Pass password from config or parameter
                    password_to_use = None
                    if config.get('access', {}).get('require_auth', False):
                        # Use legacy password or empty string
                        password_to_use = legacy_password or unsafe_password or ""
                    
                    display.show_results(data, reset_data, password_to_use)
                
                with tab2:
                    try:
                        from .config import show_config
                        show_config()
                    except Exception as e:
                        st.error(f"Config module error: {str(e)}")
            
            show_sa2()
        else:
            # Show authentication dialog
            from .config import show_password_dialog
            show_password_dialog(config)


@contextmanager
def track(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[Union[str, Path]] = None,
    load_from_json: Optional[Union[str, Path]] = None,
    firestore_project_name: Optional[str] = None,
    firestore_collection_name: Optional[str] = None,
    firestore_document_name: Optional[str] = "counts",
    firestore_key_file: Optional[str] = None,
    streamlit_secrets_firestore_key: Optional[str] = None,
    session_id: Optional[str] = None,
    verbose=False,
):
    """
    Context manager to track analytics - maintains full backward compatibility.
    
    Usage:
        import streamlit_analytics2 as streamlit_analytics
        
        with streamlit_analytics.track():
            st.write("Hello World")
    """
    # Start tracking
    if (streamlit_secrets_firestore_key is not None and 
        firestore_project_name is not None):
        start_tracking(
            firestore_collection_name=firestore_collection_name,
            firestore_document_name=firestore_document_name,
            streamlit_secrets_firestore_key=streamlit_secrets_firestore_key,
            firestore_project_name=firestore_project_name,
            session_id=session_id,
            verbose=verbose,
        )
    else:
        start_tracking(
            unsafe_password=unsafe_password,
            save_to_json=save_to_json,
            load_from_json=load_from_json,
            firestore_key_file=firestore_key_file,
            firestore_collection_name=firestore_collection_name,
            firestore_document_name=firestore_document_name,
            session_id=session_id,
            verbose=verbose,
        )
    
    # Yield to run user code
    yield
    
    # Stop tracking
    if (streamlit_secrets_firestore_key is not None and 
        firestore_project_name is not None):
        stop_tracking(
            unsafe_password=unsafe_password,
            firestore_collection_name=firestore_collection_name,
            firestore_document_name=firestore_document_name,
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
            firestore_document_name=firestore_document_name,
            verbose=verbose,
            session_id=session_id,
        )


# Store original streamlit functions
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
_orig_chat_input = st.chat_input

# Sidebar originals
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


if __name__ == "streamlit_analytics2.main":
    reset_data()