# config.py - Simplified configuration management
"""
Configuration management for streamlit-analytics2
Handles setup, authentication, and settings with minimal user code
"""

import os
import toml
import streamlit as st
from pathlib import Path
from typing import Dict, Any
import hashlib
import logging

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


def ensure_streamlit_dir():
    """Ensure .streamlit directory exists"""
    streamlit_dir = Path(".streamlit")
    streamlit_dir.mkdir(exist_ok=True)
    return streamlit_dir


def is_first_run() -> bool:
    """Check if this is the first run - checks config file"""
    config_path = Path(".streamlit/analytics.toml")
    if not config_path.exists():
        return True
    
    try:
        config = load_analytics_config()
        return not config.get('setup', {}).get('completed', False)
    except:
        return True


def load_analytics_config() -> Dict[str, Any]:
    """Load configuration with automatic migration and creation if missing"""
    path = Path(".streamlit/analytics.toml")
    
    try:
        if not path.exists():
            # Create default config
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        
        with open(path, "r") as file:
            config = toml.load(file)
        
        # Migrate old configs
        migrated = migrate_old_config(config)
        
        # Save migrated config if changed
        if migrated != config:
            save_config(migrated)
        
        return migrated
        
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return DEFAULT_CONFIG.copy()


def migrate_old_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate old configuration format to new simplified format"""
    new_config = DEFAULT_CONFIG.copy()
    
    # Migrate basic settings
    if 'streamlit_analytics2' in config:
        new_config['streamlit_analytics2']['enabled'] = config['streamlit_analytics2'].get('enabled', True)
    
    # Migrate storage settings
    if 'storage' in config:
        new_config['storage']['save'] = config['storage'].get('save', True)
        new_config['storage']['type'] = config['storage'].get('type', 'json')
        # Migrate old path field
        if 'save_to_json' in config['storage']:
            new_config['storage']['path'] = config['storage']['save_to_json']
        elif 'path' in config['storage']:
            new_config['storage']['path'] = config['storage']['path']
    
    # Migrate access settings
    if 'access' in config:
        new_config['access']['require_auth'] = config['access'].get('require_auth', False)
        # Prefer password_hash over unsafe_password
        if 'password_hash' in config['access'] and config['access']['password_hash']:
            new_config['access']['password_hash'] = config['access']['password_hash']
        elif 'unsafe_password' in config['access'] and config['access']['unsafe_password']:
            # Convert unsafe password to hash
            new_config['access']['password_hash'] = hashlib.sha256(
                config['access']['unsafe_password'].encode()
            ).hexdigest()
            new_config['access']['require_auth'] = True
    
    # Migrate setup info
    if 'setup' in config:
        new_config['setup'] = config['setup'].copy()
    
    return new_config


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file"""
    path = Path(".streamlit/analytics.toml")
    
    try:
        ensure_streamlit_dir()
        with open(path, "w") as file:
            toml.dump(config, file)
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Failed to save configuration: {str(e)}")


def show_initial_setup():
    """Simplified initial setup - shown in dialog"""
    st.markdown("### Quick Setup")
    st.info("Set up analytics in 30 seconds! All settings can be changed later.")
    
    with st.form("quick_setup"):
        # Storage format
        storage_type = st.radio(
            "How should analytics be saved?",
            ["JSON (Simple)", "CSV (Excel-friendly)", "Don't save"],
            index=0,
            horizontal=True
        )
        
        # Optional password
        enable_password = st.checkbox(
            "Password protect analytics dashboard",
            value=False,
            help="You can add this later if needed"
        )
        
        password = ""
        confirm = ""
        if enable_password:
            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("Set password", type="password")
            with col2:
                confirm = st.text_input("Confirm password", type="password")
        
        if st.form_submit_button("Complete Setup", type="primary"):
            config = DEFAULT_CONFIG.copy()
            
            # Set storage
            if storage_type == "CSV (Excel-friendly)":
                config['storage']['type'] = 'csv'
            elif storage_type == "Don't save":
                config['storage']['save'] = False
            
            # Set password if enabled
            if enable_password:
                if not password:
                    st.error("Please enter a password")
                    return
                elif password != confirm:
                    st.error("Passwords don't match!")
                    return
                else:
                    config['access']['password_hash'] = hashlib.sha256(password.encode()).hexdigest()
                    config['access']['require_auth'] = True
            
            config['setup']['completed'] = True
            save_config(config)
            st.success("✅ Setup complete!")
            st.balloons()
            # Small delay to show success message
            import time
            time.sleep(1)
            st.rerun()


def show_password_dialog(config: Dict[str, Any]):
    """Show password dialog for analytics access"""
    @st.dialog("Analytics Dashboard - Authentication Required")
    def auth_dialog():
        password_input = st.text_input("Enter password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit", type="primary", use_container_width=True):
                # Check password hash
                if config.get('access', {}).get('password_hash'):
                    input_hash = hashlib.sha256(password_input.encode()).hexdigest()
                    if input_hash == config['access']['password_hash']:
                        st.session_state.sa2_authenticated = True
                        st.rerun()
                
                # Check legacy password
                if config.get('access', {}).get('unsafe_password'):
                    if password_input == config['access']['unsafe_password']:
                        st.session_state.sa2_authenticated = True
                        st.rerun()
                
                st.error("Invalid password")
        
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.rerun()
    
    auth_dialog()


def show_config():
    """Simplified config interface"""
    st.title("⚙️ Analytics Configuration")
    
    config = load_analytics_config()
    
    # Quick status
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Storage Type", config['storage']['type'].upper())
    with col2:
        st.metric("Password", "ON" if config['access']['require_auth'] else "OFF")
    
    st.divider()
    
    # Storage settings
    st.subheader("💾 Storage Settings")
    
    storage_enabled = st.checkbox(
        "Save analytics data",
        value=config['storage']['save']
    )
    
    storage_type = st.radio(
        "Format",
        ["json", "csv"],
        index=0 if config['storage']['type'] == 'json' else 1,
        horizontal=True
    )
    
    # Security settings
    st.subheader("🔒 Security")
    
    require_auth = st.checkbox(
        "Require password for analytics",
        value=config['access']['require_auth']
    )
    
    if require_auth:
        if st.button("Set/Change Password"):
            with st.form("password_form"):
                new_pass = st.text_input("New password", type="password")
                confirm = st.text_input("Confirm password", type="password")
                
                if st.form_submit_button("Update Password"):
                    if new_pass and new_pass == confirm:
                        config['access']['password_hash'] = hashlib.sha256(new_pass.encode()).hexdigest()
                        config['access']['require_auth'] = True
                        save_config(config)
                        st.success("Password updated!")
                        st.rerun()
                    elif not new_pass:
                        st.error("Please enter a password")
                    else:
                        st.error("Passwords don't match")
    
    # Save button
    if st.button("💾 Save Configuration", type="primary"):
        config['storage']['save'] = storage_enabled
        config['storage']['type'] = storage_type
        config['access']['require_auth'] = require_auth
        
        save_config(config)
        st.success("✅ Configuration saved!")
        st.rerun()
    
    # Data location info
    st.divider()
    st.subheader("📁 Data Location")
    if config['storage']['type'] == 'csv':
        st.code("sa2_data/analytics_data.csv\nsa2_data/analytics_data_daily.csv\nsa2_data/analytics_data_widgets.csv")
    else:
        st.code("sa2_data/analytics_data.json")