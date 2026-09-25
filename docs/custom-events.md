# Custom events

Widgets tell you what people clicked. Custom events tell you what your app
did for them: a report generated, a model run, a file exported, a search with
no results.

```python
import streamlit_analytics2 as sa2

with sa2.track():
    query = st.text_input("Search")
    if query:
        results = search(query)
        sa2.event("search", results=len(results), empty=len(results) == 0)
    if st.button("Export CSV"):
        sa2.event("export", format="csv", rows=len(results))
```

Rules:

- Call it inside the tracked block (or between `start_tracking` and
  `stop_tracking`). Outside, the event is kept in memory only.
- `name` is a short, stable string. Use the same name for the same thing so
  counts add up. Put variation into `props`.
- `props` must be JSON-serialisable. Keep them small. Do not put personal data
  in them; the log is yours to protect.
- One call, one event. Guard it with the condition that means "it happened",
  as in the example, so a rerun does not double count.

Where they show up:

- Dashboard, Overview tab, "Events" panel: count and number of visits per name.
- Event log: `kind = "custom"`, `name`, `props`, with page, session and visitor.
- SQL tab: `SELECT name, json_extract(props, '$.rows') FROM events WHERE kind='custom'`.
