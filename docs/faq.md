# FAQ and troubleshooting

**The dashboard does not appear.**
The query parameter must be exactly `analytics=on`. `?analytics=true` does
nothing. The dashboard renders where `stop_tracking()` runs, so the tracked
block must reach its end without an exception.

**`ModuleNotFoundError: No module named 'streamlit_analytics2'` with uv.**
`uvx streamlit run app.py` runs Streamlit in an isolated tool environment
that does not contain your project's dependencies. Use `uv run streamlit run
app.py` (or `uv add streamlit-analytics2` and activate the venv).

**The numbers are lower than on 0.10.**
By design. A widget rendering with its default value no longer counts as an
interaction; only changes the user made are counted. See
[upgrading.md](upgrading.md).

**Views are higher than Streamlit Community Cloud's viewers.**
Views count page loads and page switches; Community Cloud counts unique
viewers. Compare Visitors instead, and expect a small difference from the
daily rotation of the visitor id.

**Two buttons with the same label are counted together.**
In `sa2.data` (legacy), yes. In the event log and on the dashboard they are
separate as long as they have different `key=` values or sit in different
places.

**A widget inside a form only counts on submit.**
Correct: Streamlit delivers form values when the form is submitted, so that
is when the change is recorded.

**Clicks are lost when the page raises an exception.**
The run never reaches `stop_tracking()`, so nothing is written for that run.
Fix the exception; the next successful run records normally.

**`st.selectbox(..., index=None)` crashed on 0.10.**
Fixed in 0.11: no crash, and nothing counted until a value is chosen.

**Is it heavy?**
No. One hook per process, one dictionary lookup per rendered widget per run,
one append per run. The 0.10 approach of patching thirty functions on every
run is gone.

**Where is the config screen?**
Removed in 0.11. It wrote a file nothing read. Configure with `track()`
arguments.

**How do I reset?**
`sa2.reset_data()` from code, or the Danger zone on the dashboard (needs a
password). Both reset the counters only. Delete or prune the event log file
to reset events.

**The logger prints into my app's logs.**
Since 0.11 the library uses `logging.getLogger("streamlit_analytics2")` with
a `NullHandler` and never configures the root logger. Set its level to
`WARNING` to silence it entirely.

**Does it work with `st.fragment`?**
Partly. A fragment rerun executes only the fragment, so `track()` does not
run and changes made during fragment-only reruns are not captured. Widgets
outside fragments, page loads and full reruns are recorded as usual. Full
fragment support is on the list for a later release.

**Can I send data to Google Analytics, PostHog or Plausible?**
Not from this library: Streamlit cannot inject client-side scripts. Use a
custom `store=` to forward events server-side, or read the log with your own
job.

**I upgraded Streamlit and widget counts stopped, with a warning in the log.**
The capture hook checks for two Streamlit internals. If a Streamlit release
changes them, the library logs one warning and keeps counting page loads and
runs. Open an issue with the Streamlit version; the fix is usually small.
