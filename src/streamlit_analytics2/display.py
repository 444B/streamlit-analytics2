"""The ``?analytics=on`` dashboard: Umami-style, read-only, privacy-safe."""

from __future__ import annotations

import datetime
from typing import Any, Callable, Dict, List, Optional

import altair as alt
import pandas as pd
import streamlit as st

from . import aggregate, utils
from .state import data  # noqa: F401

RANGES = {
    "Today": 1,
    "7 days": 7,
    "30 days": 30,
    "90 days": 90,
    "All time": None,
}
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


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

    if not events:
        st.info(
            "No events yet. Counters below come from the legacy `data` dict; "
            "the event log fills as people use the app."
        )
        _legacy(data, unsafe_password, reset_callback)
        return

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

    series = s["series_hour"] if days == 1 else s["series_day"]
    per_page = s["series_hour_pages"] if days == 1 else s["series_day_pages"]
    if series:
        _views_chart(series, per_page, hourly=days == 1)

    left, right = st.columns(2)
    with left:
        _table("Pages", s["pages"])
        _table("Browsers", s["browsers"])
        _table("Devices", s["devices"])
        _table("Languages", s["languages"])
        _table("Campaigns (utm_campaign)", s["utm_campaigns"])
    with right:
        _table(
            "Widgets",
            [
                {
                    "widget": f"{w['label'] or w['key']} ({w['type']})",
                    "changes": w["changes"],
                    "visits": w["sessions"],
                }
                for w in s["widgets"][:10]
            ],
        )
        _table("OS", s["os"])
        _table("Regions (timezone)", s["timezones"])
        _table("Events", s["custom"])
        _table("Sources (utm_source)", s["utm_sources"])

    st.subheader("Traffic load")
    if s["load"]:
        load = pd.DataFrame(s["load"])
        load["day"] = load["weekday"].map(lambda i: WEEKDAYS[i])
        heat = (
            alt.Chart(load)
            .mark_rect()
            .encode(
                x=alt.X("hour:O", title="hour of day", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("day:O", title="", sort=WEEKDAYS),
                color=alt.Color(
                    "runs:Q", title="runs", scale=alt.Scale(scheme="blues")
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
    _legacy(data, unsafe_password, reset_callback)


def _views_chart(
    series: List[Dict[str, Any]], per_page: List[Dict[str, Any]], hourly: bool
) -> None:
    """Stacked area of views per page with a visitors line on top."""
    fmt = "%H:%M" if hourly else "%b %d"
    x = alt.X(
        "when:T",
        title="",
        axis=alt.Axis(format=fmt, labelAngle=0, grid=False),
    )
    pages = pd.DataFrame(per_page)
    pages["when"] = pd.to_datetime(pages["when"])
    area = (
        alt.Chart(pages)
        .mark_area(interpolate="monotone", opacity=0.75)
        .encode(
            x=x,
            y=alt.Y(
                "views:Q", title="views", stack="zero", axis=alt.Axis(tickMinStep=1)
            ),
            color=alt.Color("page:N", title="page", legend=alt.Legend(orient="bottom")),
            tooltip=[
                alt.Tooltip("when:T", format=fmt if hourly else "%Y-%m-%d"),
                "page:N",
                "views:Q",
            ],
        )
    )
    totals = pd.DataFrame(series)
    totals["when"] = pd.to_datetime(totals["when"])
    line = (
        alt.Chart(totals)
        .mark_line(
            interpolate="monotone", strokeWidth=2, color="#FFFFFF", strokeDash=[4, 3]
        )
        .encode(
            x=x,
            y=alt.Y("visitors:Q", title="visitors", axis=alt.Axis(tickMinStep=1)),
            tooltip=[alt.Tooltip("when:T", format="%Y-%m-%d"), "visitors:Q", "views:Q"],
        )
    )
    chart = alt.layer(area, line).resolve_scale(y="independent").properties(height=260)
    st.altair_chart(chart, width="stretch")
    st.caption("Stacked areas: views per page. Dashed line: visitors (right axis).")


def _viewer_offset() -> int:
    try:
        off = st.context.timezone_offset
        return int(off) if off is not None else 0
    except Exception:
        return 0


def _table(title: str, rows: List[Dict[str, Any]]) -> None:
    st.markdown(f"**{title}**")
    if rows:
        st.dataframe(
            pd.DataFrame(rows), hide_index=True, height=min(38 + 35 * len(rows), 400)
        )
    else:
        st.caption("nothing yet")


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
