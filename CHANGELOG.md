# Changelog

## 0.11.0 (2026-09-25)

The tracking engine, the data model and the dashboard are new. The public API
is not: `track()`, `start_tracking()`, `stop_tracking()`, all their keyword
arguments, `streamlit_analytics2.data` and the `save_to_json` file shape work
exactly as in 0.10. Read "Behaviour changes" before upgrading a live app.

### Behaviour changes (not API changes)

- **Counts start at zero.** A widget rendering with its default value is no
  longer an interaction. In 0.10 every new session added +1 to every checkbox,
  selectbox, slider and text input (issue 102). Expect lower, honest numbers.
- **Typed text is not stored.** `text_input`, `text_area` and `chat_input`
  are recorded as `<text>`. Pass `store_values=True` to keep the old behaviour.
- **Dashboard reset needs a password.** The reset button only appears when
  `unsafe_password` is set. `reset_data()` still works from code.
- **The Config tab is gone**, with the `.streamlit/analytics.toml` it wrote.
  Nothing ever read that file.
- **Minimum Streamlit is 1.47** (August 2025).
- **Firestore is still installed by default** in 0.11 so upgrades do not
  break, and `pip install "streamlit-analytics2[firestore]"` is available.
  From 1.0 the extra is required.
- Widgets keyed by label in `data["widgets"]` are unchanged; same-label
  widgets still merge there, but are distinct in the event log (issue 26).

### New

- One capture seam instead of thirty patched functions. Widgets inside
  `st.columns`, `st.form`, `st.expander`, `st.tabs`, dialogs and the sidebar
  are all tracked, along with `st.toggle`, `st.download_button`,
  `st.camera_input` and every other widget (issues 46, 47 groundwork).
- `st.selectbox(..., index=None)` and other `None` defaults no longer crash
  (issue 13).
- An append-only event log: session, pageview, run, widget and custom events
  with page, a daily-rotating visitor hash, browser, OS and device family,
  language, timezone, theme and UTM tags. Written as `<name>.events.jsonl`
  next to `save_to_json`, or wherever `events_path` points (`.db` = SQLite).
  Any object with `append()` and `read()` works via `store=`.
- `streamlit_analytics2.event("name", **props)` for custom events.
- A new dashboard: views, visits, visitors, bounce rate, average visit time,
  active now; views per page over time; pages, browsers, OS, devices,
  languages, regions, sources and campaigns, widgets and events; a
  weekday-by-hour traffic-load heatmap; recent visits; a "what is collected"
  note. Your own runs with the dashboard open are not counted.
- A "Raw data query" tab: read-only SQL over the SQLite log with examples,
  CSV download and a chart picker. Requires `events_path` on a `.db` file and
  `unsafe_password`.
- Firestore `save()` merges instead of overwriting, so fields you add to the
  document survive (from PR 137).
- Logging goes through `logging.getLogger("streamlit_analytics2")` with a
  `NullHandler`; the library no longer configures the root logger (PR 119,
  issue 78).
- Tests run through `streamlit.testing.v1.AppTest` on Python 3.10 to 3.14.

### Removed

- `config.py`, `wrappers.py`, `widgets.py` and the per-widget monkeypatching.
