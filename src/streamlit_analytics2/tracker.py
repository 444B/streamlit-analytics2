import logging
import uuid

from .config import setup_logging

setup_logging()

# Dict that holds all analytics results. Note that this is persistent across users,
# as modules are only imported once by a streamlit app.
# counts = {"loaded_from_firestore": False}
counts = {"loaded_from_firestore": False}
