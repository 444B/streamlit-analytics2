import datetime

# Dict that holds all analytics results. Note that this is persistent across users,
# as modules are only imported once by a streamlit app.
data = {"loaded_from_firestore": False}


def reset_data():
    # Use yesterday as first entry to make chart look better.
    yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
    data["total_pageviews"] = 0
    data["total_script_runs"] = 0
    data["total_time_seconds"] = 0
    data["per_day"] = {"days": [str(yesterday)], "pageviews": [0], "script_runs": [0]}
    data["widgets"] = {}
    data["start_time"] = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")
