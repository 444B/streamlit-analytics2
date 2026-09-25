# Multipage apps

Call `sa2.track()` on every page. The page path is recorded on each event,
and the dashboard shows views per page, a page filter, and a per-page path in
"Recent visits".

## `pages/` directory

```
app.py
pages/
  reports.py
  settings.py
```

```python
# app.py and each file in pages/
import streamlit as st
import streamlit_analytics2 as sa2

with sa2.track(events_path="analytics.db"):
    st.title("Reports")
    ...
```

Pass the same storage arguments on every page so they write to the same log.

## `st.Page` and `st.navigation`

```python
import streamlit as st
import streamlit_analytics2 as sa2

def home():
    st.title("Home")

def reports():
    st.title("Reports")

with sa2.track(events_path="analytics.db"):
    st.navigation([st.Page(home, url_path="home"), st.Page(reports, url_path="reports")]).run()
```

Wrapping the `navigation(...).run()` call is enough: the page that runs is
the one recorded.

## What is per page and what is shared

- Per page: views, visits that saw the page, widget changes, custom events,
  bounce and visit time when the page filter is set.
- Shared: the legacy counters in `sa2.data` (`total_pageviews`,
  `widgets`, ...), which have one global dict as in 0.10. This is a
  compatibility constraint until 1.0.

## Page names

The recorded `page` is the URL path (`/`, `/reports`). Rename a page and its
history stays under the old path.
