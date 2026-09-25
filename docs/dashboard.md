# The dashboard

Open your app with `?analytics=on`. A dialog appears; if `unsafe_password` is
set, enter it first. Runs made while the dashboard is open are not recorded,
so browsing the analytics does not inflate them.

Two tabs: **Overview** and **Raw data query** (see [query.md](query.md)).

## Filters

- **Range**: Today (hourly buckets), 7 days, 30 days (default), 90 days, All time.
- **Page**: one page or all. With one page selected, every number and chart is
  about that page only, and visitor facts cover the visits that saw it.

Times are shown in your browser's timezone.

## Headline numbers

| Number | Definition |
|---|---|
| Views | Page loads, including switching to another page within a visit. |
| Visits | Browser sessions (one Streamlit session each). |
| Visitors | Distinct people per day, counted from a hash that rotates daily. Two visits by one person on one day count once; on two days, twice. |
| Bounce rate | Share of visits that loaded one page and never interacted or reran. |
| Avg visit time | Mean time from first to last activity within a visit, over visits with more than one run. |
| Active now | Visits with activity in the last 5 minutes. |

## Views over time

A stacked area of views per page (up to seven pages, the rest folded into
"Other") and, below it on the same time axis, a line of visitors. Hover for
exact values. "Today" switches both to hourly buckets.

## Breakdowns

Left column: Pages, Browsers, Languages, Sources (`utm_source`), Events.
Right column: Widgets, Devices, Regions (timezone), Campaigns
(`utm_campaign`), OS.

Bars show counts with labels; donuts show share with a legend. Browsers, OS
and devices come from the User-Agent reduced to a family name. Regions come
from the browser's timezone, which is how the library stands in for country
without touching IP addresses. Sources and campaigns come from UTM parameters
on the URL the visitor arrived with, the stand-in for referrers, which
Streamlit cannot see server-side.

## Traffic load

A weekday-by-hour heatmap of script runs in your timezone, with the busiest
hour and its number of concurrent visits underneath. This answers "when is
the app under load".

## Expanders

- **Widget detail**: one row per widget with type, label, key, page, number of
  changes, number of visits that used it, and the top three values chosen.
- **Recent visits**: the last 25 visits with start time, duration, page path,
  runs, interactions, browser, device and timezone.
- **What is collected**: the privacy summary, see [privacy.md](privacy.md).
- **Legacy counters**: the 0.10-style numbers from `sa2.data`.
- **Danger zone** (only with a password): reset the legacy counters. The
  event log is never deleted from the dashboard.

## When there are no events yet

The Overview shows the legacy counters and a note. Events appear as soon as
someone uses the app outside the dashboard.
