# Firestore

Persists the aggregate counters (`sa2.data`) in a Firestore document, and
optionally the current session's counters under `session_id`. The event log
is not sent to Firestore; use `store=` for that.

Requires `google-cloud-firestore`. It is installed by default in 0.11; from
1.0 you will need `pip install "streamlit-analytics2[firestore]"`. Install
the extra now to be ready.

## Set up a project

1. Open https://console.firebase.google.com and create a project (or pick an
   existing GCP project).
2. Project settings (cog, top left) > Usage and billing. It should say
   **Spark** (free). Anything else can cost money.
3. Build > Firestore Database > Create database. Only the `(default)`
   database is on the free tier. Choose a region near your users, or a
   multi-region like `eur3` or `nam5`. Start in **production mode**.
4. Start a collection, e.g. `streamlit_analytics2`. Add any document; the
   library creates its own.
5. Project settings > Service accounts > Python > **Generate new private
   key**. Save the JSON. Do not commit it.

## Option A: key file on disk

```python
with sa2.track(
    firestore_key_file="firestore-key.json",
    firestore_collection_name="streamlit_analytics2",
    firestore_document_name="counts",        # default
):
    main()
```

## Option B: key in `st.secrets` (Streamlit Community Cloud, no file in the repo)

Put the JSON into `.streamlit/secrets.toml` (locally) or the app's Secrets
(on Community Cloud) as one string under a key of your choice, here
`firebase`:

```toml
firebase = '{"type": "service_account", "project_id": "my-project", ...}'
project_name = "my-project"
```

Then:

```python
with sa2.track(
    streamlit_secrets_firestore_key="firebase",        # the key NAME in st.secrets
    firestore_project_name=st.secrets["project_name"],
    firestore_collection_name="streamlit_analytics2",
):
    main()
```

`streamlit_secrets_firestore_key` is the name of the secret, not a file
path. Both `streamlit_secrets_firestore_key` and `firestore_project_name` must
be given for this mode.

## Option C: environment variable (Cloud Run and similar)

Write the JSON from the environment to a temporary file at start and use
option A, or load it into `st.secrets` before `track()`.

## Per-session counters

`session_id="..."` also stores the current session's counters in a document
of that name in the same collection. Choose ids that cannot collide with
`firestore_document_name`.

## Behaviour

- Loaded once per process at start, saved after every run with `merge=True`,
  so extra fields you add to the document survive.
- Keys are sanitised: empty keys are dropped, others become strings.
- The dashboard's reset also overwrites the Firestore document on the next
  save.

## Troubleshooting

- `Firestore support needs the extra`: install
  `streamlit-analytics2[firestore]`.
- `One or more components is not a string or is empty`: a widget label or
  value was empty; 0.11 sanitises these, upgrade.
- Permission errors: the service account needs the Cloud Datastore User role.
