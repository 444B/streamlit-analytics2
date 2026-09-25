import pytest

from streamlit_analytics2.events import Event
from streamlit_analytics2.query import EXAMPLES, QueryError, run_query
from streamlit_analytics2.storage import SqliteStore


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "e.db"
    SqliteStore(path).append(
        [
            Event(
                "2026-09-25T10:00:00Z",
                "session",
                "s1",
                page="/",
                props={"browser": "Chrome", "device": "Desktop"},
            ),
            Event("2026-09-25T10:00:00Z", "pageview", "s1", page="/"),
            Event("2026-09-25T10:00:00Z", "run", "s1", page="/"),
            Event(
                "2026-09-25T10:01:00Z",
                "widget",
                "s1",
                page="/",
                name="Select your favorite",
                widget_type="selectbox",
                value="dog",
            ),
            Event(
                "2026-09-25T10:02:00Z",
                "custom",
                "s1",
                page="/",
                name="report",
                props={"rows": 1},
            ),
        ]
    )
    return path


def test_select_works_and_examples_run(db):
    cols, rows = run_query(
        db, "SELECT kind, count(*) FROM events GROUP BY kind ORDER BY kind"
    )
    assert cols == ["kind", "count(*)"]
    assert dict(rows) == {
        "custom": 1,
        "pageview": 1,
        "run": 1,
        "session": 1,
        "widget": 1,
    }
    for _, sql in EXAMPLES:
        run_query(db, sql)


def test_writes_and_escapes_are_refused(db):
    for bad in [
        "DELETE FROM events",
        "INSERT INTO events (ts, kind, session) VALUES ('x', 'y', 'z')",
        "DROP TABLE events",
        "PRAGMA journal_mode",
        "ATTACH DATABASE '/etc/passwd' AS x",
        "SELECT 1; DELETE FROM events",
        "-- sneaky\nUPDATE events SET kind = 'x'",
        "",
    ]:
        with pytest.raises(QueryError):
            run_query(db, bad)
    with pytest.raises(QueryError):
        run_query(
            db,
            "WITH x AS (SELECT 1) INSERT INTO events (ts, kind, session) SELECT 'a', 'b', 'c'",
        )
    with pytest.raises(QueryError):
        run_query(db, "SELECT * FROM events; ATTACH DATABASE 'x' AS y")
    assert run_query(db, "SELECT count(*) FROM events")[1] == [(5,)]


def test_row_cap_and_step_budget(db):
    cols, rows = run_query(db, "SELECT * FROM events", limit=2)
    assert len(rows) == 2
    with pytest.raises(QueryError, match="ran longer"):
        run_query(
            db,
            "WITH RECURSIVE c(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM c) SELECT count(*) FROM c",
            timeout_seconds=0.2,
        )


def test_dangerous_functions_and_comments(db):
    from streamlit_analytics2.query import strip_comments

    for bad in [
        "SELECT zeroblob(1000000000)",
        "SELECT load_extension('x')",
        "SELECT randomblob(10)",
    ]:
        with pytest.raises(QueryError):
            run_query(db, bad)
    assert (
        strip_comments("SELECT 1 -- x\n/* y */ FROM events")
        == "SELECT 1 \n  FROM events"
    )
    assert (
        strip_comments("SELECT '--not a comment' FROM events")
        == "SELECT '--not a comment' FROM events"
    )
    assert strip_comments("SELECT /* unterminated") == "SELECT  "
    cols, rows = run_query(db, "/* leading */ SELECT count(*) FROM events -- trailing")
    assert rows == [(5,)]
    with pytest.raises(QueryError):
        run_query(db, "SELECTION 1")
    with pytest.raises(QueryError):
        run_query(db, "WITHDRAW 1")


def test_missing_db(tmp_path):
    with pytest.raises(QueryError, match="No database"):
        run_query(tmp_path / "nope.db", "SELECT 1")
