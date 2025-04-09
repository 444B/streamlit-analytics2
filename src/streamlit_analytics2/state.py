import datetime

# Dict that holds all analytics results. Note that this is persistent across
# users, as modules are only imported once by a streamlit app.
data = {"loaded_from_firestore": False}
session_data = {"loaded_from_firestore": False}


def reset_data():
    # Use yesterday as first entry to make chart look better.
    yesterday = str(datetime.date.today() - datetime.timedelta(days=1))

    for d in [data, session_data]:
        d["total_pageviews"] = 0
        d["total_script_runs"] = 0
        d["total_time_seconds"] = 0
        d["per_day"] = {
            "days": [str(yesterday)],
            "pageviews": [0],
            "script_runs": [0],
            "session_time_seconds": [0],
            "widgets": [{}],
        }
        d["widgets"] = {}
        d["start_time"] = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")
