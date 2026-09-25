"""Event records: the one thing every backend stores and every view reads."""

from __future__ import annotations

import dataclasses
import datetime
from typing import Any, Dict, Optional

# Event kinds
SESSION = "session"  # first run of a browser session
PAGEVIEW = "pageview"  # session landed on a page (first run, or page changed)
RUN = "run"  # every script run (a rerun after any interaction)
WIDGET = "widget"  # a widget value changed because the user acted on it
CUSTOM = "custom"  # sa2.event(...) from app code

_FIELDS: Optional[frozenset] = None


def now_iso() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclasses.dataclass(frozen=True)
class Event:
    ts: str
    kind: str
    session: str
    visitor: Optional[str] = None
    page: Optional[str] = None
    name: Optional[str] = None  # widget label or custom event name
    widget_id: Optional[str] = None
    widget_type: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    props: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in dataclasses.asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Event":
        global _FIELDS
        if _FIELDS is None:
            _FIELDS = frozenset(f.name for f in dataclasses.fields(cls))
        return cls(**{k: v for k, v in d.items() if k in _FIELDS})

    def parsed_ts(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
