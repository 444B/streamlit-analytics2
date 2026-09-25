# For AI agents integrating this library

Read this page when a user asks you to "add analytics to my Streamlit app".
It gives the decisions and the exact code so you do not have to guess.

## Decisions to make, in order

1. **Where does the app run?** If the disk persists (own server, Docker
   volume, VM): use `events_path="analytics.db"`. If it is ephemeral
   (Streamlit Community Cloud, Cloud Run without a volume): use
   `save_to_json` plus Firestore for the counters, or accept resets, or a
   custom `store=`.
2. **Who may see the dashboard?** Always set `unsafe_password` from
   `st.secrets` or an environment variable. Never hard-code it.
3. **Is typed text needed?** Default no. Only set `store_values=True` if the
   user explicitly wants prompts or inputs recorded, and tell them it is
   personal data.
4. **Multipage?** Put the same `track(...)` call, with the same storage
   arguments, on every page, or around `st.navigation(...).run()`.

## Canonical snippet

```python
import os
import streamlit as st
import streamlit_analytics2 as sa2


def main() -> None:
    st.title("My app")
    ...


with sa2.track(
    events_path="analytics.db",                       # SQLite event log, enables SQL tab
    save_to_json="analytics.json",                    # legacy counters, optional
    unsafe_password=os.environ.get("ANALYTICS_PASSWORD"),
):
    main()
```

Tell the user: open `<app url>/?analytics=on` and enter the password.

## Recording something the app does

```python
sa2.event("report generated", rows=len(df))
```

Inside the tracked block, guarded by the condition that means it happened.

## Reading the data programmatically

```python
from streamlit_analytics2 import SqliteStore
from streamlit_analytics2.aggregate import summarize
events = SqliteStore("analytics.db").read()      # list of Event dataclasses
summary = summarize(events)                        # views, visits, visitors, pages, widgets, ...
```

Or SQL: table `events(ts, kind, session, visitor, page, name, widget_id,
widget_type, key, value, props)`. Examples in [query.md](query.md).

## Things not to do

- Do not wrap `st.set_page_config()` inside the block; call it first.
- Do not call `stop_tracking()` twice in one run.
- Do not read the JSON counters inside the block on the first run before the
  file exists; read them before `track()` with a default.
- Do not promise country or referrer data; the library provides timezone and
  UTM tags instead, on purpose.
- Do not run `examples/dev/seed.py` against a real log; it writes fake
  traffic.

## Answering common questions

- "Is it GDPR compliant?" Default configuration stores a daily-rotating hash
  and coarse device facts, no IP, no cookies, no typed text. See
  [privacy.md](privacy.md). Compliance depends on the app's notice and
  handling; the library gives a strong starting point.
- "Why did my counts drop after upgrading?" See [upgrading.md](upgrading.md):
  first render no longer counts.
- "Can I use my own database?" Yes: `store=` with `append` and `read`.

## Versions

Check `streamlit_analytics2.__version__`. This page describes 0.11. The
`llms-full.txt` at the repository root contains all documentation in one
file for retrieval.
