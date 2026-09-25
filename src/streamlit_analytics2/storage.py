"""Event stores. JSONL by default, SQLite as the second built-in backend.

A store only needs ``append`` and ``read``; pass your own object with those
two methods to ``track(store=...)`` for any other backend.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol, Union

from .events import Event

log = logging.getLogger("streamlit_analytics2")

PathLike = Union[str, Path]


class Store(Protocol):
    def append(self, events: Iterable[Event]) -> None: ...

    def read(self) -> List[Event]: ...


class MemoryStore:
    """Process memory only. The default when nothing is persisted."""

    def __init__(self) -> None:
        self._events: List[Event] = []
        self._lock = threading.Lock()

    def append(self, events: Iterable[Event]) -> None:
        with self._lock:
            self._events.extend(events)

    def read(self) -> List[Event]:
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


class JsonlStore:
    """One JSON object per line, appended. Human-readable and easy to ship."""

    def __init__(self, path: PathLike) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def append(self, events: Iterable[Event]) -> None:
        lines = [json.dumps(e.to_dict(), ensure_ascii=False) for e in events]
        if not lines:
            return
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

    def read(self) -> List[Event]:
        if not self.path.exists():
            return []
        out: List[Event] = []
        with self._lock, self.path.open("r", encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(Event.from_dict(json.loads(line)))
                except (ValueError, TypeError):
                    log.warning("%s line %d is not an event, skipped", self.path, n)
        return out


class SqliteStore:
    """A single ``events`` table. Safe for many sessions in one process."""

    _COLS = (
        "ts",
        "kind",
        "session",
        "visitor",
        "page",
        "name",
        "widget_id",
        "widget_type",
        "key",
        "value",
        "props",
    )

    def __init__(self, path: PathLike) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "id INTEGER PRIMARY KEY, ts TEXT NOT NULL, kind TEXT NOT NULL, "
                "session TEXT NOT NULL, visitor TEXT, page TEXT, name TEXT, "
                "widget_id TEXT, widget_type TEXT, key TEXT, value TEXT, props TEXT)"
            )
            self._conn.execute("CREATE INDEX IF NOT EXISTS events_ts ON events(ts)")
            self._conn.commit()

    def append(self, events: Iterable[Event]) -> None:
        rows = []
        for e in events:
            d = e.to_dict()
            rows.append(
                tuple(
                    json.dumps(d.get(c)) if c == "props" and d.get(c) else d.get(c)
                    for c in self._COLS
                )
            )
        if not rows:
            return
        with self._lock:
            self._conn.executemany(
                f"INSERT INTO events ({', '.join(self._COLS)}) VALUES "  # nosec B608: column names are a constant tuple
                f"({', '.join('?' * len(self._COLS))})",
                rows,
            )
            self._conn.commit()

    def read(self) -> List[Event]:
        with self._lock:
            cur = self._conn.execute(
                f"SELECT {', '.join(self._COLS)} FROM events ORDER BY id"  # nosec B608: constant columns
            )
            rows = cur.fetchall()
        out = []
        for row in rows:
            d: Dict[str, Any] = dict(zip(self._COLS, row))
            if d.get("props"):
                d["props"] = json.loads(d["props"])
            out.append(Event.from_dict({k: v for k, v in d.items() if v is not None}))
        return out


_open: Dict[str, Store] = {}
_open_lock = threading.Lock()


def open_store(path: PathLike) -> Store:
    """JSONL unless the suffix says SQLite. One store object per path."""
    p = Path(path)
    key = str(p.resolve())
    with _open_lock:
        store = _open.get(key)
        if store is None:
            if p.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
                store = SqliteStore(p)
            else:
                store = JsonlStore(p)
            _open[key] = store
        return store


def events_path_for(save_to_json: Optional[PathLike]) -> Optional[Path]:
    """Sidecar event log next to a legacy ``save_to_json`` file."""
    if save_to_json is None:
        return None
    p = Path(save_to_json)
    return p.with_name(p.stem + ".events.jsonl")
