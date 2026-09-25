# Raw data query

The second tab of the dashboard runs SQL over your event log and shows the
result as a table or a chart. It exists so you can ask the question the
dashboard did not think of.

## Requirements

1. The event log must be SQLite: `sa2.track(events_path="analytics.db")`.
   With the default JSONL log the tab explains this and stops.
2. The dashboard must have a password: `sa2.track(unsafe_password=...)`.
   Without one the tab refuses, because anyone who finds `?analytics=on`
   would otherwise read the raw log.

Why SQLite: the JSONL log is fine to read as a whole, but SQLite lets you ask
exact questions (one page, one widget, one week), handles many concurrent
visitors safely, and stays fast past a few hundred thousand events.

## Using it

- Pick an example from the dropdown or write your own `SELECT`.
- **Run query** shows up to 500 rows and a CSV download.
- **Present as** turns the result into a Bar, Line, Area, Pie or Scatter
  chart. Choose the x or category column, the value column, and an optional
  colour column. Not every result suits every chart; a line needs an ordered x
  column, a pie needs a few categories and one number.

Schema: `events(id, ts, kind, session, visitor, page, name, widget_id,
widget_type, key, value, props)`; `props` is JSON on `session` and `custom`
rows. `ts` is ISO 8601 UTC text, so `substr(ts, 1, 10)` is the day and
`date('now', '-30 days')` compares correctly.

## Example queries

Views per day, last 30 days:

```sql
SELECT substr(ts, 1, 10) AS day, count(*) AS views
FROM events
WHERE kind = 'pageview' AND ts >= date('now', '-30 days')
GROUP BY day ORDER BY day
```

Top pages:

```sql
SELECT page, count(*) AS views, count(DISTINCT session) AS visits
FROM events WHERE kind = 'pageview'
GROUP BY page ORDER BY views DESC
```

Most used widgets:

```sql
SELECT widget_type, name, key, count(*) AS changes
FROM events WHERE kind = 'widget'
GROUP BY widget_type, name, key ORDER BY changes DESC LIMIT 20
```

Option popularity for one selectbox:

```sql
SELECT value, count(*) AS n FROM events
WHERE kind = 'widget' AND name = 'Select your favorite'
GROUP BY value ORDER BY n DESC
```

Visit length:

```sql
SELECT session, min(ts) AS started,
       (julianday(max(ts)) - julianday(min(ts))) * 86400 AS seconds,
       sum(kind = 'widget') AS interactions
FROM events GROUP BY session ORDER BY started DESC LIMIT 50
```

Browsers and devices from the session row:

```sql
SELECT json_extract(props, '$.browser') AS browser,
       json_extract(props, '$.device') AS device, count(*) AS visits
FROM events WHERE kind = 'session'
GROUP BY browser, device ORDER BY visits DESC
```

Funnel: visits that used widget A and then fired event B:

```sql
WITH a AS (SELECT session, min(ts) t FROM events WHERE kind='widget' AND name='Generate' GROUP BY session),
     b AS (SELECT session, min(ts) t FROM events WHERE kind='custom' AND name='report generated' GROUP BY session)
SELECT count(*) AS started, sum(b.t IS NOT NULL AND b.t >= a.t) AS completed
FROM a LEFT JOIN b USING (session)
```

## Security model

Treat the query box as a feature for the app owner, not for visitors.

- The database file is opened **read-only** and the connection is
  `query_only`.
- An **authorizer** allows only SELECT, reads and ordinary functions. Writes,
  schema changes, `PRAGMA`, `ATTACH` and functions that allocate or touch the
  filesystem (`zeroblob`, `randomblob`, `load_extension`, `readfile`,
  `writefile`, ...) are refused.
- One statement per run; comments are stripped by a linear scanner; the text
  must start with `SELECT` or `WITH`.
- Limits: 500 rows, a 2 second wall-clock deadline, a 64 MB heap, 10 MB per
  string, 100 KB of SQL.
- The tab is behind the dashboard password, which is plain text in your app.
  Anyone with the password can read the whole log and spend up to 2 seconds
  of CPU per query. Rotate it if it leaks.
- With `store_values=True` the log contains typed text: personal data.
  See [privacy.md](privacy.md).

These are also the reasons the GitHub code-scanning alert on the SQL sink is
dismissed as intentional.
