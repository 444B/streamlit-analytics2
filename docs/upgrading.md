# Upgrading

## From 0.10 to 0.11

Nothing to change in code. Every function, argument, the `sa2.data` shape and
the `save_to_json` file shape are unchanged.

What you will notice:

- **Lower counts.** A widget rendering with its default is no longer an
  interaction. 0.10 added +1 to every checkbox, selectbox, slider and text
  input on every new session; 0.11 counts only what users change.
- **`<text>` instead of typed text.** Pass `store_values=True` to keep the
  0.10 behaviour of storing what users type.
- **Reset needs a password.** The reset button on the dashboard only shows
  when `unsafe_password` is set.
- **No Config tab.** It wrote `.streamlit/analytics.toml`, which nothing read.
- **Streamlit 1.47 or newer.**
- **A new file appears** next to `save_to_json`: `<name>.events.jsonl`, the
  event log. It is safe to delete at any time; only the dashboard reads it.

## From the original `streamlit-analytics`

```
pip uninstall streamlit-analytics
pip install streamlit-analytics2
```

```python
import streamlit_analytics2 as streamlit_analytics   # keep the old alias if you like
```

The `track`, `start_tracking` and `stop_tracking` calls are the same. The
deprecation warnings about `experimental_get_query_params` and
`experimental_dialog` go away.

## Towards 1.0

Planned breaking changes, announced here first:

- `google-cloud-firestore` becomes an optional extra: `pip install
  "streamlit-analytics2[firestore]"`.
- `sa2.data["widgets"]` keys by `key=` when present, then label, so
  same-label widgets stop merging.
- `unsafe_password` gets a hashed alternative.
- A deletion API for sessions and visitors.
