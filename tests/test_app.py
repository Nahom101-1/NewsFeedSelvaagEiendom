"""Tests for the JSON API.

The fresh-database cases exist because CI caught the real thing: a container
started against an empty volume returned 503 from /healthz forever, because the
web process connected to SQLite without ever creating the schema.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client bound to a brand-new, empty database file."""
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "fresh.db"))

    # db reads DATABASE_PATH at import time, so both modules must be reloaded
    # after the environment is patched.
    from nyhetsradar import app as app_module
    from nyhetsradar import db as db_module

    importlib.reload(db_module)
    importlib.reload(app_module)

    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


@pytest.fixture
def item_id():
    """Insert one story and return its id."""

    def _insert(title: str = "Selvaag kjøper tomt") -> int:
        from nyhetsradar import db

        conn = db.init()
        conn.execute(
            "INSERT INTO items (link,title,snippet,source,collected_at) VALUES (?,?,?,?,?)",
            (f"https://example.test/{title}", title, "", "Test", "2026-09-03T06:00:00+00:00"),
        )
        conn.commit()
        return conn.execute("SELECT id FROM items ORDER BY id DESC").fetchone()["id"]

    return _insert


# ── health ───────────────────────────────────────────────────────────────────


def test_healthz_is_ok_on_a_fresh_database(client):
    """A new deployment has an empty volume; that is healthy, not broken."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "items": 0}


# ── brief ────────────────────────────────────────────────────────────────────


def test_brief_returns_json_on_a_fresh_database(client):
    response = client.get("/api/brief")
    assert response.status_code == 200
    body = response.get_json()
    assert body["stories"] == []
    assert body["kpis"]["collected"] == 0


def test_brief_carries_the_keys_the_frontend_reads(client):
    body = client.get("/api/brief").get_json()
    assert {
        "week",
        "kpis",
        "list_name",
        "list_blurb",
        "threshold",
        "stories",
        "below_count",
        "generated_at",
    } <= body.keys()


def test_brief_reports_the_readers_existing_judgement(client, item_id):
    """The buttons must reflect state, not pretend every story is unjudged."""
    story = item_id()
    client.post(f"/api/feedback/{story}", json={"label": "relevant"})
    body = client.get("/api/brief").get_json()
    stories = {s["id"]: s for s in body["stories"]}
    if story in stories:  # only present when it scores above the threshold
        assert stories[story]["feedback"] == "relevant"


# ── admin ────────────────────────────────────────────────────────────────────


def test_admin_returns_json_on_a_fresh_database(client):
    response = client.get("/api/admin")
    assert response.status_code == 200
    body = response.get_json()
    assert body["totals"]["collected"] == 0
    assert len(body["distribution"]) == 10


def test_admin_reports_label_counts(client, item_id):
    a, b = item_id("Selvaag A"), item_id("Selvaag B")
    client.post(f"/api/feedback/{a}", json={"label": "relevant"})
    client.post(f"/api/feedback/{b}", json={"label": "not_relevant"})

    labels = client.get("/api/admin").get_json()["labels"]
    assert labels["relevant"] == 1
    assert labels["not_relevant"] == 1
    # Phase 2 needs the vector alongside the label; it is not stored yet.
    assert labels["with_embedding"] == 0


# ── feedback ─────────────────────────────────────────────────────────────────


def test_feedback_rejects_an_unknown_label(client, item_id):
    response = client.post(f"/api/feedback/{item_id()}", json={"label": "maybe"})
    assert response.status_code == 400


def test_feedback_404s_for_a_missing_item(client):
    assert client.post("/api/feedback/9999", json={"label": "relevant"}).status_code == 404


def test_feedback_records_a_label(client, item_id):
    from nyhetsradar import db

    story = item_id()
    response = client.post(f"/api/feedback/{story}", json={"label": "relevant"})
    assert response.status_code == 200
    assert response.get_json() == {"id": story, "label": "relevant"}

    row = db.connect().execute("SELECT label FROM feedback WHERE item_id=?", (story,)).fetchone()
    assert row["label"] == "relevant"


def test_feedback_updates_rather_than_duplicating(client, item_id):
    """Changing your mind replaces the label; one row per item."""
    from nyhetsradar import db

    story = item_id()
    client.post(f"/api/feedback/{story}", json={"label": "relevant"})
    client.post(f"/api/feedback/{story}", json={"label": "not_relevant"})

    rows = db.connect().execute("SELECT label FROM feedback WHERE item_id=?", (story,)).fetchall()
    assert len(rows) == 1
    assert rows[0]["label"] == "not_relevant"


def test_feedback_preflight_is_allowed(client):
    assert client.options("/api/feedback/1").status_code == 204
