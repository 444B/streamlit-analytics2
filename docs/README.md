# streamlit-analytics2 documentation

Privacy-first usage analytics for Streamlit apps. These pages are the
reference for humans and for AI assistants alike: every page states what a
feature does, the exact code to use it, and what data it produces.

| Page | Read it when you want to |
|---|---|
| [Getting started](getting-started.md) | add analytics to an app in two minutes |
| [API reference](api.md) | know every argument of `track()`, `start_tracking()`, `stop_tracking()`, `event()` |
| [Dashboard](dashboard.md) | understand each number and chart at `?analytics=on` |
| [Storage](storage.md) | keep data across restarts: JSON, JSONL, SQLite, your own backend |
| [Events and data model](events.md) | read the event log with pandas, SQLite or DuckDB |
| [Custom events](custom-events.md) | count things your app does, not just widgets |
| [Raw data query](query.md) | run SQL on the dashboard, with examples and the security model |
| [Privacy](privacy.md) | what is stored, what never is, GDPR notes |
| [Multipage apps](multipage.md) | per-page numbers with `pages/` or `st.navigation` |
| [Deployment](deployment.md) | Streamlit Community Cloud, Docker, Cloud Run, secrets |
| [Firestore](firestore.md) | persist the counters in Firestore, step by step |
| [FAQ](faq.md) | the dashboard does not show, numbers look wrong, install problems |
| [Upgrading](upgrading.md) | moving from 0.10 or from the original streamlit-analytics |
| [For AI agents](for-ai-agents.md) | canonical snippets and decisions when integrating on someone's behalf |

Machine-readable summaries: [`llms.txt`](../llms.txt) (short) and
[`llms-full.txt`](../llms-full.txt) (all of these pages in one file).

Source: https://github.com/444B/streamlit-analytics2. Package:
`pip install streamlit-analytics2` or `uv add streamlit-analytics2`.
