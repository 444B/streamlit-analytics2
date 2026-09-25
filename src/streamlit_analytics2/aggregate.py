"""Derive the 0.10-shaped counters and the dashboard summaries from events."""

from __future__ import annotations

import datetime
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

from . import events as ev
from .capture import COUNT_ONLY_TYPES

ACTIVE_WINDOW = datetime.timedelta(minutes=5)


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


def _top(counter: Counter, key: str, limit: int = 10) -> List[Dict[str, Any]]:
    total = sum(counter.values()) or 1
    return [
        {key: name, "visits": n, "share": round(100 * n / total)}
        for name, n in counter.most_common(limit)
    ]


def summarize(
    events: List[ev.Event],
    since: Optional[datetime.datetime] = None,
    page: Optional[str] = None,
    tz_offset_minutes: int = 0,
    now: Optional[datetime.datetime] = None,
) -> Dict[str, Any]:
    """Umami-style summary of an event list. Pure function.

    ``since`` filters by event time (UTC). ``page`` keeps only sessions that
    viewed that page. ``tz_offset_minutes`` is the viewer's offset from UTC
    (as ``st.context.timezone_offset`` reports it, positive west of UTC).
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    shift = datetime.timedelta(minutes=-tz_offset_minutes)

    # Session facts come from the session event even if it is outside the range.
    session_props: Dict[str, Dict[str, Any]] = {}
    for e in events:
        if e.kind == ev.SESSION:
            session_props[e.session] = e.props or {}

    if since is not None:
        events = [e for e in events if e.parsed_ts() >= since]
    if page:
        # Only what happened on that page; session facts for visits that saw it.
        keep = {e.session for e in events if e.kind == ev.PAGEVIEW and e.page == page}
        events = [
            e
            for e in events
            if (e.kind == ev.SESSION and e.session in keep) or e.page == page
        ]

    runs: Dict[str, List[datetime.datetime]] = defaultdict(list)
    interactions: Counter = Counter()
    visitors_by_day: Dict[str, set] = defaultdict(set)
    views_by_bucket_day: Counter = Counter()
    visitors_by_bucket_day: Dict[str, set] = defaultdict(set)
    views_by_bucket_hour: Counter = Counter()
    visitors_by_bucket_hour: Dict[str, set] = defaultdict(set)
    page_views_day: Counter = Counter()  # (day, page) -> views
    page_views_hour: Counter = Counter()  # (hour, page) -> views
    load: Counter = Counter()  # (weekday, hour) -> runs
    sessions_by_hour: Dict[str, set] = defaultdict(set)
    pages: Counter = Counter()
    page_sessions: Dict[str, set] = defaultdict(set)
    widgets: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    custom: Counter = Counter()
    custom_sessions: Dict[str, set] = defaultdict(set)
    session_pages: Dict[str, List[str]] = defaultdict(list)
    last_seen: Dict[str, datetime.datetime] = {}

    for e in events:
        ts = e.parsed_ts()
        local = ts + shift
        last_seen[e.session] = max(ts, last_seen.get(e.session, ts))
        if e.kind == ev.RUN:
            runs[e.session].append(ts)
            load[(local.weekday(), local.hour)] += 1
            sessions_by_hour[local.strftime("%Y-%m-%d %H")].add(e.session)
        if e.visitor:
            visitors_by_day[local.date().isoformat()].add(e.visitor)
        if e.kind == ev.PAGEVIEW:
            p = e.page or "/"
            pages[p] += 1
            page_sessions[p].add(e.session)
            session_pages[e.session].append(p)
            day = local.date().isoformat()
            hour = local.strftime("%Y-%m-%d %H:00")
            views_by_bucket_day[day] += 1
            views_by_bucket_hour[hour] += 1
            page_views_day[(day, p)] += 1
            page_views_hour[(hour, p)] += 1
            if e.visitor:
                visitors_by_bucket_day[day].add(e.visitor)
                visitors_by_bucket_hour[hour].add(e.visitor)
        elif e.kind == ev.WIDGET:
            interactions[e.session] += 1
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
            interactions[e.session] += 1
            custom[e.name or ""] += 1
            custom_sessions[e.name or ""].add(e.session)

    session_ids = set(runs) | set(interactions)
    durations = {
        s: (max(t) - min(t)).total_seconds() for s, t in runs.items() if len(t) > 1
    }
    bounced = [
        s for s in session_ids if len(runs.get(s, [])) <= 1 and interactions[s] == 0
    ]
    views = sum(pages.values())
    active_now = sum(1 for s, t in last_seen.items() if now - t <= ACTIVE_WINDOW)

    def facet(prop: str) -> Counter:
        c: Counter = Counter()
        for s in session_ids:
            v = session_props.get(s, {}).get(prop)
            if v:
                c[str(v)] += 1
        return c

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

    recent = []
    for s in sorted(session_ids, key=lambda s: last_seen.get(s, now), reverse=True)[
        :25
    ]:
        t = runs.get(s) or []
        props = session_props.get(s, {})
        recent.append(
            {
                "started": (min(t) + shift).strftime("%Y-%m-%d %H:%M") if t else "",
                "duration": _hms(durations.get(s, 0)),
                "pages": " > ".join(session_pages.get(s, [])[:6]),
                "runs": len(t),
                "interactions": interactions[s],
                "browser": props.get("browser", ""),
                "device": props.get("device", ""),
                "timezone": props.get("timezone", ""),
            }
        )

    days = sorted(set(views_by_bucket_day) | set(visitors_by_bucket_day))
    hours = sorted(set(views_by_bucket_hour) | set(visitors_by_bucket_hour))
    peak_hour = max(sessions_by_hour.items(), key=lambda kv: len(kv[1]), default=None)

    return {
        "events": len(events),
        "views": views,
        "visits": len(session_ids),
        "visitors": sum(len(v) for v in visitors_by_day.values()),
        "bounce_rate": (
            round(100 * len(bounced) / len(session_ids)) if session_ids else 0
        ),
        "avg_visit_seconds": (
            (sum(durations.values()) / len(durations)) if durations else 0
        ),
        "active_now": active_now,
        "series_day": [
            {
                "when": d,
                "views": views_by_bucket_day[d],
                "visitors": len(visitors_by_bucket_day[d]),
            }
            for d in days
        ],
        "series_hour": [
            {
                "when": h,
                "views": views_by_bucket_hour[h],
                "visitors": len(visitors_by_bucket_hour[h]),
            }
            for h in hours
        ],
        # Dense: every page has a point in every bucket, or stacked areas
        # interpolate across the gaps and draw through each other.
        "series_day_pages": [
            {"when": d, "page": pg, "views": page_views_day.get((d, pg), 0)}
            for d in days
            for pg in pages
        ],
        "series_hour_pages": [
            {"when": h, "page": pg, "views": page_views_hour.get((h, pg), 0)}
            for h in hours
            for pg in pages
        ],
        "load": [
            {"weekday": wd, "hour": h, "runs": n} for (wd, h), n in sorted(load.items())
        ],
        "peak": (
            {"hour": peak_hour[0], "sessions": len(peak_hour[1])} if peak_hour else None
        ),
        "pages": [
            {"page": p, "views": n, "visits": len(page_sessions[p])}
            for p, n in pages.most_common()
        ],
        "browsers": _top(facet("browser"), "browser"),
        "os": _top(facet("os"), "os"),
        "devices": _top(facet("device"), "device"),
        "languages": _top(facet("locale"), "language"),
        "timezones": _top(facet("timezone"), "timezone"),
        "themes": _top(facet("theme"), "theme"),
        "utm_sources": _top(facet("utm_source"), "source"),
        "utm_campaigns": _top(facet("utm_campaign"), "campaign"),
        "widgets": widget_rows,
        "custom": [
            {"event": n, "count": c, "visits": len(custom_sessions[n])}
            for n, c in custom.most_common()
        ],
        "sessions": recent,
    }


def _hms(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02}:{m:02}:{s:02}"
