"""
Streamlit Analytics 2
Track & visualize user interactions with your streamlit app.
"""

from .main import (  # noqa: F401
    delete_session_data,
    start_tracking,
    stop_tracking,
    track,
)
from .state import data, session_data  # noqa: F401

from .state import data as counts  # noqa: F401  # isort:skip

__version__ = "0.11.0"
__name__ = "streamlit_analytics2"
