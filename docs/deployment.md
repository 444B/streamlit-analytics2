# Deployment

The only question that matters: does your host keep files between restarts?

| Host | Disk | Recommended |
|---|---|---|
| Streamlit Community Cloud | ephemeral (survives reruns, lost on restart or redeploy) | Firestore for counters (see [firestore.md](firestore.md)); or accept that the event log resets; or a custom `store=` that posts elsewhere |
| Your own server, Docker with a volume, a VM | persistent | `events_path="/data/analytics.db"` and `save_to_json="/data/analytics.json"` |
| Cloud Run, Fly, Railway, Hugging Face Spaces without a volume | ephemeral | same as Community Cloud, or mount a volume |
| Snowflake in Streamlit, Databricks apps | usually ephemeral | custom `store=` writing to your warehouse |

## Streamlit Community Cloud

- Add `streamlit-analytics2` to `requirements.txt` or `pyproject.toml`.
- Put the dashboard password in the app's Secrets and read it with
  `st.secrets["analytics_password"]`.
- Community Cloud's own "App viewers" counts unique viewers; this library
  counts views, visits and daily visitors. They will not match, and both are
  right.

## Docker

```yaml
services:
  app:
    image: my-streamlit-app
    volumes:
      - analytics:/data
    environment:
      - ANALYTICS_PASSWORD=...
volumes:
  analytics:
```

```python
with sa2.track(events_path="/data/analytics.db", unsafe_password=os.environ["ANALYTICS_PASSWORD"]):
    main()
```

## Secrets and passwords

- `unsafe_password` is compared in plain text inside the app. Use a dedicated
  value, store it in `st.secrets` or an environment variable, rotate it if it
  leaks. It gates the dashboard, the reset button and the SQL tab.
- Firestore credentials: never commit the key file. Use
  `streamlit_secrets_firestore_key` with the JSON in `st.secrets`, or an
  environment variable written to a file at start.

## Reverse proxies and embedding

The library reads the request headers Streamlit exposes. Behind a proxy,
`st.context.ip_address` is what the proxy forwards; the visitor hash is
derived from it and never stored. Embedded apps (`?embed=true`) record
`embedded: true` on the session.

## Multiple replicas

Each replica has its own memory. With a shared volume, SQLite handles
concurrent writers within one process; across processes on the same file
it also works, with SQLite's usual locking. For many replicas, use a custom
`store=` against a database.

## Resource use

Per run: one lookup per rendered widget and one append. The dashboard reads
the whole log when opened; at 100k events that is well under a second with
SQLite. The SQL tab caps each query at 2 seconds and 64 MB.
