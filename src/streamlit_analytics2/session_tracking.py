# session_tracking.py - Basic session tracking
"""
Minimal session tracking for streamlit-analytics2
"""

import uuid
import streamlit as st
from datetime import datetime
from typing import Dict, Any


class SessionManager:
    """Basic session manager for tracking users"""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self._ensure_session_structure()
    
    def _ensure_session_structure(self):
        """Ensure data has session tracking structure"""
        if 'sessions' not in self.data:
            self.data['sessions'] = {}
        if 'active_users' not in self.data:
            self.data['active_users'] = {}
    
    def get_or_create_session(self) -> str:
        """Get current session ID or create new one"""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.session_start = datetime.now()
            
            # Initialize session data
            self.data['sessions'][st.session_state.session_id] = {
                'id': st.session_state.session_id,
                'start_time': st.session_state.session_start.isoformat(),
                'last_activity': datetime.now().isoformat(),
                'interactions': 0
            }
        
        # Update last activity
        session_id = st.session_state.session_id
        if session_id in self.data['sessions']:
            self.data['sessions'][session_id]['last_activity'] = datetime.now().isoformat()
        
        # Update active users
        self.data['active_users'][session_id] = datetime.now().isoformat()
        
        return session_id