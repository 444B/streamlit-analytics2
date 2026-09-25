# streamlit-analytics2 issue and PR triage, 2026-09-25

Read-only triage of github.com/444B/streamlit-analytics2 against main = 0.10.7 (PR #146 merged today). 9 open issues, 2 open PRs. Reproductions were run locally with Streamlit's AppTest against the 0.10.7 tree; nothing on GitHub was touched.

Closed PRs in the last 12 months, for context: #146 (0.10.7: lock refresh, AppTest smoke suite), #144 and #143 (dependabot, merged 2026-03-17), #142 and #141 (0.10.6: streamlit 1.54, 2026-02-25), #145 (dependabot requests bump, closed unmerged today, superseded by #146). No feature PR has merged since 0.10.x began; every open issue predates 0.10.

## 1. Open issues

| # | Title | Opened | Last activity | Author | Labels | Gist | Class |
|---|---|---|---|---|---|---|---|
| 122 | [BUG] click on st.toggle then pages_view become 1 | 2024-12-18 | 2024-12-26 | bitcometz | bug | Passes `save_to_json` without `load_from_json`, so every process start resets to 0 and overwrites the file; also reads the file inside `track()` before the first save. `st.toggle` is not wrapped either. Owner posted a workaround; no reply in 21 months | QUESTION/SUPPORT (user config), toggle part is covered by #46 |
| 103 | [FEATURE] export to various backend services | 2024-07-02 | 2024-07-02 | Mjboothaus | enhancement | Wants pluggable backends (MotherDuck/DuckDB) or a documented API to read the data out; also asks for `st.Page` multipage | FEATURE (folds into #53 config screen); multipage part is a DUPLICATE of #47 |
| 102 | [BUG] Checkbox counts are incremented on startup | 2024-06-29 | 2024-06-30 | robino16 | bug | First script run counts the default state as an interaction, so every fresh session adds +1 to checkbox, text_input, selectbox, slider and the other `value` widgets. Reproduced on 0.10.7 today: `cb: 1` after run 1, `cb: 2` after a second untouched session; same for `ti` and `sb` | BUG |
| 53 | [FEATURE] v1.0.0 Settings Page + Refactor + GA4 | 2024-03-11 | 2025-01-20 | 444B | enhancement, future release | Owner's roadmap umbrella. Ticked: #54, GA4 #16, settings page, logic split. Open: #57, #31, #46, #47, #26, traffic plot, multiselect memory, AppTest (AppTest landed in #146 today) | STALE as a tracker (mixes done, dropped and undecided items); replace with a milestone |
| 47 | [BUG] cannot track multi-page separately | 2024-03-08 | 2024-07-13 | Joyce920hope | bug, future release | `pages/` apps share one module-global `data` dict, so page 2 shows page 1 + page 2 totals. README itself lists `pages/` as not working and `st.navigation` as unchecked. alon-sht tried `reset_counts()` inside `start_tracking()` and got per-page but non-persistent counts | FEATURE (documented limitation, most-requested item) |
| 46 | [FEATURE] add new input widgets | 2024-03-08 | 2024-03-11 | 444B | enhancement, future release | Wrap download_button, link_button, page_link, toggle, camera_input (plus sidebar variants). None done; only chat_input (#44) landed. Found in passing: `st.sidebar.checkbox` is saved and restored in main.py (lines 285, 491) but never wrapped, so sidebar checkboxes are not counted at all | FEATURE (plus one latent BUG for sidebar.checkbox) |
| 31 | Timestamp data? | 2024-03-02 | 2024-04-25 | 444B (orig nixshal, 2022) | enhancement, future release | Per-event timestamps in the JSON rather than only `per_day` counters. Reporter never answered the 2024 ping | STALE, NEEDS-INFO (keep the idea under the time-dimension theme) |
| 26 | Tracking buttons with the same name | 2024-03-02 | 2025-02-24 | 444B (orig amirmk89, 2023) | bug, future release | Wrappers key everything by label, so same-label widgets merge; users want `key=` as the tracking identity. nathanjones4323 located the cause in the monkey patching; emigre459 needs it for LLM-generated follow-up buttons; owner promised it for "the next release" in Feb 2025. PR #137's branch is named after this but its diff does not implement it | FEATURE (design change, not a defect against the docs) |
| 13 | None Selected | 2024-03-02 | 2024-03-13 | 444B (orig hansipie) | bug, good first issue | `st.selectbox(..., index=None)` raises `KeyError: ' '` because `utils.replace_empty(None)` returns `" "`, which is not one of the option keys in `wrappers.select`. Reproduced on 0.10.7 today with the reporter's 4-line app | BUG (good first issue, small fix in `wrappers.select`, same shape of bug exists for `st.radio` with `index=None`) |

## 2. Open pull requests

| # | Title | Author | Opened | Last activity | Files | Mergeable | What it does | Recommendation |
|---|---|---|---|---|---|---|---|---|
| 137 | Merge records instead of overwrite and updates to metric portfolio | emigre459 | 2025-03-02 | 2025-04-09 | 9 files, +314/-227, 24 commits: examples/minimal.py, examples/pages/firebase_test.py, src `__init__`, display, firestore, main, state, utils, wrappers | CONFLICTING (DIRTY), 0 reviews, no CI status | (a) Firestore `.set(..., merge=True)` so custom fields such as a username survive; (b) moves `session_data` out of `st.session_state` into a module-level dict "similar to `data`"; (c) adds `per_day.session_time_seconds` and `per_day.widgets` with back-fill for old records; (d) adds `delete_session_data()` for GDPR deletion; example pages take `session_id` from a text input. Owner asked about consent and deletion; author added deletion and asked twice for review, last on 2025-04-09 | REWORK. Four concerns in one PR, conflicts with main after 0.10.x, and (b) is a regression: a process-global session dict is shared by every concurrent user, which breaks the session isolation that `st.session_state` gave. Salvage (a) as a one-line PR and (d) as a small API PR; (c) changes the on-disk schema and needs a decision first. Thank the author, ask to split |
| 119 | set up logging | spolisar | 2024-11-14 | 2024-11-21 | 2 files, +15/-10: src `__init__.py`, main.py | CONFLICTING (DIRTY), 0 reviews | Replaces root `logging.info/warning/error` calls with `logging.getLogger(__name__)` plus a `NullHandler`, the urllib3 pattern, so SA2 stops printing INFO lines into host apps that never configured logging. Author supplied a gist reproducing the leak | MERGE-CANDIDATE after a trivial redo. Correct, tiny, standard practice, owner wrote "I love this PR". Conflicts only because main.py renamed `counts` to `data` and `__version__` moved. Re-apply by hand on main (5 minutes), credit spolisar in the commit, close #119 as merged-by-hand |

## 3. Themes

1. Multipage apps: #47, #103 (second ask), #53 (line item). Users want per-page pageviews and per-page widget counts for both `pages/` and `st.Page`/`st.navigation` apps, with persistence, instead of one shared total. This is the single most-wanted change and the README already admits `pages/` is broken.
2. Counting accuracy: #102, #13, #122. Users want counts that mean "a person did something", not "the script reran with a default value", and no crashes on `None` defaults. #102 and #13 are confirmed defects in 0.10.7 and share one root cause: `state_dict.get(label, None)` treats the first render as a change.
3. Widget identity and coverage: #26, #46, plus the unwrapped `st.sidebar.checkbox`. Users want `key=` as the identity (same-label buttons, generated labels) and coverage of widgets added after the upstream fork: toggle, download_button, link_button, page_link, camera_input.
4. Storage backends and export: #103, #53, PR #137 (Firestore merge), README claim of CSV. Users want a pluggable backend (DuckDB/MotherDuck, SQL) or at least a documented way to read the data out. The README advertises CSV storage but no CSV code exists (`grep -ri csv src/` finds only the config-tab label).
5. Time dimension: #31, PR #137 (session_time_seconds, per-day widgets). Users want to know when things happened and how long sessions last, not only lifetime totals.
6. Config screen and the v1 roadmap: #53, #103. The dream is choosing backend and options in-app; today the Config tab is a self-described proof of concept whose buttons "do not currently do anything" except write `.streamlit/analytics.toml`.
7. Library hygiene: PR #119 (logging), #53 AppTest item (done in #146). Host apps want SA2 to be a quiet, well-behaved dependency.
8. Privacy and consent: PR #137 thread (consent, deletion), session tracking by UUID. The owner raised GDPR questions; nothing in the released code addresses them.
9. Docs drift: README promises CSV, "Multipage tracking" as upcoming since 2024, and `st.navigation` as "Checking"; the Wiki is the only place password and Firestore setup are described.

## 4. Most-requested capabilities (distinct people asking or reacting)

1. Per-page tracking for multipage apps: 4 (Joyce920hope, alon-sht, ZFhuang, Mjboothaus), #47 and #103; the owner calls it the biggest request.
2. v1 settings page / refactor: 3 reactions (claromes, desenvolvimento2novalar, sxy-trans-n), #53.
3. Wrap the newer widgets, toggle first: 3 (alexander-ugent, christoffer-sannes-statnett, bitcometz), #46 and #122.
4. Key-based widget identity: 3 (amirmk89, nathanjones4323, emigre459), #26.
5. Accurate counts, no startup increments: 2 (robino16, and bitcometz's confusion in #122 stems from the same reset behaviour), #102.
6. Firestore merge semantics and session deletion: 1 active contributor with a working PR (emigre459), #137.
7. Other backends / export API: 1 (Mjboothaus), #103.
8. Per-event timestamps: 1, unresponsive (nixshal), #31.
9. `index=None` crash: 1 (hansipie) but it is a confirmed crash with a supplied repro, #13.

Reactions were pulled from `issues/N/reactions`; issues 122, 103, 102, 31, 26 and 13 have none.

## 5. Security and privacy concerns

1. Dashboard is public by default. `?analytics=on` opens the dialog for anyone; `unsafe_password` is optional, compared with plain `!=`, and lives in app source. The "Danger zone" reset (erases everything, including Firestore) sits inside the same gate, so with no password any visitor can wipe the analytics. `display.py` lines 26-34 and 152-174.
2. The Config tab is outside the password gate. `main.py` `show_sa2()` renders `config.show_config()` in tab 2 unconditionally. On first view it creates `.streamlit/analytics.toml` in the server's working directory with the default password `hunter2`; it echoes the stored password, Firestore key-file path and secrets key name back into inputs; and "Save Configuration" / "Reset to Defaults" write visitor-supplied content to that file. `track()` does not read the file today, so the impact is an unauthenticated file write plus information disclosure rather than a takeover, but it should be gated by the password or removed until it does something. `config.py` lines 23, 41-67, 92-105.
3. Free-text capture by design. `wrappers.value` and `wrappers.chat_input` store every text_input, text_area, number_input and chat_input value verbatim as a dictionary key in the JSON file or Firestore document (the committed `sa2_data.json` shows `"Write your name": {" ": 2}`). Chat prompts and names are personal data; there is no hash, redact or opt-out option and the README does not warn. This is the GDPR issue the owner raised on #137, and it exists without session tracking.
4. Session tracking. Per-session documents share the Firestore collection with the `counts` document, keyed by the caller's `session_id`; a `session_id` equal to `firestore_document_name` would overwrite the aggregate. PR #137's example takes the id from a user text input. Released code has no deletion or TTL path; #137 proposes `delete_session_data()`.
5. Data on disk in the repo. `sa2_data.json` and `analytics.toml` are tracked in git even though `analytics.toml` is in `.gitignore` (added after the file). Sample data only, but the example apps write to these paths, so a careless commit would publish real data. `firebase-key.json` and `secrets.toml` are correctly ignored.
6. Verbose mode dumps the whole data dict, including session data loaded from Firestore, to the root logger and to stdout via `print()` (`main.py` lines 106-128, 254-258). PR #119 fixes the logger half; the `print()` calls remain.
7. Firestore `save()` overwrites the document instead of merging, so any custom fields a deployment adds are silently lost on the next write. Data loss rather than exposure; the one-line fix is in #137.

## Suggested order of work

1. Redo #119 by hand on main (logging). Close #13 with the `replace_empty(None)` fix in `wrappers.select` and add an AppTest case; wrap `st.sidebar.checkbox`.
2. Fix #102 by seeding `state_dict` on first render instead of counting it (one change in each wrapper), release as 0.10.8 with a changelog note that startup inflation stops.
3. Gate or remove the Config tab (#5 item 2), and add a README privacy note about verbatim text capture.
4. Reply on #137: accept `merge=True` and `delete_session_data()` as two small PRs, decline the global session dict, park the per-day schema.
5. Replace #53 with a milestone; close #31 as needs-info; close #122 with a pointer to the `load_from_json` requirement and to #46 for toggle.
6. Then the two real features people ask for: #46 widget coverage (toggle first) and #47 per-page tracking, with #26 key-based identity designed alongside it because both change the shape of `data["widgets"]`.
