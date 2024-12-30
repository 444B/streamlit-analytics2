import datetime
from typing import Any, Dict

from streamlit import session_state as ss


def format_seconds(s: int) -> str:
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
    return output


def replace_empty(s):
    """Replace an empty string or None with a space."""
    if s == "" or s is None:
        return " "
    else:
        return s


def session_data_reset() -> Dict[str, Any]:
    """
    Reset the session data to a new session.

    Returns
    -------
    Dict[str, Any]
        The new session data.
    """
    # Use yesterday as first entry to make chart look better.
    yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
    output: Dict[str, Any] = {}
    output["total_pageviews"] = 0
    output["total_script_runs"] = 0
    output["total_time_seconds"] = 0
    output["per_day"] = {"days": [str(yesterday)], "pageviews": [0], "script_runs": [0]}
    output["widgets"] = {}
    output["start_time"] = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")

    return output


def initialize_session_data():
    """
    Initialize the session data if not already initialized.
    """
    if "session_data" not in ss:
        ss.session_data = session_data_reset()
