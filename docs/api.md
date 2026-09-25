# API reference

```python
import streamlit_analytics2 as sa2
```

## `sa2.track(...)`

Context manager. Calls `start_tracking(...)` on entry and `stop_tracking(...)`
on exit. Use it around everything you want tracked.

```python
with sa2.track(
    unsafe_password=None,
    save_to_json=None,
    load_from_json=None,
    firestore_project_name=None,
    firestore_collection_name=None,
    firestore_document_name="counts",
    firestore_key_file=None,
    streamlit_secrets_firestore_key=None,
    session_id=None,
    verbose=False,
    *,
    store_values=False,
    events_path=None,
    store=None,
):
    ...
```

| Argument | Type | Default | Meaning |
|---|---|---|---|
| `unsafe_password` | `str` | `None` | Password for the dashboard. Also gates the reset button and the SQL tab. Plain-text comparison. |
| `save_to_json` | path | `None` | Write the legacy counters (`sa2.data`) to this file after every run. Events go to `<stem>.events.jsonl` next to it unless `events_path` or `store` is given. |
| `load_from_json` | path | `None` | Load the counters from this file once per process at start. |
| `firestore_key_file` | path | `None` | Service-account JSON for Firestore. Turns Firestore on. |
| `firestore_collection_name` | `str` | `None` | Firestore collection. |
| `firestore_document_name` | `str` | `"counts"` | Firestore document for the aggregate counters. |
| `firestore_project_name` | `str` | `None` | GCP project. Required with `streamlit_secrets_firestore_key`. |
| `streamlit_secrets_firestore_key` | `str` | `None` | Name of the key in `st.secrets` that holds the service-account JSON as a string. Alternative to `firestore_key_file`. |
| `session_id` | `str` | `None` | Also persist the current session's counters to Firestore under this document id. |
| `verbose` | `bool` | `False` | Log loads and saves at INFO through the `streamlit_analytics2` logger. |
| `store_values` | `bool` | `False` | Record what users type into `text_input`, `text_area` and `chat_input`. Off: recorded as `<text>`. |
| `events_path` | path | `None` | Where the event log goes. `.jsonl` (default) or `.db` / `.sqlite` / `.sqlite3` for SQLite. |
| `store` | object | `None` | Your own event backend: anything with `append(events)` and `read() -> list[Event]`. Overrides `events_path`. |

The three keyword-only arguments are new in 0.11. Everything else is
unchanged since 0.10 and behaves the same.

## `sa2.start_tracking(...)` and `sa2.stop_tracking(...)`

The same arguments as `track()`. Use them when a `with` block is awkward:

```python
sa2.start_tracking(save_to_json="analytics.json")
st.button("Click me")
sa2.stop_tracking(save_to_json="analytics.json")
```

Arguments given to `start_tracking` are remembered for the matching
`stop_tracking` in the same run, so you may pass them to either. Call
`stop_tracking` once per run: it renders the dashboard.

## `sa2.event(name, **props)`

Record a custom event inside a tracked block.

```python
if st.button("Generate report"):
    sa2.event("report generated", rows=len(df), format="csv")
```

`name` is a short string; `props` must be JSON-serialisable. Events show on
the dashboard under "Events" and in the log with `kind = "custom"`. Called
outside a tracked run, the event goes to the in-memory store only.

## `sa2.data`

The legacy aggregate counters, a plain dict kept for compatibility with 0.10:

```python
{
    "total_pageviews": 12,
    "total_script_runs": 57,
    "total_time_seconds": 823.4,
    "per_day": {"days": ["2026-09-24", "2026-09-25"], "pageviews": [5, 7], "script_runs": [20, 37]},
    "widgets": {"Click me": 9, "Select your favorite": {"cat": 3, "dog": 5}},
    "start_time": "25 Sep 2026, 10:00:00",
    "loaded_from_firestore": False,
}
```

Count-only widgets (buttons, checkboxes, toggles, uploads) are integers; the
rest are `{value: count}` dicts. Widgets are keyed by label here; the event
log keeps same-label widgets apart.

## `sa2.reset_data()`

Reset `sa2.data` to zero. Does not touch the event log.

## Stores

```python
from streamlit_analytics2 import JsonlStore, SqliteStore, MemoryStore
```

Each has `append(events)` and `read()`. `SqliteStore(path).read()` returns
`Event` objects; see [Events](events.md). Use them to read a log outside the
app, or pass an instance to `track(store=...)`.

## Logging

The library logs through `logging.getLogger("streamlit_analytics2")` with a
`NullHandler`. It never configures the root logger. Set the level yourself to
see loads, saves and capture warnings.

## Streamlit version guard

Widget capture relies on two internal Streamlit hooks. If a future Streamlit
removes them, the library logs one warning, keeps counting page loads and
runs, and never breaks your app.
