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
    import datetime

    now = datetime.datetime(2026, 9, 25, 11, 2, tzinfo=datetime.timezone.utc)
    s = summarize(_events(), now=now)
    assert s["views"] == 2 and s["visits"] == 2 and s["visitors"] == 2
    assert s["pages"] == [
        {"page": "/", "views": 1, "visits": 1},
        {"page": "/two", "views": 1, "visits": 1},
    ]
    assert [w["label"] for w in s["widgets"]] == ["Go", "Pick"]
    assert s["widgets"][1]["top values"] == "dog (1)"
    assert s["custom"] == [{"event": "report", "count": 1, "visits": 1}]
    assert s["bounce_rate"] == 0  # s1 interacted, s2 fired a custom event
    assert s["active_now"] == 1  # s2 ran at 11:00, now is 11:02
    assert s["series_day"] == [{"when": "2026-09-25", "views": 2, "visitors": 2}]
    assert len(s["series_hour"]) == 2
    assert s["load"] == [{"weekday": 4, "hour": 10, "runs": 0}] or s["load"] == []
    assert json.dumps(s)


def test_summarize_filters_and_timezone():
    import datetime

    since = datetime.datetime(2026, 9, 25, 10, 30, tzinfo=datetime.timezone.utc)
    s = summarize(_events(), since=since, tz_offset_minutes=-60)
    assert s["visits"] == 1 and s["pages"][0]["page"] == "/two"
    assert s["series_hour"][0]["when"] == "2026-09-25 12:00"  # UTC+1 viewer
    s = summarize(_events(), page="/")
    assert s["visits"] == 1 and s["custom"] == []
    assert s["browsers"] == [] and s["timezones"] == []
