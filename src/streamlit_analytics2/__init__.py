"""streamlit-analytics2: track usage of Streamlit apps."""

import logging

from .main import event, start_tracking, stop_tracking, track  # noqa: F401
from .state import data, reset_data  # noqa: F401
from .storage import JsonlStore, MemoryStore, SqliteStore  # noqa: F401

logging.getLogger("streamlit_analytics2").addHandler(logging.NullHandler())

__version__ = "0.11.1"
__all__ = [
    "track",
    "start_tracking",
    "stop_tracking",
    "event",
    "data",
    "reset_data",
    "JsonlStore",
    "SqliteStore",
    "MemoryStore",
    "__version__",
]
