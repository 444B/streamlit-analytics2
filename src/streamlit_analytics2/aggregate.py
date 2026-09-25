"""Derive the 0.10-shaped counters and the dashboard summaries from events."""

from __future__ import annotations

import datetime
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

from . import events as ev
from .capture import COUNT_ONLY_TYPES


def widget_name(label: str, key: Optional[str], widget_id: str) -> str:
    """The key used in the legacy ``data["widgets"]`` dict."""
    if label:
        return label
    if key:
        return key
    return widget_id[-8:]


def apply_widget(
    agg: Dict[str, Any], widget_type: str, name: str, value: Optional[str]
) -> None:
    """Increment one legacy counter: int for count-only widgets, dict otherwise."""
    widgets = agg.setdefault("widgets", {})
    if widget_type in COUNT_ONLY_TYPES or value is None:
        current = widgets.get(name, 0)
        widgets[name] = (current if isinstance(current, int) else 0) + 1
        return
    current = widgets.get(name)
    if not isinstance(current, dict):
        current = {}
        widgets[name] = current
    current[value] = current.get(value, 0) + 1


def summarize(events: List[ev.Event]) -> Dict[str, Any]:
    """Aggregate an event list for the dashboard. Pure function."""
    sessions: Dict[str, List[datetime.datetime]] = defaultdict(list)
    visitors_by_day: Dict[str, set] = defaultdict(set)
    pages: Counter = Counter()
    page_sessions: Dict[str, set] = defaultdict(set)
    widgets: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    custom: Counter = Counter()
    for e in events:
        ts = e.parsed_ts()
        sessions[e.session].append(ts)
        if e.visitor:
            visitors_by_day[ts.date().isoformat()].add(e.visitor)
        if e.kind == ev.PAGEVIEW:
            page = e.page or "/"
            pages[page] += 1
            page_sessions[page].add(e.session)
        elif e.kind == ev.WIDGET:
            k = (e.widget_type or "", e.name or "", e.key or "")
            w = widgets.setdefault(
                k,
                {
                    "type": e.widget_type,
                    "label": e.name,
                    "key": e.key,
                    "page": e.page,
                    "changes": 0,
                    "sessions": set(),
                    "values": Counter(),
                },
            )
            w["changes"] += 1
            w["sessions"].add(e.session)
            if e.value is not None:
                w["values"][e.value] += 1
        elif e.kind == ev.CUSTOM:
            custom[e.name or ""] += 1
    durations = [
        (max(t) - min(t)).total_seconds() for t in sessions.values() if len(t) > 1
    ]
    widget_rows = []
    for w in widgets.values():
        top = ", ".join(f"{v} ({n})" for v, n in w["values"].most_common(3))
        widget_rows.append(
            {
                "type": w["type"],
                "label": w["label"],
                "key": w["key"] or "",
                "page": w["page"] or "",
                "changes": w["changes"],
                "sessions": len(w["sessions"]),
                "top values": top,
            }
        )
    widget_rows.sort(key=lambda r: -r["changes"])
    return {
        "events": len(events),
        "sessions": len(sessions),
        "visitors": sum(len(v) for v in visitors_by_day.values()),
        "avg_session_seconds": (sum(durations) / len(durations)) if durations else 0,
        "pages": [
            {"page": p, "pageviews": n, "sessions": len(page_sessions[p])}
            for p, n in pages.most_common()
        ],
        "widgets": widget_rows,
        "custom": [{"event": n, "count": c} for n, c in custom.most_common()],
    }
