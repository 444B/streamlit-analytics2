import logging
import uuid


def setup_logging():
    unique_id = str(uuid.uuid4())[:4]
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - streamlit_analytics2 %(filename)s: %(message)s",
        handlers=[
            logging.StreamHandler(),  # STDOUT
            logging.FileHandler("app.log", mode='a')  # Log to file
        ]
    )
    logging.debug(f"{unique_id} - setup_logging called")
