---
name: check-feeds
description: Probe every configured RSS feed and report which are alive, stale, or dead. Use before trusting the collector, after a drop in daily volume, or when a source seems to have gone quiet.
argument-hint: "[optional: feed name or URL to check just one]"
allowed-tools: Bash(uv run scripts/check_feeds.py*), Read, Grep
---

Probe the feed list and report health. RSS endpoints rot silently — this is the check that
catches it before a week of digests has quietly been missing a source.

## Steps

1. Read `config/feeds.toml`, including commented-out dead entries.
2. Run the prober:
   ```
   uv run scripts/check_feeds.py
   ```
   If `$ARGUMENTS` names a specific feed or URL, pass it through and check only that one.
   If `scripts/check_feeds.py` does not exist yet, this is MVP step 1 and writing it is
   the task — it should report HTTP status, item count, and newest item date per URL, and
   emit a config file listing only feeds that responded.
3. Classify each result:
   - **Alive** — parses, and newest item is within the last few days
   - **Stale** — parses, but newest item is weeks or months old. Treat as dead in practice.
   - **Dead** — non-200, unparseable body, or a 200 HTML error page
4. For anything newly dead, check whether the feed simply moved: look for a
   `<link rel="alternate">` on the site root before writing it off.

## Report

A table of feed, status, item count, newest item, and the delta against the last known
state. Call out specifically:
- Feeds that were alive and are now not
- Feeds whose volume has dropped sharply — a partial failure the status code won't show

## When editing config

Dead feeds get **commented out, never deleted**. The record of what was tried is the point;
a URL removed from the file will be rediscovered and re-tried by someone in three months.
Note the date and the observed failure beside the commented line.
