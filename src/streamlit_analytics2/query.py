"""Read-only SQL over a SQLite event log, for the dashboard's query tab.

Defence in depth, because the query text comes from whoever can open the
dashboard: the file is opened read-only, the connection is ``query_only``, an
authorizer allows only SELECT/READ/functions (no ATTACH, PRAGMA, writes or
schema changes), one statement per call, a step budget aborts runaway
queries, and rows are capped.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, List, Sequence, Tuple, Union

MAX_ROWS = 500
_ALLOWED = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    getattr(sqlite3, "SQLITE_RECURSIVE", 33),
}
_COMMENT = re.compile(r"(--[^\n]*|/\*.*?\*/)", re.S)

EXAMPLES = [
    (
        "Views per day, last 30 days",
        "SELECT substr(ts, 1, 10) AS day, count(*) AS views\n"
        "FROM events\nWHERE kind = 'pageview' AND ts >= date('now', '-30 days')\n"
        "GROUP BY day ORDER BY day",
    ),
    (
        "Top pages",
        "SELECT page, count(*) AS views, count(DISTINCT session) AS visits\n"
        "FROM events WHERE kind = 'pageview'\n"
        "GROUP BY page ORDER BY views DESC",
    ),
    (
        "Most used widgets",
        "SELECT widget_type, name, key, count(*) AS changes\n"
        "FROM events WHERE kind = 'widget'\n"
        "GROUP BY widget_type, name, key ORDER BY changes DESC LIMIT 20",
    ),
    (
        "Option popularity for one selectbox",
        "SELECT value, count(*) AS n FROM events\n"
        "WHERE kind = 'widget' AND name = 'Select your favorite'\n"
        "GROUP BY value ORDER BY n DESC",
    ),
    (
        "Visit length in seconds",
        "SELECT session, min(ts) AS started,\n"
        "       (julianday(max(ts)) - julianday(min(ts))) * 86400 AS seconds,\n"
        "       sum(kind = 'widget') AS interactions\n"
        "FROM events GROUP BY session ORDER BY started DESC LIMIT 50",
    ),
    (
        "Browsers and devices (from the session row's JSON props)",
        "SELECT json_extract(props, '$.browser') AS browser,\n"
        "       json_extract(props, '$.device') AS device, count(*) AS visits\n"
        "FROM events WHERE kind = 'session'\n"
        "GROUP BY browser, device ORDER BY visits DESC",
    ),
    (
        "Custom events per day",
        "SELECT substr(ts, 1, 10) AS day, name, count(*) AS n\n"
        "FROM events WHERE kind = 'custom' GROUP BY day, name ORDER BY day DESC",
    ),
    (
        "Busiest hours (UTC)",
        "SELECT substr(ts, 12, 2) AS hour_utc, count(DISTINCT session) AS visits\n"
        "FROM events WHERE kind = 'run' GROUP BY hour_utc ORDER BY visits DESC",
    ),
]

SCHEMA = (
    "events(id, ts, kind, session, visitor, page, name, widget_id, "
    "widget_type, key, value, props)\n"
    "kind: session | pageview | run | widget | custom. props is JSON on "
    "session and custom rows."
)


class QueryError(ValueError):
    pass


def _authorizer(action: int, *_: Any) -> int:
    return sqlite3.SQLITE_OK if action in _ALLOWED else sqlite3.SQLITE_DENY


def run_query(
    path: Union[str, Path],
    sql: str,
    limit: int = MAX_ROWS,
    step_budget: int = 2_000_000,
) -> Tuple[List[str], List[Sequence[Any]]]:
    """Run one read-only SELECT and return (columns, rows)."""
    text = _COMMENT.sub("", sql).strip().rstrip(";").strip()
    if not text:
        raise QueryError("Empty query.")
    if ";" in text:
        raise QueryError("One statement at a time.")
    if not re.match(r"(?is)^(select|with)\b", text):
        raise QueryError("Only SELECT (or WITH ... SELECT) queries are allowed.")
    if not Path(path).exists():
        raise QueryError(f"No database at {path}.")
    uri = f"file:{Path(path).resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    try:
        conn.execute("PRAGMA query_only = 1")
        conn.set_authorizer(_authorizer)
        steps = {"n": 0}

        def _budget() -> int:
            steps["n"] += 1
            return 1 if steps["n"] > step_budget else 0

        conn.set_progress_handler(_budget, 1000)
        try:
            cur = conn.execute(text)
            rows = cur.fetchmany(limit)
        except sqlite3.DatabaseError as exc:
            msg = str(exc)
            if "not authorized" in msg or "prohibited" in msg:
                raise QueryError("That statement is not allowed here.") from exc
            if "interrupted" in msg:
                raise QueryError(
                    "Query aborted: too much work. Add a WHERE or LIMIT."
                ) from exc
            raise QueryError(msg) from exc
        columns = [d[0] for d in cur.description] if cur.description else []
        return columns, rows
    finally:
        conn.close()
