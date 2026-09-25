"""Seed a DEV event log with months of made-up traffic. Never run it against
a real app's log: the numbers are fiction and they only append.

    uv run python examples/dev/seed.py /data/sa2_events.db --months 6 --yes

Synthetic sessions follow a weekday and office-hours pattern with a slow
growth trend, a few pages, a spread of browsers and regions, and widget use.
Delete the file to start over. Only the dev app in examples/dev uses this.
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
import uuid

from streamlit_analytics2.events import (
    CUSTOM,
    PAGEVIEW,
    RUN,
    SESSION,
    WIDGET,
    Event,
)
from streamlit_analytics2.storage import open_store

PAGES = ["/app", "/second_page", "/reports"]
BROWSERS = [("Chrome", 55), ("Safari", 20), ("Firefox", 12), ("Edge", 10), ("Other", 3)]
OS = [("Windows", 40), ("macOS", 30), ("iOS", 12), ("Android", 10), ("Linux", 8)]
DEVICES = [("Desktop", 70), ("Mobile", 25), ("Tablet", 5)]
LOCALES = [
    ("en-IE", 35),
    ("en-US", 30),
    ("en-GB", 15),
    ("de-DE", 8),
    ("pt-BR", 7),
    ("ja-JP", 5),
]
TZS = [
    ("Europe/Dublin", 35),
    ("America/New_York", 20),
    ("Europe/London", 15),
    ("Europe/Berlin", 10),
    ("America/Sao_Paulo", 10),
    ("Asia/Tokyo", 10),
]
UTM = [(None, 80), ("newsletter", 8), ("linkedin", 7), ("github", 5)]
WIDGETS = [
    ("selectbox", "Select your favorite", None, ["cat", "dog", "flower"]),
    ("button", "Click me", None, None),
    ("button", "Column button", None, None),
    ("toggle", "Column toggle", None, None),
    ("slider", "Pick a number", None, [str(i) for i in range(11)]),
    ("radio", "Rating", None, ["good", "ok", "bad"]),
    ("text_input", "Write your name", None, ["<text>"]),
    ("button", "Same label", "second", None),
    ("multiselect", "Tags", None, ["a", "b", "c"]),
]


def pick(weighted):
    names, weights = zip(*weighted)
    return random.choices(names, weights=weights, k=1)[0]


def hour_weight(h: int) -> float:
    return {
        **{h: 0.15 for h in range(0, 7)},
        7: 0.5,
        8: 1.0,
        9: 1.6,
        10: 1.9,
        11: 1.8,
        12: 1.3,
        13: 1.5,
        14: 1.8,
        15: 1.7,
        16: 1.4,
        17: 1.0,
        18: 0.7,
        19: 0.6,
        20: 0.6,
        21: 0.5,
        22: 0.35,
        23: 0.2,
    }[h]


def iso(t: dt.datetime) -> str:
    return t.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def session_events(start: dt.datetime) -> list[Event]:
    sid = uuid.uuid4().hex
    visitor = uuid.uuid4().hex[:16]
    tz = pick(TZS)
    props = {
        "browser": pick(BROWSERS),
        "os": pick(OS),
        "device": pick(DEVICES),
        "locale": pick(LOCALES),
        "timezone": tz,
        "theme": random.choice(["light", "dark"]),
    }
    src = pick(UTM)
    if src:
        props["utm_source"] = src
        props["utm_campaign"] = "launch" if random.random() < 0.6 else "docs"
    page = "/app" if random.random() < 0.7 else random.choice(PAGES)
    t = start
    out = [
        Event(iso(t), SESSION, sid, visitor, page, props=props),
        Event(iso(t), PAGEVIEW, sid, visitor, page),
        Event(iso(t), RUN, sid, visitor, page),
    ]
    if random.random() < 0.35:  # bounce
        return out
    for _ in range(random.randint(1, 12)):
        t += dt.timedelta(seconds=random.randint(5, 120))
        if random.random() < 0.15:
            page = random.choice(PAGES)
            out.append(Event(iso(t), PAGEVIEW, sid, visitor, page))
        out.append(Event(iso(t), RUN, sid, visitor, page))
        wtype, label, key, values = random.choice(WIDGETS)
        out.append(
            Event(
                iso(t),
                WIDGET,
                sid,
                visitor,
                page,
                name=label,
                widget_id=f"$$ID-{abs(hash(label)) % 10**8}-{key}",
                widget_type=wtype,
                key=key,
                value=random.choice(values) if values else None,
            )
        )
        if random.random() < 0.08:
            out.append(
                Event(
                    iso(t),
                    CUSTOM,
                    sid,
                    visitor,
                    page,
                    name="report generated",
                    props={"rows": random.randint(1, 500)},
                )
            )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--months", type=int, default=6)
    ap.add_argument(
        "--per-day", type=int, default=18, help="average sessions per weekday now"
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--yes", action="store_true", help="confirm this is a dev log, not a real app's"
    )
    args = ap.parse_args()
    if not args.yes:
        ap.error("refusing without --yes: this writes fake traffic into the log")
    random.seed(args.seed)
    store = open_store(args.path)
    now = dt.datetime.now(dt.timezone.utc)
    start = now - dt.timedelta(days=30 * args.months)
    events: list[Event] = []
    day = start
    while day < now:
        age = (now - day).days
        growth = 0.4 + 0.6 * (1 - age / max(1, 30 * args.months))  # slow ramp up
        weekday = day.weekday()
        base = args.per_day * growth * (1.0 if weekday < 5 else 0.35)
        n = max(0, int(random.gauss(base, base * 0.3)))
        for _ in range(n):
            h = pick([(h, hour_weight(h)) for h in range(24)])
            t = day.replace(
                hour=h, minute=random.randint(0, 59), second=random.randint(0, 59)
            )
            if t < now:
                events.extend(session_events(t))
        day += dt.timedelta(days=1)
    events.sort(key=lambda e: e.ts)
    store.append(events)
    sessions = sum(1 for e in events if e.kind == SESSION)
    print(f"appended {len(events)} events, {sessions} sessions, to {args.path}")


if __name__ == "__main__":
    main()
