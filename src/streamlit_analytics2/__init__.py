"""
Streamlit Analytics 2
Track & visualize user interactions with your streamlit app.
"""

from .main import start_tracking, stop_tracking, track  # noqa: F401
from .state import data  # noqa: F401

from .state import data as counts  # noqa: F401  # isort:skip

__version__ = "0.10.5"
__name__ = "streamlit_analytics2"
