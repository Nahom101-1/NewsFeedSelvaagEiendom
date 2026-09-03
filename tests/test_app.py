"""Tests for the web layer.

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


def test_healthz_is_ok_on_a_fresh_database(client):
    """A new deployment has an empty volume; that is healthy, not broken."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "items": 0}


def test_brief_renders_on_a_fresh_database(client):
    """No stories yet must still produce a page, not a 500."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"UKENS BRIEF" in response.data.upper() or b"ukens brief" in response.data.lower()


def test_feedback_rejects_an_unknown_label(client):
    assert client.post("/feedback/1", data={"label": "maybe"}).status_code == 400


def test_feedback_404s_for_a_missing_item(client):
    assert client.post("/feedback/9999", data={"label": "relevant"}).status_code == 404


def test_feedback_records_a_label(client):
    from nyhetsradar import db

    conn = db.init()
    conn.execute(
        "INSERT INTO items (link,title,snippet,source,collected_at) VALUES (?,?,?,?,?)",
        ("https://example.test/1", "Selvaag kjøper tomt", "", "Test", "2026-09-03T06:00:00+00:00"),
    )
    conn.commit()
    item_id = conn.execute("SELECT id FROM items").fetchone()["id"]

    assert client.post(f"/feedback/{item_id}", data={"label": "relevant"}).status_code == 302

    row = db.connect().execute("SELECT label FROM feedback WHERE item_id=?", (item_id,)).fetchone()
    assert row["label"] == "relevant"


def test_feedback_updates_rather_than_duplicating(client):
    """Changing your mind replaces the label; one row per item."""
    from nyhetsradar import db

    conn = db.init()
    conn.execute(
        "INSERT INTO items (link,title,snippet,source,collected_at) VALUES (?,?,?,?,?)",
        ("https://example.test/2", "Selvaag selger tomt", "", "Test", "2026-09-03T06:00:00+00:00"),
    )
    conn.commit()
    item_id = conn.execute("SELECT id FROM items").fetchone()["id"]

    client.post(f"/feedback/{item_id}", data={"label": "relevant"})
    client.post(f"/feedback/{item_id}", data={"label": "not_relevant"})

    rows = db.connect().execute("SELECT label FROM feedback WHERE item_id=?", (item_id,)).fetchall()
    assert len(rows) == 1
    assert rows[0]["label"] == "not_relevant"
