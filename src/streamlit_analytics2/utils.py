import logging
import uuid

from .config import setup_logging

setup_logging()

def format_seconds(s: int) -> str:
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - format_seconds - BEGIN")

    """Formats seconds to 00:00:00 format."""
    # days, remainder = divmod(s, 86400)
    hours, remainder = divmod(s, 3600)
    mins, secs = divmod(remainder, 60)

    # days = int(days)
    hours = int(hours)
    mins = int(mins)
    secs = int(secs)

    # output = f"{secs} s"
    # if mins:
    #     output = f"{mins} min, " + output
    # if hours:
    #     output = f"{hours} h, " + output
    # if days:
    #     output = f"{days} days, " + output
    output = f"{hours:02}:{mins:02}:{secs:02}"
    logging.debug(f"{unique_id} - format_seconds - END")
    return output


def replace_empty(s):
    unique_id = str(uuid.uuid4())[:4]
    logging.debug(f"{unique_id} - replace_empty - BEGIN")

    """Replace an empty string or None with a space."""
    if s == "" or s is None:
        logging.debug(f"{unique_id} - replace_empty(s == "" or s is None) - END")
        return " "
    else:
        logging.debug(f"{unique_id} - replace_empty - END")
        return s

