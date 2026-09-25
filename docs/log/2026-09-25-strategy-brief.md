# streamlit-analytics2 strategy brief, 2026-09-25

Session artefact for the rework discussion. Inputs: `2026-09-25-issue-triage.md`,
`2026-09-25-community-wiki.md`, a read of the 0.10.7 source, and a throwaway
prototype in /tmp (not in the repo). No code was changed.

## Diagnosis of 0.10.x

1. Capture is 30 monkeypatches of `st.<widget>` and `st.sidebar.<widget>`, applied
   and reverted on every script run, on a process-global module. Anything created
   through a container is invisible: `col.button`, `with st.expander`, forms, tabs,
   dialogs. Verified with AppTest: a column button and a form submit are not counted.
   Sidebar checkbox is saved and restored but never wrapped.
2. Counting means "script reran and this widget rendered with a value different
   from what state_dict held", which on first render is always true. That is
   issue 102 (every fresh session adds +1 to every widget) and issue 13
   (`index=None` crashes). Pageviews are reruns, not visitors, which is the
   number one confusion in the community material.
3. Identity is the label string. Same-label widgets merge (issue 26); user `key=`
   is ignored; there is no widget type, no page, no session, no timestamp.
   The data model is nested counters, so nothing can be derived later.
4. Free-text values are stored verbatim as dict keys (text_input, text_area,
   chat_input), shown on a dashboard that is public unless a plain-text password
   is set, with a reset button behind the same gate. That is a privacy liability
   and the reason the maintainer raised GDPR on PR 137.
5. Config tab writes `.streamlit/analytics.toml` in the server cwd, outside the
   password gate, and nothing reads it. It is a proof of concept with a
   file-write side effect.
6. Firestore is a hard dependency (google-cloud-firestore, grpc, protobuf) for
   every install, though most users persist to JSON or nothing.
7. Multipage (issue 47, 7 threads) is impossible in the current shape: one global
   `data` dict, no notion of page.

## What Streamlit 1.64 gives us that 2021 did not

- `st.context`: url, ip_address, locale, timezone, cookies, headers, is_embedded, theme.
- ScriptRunContext: `session_id`, `page_script_hash`, `pages_manager`.
- SessionState: its own `_widget_changed(id)`, used to fire on_change callbacks,
  plus `widget_ids_this_run`. Streamlit already knows what the user touched.
- One element seam: `DeltaGenerator._enqueue(delta_type, element_proto)`. Every
  element in every container passes through it, carrying type, id, label and
  user key. The prototype patched this one method for the duration of the run
  and reconstructed every widget with correct change detection.

Both seams are private API, but they are two functions that have been stable
across the 1.3x to 1.6x line, versus 30 public signatures that we re-wrap.
Mitigation: pin `streamlit>=1.4x`, CI matrix against the last three Streamlit
minors plus the nightly, and a guard that disables widget capture with a
warning if the seam is missing, never breaking the host app.

## Proposal: two tiers, one event log

Tier 1, traffic (no patching, always on): session start, pageview per page,
session duration, visitor id (hashed cookie or ip+ua, salted), locale, referrer.
Cheap, accurate, and answers "how many people, from where, on which page, for
how long". This alone is more analytical value than 0.10 has.

Tier 2, interactions (one seam, on by default, switchable): widget changed
events with type, label, key, page, and a value *category* (button click,
option chosen, slider bucket, text entered: yes or no). Raw text is never
stored unless `store_values=True`.

Tier 3, explicit: `sa2.event("name", **props)` for things the app author cares
about ("report generated", "model run"). Requested since 2022 (issue 28) and the
only thing streamlit-fyr has that we do not.

Data model: append-only events `(ts, session, visitor, page, kind, widget_id,
widget_type, label, key, value)`. Aggregates (per day, per page, per widget,
funnels) are computed from events on read, so new questions do not need new
counters. Storage is a small Protocol with `append(events)` and `read(since)`:
in-memory + JSONL file by default, SQLite for self-hosted, Firestore as an
optional extra, exporters (CSV, webhook, PostHog) later.

Dashboard: read-only, behind the password, no reset button, no Config tab.
Sessions, pageviews per page, time on app, top widgets, top values. Fast on
10k events.

Config: kwargs on `track()` plus an optional `.streamlit/analytics.toml` read
once at start (for Cloud deployments that cannot change code). The UI screen
is scrapped.

## Compatibility

Keep `import streamlit_analytics2 as sa2; with sa2.track(): ...` unchanged.
Keep `start_tracking` / `stop_tracking` as thin wrappers. Provide a `data`
property that renders the old nested shape from the event log for anyone who
reads `sa2.data`. Ship as 1.0.0; 0.10 gets one last patch (logging PR 119,
issue 13, issue 102, sidebar checkbox) so current users stop bleeding while
1.0 is built.

## Decisions for Alfred

1. Accept the two private seams with the guard and matrix, or stay public-API
   only (which means Tier 1 only, no automatic widget tracking).
2. Default storage: JSONL file in cwd (Cloud-friendly, matches today) or SQLite.
3. `store_values` default off. Yes or no.
4. Firestore moves to an optional extra `streamlit-analytics2[firestore]`.
5. Config screen: scrap (recommended) or keep as read-only "current settings".
6. Ship a 0.10.8 fix release first, or go straight to 1.0.
