# Storage

Two things can be persisted:

1. **The counters** (`sa2.data`): the 0.10 aggregate, one dict.
2. **The event log**: one record per session, page view, run, widget change
   and custom event. The dashboard is built from this.

| You pass | Counters go to | Events go to |
|---|---|---|
| nothing | memory | memory (lost on restart) |
| `save_to_json="a.json"` | `a.json` | `a.events.jsonl` next to it |
| `events_path="a.jsonl"` | memory (or `save_to_json` if also given) | `a.jsonl` |
| `events_path="a.db"` | memory (or `save_to_json`) | SQLite file `a.db` |
| `store=obj` | memory (or `save_to_json`) | `obj.append(...)` |
| `firestore_*` | Firestore document | as above |

## JSON counters (`save_to_json`, `load_from_json`)

The file has the shape shown in [api.md](api.md#sa2data). It is rewritten
after every run and read once per process at start. Reading it yourself for
a visitor counter is fine; do it before entering `track()`.

## JSONL event log (default when persisting)

One JSON object per line, appended. Human-readable, diffable, trivially
shipped anywhere. Bad lines are skipped with a warning. Fine into the low
hundreds of thousands of events; the dashboard reads the whole file.

```
{"ts":"2026-09-25T10:00:00Z","kind":"session","session":"a1b2","visitor":"9f3c","page":"/","props":{"browser":"Chrome","os":"macOS","device":"Desktop","locale":"en-IE","timezone":"Europe/Dublin"}}
{"ts":"2026-09-25T10:00:00Z","kind":"pageview","session":"a1b2","visitor":"9f3c","page":"/"}
{"ts":"2026-09-25T10:00:00Z","kind":"run","session":"a1b2","visitor":"9f3c","page":"/"}
{"ts":"2026-09-25T10:00:12Z","kind":"widget","session":"a1b2","visitor":"9f3c","page":"/","name":"Select your favorite","widget_id":"$$ID-7d0-None","widget_type":"selectbox","value":"dog"}
```

## SQLite event log (`events_path="x.db"`)

A single `events` table (schema in [events.md](events.md)). Safe for many
concurrent visitors in one process, fast past millions of rows, and it unlocks
the **Raw data query** tab. Choose this for anything self-hosted with a disk.

## Your own backend (`store=`)

Any object with two methods:

```python
class MyStore:
    def append(self, events):        # iterable of streamlit_analytics2.events.Event
        ...
    def read(self):                  # -> list[Event], oldest first
        ...

with sa2.track(store=MyStore()):
    main()
```

`Event.to_dict()` and `Event.from_dict()` convert to and from plain dicts,
so a Postgres, DuckDB, S3 or HTTP store is a few lines. `read()` is only
called when the dashboard is opened.

## Firestore (counters only)

The Firestore options persist `sa2.data`, not the event log. They exist for
compatibility with 0.10 and for hosts without a disk. Setup in
[firestore.md](firestore.md).

## Where files land

Relative paths resolve against the working directory of `streamlit run`.
On Streamlit Community Cloud the disk is ephemeral: files survive reruns but
not a redeploy or restart. See [deployment.md](deployment.md).
