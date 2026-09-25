# Events and data model

Everything the dashboard shows is derived from an append-only list of events.
The record is small on purpose so you can analyse it with any tool.

## The Event record

| Field | Type | Present on | Meaning |
|---|---|---|---|
| `ts` | string | all | ISO 8601 UTC, second precision, e.g. `2026-09-25T10:00:12Z` |
| `kind` | string | all | `session`, `pageview`, `run`, `widget`, `custom` |
| `session` | string | all | Streamlit session id, one per browser tab |
| `visitor` | string | most | 16 hex chars: SHA-256 of `date|ip|user-agent`, truncated. Rotates daily. Absent when neither ip nor user-agent is known. |
| `page` | string | most | URL path of the page, e.g. `/`, `/reports` |
| `name` | string | widget, custom | widget label, or the custom event name |
| `widget_id` | string | widget | Streamlit's element id, stable for the same widget across runs |
| `widget_type` | string | widget | `button`, `form_submit_button`, `checkbox`, `toggle`, `selectbox`, `radio`, `multiselect`, `slider`, `text_input`, `text_area`, `chat_input`, `number_input`, `date_input`, `time_input`, `color_picker`, `file_uploader`, `camera_input`, ... |
| `key` | string | widget | the `key=` you gave the widget, if any |
| `value` | string | widget | the chosen option or value; `<text>` for free text unless `store_values=True`; absent for count-only widgets |
| `props` | object | session, custom | session: `browser`, `os`, `device`, `locale`, `timezone`, `theme`, `embedded`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` (only those known). custom: whatever you passed. |

## What each kind means

- **session**: first run of a browser session. Carries the visitor facts.
- **pageview**: the session landed on a page: on the first run, and whenever
  the page changes within the session.
- **run**: every script run, so every rerun after an interaction. Runs with
  the dashboard open are not recorded.
- **widget**: a widget's value changed because the user acted. Never on first
  render. Buttons only when clicked. For a multiselect, one event per newly
  added option.
- **custom**: `sa2.event(...)`.

## Reading the log

### pandas

```python
import pandas as pd
df = pd.read_json("analytics.events.jsonl", lines=True)
views_per_day = df[df.kind == "pageview"].groupby(df.ts.str[:10]).size()
```

### SQLite

```python
import sqlite3, pandas as pd
con = sqlite3.connect("analytics.db")
pd.read_sql("SELECT page, count(*) views FROM events WHERE kind='pageview' GROUP BY page", con)
```

Table:

```sql
CREATE TABLE events (
  id INTEGER PRIMARY KEY, ts TEXT NOT NULL, kind TEXT NOT NULL,
  session TEXT NOT NULL, visitor TEXT, page TEXT, name TEXT, widget_id TEXT,
  widget_type TEXT, key TEXT, value TEXT, props TEXT  -- JSON
);
CREATE INDEX events_ts ON events(ts);
```

### DuckDB

```sql
SELECT page, count(*) AS views
FROM read_json_auto('analytics.events.jsonl')
WHERE kind = 'pageview' GROUP BY page ORDER BY views DESC;
```

### The library itself

```python
from streamlit_analytics2 import SqliteStore
from streamlit_analytics2.aggregate import summarize
events = SqliteStore("analytics.db").read()
summary = summarize(events)          # the dict the dashboard renders
summary["pages"], summary["bounce_rate"]
```

## Derived metrics, exactly

- Views = number of `pageview` events.
- Visits = distinct `session` values.
- Visitors = sum over days of distinct `visitor` values that day.
- Bounce = a visit with at most one `run` and no `widget` or `custom` event.
- Visit time = last `run` minus first `run` in the visit.
- Active now = visits with any event in the last 5 minutes.
