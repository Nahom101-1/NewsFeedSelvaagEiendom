"""MVP step 6 — the JSON API behind the Next.js frontend.

Flask owns data and ranking; the React app in web/ owns presentation. There is
no server-rendered HTML here any more.

    uv run flask --app nyhetsradar.app run --debug     # API on :5000
    cd web && npm run dev                              # UI  on :3000
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from flask import Flask, jsonify, request

from . import config, db

app = Flask(__name__)

# Create the schema if it is missing. A fresh deployment starts with an empty
# volume and the pipeline container may not have run yet; without this every
# query fails with "no such table: items", so a brand-new install reports itself
# permanently unhealthy. The DDL is CREATE TABLE IF NOT EXISTS throughout, so
# this is idempotent and safe to run from every gunicorn worker.
db.init().close()

ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}

CANONICAL = "(cluster_id = id OR cluster_id IS NULL)"

MONTHS = [
    "januar", "februar", "mars", "april", "mai", "juni",
    "juli", "august", "september", "oktober", "november", "desember",
]  # fmt: skip
MONTHS_SHORT = [
    "jan", "feb", "mar", "apr", "mai", "jun",
    "jul", "aug", "sep", "okt", "nov", "des",
]  # fmt: skip


@app.after_request
def allow_frontend(response):
    """The Next.js dev server is a different origin; production is same-origin."""
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Vary"] = "Origin"
    return response


# ── formatting ───────────────────────────────────────────────────────────────


def parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def short_date(ts: str | None) -> str:
    """'2. sep' — Norwegian, lowercase month, no leading zero."""
    dt = parse(ts)
    return f"{dt.day}. {MONTHS_SHORT[dt.month - 1]}" if dt else ""


def long_date(dt: datetime) -> str:
    """'31. august'."""
    return f"{dt.day}. {MONTHS[dt.month - 1]}"


def week_window(now: datetime) -> dict:
    """ISO week number and the Monday-Sunday range, formatted Norwegian."""
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    sunday = monday + timedelta(days=6)
    if monday.year == sunday.year:
        span = f"{long_date(monday)} – {long_date(sunday)} {sunday.year}"
    else:
        span = f"{long_date(monday)} {monday.year} – {long_date(sunday)} {sunday.year}"
    return {"number": now.isocalendar().week, "range": span, "start": monday}


# ── payloads ─────────────────────────────────────────────────────────────────


def story_row(row: sqlite3.Row, cluster_size: int, label: str | None) -> dict:
    return {
        "id": row["id"],
        "score": row["score"] or 0,
        "source": row["source"],
        "published": short_date(row["published_at"] or row["collected_at"]),
        "cluster_size": cluster_size,
        "title": row["title"],
        "summary": row["summary_no"] or row["snippet"] or "",
        "why": row["why_matters"] or "",
        "url": row["link"],
        "category": "",
        # Lets the UI show which way the reader already voted, so the buttons
        # reflect state instead of pretending every story is unjudged.
        "feedback": label,
    }


def brief_payload() -> dict:
    conn = db.connect()
    now = datetime.now(UTC)
    threshold = config.THRESHOLD

    sizes = dict(
        conn.execute(
            "SELECT cluster_id, COUNT(*) FROM items WHERE cluster_id IS NOT NULL "
            "GROUP BY cluster_id"
        ).fetchall()
    )
    labels = dict(conn.execute("SELECT item_id, label FROM feedback").fetchall())

    rows = conn.execute(
        f"""SELECT * FROM items
            WHERE {CANONICAL} AND score >= ?
            ORDER BY score DESC, COALESCE(published_at, collected_at) DESC
            LIMIT 40""",
        (threshold,),
    ).fetchall()

    collected = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    unique = conn.execute(f"SELECT COUNT(*) FROM items WHERE {CANONICAL}").fetchone()[0]
    over = conn.execute(
        f"SELECT COUNT(*) FROM items WHERE {CANONICAL} AND score >= ?", (threshold,)
    ).fetchone()[0]
    below = conn.execute(
        f"SELECT COUNT(*) FROM items WHERE {CANONICAL} AND gated = 1 AND score < ?",
        (threshold,),
    ).fetchone()[0]

    used_llm = conn.execute("SELECT COUNT(*) FROM items WHERE scorer='haiku'").fetchone()[0]
    week = week_window(now)
    return {
        "week": {"number": week["number"], "range": week["range"]},
        "kpis": {
            "collected": collected,
            "unique": unique,
            "over_threshold": over,
            "pending": below,
        },
        "list_name": "Alle saker",
        "list_count": over,
        "list_blurb": (
            "Rangert av språkmodell mot ledelsesprofilen."
            if used_llm
            else "Rangert på nøkkelord, kildebredde og ferskhet."
        ),
        "threshold": threshold,
        "stories": [story_row(r, sizes.get(r["id"], 1), labels.get(r["id"])) for r in rows],
        "below_count": below,
        "generated_at": f"{long_date(now)} {now:%H:%M}",
    }


def admin_payload() -> dict:
    """Everything the user page deliberately hides: scores, sources, health."""
    conn = db.connect()
    now = datetime.now(UTC)
    threshold = config.THRESHOLD

    collected = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    unique = conn.execute(f"SELECT COUNT(*) FROM items WHERE {CANONICAL}").fetchone()[0]
    gated = conn.execute(f"SELECT COUNT(*) FROM items WHERE {CANONICAL} AND gated=1").fetchone()[0]
    blocked = conn.execute(f"SELECT COUNT(*) FROM items WHERE {CANONICAL} AND gated=0").fetchone()[
        0
    ]
    over = conn.execute(
        f"SELECT COUNT(*) FROM items WHERE {CANONICAL} AND score >= ?", (threshold,)
    ).fetchone()[0]

    distribution = [
        {
            "from": lo,
            "to": lo + 9,
            "count": conn.execute(
                f"SELECT COUNT(*) FROM items WHERE {CANONICAL} AND gated=1 "
                f"AND score >= ? AND score < ?",
                (lo, lo + 10),
            ).fetchone()[0],
        }
        for lo in range(0, 100, 10)
    ]

    sources = [
        {"name": r["source"], "count": r["n"], "latest": short_date(r["latest"])}
        for r in conn.execute(
            """SELECT source, COUNT(*) n, MAX(COALESCE(published_at, collected_at)) latest
               FROM items GROUP BY source ORDER BY n DESC LIMIT 25"""
        )
    ]

    runs = [
        {
            "started": r["started_at"],
            "finished": r["finished_at"],
            "feeds_ok": r["feeds_ok"],
            "feeds_failed": r["feeds_failed"],
            "seen": r["seen"],
            "inserted": r["inserted"],
        }
        for r in conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 10")
    ]

    label_counts = dict(conn.execute("SELECT label, COUNT(*) FROM feedback GROUP BY label"))
    with_embedding = conn.execute(
        "SELECT COUNT(*) FROM feedback WHERE embedding IS NOT NULL"
    ).fetchone()[0]

    clusters = conn.execute(
        "SELECT COUNT(*) FROM "
        "(SELECT cluster_id FROM items GROUP BY cluster_id HAVING COUNT(*) > 1)"
    ).fetchone()[0]

    try:
        feeds = config.feeds()
    except FileNotFoundError:
        feeds = []

    scored_by = dict(
        conn.execute("SELECT COALESCE(scorer,'ikke scoret'), COUNT(*) FROM items GROUP BY scorer")
    )

    return {
        "generated_at": f"{long_date(now)} {now:%H:%M}",
        "threshold": threshold,
        "totals": {
            "collected": collected,
            "unique": unique,
            "gated": gated,
            "blocked": blocked,
            "over_threshold": over,
            "multi_source_clusters": clusters,
            "collapse_pct": round((1 - unique / collected) * 100, 1) if collected else 0.0,
        },
        "distribution": distribution,
        "sources": sources,
        "feeds": [{"name": f["name"], "type": f.get("type", ""), "url": f["url"]} for f in feeds],
        "runs": runs,
        "labels": {
            "relevant": label_counts.get("relevant", 0),
            "not_relevant": label_counts.get("not_relevant", 0),
            "with_embedding": with_embedding,
        },
        "scored_by": scored_by,
    }


# ── routes ───────────────────────────────────────────────────────────────────


@app.get("/api/brief")
def api_brief():
    return jsonify(brief_payload())


@app.get("/api/admin")
def api_admin():
    return jsonify(admin_payload())


@app.route("/api/feedback/<int:item_id>", methods=["POST", "OPTIONS"])
def api_feedback(item_id: int):
    """Record a relevant / not-relevant judgement.

    Every click is a labelled training example, and generating them is the
    MVP's second job. The embedding column is written alongside the label so
    phase 2 needs no reprocessing; it is NULL for now because dedup still runs
    on title similarity rather than nb-sbert-base.
    """
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or request.form
    label = payload.get("label")
    if label not in {"relevant", "not_relevant"}:
        return jsonify({"error": "label must be 'relevant' or 'not_relevant'"}), 400

    conn = db.init()
    if not conn.execute("SELECT 1 FROM items WHERE id=?", (item_id,)).fetchone():
        return jsonify({"error": "unknown item"}), 404

    conn.execute(
        """INSERT INTO feedback (item_id, label, embedding, created_at) VALUES (?, ?, ?, ?)
           ON CONFLICT(item_id) DO UPDATE SET label=excluded.label,
                                              created_at=excluded.created_at""",
        (item_id, label, None, datetime.now(UTC).isoformat()),
    )
    conn.commit()
    return jsonify({"id": item_id, "label": label})


@app.get("/healthz")
def healthz():
    """Liveness for the container healthcheck.

    Touches the database on purpose: a process that cannot read SQLite is not
    healthy even though it answers HTTP. Returns 503 so an orchestrator
    restarts it rather than serving a broken API.
    """
    try:
        items = db.connect().execute("SELECT COUNT(*) FROM items").fetchone()[0]
    except sqlite3.Error as exc:
        return {"status": "error", "detail": str(exc)}, 503
    return {"status": "ok", "items": items}


if __name__ == "__main__":
    app.run(debug=True)
