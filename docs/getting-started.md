# Getting started

## 1. Install

```
pip install streamlit-analytics2   # pip
uv add streamlit-analytics2        # or uv
```

Python 3.10 or newer, Streamlit 1.47 or newer.

## 2. Wrap your app

```python
import streamlit as st
import streamlit_analytics2 as sa2

with sa2.track():
    st.title("My app")
    name = st.text_input("Your name")
    if st.button("Say hello"):
        st.write(f"Hello {name}")
```

Everything inside the `with` block is tracked: page loads, reruns, and every
widget the user changes, wherever it sits (columns, forms, expanders, tabs,
dialogs, the sidebar). A common pattern is to put the whole app in a function:

```python
def main():
    ...

with sa2.track():
    main()
```

## 3. Look at the dashboard

Run the app and add `?analytics=on` to the URL:

```
http://localhost:8501/?analytics=on
```

A dialog opens with views, visits, visitors, bounce rate, visit time, active
users, views per page over time, and breakdowns by page, widget, browser,
device, OS, language, region and campaign. Your own runs with the dashboard
open are not counted.

## 4. Keep the numbers (optional)

By default everything lives in memory and disappears when the process stops.
Pick one:

```python
with sa2.track(save_to_json="analytics.json"):   # counters in JSON, events in analytics.events.jsonl
    main()

with sa2.track(events_path="analytics.db"):      # events in SQLite; enables the SQL tab
    main()
```

See [Storage](storage.md) for the trade-offs and [Deployment](deployment.md)
for hosts with an ephemeral disk.

## 5. Protect the dashboard (recommended)

```python
with sa2.track(unsafe_password=st.secrets["analytics_password"]):
    main()
```

The password gates the dashboard, the reset button and the SQL tab. It is
compared in plain text inside the app, so keep it in `st.secrets` or an
environment variable and do not reuse a real password.

## Next

- [Dashboard](dashboard.md): what each number means.
- [Custom events](custom-events.md): `sa2.event("report generated")`.
- [Privacy](privacy.md): what is and is not collected.
