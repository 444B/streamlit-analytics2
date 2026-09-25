# Privacy

The library is built so that the default install collects nothing that
identifies a person. You can turn some of that off; you cannot turn on IP or
raw User-Agent storage, because the code never keeps them.

## Stored by default

| Per visit (once, on the `session` event) | Per interaction (`widget` event) |
|---|---|
| visitor id: SHA-256 of `today|ip|user-agent`, first 16 hex chars | widget type, label, key, page |
| browser family (Chrome, Safari, ...), OS family, device family (Desktop, Mobile, Tablet) | the chosen option for selectboxes, radios, sliders, dates, colours, multiselects |
| language (`locale`), timezone, theme, embedded flag | `<text>` for text inputs, text areas and chat inputs |
| UTM tags from the URL: source, medium, campaign, content, term | |
| pages viewed, with timestamps | |

The visitor id changes every day, so the same person on two days is two
visitors and cannot be followed over time. Two people behind one IP with the
same browser on the same day are one visitor. That is the trade the library
makes on purpose; it is the same approach as cookieless analytics tools.

## Never stored

- IP addresses. They enter the hash and are discarded.
- Raw User-Agent strings. Only the family names survive.
- Query strings other than the five UTM keys.
- Typed text, unless you set `store_values=True`.
- Cookies. None are set or read.
- File contents or names from uploaders. Only "a file was uploaded".

## `store_values=True`

Records what users type into `text_input`, `text_area` and `chat_input`,
capped at 200 characters per value. Prompts and names are personal data. If
you enable this you become responsible for the log under GDPR and similar
laws: tell users, secure the file, and be ready to delete on request.

## GDPR notes

- Without `store_values`, the log holds pseudonymous usage data: a daily
  hash, coarse device facts, timezone, language, page paths, widget choices.
  Under GDPR this is still processing of personal data (the hash is derived
  from an IP), with a strong legitimate-interest case similar to server logs,
  and no cross-day profile. Say so in your privacy notice.
- Timezone and language are shared by millions of people; they are kept
  because they answer "where are my users" without geolocating anyone.
- The dashboard and the SQL tab expose the log to whoever knows the
  password. Use one, and keep it in secrets.
- Deletion: today you delete rows yourself (`DELETE FROM events WHERE
  session = ...` on the SQLite file, or filter the JSONL). A deletion API is
  planned; see issue #148.
- Retention: the log grows forever. Rotate the file or prune old rows on your
  own schedule.
- Firestore: the aggregate counters contain widget labels and chosen values,
  and `session_id` documents if you use them. Same rules apply.

## What the visitor sees

Nothing. No banner is needed for the default configuration in most
jurisdictions, because no cookie or client-side identifier is set. That is a
statement about the library's behaviour, not legal advice for your app.
