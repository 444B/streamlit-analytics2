"""Read-only SQL over a SQLite event log, for the dashboard's query tab.

Defence in depth, because the query text comes from whoever can open the
dashboard: the file is opened read-only, the connection is ``query_only``, an
authorizer allows only SELECT/READ/functions (no ATTACH, PRAGMA, writes or
schema changes), one statement per call, a step budget aborts runaway
queries, and rows are capped.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple, Union

MAX_ROWS = 500
TIMEOUT_SECONDS = 2.0
HEAP_LIMIT_BYTES = 64 * 1024 * 1024
_ALLOWED = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    getattr(sqlite3, "SQLITE_RECURSIVE", 33),
}
# SQL functions that allocate at will, touch the filesystem or load code.
_DENIED_FUNCTIONS = frozenset(
    {
        "zeroblob",
        "randomblob",
        "load_extension",
        "readfile",
        "writefile",
        "edit",
        "fsdir",
        "sqlar_compress",
        "sqlar_uncompress",
        "eval",
    }
)

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


def _authorizer(action: int, arg1: Any, arg2: Any, *_: Any) -> int:
    if action not in _ALLOWED:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION:
        name = (arg2 or arg1 or "").lower()
        if name in _DENIED_FUNCTIONS:
            return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def strip_comments(sql: str) -> str:
    """Remove -- and /* */ comments in one linear pass, respecting quotes."""
    out: List[str] = []
    i, n, quote = 0, len(sql), None
    while i < n:
        c = sql[i]
        if quote:
            out.append(c)
            if c == quote:
                quote = None
            i += 1
        elif c in ("'", '"', "`"):
            quote = c
            out.append(c)
            i += 1
        elif c == "-" and sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j < 0 else j
        elif c == "/" and sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _is_select(text: str) -> bool:
    head = text[:6].lower()
    return head == "select" or (
        head[:4] == "with" and (len(text) == 4 or not text[4].isalnum())
    )


def run_query(
    path: Union[str, Path],
    sql: str,
    limit: int = MAX_ROWS,
    timeout_seconds: Optional[float] = TIMEOUT_SECONDS,
) -> Tuple[List[str], List[Sequence[Any]]]:
    """Run one read-only SELECT from an untrusted string; return (columns, rows).

    The string is executed on purpose: this is the dashboard's query box.
    Safety comes from the connection, not from parsing the text: read-only
    file, ``query_only``, an authorizer that allows SELECT and reads only
    (no ATTACH, PRAGMA, writes, schema, extension loading or blob allocation
    functions), a heap limit, a wall-clock deadline and a row cap.
    """
    text = strip_comments(sql).strip().rstrip(";").strip()
    if not text:
        raise QueryError("Empty query.")
    if ";" in text:
        raise QueryError("One statement at a time.")
    if not _is_select(text):
        raise QueryError("Only SELECT (or WITH ... SELECT) queries are allowed.")
    if not Path(path).exists():
        raise QueryError(f"No database at {path}.")
    uri = f"file:{Path(path).resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    try:
        conn.execute("PRAGMA query_only = 1")
        for pragma in ("hard_heap_limit", "soft_heap_limit"):
            try:
                conn.execute(f"PRAGMA {pragma} = {HEAP_LIMIT_BYTES}")
            except sqlite3.DatabaseError:  # older SQLite without the pragma
                pass
        for limit_name, value in (
            ("SQLITE_LIMIT_LENGTH", 10_000_000),
            ("SQLITE_LIMIT_SQL_LENGTH", 100_000),
            ("SQLITE_LIMIT_COMPOUND_SELECT", 50),
        ):
            try:  # Python 3.11+
                conn.setlimit(getattr(sqlite3, limit_name), value)
            except (AttributeError, sqlite3.Error):
                pass
        conn.set_authorizer(_authorizer)
        if timeout_seconds is not None:
            deadline = time.monotonic() + timeout_seconds

            def _check_deadline() -> int:
                return 1 if time.monotonic() > deadline else 0

            conn.set_progress_handler(_check_deadline, 1000)
        try:
            cur = conn.execute(text)
            rows = cur.fetchmany(limit)
        except sqlite3.DatabaseError as exc:
            msg = str(exc)
            if "not authorized" in msg or "prohibited" in msg:
                raise QueryError("That statement is not allowed here.") from exc
            if "interrupted" in msg:
                raise QueryError(
                    "Query aborted: it ran longer than "
                    f"{timeout_seconds}s. Add a WHERE or LIMIT."
                ) from exc
            raise QueryError(msg) from exc
        columns = [d[0] for d in cur.description] if cur.description else []
        return columns, rows
    finally:
        conn.close()
