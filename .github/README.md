# streamlit-analytics2

Know who uses your Streamlit app and what they click. No JavaScript, no
cookies, no IP addresses stored.

[![PyPI](https://img.shields.io/pypi/v/streamlit-analytics2)](https://pypi.org/project/streamlit-analytics2/)
[![Downloads](https://static.pepy.tech/badge/streamlit-analytics2/month)](https://pepy.tech/projects/streamlit-analytics2)
![Build](https://github.com/444B/streamlit-analytics2/actions/workflows/release.yml/badge.svg)

## Use it

1. Install:
   ```
   pip install streamlit-analytics2
   ```
2. Wrap your app:
   ```python
   import streamlit as st
   import streamlit_analytics2 as sa2

   with sa2.track():
       st.write("Hello")
       st.button("Click me")
   ```
3. Open your app with `?analytics=on` on the URL:
   ```
   http://localhost:8501/?analytics=on
   ```

That is the whole integration. Everything below is optional.

## Keep the numbers across restarts

```python
with sa2.track(save_to_json="analytics.json"):   # counters + analytics.events.jsonl
    ...

with sa2.track(events_path="analytics.db"):      # SQLite, unlocks the query tab
    ...
```

## Protect the dashboard

```python
with sa2.track(unsafe_password="something-simple"):
    ...
```

Put the password in `st.secrets` or an environment variable, not in the code.
It is plain text inside the app, so pick something you would not reuse.

## What the dashboard shows

- Views, visits, visitors, bounce rate, average visit time, active now.
- Views per page over time, hourly for today.
- Pages, widgets, browsers, OS, devices, languages, regions, UTM sources and
  campaigns, custom events.
- A weekday-by-hour traffic-load heatmap and the busiest hour.
- Recent visits.
- Raw data query: read-only SQL over the SQLite log with example queries,
  CSV download and a chart picker (needs `events_path` on a `.db` and a
  password).

Your own runs with `?analytics=on` open are not counted.

## Track your own events

```python
if st.button("Generate report"):
    sa2.event("report generated", rows=len(df))
```

## Privacy

Stored per visit: a hash of address and browser that changes every day,
browser, OS and device family, language, timezone, theme, UTM tags, pages.
Stored per interaction: widget type, label, key, page and the chosen option.

Never stored: IP addresses, raw User-Agent strings, query strings, or anything
typed into text fields. Set `store_values=True` if you do want typed text.

## Options

| Argument | Default | What it does |
|---|---|---|
| `unsafe_password` | `None` | Password for the dashboard. Also gates the reset and the query tab. |
| `save_to_json` | `None` | Legacy counters file (0.10 shape). Events go to `<name>.events.jsonl` beside it. |
| `load_from_json` | `None` | Load counters from that file at start. |
| `events_path` | `None` | Event log path. `.jsonl` by default, `.db` / `.sqlite` for SQLite. |
| `store` | `None` | Your own backend: any object with `append(events)` and `read()`. |
| `store_values` | `False` | Record typed text instead of `<text>`. |
| `session_id` | `None` | Also keep per-session counters in Firestore under this document. |
| `firestore_key_file`, `firestore_collection_name`, `firestore_document_name`, `firestore_project_name`, `streamlit_secrets_firestore_key` | | Persist the counters in Firestore. See the [wiki](https://github.com/444B/streamlit-analytics2/wiki). |
| `verbose` | `False` | Log what is loaded and saved. |

`start_tracking()` and `stop_tracking()` take the same arguments if you
prefer them to the `with` block.

## Multipage apps

Call `sa2.track()` on every page. Views and widgets are recorded per page in
the event log and on the dashboard. The legacy counters in
`streamlit_analytics2.data` are shared across pages, as before.

## Upgrading from 0.10

Nothing to change in your code. The numbers will be lower because a widget
rendering with its default no longer counts as an interaction, typed text is
no longer stored unless you ask, and the dashboard reset now needs a
password. Details in [CHANGELOG.md](https://github.com/444B/streamlit-analytics2/blob/main/CHANGELOG.md).

## Contributing

Issues and pull requests are welcome. See
[CONTRIBUTING.md](https://github.com/444B/streamlit-analytics2/blob/main/.github/CONTRIBUTING.md).
Development: `uv sync --all-extras && uv run pytest`.

## License

MIT. See [LICENSE](https://github.com/444B/streamlit-analytics2/blob/main/LICENSE).
