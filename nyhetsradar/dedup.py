"""MVP step 3 — collapse near-identical coverage into single stories.

Syndication is heavy in Norwegian news: the same story reaches us from the
publisher, from Google News, and from two keyword queries. Collapsing it is the
single biggest volume reduction in the pipeline, and the collapse ratio is a
number worth showing to whoever approves the project.

This first cut clusters on title similarity, which needs no model download. The
plan's `NbAiLab/nb-sbert-base` embedding is the intended replacement once the
pipeline is proven — it catches paraphrases this misses, and it produces the
vectors the feedback table wants for phase 2. Swap `similar()` and keep the rest.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher

from . import db

# Titles above this similarity are treated as the same story.
THRESHOLD = 0.82

# Only compare within this window; the same headline three weeks apart is a
# different story, not a duplicate.
WINDOW = timedelta(days=7)

_NOISE = re.compile(r"[^\wæøå ]+", re.IGNORECASE)
_NUM = re.compile(r"\d+")
_STOP = {
    "og",
    "i",
    "på",
    "til",
    "for",
    "med",
    "av",
    "en",
    "et",
    "den",
    "det",
    "som",
    "er",
    "har",
    "the",
    "a",
    "of",
    "to",
    "in",
    "so",
    "her",
    "sier",
    "nye",
    "ny",
    "fra",
    "ved",
    "om",
    "blir",
    "ble",
    "hun",
    "han",
    "de",
    "etter",
    "før",
    "mot",
    "over",
    "under",
    "skal",
    "vil",
    "seg",
}


def normalise(title: str) -> str:
    """Lowercase, strip punctuation and stopwords — cheap noise reduction."""
    words = _NOISE.sub(" ", title.lower()).split()
    return " ".join(w for w in words if w not in _STOP)


def numbers(text: str) -> set[str]:
    return set(_NUM.findall(text))


def similar(a: str, b: str) -> float:
    """Similarity of two normalised titles, 0..1.

    Three signals, in order of how much they are trusted:

    1. **Conflicting figures veto a merge.** Norwegian market headlines are
       often identical in shape and differ only in the number: "Obos-prisene i
       Oslo falt med 0,3 prosent" against "... falt 2 prosent i september"
       shares most of its words but reports a different month, and "Q1 2026"
       against "Q2 2026" is two quarters of results. The test is subset, not
       intersection — sharing a year is not enough, but one outlet adding the
       deal value to an otherwise identical headline still merges.
    2. **Token containment.** Catches the same deal told from either side —
       "Skanska kjøper Skøyen-tomt fra Selvaag" against "Selvaag selger
       Skøyen-tomt til Skanska" — which a character-ratio scores far too low.
       Requires at least three shared content words so short headlines don't
       collapse into each other.
    3. **Character ratio**, as the fallback for everything else.
    """
    if not a or not b:
        return 0.0

    na, nb = numbers(a), numbers(b)
    if na and nb and not (na <= nb or nb <= na):
        return 0.0

    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    shared = len(ta & tb)
    contained = shared / min(len(ta), len(tb))
    overlap = shared / len(ta | tb)
    # Containment alone merges a short headline into any longer one that happens
    # to repeat its generic words ("største", "bygg", "anlegg"). Requiring the
    # overlap across both titles to clear a floor as well keeps that from
    # collapsing unrelated trade stories into one.
    if shared >= 3 and contained >= 0.65 and overlap >= 0.45:
        return 1.0

    return SequenceMatcher(None, a, b).ratio()


def parse_when(row: sqlite3.Row) -> datetime:
    for field in ("published_at", "collected_at"):
        if row[field]:
            try:
                return datetime.fromisoformat(row[field])
            except ValueError:
                continue
    return datetime.now(UTC)


def main() -> int:
    conn = db.init()
    rows = conn.execute(
        """SELECT id, title, published_at, collected_at FROM items
           ORDER BY COALESCE(published_at, collected_at) ASC"""
    ).fetchall()

    # (id, normalised title, when) for each canonical story so far.
    canonicals: list[tuple[int, str, datetime]] = []
    assignments: list[tuple[int, int]] = []

    for row in rows:
        norm = normalise(row["title"])
        when = parse_when(row)
        match = None
        for cid, ctitle, cwhen in reversed(canonicals):
            if when - cwhen > WINDOW:
                break  # rows are time-ordered, so everything earlier is older still
            if similar(norm, ctitle) >= THRESHOLD:
                match = cid
                break
        if match is None:
            canonicals.append((row["id"], norm, when))
            assignments.append((row["id"], row["id"]))
        else:
            assignments.append((match, row["id"]))

    conn.executemany("UPDATE items SET cluster_id=? WHERE id=?", assignments)
    conn.commit()

    total = len(rows)
    unique = len(canonicals)
    ratio = (1 - unique / total) * 100 if total else 0
    print(f"{total} items -> {unique} unique stories ({ratio:.0f}% collapsed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
