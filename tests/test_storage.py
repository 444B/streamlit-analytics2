import json

from streamlit_analytics2.aggregate import summarize
from streamlit_analytics2.events import Event
from streamlit_analytics2.storage import JsonlStore, SqliteStore, open_store


def _events():
    return [
        Event("2026-09-25T10:00:00Z", "session", "s1", visitor="v1", page="/"),
        Event("2026-09-25T10:00:00Z", "pageview", "s1", visitor="v1", page="/"),
        Event(
            "2026-09-25T10:05:00Z",
            "widget",
            "s1",
            page="/",
            name="Go",
            widget_id="$$ID-1-None",
            widget_type="button",
        ),
        Event(
            "2026-09-25T10:06:00Z",
            "widget",
            "s1",
            page="/",
            name="Pick",
            widget_id="$$ID-2-None",
            widget_type="selectbox",
            value="dog",
        ),
        Event("2026-09-25T11:00:00Z", "session", "s2", visitor="v2", page="/two"),
        Event("2026-09-25T11:00:00Z", "pageview", "s2", visitor="v2", page="/two"),
        Event("2026-09-25T11:00:01Z", "custom", "s2", name="report", props={"rows": 2}),
    ]


def test_jsonl_round_trip_and_bad_lines(tmp_path):
    path = tmp_path / "e.jsonl"
    store = JsonlStore(path)
    store.append(_events())
    path.open("a").write('not json\n{"kind": "widget"}\n')
    back = store.read()
    assert back == _events()


def test_sqlite_round_trip(tmp_path):
    store = SqliteStore(tmp_path / "e.db")
    store.append(_events())
    assert store.read() == _events()


def test_open_store_picks_backend(tmp_path):
    assert isinstance(open_store(tmp_path / "a.jsonl"), JsonlStore)
    assert isinstance(open_store(tmp_path / "a.db"), SqliteStore)
    assert open_store(tmp_path / "a.jsonl") is open_store(tmp_path / "a.jsonl")


def test_summarize():
    s = summarize(_events())
    assert s["sessions"] == 2 and s["visitors"] == 2
    assert s["pages"] == [
        {"page": "/", "pageviews": 1, "sessions": 1},
        {"page": "/two", "pageviews": 1, "sessions": 1},
    ]
    assert [w["label"] for w in s["widgets"]] == ["Go", "Pick"]
    assert s["widgets"][1]["top values"] == "dog (1)"
    assert s["custom"] == [{"event": "report", "count": 1}]
    assert s["avg_session_seconds"] == (360 + 1) / 2
    assert json.dumps(s)
