"""MVP steps 4 and 5 — the keyword gate, then scoring.

Two stages, in this order, always:

1. **Gate.** An item matching zero entities and zero themes is blocked and never
   reaches the scorer. This is crude on purpose: it exists to keep the API bill
   near zero, and it costs two hours to maintain.

2. **Score.** By default a transparent keyword + recency + cluster-size score
   that needs no API key and no network. If ANTHROPIC_API_KEY is set and
   `--llm` is passed, surviving candidates additionally go to Claude Haiku in
   batches for a Norwegian summary and a "why this matters" sentence.

    uv run python -m nyhetsradar.score          # keyword only, free
    uv run python -m nyhetsradar.score --llm    # + Haiku summaries
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from datetime import UTC, datetime
from functools import lru_cache

from . import config, db

BATCH = 15  # items per LLM request
MODEL = "claude-haiku-4-5"

# Weights. Entities matter more than themes: a story naming Selvaag is nearly
# always worth surfacing, while a theme match alone is weak evidence.
W_OWN = 34
W_COMPETITOR = 16
W_PLACE = 8
W_INSTITUTION = 8
W_THEME = 7
W_CLUSTER = 6  # per extra source carrying the story, capped
W_FRESH = 12  # full marks today, decaying to zero over a week


@lru_cache(maxsize=2048)
def _pattern(term: str) -> re.Pattern[str]:
    """Word-boundary matcher for one term.

    Plain substring matching is wrong here and quietly inflates scores: "Ski"
    matches inside "skisse" and "skille", and "Løren" matches inside
    "Lørenskog". Anchoring on word boundaries fixes both. Multi-word terms are
    matched with flexible whitespace so "Selvaag  Bolig" still hits.
    """
    body = r"\s+".join(re.escape(part) for part in term.split())
    return re.compile(rf"(?<!\w){body}(?!\w)", re.IGNORECASE)


def find_terms(haystack: str, terms: list[str]) -> list[str]:
    return [t for t in terms if _pattern(t).search(haystack)]


def gate_and_score(row: sqlite3.Row, vocab: dict, cluster_size: int) -> dict:
    """Return gate result and a 0-100 keyword score for one item."""
    hay = f"{row['title']} {row['snippet']}".lower()

    hits = {group: find_terms(hay, terms) for group, terms in vocab["entities"].items()}
    theme_hits = find_terms(hay, vocab["themes"])
    entity_hits = [t for group in hits.values() for t in group]

    passed = bool(entity_hits or theme_hits)
    if not passed:
        return {"gated": 0, "entity_hits": "", "theme_hits": "", "score": None}

    score = 0
    score += W_OWN * min(len(hits.get("own", [])), 1)
    score += W_COMPETITOR * min(len(hits.get("competitors", [])), 1)
    score += W_PLACE * min(len(hits.get("places", [])), 2)
    score += W_INSTITUTION * min(len(hits.get("institutions", [])), 1)
    score += W_THEME * min(len(theme_hits), 3)
    score += min(W_CLUSTER * max(cluster_size - 1, 0), 18)

    # Recency: today = full marks, a week old = none.
    when = row["published_at"] or row["collected_at"]
    try:
        age_days = (datetime.now(UTC) - datetime.fromisoformat(when)).days
    except (TypeError, ValueError):
        age_days = 7
    score += max(0, W_FRESH - 2 * max(age_days, 0))

    return {
        "gated": 1,
        "entity_hits": ",".join(sorted(set(entity_hits))),
        "theme_hits": ",".join(sorted(set(theme_hits))),
        "score": max(0, min(100, score)),
    }


# ── LLM pass (optional) ───────────────────────────────────────────────────────

SYSTEM = """Du vurderer nyhetssaker for ledelsen i Selvaag Eiendom, en norsk boligutvikler.

Profilen under beskriver hva ledelsen bryr seg om, og hva de ikke bryr seg om. \
Vurder hver sak mot den profilen.

{profile}

For hver sak, svar med:
- score: 0-100, hvor relevant saken er for denne leseren
- kategori: ett av "egne", "konkurrent", "marked", "regulering", "kostnad", "politikk"
- sammendrag: én setning på norsk som oppsummerer saken
- derfor: én setning på norsk om hvorfor dette betyr noe for Selvaag Eiendom

Vær streng. De fleste saker er ikke relevante."""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "vurderinger": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "score": {"type": "integer"},
                    "kategori": {"type": "string"},
                    "sammendrag": {"type": "string"},
                    "derfor": {"type": "string"},
                },
                "required": ["id", "score", "kategori", "sammendrag", "derfor"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["vurderinger"],
    "additionalProperties": False,
}


def score_with_llm(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> int:
    """Send gated candidates to Haiku in batches. Returns count scored."""
    try:
        import anthropic
    except ImportError:
        print("anthropic not installed — run `uv sync --extra llm`")
        return 0
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — skipping LLM pass")
        return 0

    client = anthropic.Anthropic()
    system = SYSTEM.format(profile=config.profile())
    scored = 0

    for start in range(0, len(rows), BATCH):
        batch = rows[start : start + BATCH]
        saker = "\n\n".join(
            f"[{r['id']}] {r['title']}\nKilde: {r['source']}\n{r['snippet'][:300]}" for r in batch
        )
        # No `effort` — the parameter errors on Haiku 4.5.
        resp = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=system,
            messages=[{"role": "user", "content": f"Vurder disse sakene:\n\n{saker}"}],
            output_config={"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
        )
        if resp.stop_reason == "refusal":
            print(f"  batch {start // BATCH + 1}: refused, skipping")
            continue

        text = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            verdicts = json.loads(text)["vurderinger"]
        except (json.JSONDecodeError, KeyError) as exc:
            print(f"  batch {start // BATCH + 1}: unparseable response ({exc})")
            continue

        now = datetime.now(UTC).isoformat()
        conn.executemany(
            """UPDATE items SET score=?, scorer='haiku', summary_no=?, why_matters=?,
                                scored_at=? WHERE id=?""",
            [
                (
                    max(0, min(100, int(v["score"]))),
                    v["sammendrag"],
                    v["derfor"],
                    now,
                    int(v["id"]),
                )
                for v in verdicts
            ],
        )
        conn.commit()
        scored += len(verdicts)
        print(f"  batch {start // BATCH + 1}: scored {len(verdicts)}")

    return scored


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--llm", action="store_true", help="also run the Haiku pass")
    ap.add_argument("--limit", type=int, default=60, help="max candidates for the LLM pass")
    args = ap.parse_args()

    conn = db.init()
    vocab = {"entities": config.entities(), "themes": config.theme_terms()}

    sizes = dict(
        conn.execute(
            "SELECT cluster_id, COUNT(*) FROM items "
            "WHERE cluster_id IS NOT NULL GROUP BY cluster_id"
        ).fetchall()
    )

    # Canonical items only — duplicates inherit their cluster's verdict.
    rows = conn.execute(
        "SELECT * FROM items WHERE cluster_id = id OR cluster_id IS NULL"
    ).fetchall()

    updates = []
    passed = 0
    for row in rows:
        result = gate_and_score(row, vocab, sizes.get(row["id"], 1))
        passed += result["gated"]
        updates.append(
            (
                result["gated"],
                result["entity_hits"],
                result["theme_hits"],
                result["score"],
                "keyword" if result["gated"] else None,
                datetime.now(UTC).isoformat(),
                row["id"],
            )
        )
    conn.executemany(
        """UPDATE items SET gated=?, entity_hits=?, theme_hits=?, score=?, scorer=?, scored_at=?
           WHERE id=?""",
        updates,
    )
    conn.commit()

    blocked = len(rows) - passed
    print(f"gate: {passed} passed, {blocked} blocked ({len(rows)} canonical stories)")

    if args.llm:
        candidates = conn.execute(
            """SELECT * FROM items WHERE gated=1 AND (cluster_id = id OR cluster_id IS NULL)
               ORDER BY score DESC LIMIT ?""",
            (args.limit,),
        ).fetchall()
        print(f"LLM pass over top {len(candidates)} candidates:")
        score_with_llm(conn, candidates)

    over = conn.execute(
        "SELECT COUNT(*) FROM items WHERE score >= ? AND (cluster_id = id OR cluster_id IS NULL)",
        (config.THRESHOLD,),
    ).fetchone()[0]
    print(f"{over} stories at or above threshold {config.THRESHOLD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
