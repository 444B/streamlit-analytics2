"""The ``?analytics=on`` dashboard: Umami-style, read-only, privacy-safe."""

from __future__ import annotations

import datetime
from typing import Any, Callable, Dict, List, Optional

import altair as alt
import pandas as pd
import streamlit as st

from . import aggregate, query, utils
from .state import data  # noqa: F401
from .storage import SqliteStore

RANGES = {"Today": 1, "7 days": 7, "30 days": 30, "90 days": 90, "All time": None}
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Categorical slots in a fixed, colour-vision-safe order; the dark column is the
# same hues stepped for a dark surface. Sequential ramps are one hue.
PALETTE = {
    "light": {
        "series": [
            "#2a78d6",
            "#eb6834",
            "#1baf7a",
            "#eda100",
            "#e87ba4",
            "#008300",
            "#4a3aa7",
            "#e34948",
        ],
        "seq": [
            "#cde2fb",
            "#9ec5f4",
            "#6da7ec",
            "#3987e5",
            "#256abf",
            "#184f95",
            "#0d366b",
        ],
        "muted": "#52514e",
    },
    "dark": {
        "series": [
            "#3987e5",
            "#d95926",
            "#199e70",
            "#c98500",
            "#d55181",
            "#008300",
            "#9085e9",
            "#e66767",
        ],
        "seq": [
            "#184f95",
            "#256abf",
            "#3987e5",
            "#5598e7",
            "#6da7ec",
            "#9ec5f4",
            "#cde2fb",
        ],
        "muted": "#c3c2b7",
    },
}


def _theme() -> Dict[str, Any]:
    try:
        kind = st.context.theme.type if st.context.theme else None
    except Exception:
        kind = None
    return PALETTE["dark" if kind == "dark" else "light"]


def show_results(
    data: Dict[str, Any],  # noqa: F811
    reset_callback: Callable[[], None],
    unsafe_password: Optional[str] = None,
    store: Any = None,
) -> None:
    """Show analytics results in streamlit, asking for password if given."""
    st.title("Analytics")
    st.caption(
        "Powered by [streamlit-analytics2]"
        "(https://github.com/444B/streamlit-analytics2). Remove `?analytics=on` "
        "from the URL to leave. Your own visits with the dashboard open are "
        "not counted."
    )
    if unsafe_password is not None:
        password_input = st.text_input("Password", type="password")
        if password_input != unsafe_password:
            if password_input:
                st.error("That is not the password.")
            return

    events: List[Any] = []
    if store is not None:
        try:
            events = store.read()
        except Exception as exc:
            st.warning(f"Could not read the event log: {exc}")

    overview, raw = st.tabs(["Overview", "Raw data query"])
    with overview:
        if events:
            _overview(events)
        else:
            st.info(
                "No events yet. Counters below come from the legacy `data` "
                "dict; the event log fills as people use the app."
            )
        _legacy(data, unsafe_password, reset_callback)
    with raw:
        _raw_query(store, unsafe_password)


def _overview(events: List[Any]) -> None:
    pal = _theme()
    top_left, top_right = st.columns([3, 2])
    with top_left:
        choice = st.segmented_control(
            "Range", list(RANGES), default="30 days", key="_sa2_range"
        )
    pages_all = sorted({e.page or "/" for e in events if e.kind == "pageview"})
    with top_right:
        page = st.selectbox("Page", ["All pages"] + pages_all, key="_sa2_page_filter")
    days = RANGES.get(choice or "30 days")
    now = datetime.datetime.now(datetime.timezone.utc)
    tz_offset = _viewer_offset()
    since = None
    if days == 1:
        local_now = now - datetime.timedelta(minutes=tz_offset)
        since = local_now.replace(hour=0, minute=0, second=0, microsecond=0) + (
            datetime.timedelta(minutes=tz_offset)
        )
    elif days:
        since = now - datetime.timedelta(days=days)
    s = aggregate.summarize(
        events,
        since=since,
        page=None if page == "All pages" else page,
        tz_offset_minutes=tz_offset,
        now=now,
    )

    k = st.columns(6)
    k[0].metric("Views", s["views"], help="Page loads, including page switches.")
    k[1].metric("Visits", s["visits"], help="Browser sessions.")
    k[2].metric(
        "Visitors",
        s["visitors"],
        help="Distinct people per day. A hash that rotates daily, no IP is kept.",
    )
    k[3].metric(
        "Bounce rate",
        f"{s['bounce_rate']}%",
        help="Visits that loaded one page and never interacted.",
    )
    k[4].metric(
        "Avg visit time",
        utils.format_seconds(s["avg_visit_seconds"]),
        help="First to last activity in a visit.",
    )
    k[5].metric(
        "Active now", s["active_now"], help="Visits active in the last 5 minutes."
    )

    hourly = days == 1
    series = s["series_hour"] if hourly else s["series_day"]
    per_page = s["series_hour_pages"] if hourly else s["series_day_pages"]
    if series:
        _views_chart(series, per_page, hourly, pal)

    left, right = st.columns(2)
    with left:
        _bars("Pages", s["pages"], "page", "views", pal)
        _donut("Browsers", s["browsers"], "browser", pal)
        _bars("Languages", s["languages"], "language", "visits", pal)
        _bars("Sources (utm_source)", s["utm_sources"], "source", "visits", pal)
        _bars("Events", s["custom"], "event", "count", pal)
    with right:
        _bars(
            "Widgets",
            [
                {"widget": f"{w['label'] or w['key']}", "changes": w["changes"]}
                for w in s["widgets"][:8]
            ],
            "widget",
            "changes",
            pal,
        )
        _donut("Devices", s["devices"], "device", pal)
        _bars("Regions (timezone)", s["timezones"], "timezone", "visits", pal)
        _bars("Campaigns (utm_campaign)", s["utm_campaigns"], "campaign", "visits", pal)
        _donut("OS", s["os"], "os", pal)

    st.subheader("Traffic load")
    if s["load"]:
        load = pd.DataFrame(s["load"])
        load["day"] = load["weekday"].map(lambda i: WEEKDAYS[i])
        heat = (
            alt.Chart(load)
            .mark_rect(cornerRadius=2)
            .encode(
                x=alt.X("hour:O", title="hour of day", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("day:O", title="", sort=WEEKDAYS),
                color=alt.Color(
                    "runs:Q", title="runs", scale=alt.Scale(range=pal["seq"])
                ),
                tooltip=["day", "hour", "runs"],
            )
            .properties(height=200)
        )
        st.altair_chart(heat, width="stretch")
        if s["peak"]:
            st.caption(
                f"Busiest hour: {s['peak']['hour']} with {s['peak']['sessions']} "
                "concurrent visits. Times are in your timezone."
            )

    with st.expander("Widget detail"):
        if s["widgets"]:
            st.dataframe(pd.DataFrame(s["widgets"]), hide_index=True)
        else:
            st.caption("No widget interactions in this range.")
    with st.expander("Recent visits"):
        if s["sessions"]:
            st.dataframe(pd.DataFrame(s["sessions"]), hide_index=True)
    with st.expander("What is collected"):
        st.markdown("""
            - Per visit: a daily-rotating hash of address and browser (no IP,
              no cookie), browser, OS and device family, language, timezone,
              theme, UTM tags from the URL, and the pages viewed.
            - Per interaction: widget type, label, key, page and the chosen
              option. Free text is stored as `<text>` unless the app passes
              `store_values=True`.
            - Never: IP addresses, raw User-Agent strings, query strings,
              anything typed into text fields by default.
            """)


def _views_chart(
    series: List[Dict[str, Any]],
    per_page: List[Dict[str, Any]],
    hourly: bool,
    pal: Dict[str, Any],
) -> None:
    """Views per page as a stacked area, visitors as its own small line below.

    Two measures, two charts, one axis each; they share the time axis.
    """
    fmt = "%H:%M" if hourly else "%b %d"
    tip_fmt = "%Y-%m-%d %H:%M" if hourly else "%Y-%m-%d"
    pages = pd.DataFrame(per_page)
    pages["when"] = pd.to_datetime(pages["when"])
    order = list(
        pages.groupby("page")["views"].sum().sort_values(ascending=False).index
    )
    if len(order) > 7:
        keep = set(order[:7])
        pages["page"] = pages["page"].where(pages["page"].isin(keep), "Other")
        order = order[:7] + ["Other"]
    x = alt.X("when:T", title="", axis=alt.Axis(format=fmt, labelAngle=0, grid=False))
    area = (
        alt.Chart(pages)
        .mark_area(interpolate="monotone", line={"strokeWidth": 1.5}, opacity=0.8)
        .encode(
            x=x,
            y=alt.Y(
                "views:Q", title="views", stack="zero", axis=alt.Axis(tickMinStep=1)
            ),
            color=alt.Color(
                "page:N",
                title="page",
                sort=order,
                scale=alt.Scale(domain=order, range=pal["series"][: len(order)]),
                legend=alt.Legend(orient="top", direction="horizontal"),
            ),
            tooltip=[alt.Tooltip("when:T", format=tip_fmt), "page:N", "views:Q"],
        )
        .properties(height=240)
    )
    totals = pd.DataFrame(series)
    totals["when"] = pd.to_datetime(totals["when"])
    line = (
        alt.Chart(totals)
        .mark_line(
            interpolate="monotone",
            strokeWidth=2,
            point=alt.OverlayMarkDef(size=30),
            color=pal["series"][2],
        )
        .encode(
            x=x,
            y=alt.Y("visitors:Q", title="visitors", axis=alt.Axis(tickMinStep=1)),
            tooltip=[alt.Tooltip("when:T", format=tip_fmt), "visitors:Q", "views:Q"],
        )
        .properties(height=110)
    )
    st.altair_chart(
        alt.vconcat(area, line, spacing=4).resolve_scale(x="shared"), width="stretch"
    )


def _bars(
    title: str, rows: List[Dict[str, Any]], label: str, value: str, pal: Dict[str, Any]
) -> None:
    """Magnitude across categories: horizontal bars, one hue, value labels."""
    st.markdown(f"**{title}**")
    if not rows:
        st.caption("nothing yet")
        return
    df = pd.DataFrame(rows)[[label, value]].head(8)
    df[label] = df[label].astype(str)
    base = alt.Chart(df).encode(
        y=alt.Y(f"{label}:N", sort="-x", title="", axis=alt.Axis(labelLimit=180)),
        x=alt.X(f"{value}:Q", title="", axis=None),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, size=16, color=pal["series"][0]).encode(
        tooltip=[label, value]
    )
    text = base.mark_text(align="left", dx=4, color=pal["muted"]).encode(
        text=f"{value}:Q"
    )
    st.altair_chart((bars + text).properties(height=24 * len(df) + 10), width="stretch")


def _donut(
    title: str, rows: List[Dict[str, Any]], label: str, pal: Dict[str, Any]
) -> None:
    """Share of a whole with few slices: donut plus a labelled legend."""
    st.markdown(f"**{title}**")
    if not rows:
        st.caption("nothing yet")
        return
    df = pd.DataFrame(rows)[[label, "visits", "share"]].head(5)
    df[label] = df[label].astype(str)
    order = list(df[label])
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=42, outerRadius=68, padAngle=0.02, cornerRadius=3)
        .encode(
            theta=alt.Theta("visits:Q"),
            color=alt.Color(
                f"{label}:N",
                sort=order,
                scale=alt.Scale(domain=order, range=pal["series"][: len(order)]),
                legend=alt.Legend(title="", orient="right"),
            ),
            tooltip=[label, "visits", alt.Tooltip("share:Q", title="share %")],
        )
        .properties(height=150)
    )
    st.altair_chart(chart, width="stretch")


def _raw_query(store: Any, unsafe_password: Optional[str]) -> None:
    st.markdown("**Raw data query**")
    if not isinstance(store, SqliteStore):
        st.info(
            "Queries need the SQLite event log. Turn it on by giving `track()` "
            "a database path:\n\n"
            '```python\nwith sa2.track(events_path="analytics.db"):\n    ...\n```\n\n'
            "Why: the default JSONL log is fine to read as a whole, but SQLite "
            "lets you ask exact questions (one page, one widget, one week), "
            "handles many concurrent visitors safely, and stays fast past a "
            "few hundred thousand events. Everything else on this dashboard "
            "works with either backend."
        )
        return
    if unsafe_password is None:
        st.warning(
            "The query box is only available when the dashboard has a password "
            "(`track(unsafe_password=...)`). Without one, anyone who finds "
            "`?analytics=on` could read the raw event log."
        )
        return
    st.caption(
        "Read-only SQLite. One SELECT at a time, capped at "
        f"{query.MAX_ROWS} rows, with a work budget. Table: `{query.SCHEMA}`"
    )
    with st.expander("Security notes"):
        st.markdown("""
            - The database is opened read-only and `query_only`; an authorizer
              refuses writes, schema changes, `PRAGMA` and `ATTACH`, so a
              query cannot touch other files or alter the log.
            - Rows are capped and a step budget aborts runaway queries, but a
              heavy query still costs CPU on the app server. Do not expose this
              to strangers: the tab is password-gated, and that password is
              plain text in your app code.
            - The raw log holds what the dashboard shows. If you passed
              `store_values=True`, typed text is in `value`; treat the log as
              personal data under GDPR and make it deletable on request.
            - Anyone with the password sees this; rotate it if it leaks.
            """)
    names = [name for name, _ in query.EXAMPLES]
    pick = st.selectbox("Examples", ["Write your own"] + names, key="_sa2_q_example")
    default = ""
    if pick != "Write your own":
        default = dict(query.EXAMPLES)[pick]
    sql = st.text_area("SQL", value=default, height=160, key=f"_sa2_sql_{pick}")
    if st.button("Run query", type="primary"):
        try:
            cols, rows = query.run_query(store.path, sql)
        except query.QueryError as exc:
            st.error(str(exc))
            return
        if not rows:
            st.caption("No rows.")
            return
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df, hide_index=True)
        st.caption(
            f"{len(df)} rows" + (" (capped)" if len(df) >= query.MAX_ROWS else "")
        )
        st.download_button(
            "Download CSV", df.to_csv(index=False), "query.csv", "text/csv"
        )


def _viewer_offset() -> int:
    try:
        off = st.context.timezone_offset
        return int(off) if off is not None else 0
    except Exception:
        return 0


def _legacy(
    data: Dict[str, Any],  # noqa: F811
    unsafe_password: Optional[str],
    reset_callback: Callable[[], None],
) -> None:
    with st.expander("Legacy counters (`streamlit_analytics2.data`)"):
        st.write(f"since {data['start_time']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pageviews", data["total_pageviews"])
        c2.metric("Script runs", data["total_script_runs"])
        c3.metric("Time spent", utils.format_seconds(data["total_time_seconds"]))
        if not data.get("widgets"):
            st.caption("No widget counters yet.")
        for name, counts in data.get("widgets", {}).items():
            st.markdown(f"##### `{name}`")
            if isinstance(counts, dict):
                st.dataframe(
                    pd.DataFrame(
                        {
                            "value": list(counts.keys()),
                            "interactions": list(counts.values()),
                        }
                    ).sort_values(by="interactions", ascending=False),
                    hide_index=True,
                )
            else:
                st.write(f"{counts} interactions")

    if unsafe_password is not None:
        with st.expander("Danger zone"):
            st.write(
                "Reset the legacy counters. **This erases everything in "
                "`data`, including results synced to Firestore.** The event "
                "log file is not touched."
            )
            sure = st.selectbox(
                "Continue?",
                [
                    "No idea what I'm doing here",
                    "I'm sure that I want to reset the results",
                ],
            )
            if sure == "I'm sure that I want to reset the results":
                if st.button("Click here to reset"):
                    reset_callback()
                    st.write("Done! Please refresh the page.")
