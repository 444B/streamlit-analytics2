# Community knowledge for streamlit-analytics2, collected 2026-09-25

Raw material for a usage wiki. Everything below is taken from public sources
and cites its URL. Nothing is invented; where a question got no answer it says
"unanswered". Read-only collection: nothing was posted or edited on GitHub.

## Sources

| Source | Reached | Count |
|---|---|---|
| GitHub Discussions, 444B/streamlit-analytics2 | yes (GraphQL, `hasDiscussionsEnabled: true`) | 14 discussions, no second page: General 4, Performance Engineering 4, Q&A 3, Announcements 2, Ideas 1 |
| GitHub Discussions, jrieke/streamlit-analytics (upstream) | discussions disabled (`hasDiscussionsEnabled: false`, `totalCount: 0`) | 0 |
| Issues, jrieke/streamlit-analytics (upstream) | yes | 36 issues (24 open, 12 closed), 2021-01 to 2025-02 |
| Issues, 444B/streamlit-analytics2 | yes | 42 closed (of which 32 are upstream issues re-filed on 2024-03-02 as #13 to #42), 9 open |
| Wiki, 444B/streamlit-analytics2 | yes, cloned to /tmp/sa2-wiki | 4 pages (Home, 0 Migration Guide, 1 Getting Started, 2 Advanced Configuration) + 1 image, 16 commits; the "FAQs" page is listed as "Coming soon" on Home |
| Wiki, jrieke/streamlit-analytics | not reachable: `git clone` of `jrieke/streamlit-analytics.wiki.git` failed with a username prompt, which is GitHub's response when the wiki repo does not exist (the repo flag `hasWikiEnabled` is true but no pages were ever created) | 0 |
| README, 444B/streamlit-analytics2 (`.github/README.md`) | yes | 1 |
| Examples in the repo, `examples/` (read-only) | yes | `minimal.py`, `analytics.toml`, `.streamlit/analytics.toml`, `pages/Streamlit_Analytics_Demo.py`, `pages/all-features.py`, `pages/firebase_test.py`, `pages/create_key.py` |
| Streamlit forum search `q=streamlit-analytics2` | yes (Discourse JSON) | 4 topics |
| Streamlit forum search `q=streamlit-analytics` | yes | 19 topics (overlap with the above) |
| Streamlit forum threads read in full | yes | 14 threads: 38983, 61009, 60506, 118381, 20983, 12787, 121546, 69074, 70127, 13557, 34522, 23584, 121000, 13918 |

Not covered: private support channels, Stack Overflow (not in the brief), and
issues on any other fork.

## How people use it today

### The `with track():` context manager around the whole app

The dominant pattern. Most snippets wrap everything, usually via a `main()`
function.

- "with streamlit_analytics.track(save_to_json=log_path, load_from_json=log_path): main()" (Dahie's boilerplate). The maintainer confirmed: "calling with streamlit_analytics.track on your main() does work and is actually a smart way of doing it." https://github.com/444B/streamlit-analytics2/issues/45
- The maintainer's canonical shape, given as the answer to a bug report: `with streamlit_analytics.track(): main()` where `main()` holds `st.set_page_config` and the page body. https://github.com/444B/streamlit-analytics2/discussions/117
- The repo demo page does the same: `with streamlit_analytics.track(save_to_json="sa2_data.json"): main()`. `examples/pages/Streamlit_Analytics_Demo.py`
- Wrapping only part of the page also works: "with streamlit_analytics.track(): st.text_input(...); st.selectbox(...); st.button(...)" (wiki Getting Started). https://github.com/444B/streamlit-analytics2/wiki/1.-Getting-Started

### `start_tracking()` / `stop_tracking()` pairs

The older, upstream style; still in use and still documented.

- "streamlit_analytics.start_tracking() ---code--- streamlit_analytics.stop_tracking()" (eschares, 2021, deploying to share.streamlit.io). https://github.com/jrieke/streamlit-analytics/issues/5
- "sa.stop_tracking(firestore_key_file='firestore-key.json', firestore_collection_name='counts')" (jucor). https://github.com/jrieke/streamlit-analytics/issues/3
- "streamlit_analytics.stop_tracking(save_to_json='path', unsafe_password='somepass')" (tiagocampo). https://github.com/jrieke/streamlit-analytics/issues/23
- Gotcha found by the maintainer: "you can use start_tracking multiple times but you can only use stop_tracking once", because `stop_tracking` renders the dashboard and a second render duplicates widget keys. https://github.com/444B/streamlit-analytics2/issues/100
- The wiki presents start/stop as the "Custom Tracking" mechanism, with the note that the same kwargs must be passed to both `start_tracking` AND `stop_tracking`. https://github.com/444B/streamlit-analytics2/wiki/2.-Advanced-Configuration

### Firestore persistence

Used by anyone deploying on Streamlit Community Cloud or a container without a volume, because in-memory counts die on restart.

- Classic key file: `track(firestore_key_file="path_to_your_firebase_key.json", firestore_collection_name="your_collection_name")`. https://github.com/444B/streamlit-analytics2/wiki/2.-Advanced-Configuration
- Key from `st.secrets` (no JSON file in the repo): `track(firestore_collection_name="counts", streamlit_secrets_firestore_key="firebase", firestore_project_name=...)`, with a helper script that copies the JSON into `.streamlit/secrets.toml`. Wiki and `examples/pages/create_key.py`. https://github.com/444B/streamlit-analytics2/wiki/2.-Advanced-Configuration
- The repo's own test page: `track(streamlit_secrets_firestore_key="firebase_key", firestore_project_name=st.secrets["project_name"], firestore_collection_name=st.secrets["collection_secret"])`. `examples/pages/all-features.py`
- Real production use (emigre459, Cloud Run + Firestore): `track(firestore_project_name="project", firestore_collection_name="streamlit-analytics", streamlit_secrets_firestore_key="firebase", session_id="1234")`. https://github.com/444B/streamlit-analytics2/discussions/136
- Base64 workaround, pre-secrets support (puyo, forum): decode `FIREBASE_ACCESS_KEY` from env into `/tmp/firestore-key.json`, then `track(unsafe_password=os.environ.get("ANALYTICS_KEY"), firestore_key_file="/tmp/firestore-key.json", firestore_collection_name="counts")`. https://discuss.streamlit.io/t/secure-deployment-with-streamlit-analytics-track-usage-of-widgets-and-app/38983
- Custom load/save (pvpiv, Community Cloud, 100k page visits): wrote his own `load_from_firestore` / `save_to_firestore` reading `st.secrets["textkey"]` because "I'm a noob and I don't know how to access the file from community cloud". https://github.com/444B/streamlit-analytics2/issues/132 and https://github.com/444B/streamlit-analytics2/discussions/138
- Cloud Run without a secrets file (emigre459): inject the env var into `st.secrets._secrets` at startup. https://github.com/444B/streamlit-analytics2/discussions/126

### JSON save / load

- `track(save_to_json="path/to/file.json")` and `track(load_from_json="path/to/file.json")`. https://github.com/444B/streamlit-analytics2/wiki/2.-Advanced-Configuration
- The demo uses `save_to_json="sa2_data.json"`. `examples/pages/Streamlit_Analytics_Demo.py`
- Users also read the JSON themselves to show a visitor counter: "with open(analytics_file) as f: visits = json.load(f)['total_pageviews']" (open issue #122, which is where this pattern bites, see below). https://github.com/444B/streamlit-analytics2/issues/122
- Origin of the feature: "the streamlit app is deployed on a docker and we have no persistence of volume ... upload the json on a server at fixed frequency rate" (Uranium2, merged upstream PR #10). https://github.com/jrieke/streamlit-analytics/issues/9
- Since 0.5.3 the path is created if missing (`save_to_json` to a nonexistent directory). https://github.com/444B/streamlit-analytics2/issues/23

### The `?analytics=on` dashboard

- "Run your Streamlit app and append `?analytics=on` to the URL to view the analytics dashboard." README. https://github.com/444B/streamlit-analytics2
- Public demo: https://sa2analyticsdemo.streamlit.app/?analytics=on
- The dashboard has a "Danger Zone" with a reset flow: select "I'm absolutely sure that I want to reset the results" then click reset. https://github.com/444B/streamlit-analytics2/issues/97
- Widget-level display: it also shows the text people typed into `st.text_input` and `st.chat_input` (screenshot in the chat_input thread). https://github.com/444B/streamlit-analytics2/issues/44

### Password gate

- `track(unsafe_password="your_simple_password")`, "This password is not encrypted, so choose something non-sensitive." https://github.com/444B/streamlit-analytics2/wiki/2.-Advanced-Configuration
- Recommended from day one by Streamlit staff: "You could password-protect the analytics page by adding a secret key to your Streamlit Share deployment." (andfanilo, 2021). https://discuss.streamlit.io/t/streamlit-share-monitor-traffic-on-your-app/13557
- Upstream author on its limits: "keep in mind that this is obviously not 100% secure as it's just a simple text password within the app." https://discuss.streamlit.io/t/is-this-streamlit-tracking-legit/13918
- Real usage keeps the password in secrets: `unsafe_password=st.secrets["unsafe_password"]` (`examples/pages/all-features.py`) or `os.environ.get("ANALYTICS_KEY")` (forum 38983).

### Multipage apps

Status per README: `main.py` works, `pages/` directory "Not Working", `st.Page + st.navigation` "Checking". https://github.com/444B/streamlit-analytics2

- What people actually do: "I somewhat blindly just use `with streamlit_analytics.track():` on every page (including my entrypoint)" (emigre459). https://github.com/444B/streamlit-analytics2/discussions/136
- Result of doing that: counts are shared, not per page: "for page2, the number of page_view and the number of uploaded_file are ... combined with these two metrics of page1". Maintainer: "both calls to streamlit_analytics on each page is going to contribute to the session state as a whole." https://github.com/444B/streamlit-analytics2/issues/47
- Workaround tried and rejected: "calling reset_counts() within start_tracking() ... separated the info from the pages, but it resets the counts every refresh" (alon-sht). https://github.com/444B/streamlit-analytics2/issues/47
- One user forked and patched `main.py` to keep per-page `counts` (robino16), which is how the `state_dic` typo was found. https://github.com/444B/streamlit-analytics2/issues/100
- Older upstream pattern: wrapping `track()` inside an `app()` function used by a hand-rolled multiapp router. https://github.com/jrieke/streamlit-analytics/issues/13
- Community alternative born from this gap: `streamlit-fyr`, "heavily inspired on Streamlit-analytics", explicit events + SQLite/Postgres + visitor cookie, built "for multi app streamlit deployments". https://discuss.streamlit.io/t/i-created-a-tiny-package-to-enable-multi-app-page-analytics/121546

### Streamlit Community Cloud

- Works when the package is in `requirements.txt`; the 2021 "does not load on deploy to share.streamlit.io" report ended with "Found an incorrect dependency on my end". https://github.com/jrieke/streamlit-analytics/issues/5
- Persistence there means Firestore + `st.secrets` (see Firestore section). https://github.com/444B/streamlit-analytics2/discussions/138
- Numbers differ from the Cloud "App viewers" tab: "streamlit-analytics library seems to measure page views as everytime the app re-runs ... the built-in analytics on the Community Cloud measures unique views" (dataprofessor). https://discuss.streamlit.io/t/its-hard-to-assess-how-popular-my-streamlit-app-is-how-best-to-apply-analytics-to-determine-app-viability/69074

### Session tracking

- `session_id=` kwarg exists on `track`, `start_tracking`, `stop_tracking` and is used in the wild (`session_id="1234"`, discussion 136). The README advertises "Gathering Session state details based on randomized UUIDs". https://github.com/444B/streamlit-analytics2
- What users want beyond it: "analytics ... at the session/user level instead of ... in aggregate ... I'm currently tracking visitors by using UUID session IDs and setting a cookie in the client browser and then using firestore to track user-level clicks, but it's not playing nicely with other packages currently (namely streamlit-authenticator)". Proposed a `visitor_id` kwarg used as the Firestore document id. https://github.com/444B/streamlit-analytics2/discussions/120
- Maintainer's pointer for identification: `st.context.headers` and `st.context.cookies` (the `ajs_anonymous_id` cookie, suppressed by `[browser] gatherUsageStats = false`). https://github.com/444B/streamlit-analytics2/discussions/120
- Scale data point: "My streamlit-analytics2 dashboard just clocked 711 pageviews, 1,200+ widget interactions, and over 27 hours of active session time" during a 450-concurrent-user spike (Caleb2, DM Co-Pilot, Firestore). https://discuss.streamlit.io/t/showcase-how-i-used-st-session-state-groq-and-pydantic-to-scale-an-ai-app-during-a-viral-450-user-surge/121000

### Other deployment contexts seen

- AWS EC2 behind WAF + ALB, systemd-managed (Vikram_N); maintainer replied that Nginx is unnecessary in that setup. https://discuss.streamlit.io/t/nginx-for-deployment-on-aws-ec2/70127
- render.com (eightm). https://discuss.streamlit.io/t/updated-to-1-30-now-getting-a-query-params-warning/60506
- Hugging Face Spaces (david-oplatka). https://github.com/jrieke/streamlit-analytics/issues/48
- GCP Cloud Run with Secrets Manager (emigre459). https://github.com/444B/streamlit-analytics2/discussions/126
- Docker without persistent volume (Uranium2). https://github.com/jrieke/streamlit-analytics/issues/9
- Poetry-managed project (Dahie). https://github.com/444B/streamlit-analytics2/issues/45
- uv-managed project, run with `uvx streamlit run` (saisaigraph). https://github.com/444B/streamlit-analytics2/discussions/140

## Recurring questions and confusions

FAQ-style: question, then the answer that was given.

**Q: I appended the query param but the dashboard does not appear.**
A: The value must be exactly `on`: the reporter had used `?analytics=true`. "I was using the wrong parameter value in my tests. http://localhost:8501?analytics=true instead of on." https://github.com/444B/streamlit-analytics2/issues/45
Related: "Streamlit 1.4. Installed and code insert as instructed but analytics page nothing different is showing up" on the upstream repo; answer was "share your full code" and use the fork. https://github.com/jrieke/streamlit-analytics/issues/50

**Q: `ModuleNotFoundError: No module named 'streamlit_analytics2'` after `uv add streamlit-analytics2` and `uvx streamlit run main.py`.**
A: Unanswered beyond "Can you share the full code you have put in the .py file?" (2025-09-10). Same question posted on the forum with no reply. Note for the wiki: `uvx` runs a tool in an isolated environment, not the project venv. https://github.com/444B/streamlit-analytics2/discussions/140 and https://discuss.streamlit.io/t/installing-using-uv-package-manager-module-not-found/118381

**Q: I get "Please replace st.experimental_get_query_params with st.query_params" and I never call it.**
A: It is the upstream `streamlit-analytics` package; switch to `streamlit-analytics2`, which fixed it. "This was the culprit, using streamlit-analytics caused the warning" (forum); "use streamlit-analytics2 where this issue has been fixed ... Thanks @444B. This worked" (upstream #49). https://discuss.streamlit.io/t/updated-to-1-30-now-getting-a-query-params-warning/60506, https://github.com/jrieke/streamlit-analytics/issues/49, https://github.com/jrieke/streamlit-analytics/issues/48, https://github.com/jrieke/streamlit-analytics/issues/39

**Q: How do I migrate from streamlit-analytics to streamlit-analytics2?**
A: `pip install streamlit-analytics2` and `import streamlit_analytics2 as streamlit_analytics`; "need to add a '2' in two locations in code". https://github.com/444B/streamlit-analytics2/wiki/0.--Migration-Guide-from-streamlit%E2%80%90analytics-to-streamlit%E2%80%90analytics2 and https://github.com/444B/streamlit-analytics/issues/39

**Q: Is the upstream project abandoned? Which one should I use?**
A: Streamlit staff (2024-02): "the project isn't abandoned; unfortunately, we just haven't had time". The upstream repo then pinned "Please open new issues in streamlit-analytics2" (2024-03) and the maintainer answers upstream issues with "this repo is not maintained but we have a maintained fork". https://discuss.streamlit.io/t/has-streamlit-analytics-been-abandonded/61009, https://github.com/jrieke/streamlit-analytics/issues/46, https://github.com/jrieke/streamlit-analytics/issues/50

**Q: Is this package legit / safe to use?**
A: Upstream author: "I don't think there's any chance for abuse ... You can even password-protect the analytics results within the app but keep in mind that this is obviously not 100% secure". https://discuss.streamlit.io/t/is-this-streamlit-tracking-legit/13918

**Q: How do I keep the numbers after a restart or redeploy?**
A: Firestore, or `save_to_json` + `load_from_json` to a path that survives. "you'll also need to configure Firestore to store your analytics, otherwise they will get destroyed everytime you restart your app." https://discuss.streamlit.io/t/streamlit-share-monitor-traffic-on-your-app/13557, https://github.com/jrieke/streamlit-analytics/issues/9

**Q: How do I use Firestore on Streamlit Cloud without committing the key file?**
A: Put the key JSON in `.streamlit/secrets.toml` and pass `streamlit_secrets_firestore_key=` plus `firestore_project_name=` (wiki, with a helper script). Alternatives seen: base64 in an env var written to /tmp; custom load/save functions. https://github.com/444B/streamlit-analytics2/wiki/2.-Advanced-Configuration, https://discuss.streamlit.io/t/secure-deployment-with-streamlit-analytics-track-usage-of-widgets-and-app/38983, https://github.com/444B/streamlit-analytics2/issues/21

**Q: Firestore on Cloud Run / outside Streamlit Cloud, where there is no secrets.toml?**
A: "You can use secrets manager + environment variables in Cloud Run". User's working hack: copy the env var into `st.secrets._secrets[...]` at startup. https://github.com/444B/streamlit-analytics2/discussions/126

**Q: `ValueError: One or more components is not a string or is empty.` when saving to Firestore.**
A: Two reports (issue #66 multipage app, discussion #59 single button). Neither was root-caused: #66 "started working" after the reporter added breakpoints and could not reproduce again; #59 unanswered after the alias red herring was ruled out. https://github.com/444B/streamlit-analytics2/issues/66, https://github.com/444B/streamlit-analytics2/discussions/59

**Q: Firestore save crashes with `TypeError: '<' not supported between instances of 'str' and 'NoneType'`.**
A: Widget values of `None` (radio with no default). Upstream replaced `None` with empty strings in 0.3.x. Workaround at the time: temporarily disable Firestore to reach the reset button, or restart. https://github.com/jrieke/streamlit-analytics/issues/3

**Q: Firestore + `file_uploader` throws at `stop_tracking`.**
A: Unresolved. Reporter's workaround: call `start_tracking()` after the uploader so it is not tracked. Author: "the return value of file uploader is actually never stored in Firestore ... please post the full error message". https://github.com/jrieke/streamlit-analytics/issues/4

**Q: How do I reset the analytics?**
A: Deleting the JSON is not enough while the app is running (counts live in memory). Use the reset section at the bottom of the dashboard (since 0.2.1) or restart `streamlit run`. A request to disable the reset UI in code ("these analytics are mostly used with no password") is unanswered. https://github.com/jrieke/streamlit-analytics/issues/2
Bug: in 0.7.5 the reset button never appeared because a lint tool removed the word "absolutely" from the comparison string; fixed in 0.7.6. https://github.com/444B/streamlit-analytics2/issues/97

**Q: Why does every checkbox / widget count start at 1 and go up without anyone touching it?**
A: Two bugs. (1) A `state_dic` typo reset `state_dict` on every rerun, so every widget counted on every action; fixed in 0.7.7. (2) Widgets are counted on first render because the wrapper runs on every script run; the maintainer confirmed it affects checkbox, radio, selectbox, slider, select_slider, text_input, number_input, text_area, date_input, color_picker and chat_input. Issue #102 still open with a proposed fix (only count when the value changed from the stored one). https://github.com/444B/streamlit-analytics2/issues/100, https://github.com/444B/streamlit-analytics2/issues/102

**Q: My pageview counter resets to 1 when I click a toggle.**
A: The user read `total_pageviews` from the JSON inside the `track()` block before the file existed. Maintainer advice: default `visits = 0`, check the file exists and is non-empty, read it before entering `track()`. Issue still open. https://github.com/444B/streamlit-analytics2/issues/122

**Q: Why do my numbers differ from Streamlit Cloud's "App viewers"?**
A: "streamlit-analytics library seems to measure page views as everytime the app re-runs ... the built-in analytics on the Community Cloud measures unique views". https://discuss.streamlit.io/t/its-hard-to-assess-how-popular-my-streamlit-app-is-how-best-to-apply-analytics-to-determine-app-viability/69074

**Q: Counts look low; two users at once only counted once.**
A: Unanswered (2025-03). Reporter suspected his custom Firestore load/save. https://github.com/444B/streamlit-analytics2/discussions/138

**Q: Does it track `st.chat_input`?**
A: Yes since 0.6.1/0.6.3, and it records the submitted text. Known minor bug: streaming chat apps add a "None" key. https://github.com/444B/streamlit-analytics2/issues/44, https://github.com/444B/streamlit-analytics2/issues/19

**Q: Does it track `download_button`, `link_button`, `page_link`, `toggle`, `camera_input`?**
A: Not yet; tracked in open issue #46 ("just need to write the wrapper"). https://github.com/444B/streamlit-analytics2/issues/46, https://github.com/444B/streamlit-analytics2/issues/24

**Q: Does it work inside `st.form`?**
A: Unanswered beyond "share a full code example". Reporter: selectbox inside a form only increments the default item. https://github.com/444B/streamlit-analytics2/discussions/113

**Q: Clicks are not recorded when the page errors or navigates away.**
A: Confirmed by the reporter's own minimal repro: a button whose handler raises records nothing until the next rerun; also seen with `@st.dialog`. No fix. https://github.com/444B/streamlit-analytics2/discussions/136

**Q: Two buttons with the same label are counted as one.**
A: Known: tracking keys on label, not `key=`. Maintainer said (2025-02) "I will focus on this fix/feature for the next release"; still open. https://github.com/444B/streamlit-analytics2/issues/26, https://github.com/jrieke/streamlit-analytics/issues/24

**Q: `KeyError` from `select_slider` / `radio` / `selectbox(index=None)`.**
A: Tuple values from `select_slider` are converted to `"a - b"` strings since upstream 0.3.1. `radio` `KeyError: 'LTM'` was caused by passing a pandas DataFrame as options; fixed by passing a column. `selectbox(index=None)` KeyError is open (#13) with a proposed one-line fix (`.get(label, " ")`). https://github.com/444B/streamlit-analytics2/issues/25, https://github.com/jrieke/streamlit-analytics/issues/6, https://github.com/444B/streamlit-analytics2/issues/13

**Q: `TypeError: Object of type int64 is not JSON serializable` on the dashboard.**
A: Closed "not reproducible" (0.8.2, Streamlit 1.38, Python 3.9); the reporter never shared full code. https://github.com/444B/streamlit-analytics2/discussions/117, https://github.com/444B/streamlit-analytics2/issues/118

**Q: `metric() got an unexpected keyword argument 'help'`.**
A: Streamlit older than 1.11; upgrade Streamlit. https://github.com/jrieke/streamlit-analytics/issues/23, https://github.com/jrieke/streamlit-analytics/issues/28

**Q: `ModuleNotFoundError: No module named 'streamlit.report_thread'` (Streamlit 1.4+).**
A: Historical, upstream 0.4.1 moved to `st.session_state` (tested on 1.13). Anyone still hitting this is on a pre-0.4 upstream release. https://github.com/jrieke/streamlit-analytics/issues/14, https://discuss.streamlit.io/t/modulenotfounderror-no-module-named-streamlit-report-thread/20983

**Q: `AttributeError: st.session_state has no attribute "last_time"`.**
A: Investigated in the fork, "seems to be WAI"; could not reproduce on current code. https://github.com/444B/streamlit-analytics2/issues/20

**Q: The app crashes when run with `python3 main.py`.**
A: Working as intended; use `streamlit run main.py`. https://github.com/444B/streamlit-analytics2/issues/11

**Q: The graph is out of order across a year boundary (December after January).**
A: Fixed in 0.10.3 using `yearmonthdate` when more than one year is present (fix contributed by Niteshiya). https://github.com/444B/streamlit-analytics2/issues/128, https://github.com/444B/streamlit-analytics2/issues/14

**Q: The first day on the traffic plot shows 0, and dates shift by a day in negative timezones.**
A: By design (starts from the previous day for comparison), acknowledged as misleading; deferred to the timestamp feature (#31). Timezone shift unaddressed. https://github.com/444B/streamlit-analytics2/issues/18

**Q: SA2 hijacked my logging / my custom logging stopped working.**
A: Confirmed (0.7.2): the package called `logging.basicConfig`. Maintainer (2024-10): "I will look into disabling the custom logging from SA2 until a more suitable solution is found". Issue closed. https://github.com/444B/streamlit-analytics2/issues/78

**Q: `st.experimental_dialog` deprecation popup (Streamlit 1.37).**
A: Fixed by moving to `st.dialog` and bumping the minimum Streamlit. https://github.com/444B/streamlit-analytics2/issues/111

**Q: Upgrading broke my custom code: `.counts` became `.data`.**
A: Unanswered on the issue; the rename happened in the 0.10.x refactor. The reporter wants "to rely on the package as is deployed (without having to edit my code for every update)". https://github.com/444B/streamlit-analytics2/issues/132

**Q: Can I add Google Analytics / GA4 through this package?**
A: No. "not possible with st.html or any other methods (such as iframes) ... yet to get a working example that does not involve a proxy of some sort" (2024-12). https://github.com/444B/streamlit-analytics2/issues/16, https://github.com/444B/streamlit-analytics2/discussions/120

**Q: Can I track custom events (e.g. count "main feature used" inside an `if`)?**
A: Requested upstream as `custom_track(name_of_element=...)`; closed as no longer relevant to the reporter, never implemented. https://github.com/444B/streamlit-analytics2/issues/28

**Q: Can I get timestamps per interaction instead of daily aggregates?**
A: Open since 2022. Maintainer: "I would love to implement this feature however it could be provided as an optional feature via the config screen". https://github.com/444B/streamlit-analytics2/issues/31

**Q: Does it collect PII / user input?**
A: It records `text_input` and `chat_input` contents. Maintainer: "not collecting by default any PII unless either the user submits it or the applicable developer chooses to collect it". One user: "this is an analytics tool, it should only show usage stats, not the usage/input itself right?" https://github.com/444B/streamlit-analytics2/issues/44

**Q: Is it heavy? It wraps every widget on every rerun.**
A: Yes: "80 function calls, on EVERY button click"; every widget function is monkey-patched each rerun. A 28-day JSON with 1.3K pageviews and 3K interactions takes about 7 seconds to render on the dashboard. A 5000-option multiselect allocates a dict with 5000 keys. https://github.com/444B/streamlit-analytics2/discussions/56, https://github.com/444B/streamlit-analytics2/discussions/131, https://github.com/444B/streamlit-analytics2/issues/17

## Pain points and wishes

Grouped; counts are distinct threads that raise the point.

**Multipage tracking (7 threads, the most-requested feature)**
Per-page counts, `pages/` directory, `st.Page`/`st.navigation`. #47 (open), #30/upstream #20, #100 (fork to get per-page), #103 ("I'd also like multipage app tracking support e.g. with latest st.Page()"), discussion 136, discussion 71 (roadmap item 4), README status table. Maintainer: "one of the biggest requested features overall". https://github.com/444B/streamlit-analytics2/issues/47, https://github.com/444B/streamlit-analytics2/issues/103, https://github.com/444B/streamlit-analytics2/discussions/136

**Counting semantics and accuracy (6 threads)**
Widgets counted on first render (#102 open), `state_dic` typo (#100 fixed), pageviews = reruns not visitors (forum 69074), low counts / concurrent users (discussion 138), toggle reset (#122 open), clicks lost on error/navigation (discussion 136). https://github.com/444B/streamlit-analytics2/issues/102, https://discuss.streamlit.io/t/its-hard-to-assess-how-popular-my-streamlit-app-is-how-best-to-apply-analytics-to-determine-app-viability/69074

**Secure Firestore credentials on hosted platforms (6 threads)**
Key-from-dict / `st.secrets` (#21, upstream #29, forum 38983 with 1631 views), Cloud Run env vars (discussion 126), custom load/save because the docs were unclear (#132, discussion 138). Now supported via `streamlit_secrets_firestore_key`, but the discussion-126 and #132 users still had to write their own code. https://discuss.streamlit.io/t/secure-deployment-with-streamlit-analytics-track-usage-of-widgets-and-app/38983, https://github.com/444B/streamlit-analytics2/discussions/126

**Unique users / sessions / visitor identity (4 threads)**
"is the observed activity driven by a small group of users or a larger number of unique users" (#121), `visitor_id` as Firestore doc id (discussion 120), Cloud "App viewers" mismatch (forum 69074), streamlit-fyr built with a visitor cookie because this was missing (forum 121546). https://github.com/444B/streamlit-analytics2/issues/121, https://github.com/444B/streamlit-analytics2/discussions/120

**Widget coverage (5 threads)**
`download_button` (#24, upstream #26), `chat_input` (#44 done, #19), new widgets `link_button`/`page_link`/`toggle`/`camera_input` (#46 open), forms (discussion 113). https://github.com/444B/streamlit-analytics2/issues/46

**Keying by `key=` instead of label (3 threads)**
Same-label buttons merge; LLM-generated follow-up buttons make label tracking "messy". #26, upstream #24, emigre459 +1 in 2025. https://github.com/444B/streamlit-analytics2/issues/26

**Other storage backends and export (4 threads)**
CSV (discussion 104, "Excellent idea"), MotherDuck/DuckDB and a documented data API (#103), GA4 and "alternative analytics providers" (#16, upstream #38, dream of a config screen with "Local json / firebase / Motherduck / SQL instance"). The current `examples/analytics.toml` in the repo shows planned `[exporters.umami]`, `ga4`, `plausible`, `webhook`, `posthog` sections and `[tracking] track_visitors`, which map directly onto these requests. https://github.com/444B/streamlit-analytics2/discussions/104, https://github.com/444B/streamlit-analytics2/issues/103, https://github.com/444B/streamlit-analytics2/issues/16

**Granular timestamps and a better traffic plot (3 threads)**
Per-event timestamps (#31 open), first-day-zero and timezone shift (#18), year boundary (#14/#128 fixed). https://github.com/444B/streamlit-analytics2/issues/31, https://github.com/444B/streamlit-analytics2/issues/18

**Performance at scale (3 threads)**
80 calls per click (discussion 56), 7-second dashboard load (discussion 131), 5000-option multiselect memory (#17), plus a caution that `st.fragment` "often we have to rollback" (discussion 71). https://github.com/444B/streamlit-analytics2/discussions/56, https://github.com/444B/streamlit-analytics2/discussions/131

**Privacy of captured input (2 threads)**
Text of `text_input`/`chat_input` is stored and shown on the dashboard (#44); the roadmap answer is a settings screen. `examples/analytics.toml` shows a planned `store_values = false` switch. https://github.com/444B/streamlit-analytics2/issues/44

**Stability across Streamlit and SA2 upgrades (6 threads)**
Deprecation warnings (`experimental_get_query_params` x4 threads, `experimental_dialog`), `report_thread` breakage (16-post forum thread, 24.6K views), `.counts` to `.data` rename (#132), `metric(help=)` on old Streamlit. Users explicitly say they avoid unmaintained packages: "It'll probably break again with new Streamlit versions, unless it's actively maintained." https://github.com/jrieke/streamlit-analytics/issues/14, https://github.com/444B/streamlit-analytics2/issues/132

**Side effects on the host app (2 threads)**
Global `logging.basicConfig` (#78), duplicated widget keys when `stop_tracking` runs twice (#100). https://github.com/444B/streamlit-analytics2/issues/78

**Documentation gaps users named**
"FAQs - Coming soon" on the wiki Home; Firestore setup was only written up after #66 ("taking the opportunity to document how to set up the connection to firestore"); the `main()` wrapping pattern was noted as worth adding to the docs in #45; the wiki's Firestore "Full Example" passes a file path to `streamlit_secrets_firestore_key`, which contradicts the paragraph above it (the key name in secrets.toml). https://github.com/444B/streamlit-analytics2/wiki, https://github.com/444B/streamlit-analytics2/issues/66, https://github.com/444B/streamlit-analytics2/issues/45

## Proposed wiki page outline

Based only on what the sources show people asking for. Pages marked "exists" are in the current wiki and need the listed additions.

1. **Home** (exists): keep the TOC; replace "FAQs - Coming soon" with a link to the FAQ page; add a one-line "Which package: streamlit-analytics2 is the maintained fork" with the upstream #46 pointer.
2. **Getting Started** (exists): add the `with track(): main()` shape (issue 45, discussion 117), the exact `?analytics=on` value (issue 45), "use `streamlit run`, not `python`" (issue 11), and an install note for uv projects (`uv run streamlit run`, not `uvx`) for discussion 140.
3. **Migration from streamlit-analytics** (exists): add the deprecation-warning symptoms as the reason to migrate (forum 60506, upstream #49/#48/#39) and the 0.10 `.counts` to `.data` rename for people with custom code (issue 132).
4. **What gets counted** (new): pageviews = script reruns, not unique visitors (forum 69074); widgets count on first render and on every change (issue 102); text_input and chat_input contents are stored (issue 44); same-label widgets merge (issue 26); clicks on a page that errors are lost until the next rerun (discussion 136). This page answers the single largest cluster of confusion.
5. **Persisting data** (new, split out of Advanced Configuration): JSON save/load with the "read the file before entering track()" pattern (issue 122), Docker-without-volume pattern (upstream #9), reset behaviour and the Danger Zone (upstream #2, issue 97).
6. **Firestore setup** (exists as a section, promote to its own page): the console walkthrough already written; fix the `streamlit_secrets_firestore_key` example so it names the secrets.toml key, not a path; add the `create_key.py` helper; add Cloud Run / env-var deployment (discussion 126) and the base64 alternative (forum 38983); add a troubleshooting list: `One or more components is not a string` (issue 66, discussion 59), `None` values (upstream #3), `file_uploader` (upstream #4).
7. **Password protection** (exists as a section): keep; add "store it in st.secrets or an env var" (examples, forum 38983) and the "not 100% secure" statement from the upstream author (forum 13918).
8. **Multipage apps** (new): the README status table; what happens when you wrap every page (shared counts, issue 47); what does not work (`reset_counts` per page, issue 47); the `session_id` kwarg; pointer to the roadmap. Users are hitting this blind today.
9. **Session and visitor tracking** (new): what `session_id` does; what is not available (unique users, issue 121); the `st.context.headers` / cookies pointer and the `gatherUsageStats` note (discussion 120).
10. **Supported widgets** (new): the list from `examples/pages/all-features.py`; chat_input caveat about "None" (issue 44); not yet supported: download_button, link_button, page_link, toggle, camera_input (issue 46); forms unverified (discussion 113); pandas options cause KeyError (issue 25); `selectbox(index=None)` open bug (issue 13).
11. **Deployment notes** (new): Streamlit Community Cloud (requirements.txt, secrets), Cloud Run, EC2 behind ALB (forum 70127), Hugging Face Spaces, render.com; which storage to use where.
12. **Performance and scale** (new): the 80-calls-per-click finding (discussion 56), the 7-second dashboard at 1.3K pageviews (discussion 131), large multiselects (issue 17), and the "one stop_tracking per run" rule (issue 100).
13. **Privacy** (new): what is stored, the PII position from issue 44, the planned `store_values` switch shown in `examples/analytics.toml`.
14. **FAQ / Troubleshooting** (new, replaces "Coming soon"): the Q/A list in the section above, ordered by frequency: dashboard not showing, module not found, deprecation warnings, Firestore errors, counts start at 1, reset, KeyErrors, int64 serialisation, old-Streamlit `metric(help=)`, `report_thread`.
15. **Roadmap and how to ask** (new): links to discussion 71 (1.0.0 plan), issue 53 (settings page + GA4 + refactor), issue 103 (exporters), discussion 104 (CSV); the maintainer's standing request for a full minimal repro before a bug is actioned (discussions 113, 117, 140; issue 118).
