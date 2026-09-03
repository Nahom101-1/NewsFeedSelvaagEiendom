"""MVP step 6 — the dashboard.

Flask with server-rendered Jinja. No build step, no bundler, no frontend
framework: the whole point is that this stays maintainable by whoever inherits
it. Caddy sits in front for TLS and basic auth.

    uv run flask --app nyhetsradar.app run --debug
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from flask import Flask, abort, redirect, render_template, request, url_for

from . import config, db

app = Flask(__name__)

# Create the schema if it is missing. A fresh deployment starts with an empty
# volume and the pipeline container may not have run yet; without this both the
# brief and /healthz fail with "no such table: items", so a brand-new install
# serves a broken dashboard and reports itself unhealthy forever. The DDL is
# CREATE TABLE IF NOT EXISTS throughout, so this is idempotent and safe to run
# from every gunicorn worker.
db.init().close()

MONTHS = [
    "januar",
    "februar",
    "mars",
    "april",
    "mai",
    "juni",
    "juli",
    "august",
    "september",
    "oktober",
    "november",
    "desember",
]
MONTHS_SHORT = [
    "jan",
    "feb",
    "mar",
    "apr",
    "mai",
    "jun",
    "jul",
    "aug",
    "sep",
    "okt",
    "nov",
    "des",
]


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


def story_row(row: sqlite3.Row, cluster_size: int) -> dict:
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
    }


@app.get("/")
def brief():
    conn = db.connect()
    now = datetime.now(UTC)
    threshold = config.THRESHOLD

    sizes = dict(
        conn.execute(
            "SELECT cluster_id, COUNT(*) FROM items WHERE cluster_id IS NOT NULL "
            "GROUP BY cluster_id"
        ).fetchall()
    )

    canonical = "(cluster_id = id OR cluster_id IS NULL)"
    rows = conn.execute(
        f"""SELECT * FROM items
            WHERE {canonical} AND score >= ?
            ORDER BY score DESC, COALESCE(published_at, collected_at) DESC
            LIMIT 40""",
        (threshold,),
    ).fetchall()

    collected = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    unique = conn.execute(f"SELECT COUNT(*) FROM items WHERE {canonical}").fetchone()[0]
    over = conn.execute(
        f"SELECT COUNT(*) FROM items WHERE {canonical} AND score >= ?", (threshold,)
    ).fetchone()[0]
    below = conn.execute(
        f"SELECT COUNT(*) FROM items WHERE {canonical} AND gated = 1 AND score < ?",
        (threshold,),
    ).fetchone()[0]

    used_llm = conn.execute("SELECT COUNT(*) FROM items WHERE scorer='haiku'").fetchone()[0]
    blurb = (
        "Rangert av språkmodell mot ledelsesprofilen i config/profile.md."
        if used_llm
        else "Rangert på nøkkelord, kildebredde og ferskhet. Språkmodellen er ikke slått på ennå."
    )

    return render_template(
        "brief.html",
        week=week_window(now),
        kpis={
            "collected": collected,
            "unique": unique,
            "over_threshold": over,
            "pending": below,
        },
        list_name="Alle saker",
        list_count=over,
        list_blurb=blurb,
        threshold=threshold,
        stories=[story_row(r, sizes.get(r["id"], 1)) for r in rows],
        below_count=below,
        generated_at=f"{long_date(now)} {now:%H:%M}",
    )


@app.get("/healthz")
def healthz():
    """Liveness for the container healthcheck.

    Touches the database on purpose: a web process that cannot read SQLite is
    not healthy, even though it answers HTTP. Returns 503 so an orchestrator
    restarts it rather than serving a broken dashboard.
    """
    try:
        conn = db.connect()
        items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    except sqlite3.Error as exc:
        return {"status": "error", "detail": str(exc)}, 503
    return {"status": "ok", "items": items}


@app.post("/feedback/<int:item_id>")
def feedback(item_id: int):
    """Record a relevant / not-relevant judgement.

    Every click is a labelled training example. The embedding column is written
    alongside the label so phase 2 (SetFit) needs no reprocessing — it is NULL
    for now because dedup is still on title similarity rather than nb-sbert-base.
    """
    label = request.form.get("label")
    if label not in {"relevant", "not_relevant"}:
        abort(400)

    conn = db.init()
    if not conn.execute("SELECT 1 FROM items WHERE id=?", (item_id,)).fetchone():
        abort(404)

    conn.execute(
        """INSERT INTO feedback (item_id, label, embedding, created_at) VALUES (?, ?, ?, ?)
           ON CONFLICT(item_id) DO UPDATE SET label=excluded.label,
                                              created_at=excluded.created_at""",
        (item_id, label, None, datetime.now(UTC).isoformat()),
    )
    conn.commit()
    return redirect(url_for("brief"))


if __name__ == "__main__":
    app.run(debug=True)
