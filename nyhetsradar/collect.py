"""MVP step 2 — collect items from every live feed into SQLite.

Run every four hours from cron:

    0 */4 * * *  cd /srv/nyhetsradar && uv run python -m nyhetsradar.collect

Stores title, snippet, link, source and date. Never article bodies.
"""

from __future__ import annotations

import html
import re
import sqlite3
from datetime import UTC, datetime

import feedparser

from . import config, db

UA = "Nyhetsradar/0.1 (+internal news monitor for Selvaag Eiendom)"

_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")

# Google News titles arrive as "Real headline - Publisher"; the trailing
# publisher is noise for dedup and display alike.
_GN_SUFFIX = re.compile(r"\s+-\s+[^-]{2,40}$")

# Several Norwegian trade titles prefix paywalled headlines with "(+)" or "+".
# It is display noise and it skews title similarity in dedup, so drop it. The
# item is still collected — the headline and snippet are public even when the
# body is not.
_PAYWALL_PREFIX = re.compile(r"^\s*(\(\+\)|\+)\s*")


def clean(text: str, limit: int = 400) -> str:
    """Strip markup and collapse whitespace. Snippets only — never bodies."""
    if not text:
        return ""
    text = html.unescape(_TAGS.sub(" ", text))
    text = _WS.sub(" ", text).strip()
    return text[:limit]


def entry_published(entry) -> str | None:
    struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if not struct:
        return None
    return datetime(*struct[:6], tzinfo=UTC).isoformat()


def entry_source(entry, feed_name: str) -> str:
    """Prefer the real publisher over the aggregator that carried the item."""
    src = entry.get("source")
    if isinstance(src, dict) and src.get("title"):
        return src["title"]
    return feed_name


def collect_feed(conn: sqlite3.Connection, feed: dict) -> tuple[int, int]:
    parsed = feedparser.parse(feed["url"], agent=UA)
    if not parsed.entries:
        return 0, 0

    now = datetime.now(UTC).isoformat()
    seen = inserted = 0
    for entry in parsed.entries:
        link = (entry.get("link") or "").strip()
        title = clean(entry.get("title", ""), 300)
        if not link or not title:
            continue
        if "news.google" in feed["url"]:
            title = _GN_SUFFIX.sub("", title).strip()
        title = _PAYWALL_PREFIX.sub("", title).strip()
        if not title:
            continue
        seen += 1

        cur = conn.execute(
            """INSERT OR IGNORE INTO items
               (link, title, snippet, source, source_type, published_at, collected_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                link,
                title,
                clean(entry.get("summary", "")),
                entry_source(entry, feed["name"]),
                feed.get("type", ""),
                entry_published(entry),
                now,
            ),
        )
        inserted += cur.rowcount
    conn.commit()
    return seen, inserted


def main() -> int:
    conn = db.init()
    feeds = config.feeds()
    started = datetime.now(UTC).isoformat()
    run = conn.execute("INSERT INTO runs (started_at) VALUES (?)", (started,)).lastrowid
    conn.commit()

    ok = failed = total_seen = total_new = 0
    for feed in feeds:
        try:
            seen, inserted = collect_feed(conn, feed)
        except Exception as exc:  # noqa: BLE001 - one bad feed must not stop the pass
            failed += 1
            print(f"  FAIL {feed['name']}: {type(exc).__name__}: {exc}")
            continue
        ok += 1
        total_seen += seen
        total_new += inserted
        print(f"  {inserted:>4} new / {seen:>4} seen   {feed['name']}")

    conn.execute(
        """UPDATE runs SET finished_at=?, feeds_ok=?, feeds_failed=?, seen=?, inserted=?
           WHERE id=?""",
        (datetime.now(UTC).isoformat(), ok, failed, total_seen, total_new, run),
    )
    conn.commit()
    print(f"\n{total_new} new items from {ok} feeds ({failed} failed), {total_seen} seen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
