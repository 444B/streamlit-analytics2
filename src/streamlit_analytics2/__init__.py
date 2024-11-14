from .main import counts, start_tracking, stop_tracking, track  # noqa: F401
import logging

__version__ = "0.8.7"

logging.getLogger(__name__).addHandler(logging.NullHandler())
