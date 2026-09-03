"""SQLite storage.

Schema constraint, enforced here and not negotiable: we store the title, the
feed's own snippet, the link, the source and the date. We never store article
bodies. That is a copyright boundary, and it went in on day one precisely so it
never has to be retrofitted.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from .config import ROOT

DB_PATH = Path(os.environ.get("DATABASE_PATH", ROOT / "data" / "news.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id            INTEGER PRIMARY KEY,
    -- Identity
    link          TEXT NOT NULL UNIQUE,
    title         TEXT NOT NULL,
    snippet       TEXT NOT NULL DEFAULT '',   -- the feed's own snippet. Never the article body.
    source        TEXT NOT NULL,
    source_type   TEXT NOT NULL DEFAULT '',
    published_at  TEXT,                        -- ISO 8601 UTC
    collected_at  TEXT NOT NULL,

    -- Stage 3: deduplication
    cluster_id    INTEGER,                     -- canonical item id; equals own id for canonicals

    -- Stage 4: keyword gate
    gated         INTEGER,                     -- 1 = passed the gate, 0 = blocked, NULL = not run
    entity_hits   TEXT NOT NULL DEFAULT '',    -- comma-separated matched terms
    theme_hits    TEXT NOT NULL DEFAULT '',

    -- Stage 5: scoring
    score         INTEGER,                     -- 0-100
    scorer        TEXT,                        -- 'keyword' or 'haiku'
    summary_no    TEXT,                        -- one-line Norwegian summary
    why_matters   TEXT,                        -- why it matters to Selvaag Eiendom
    scored_at     TEXT
);

CREATE INDEX IF NOT EXISTS items_published ON items(published_at DESC);
CREATE INDEX IF NOT EXISTS items_cluster   ON items(cluster_id);
CREATE INDEX IF NOT EXISTS items_score     ON items(score DESC);

-- Every relevant / not-relevant click. The embedding is stored alongside the
-- label so phase 2 (SetFit) has a training set that needs no reprocessing.
-- Writing the label without the vector makes the row useless.
CREATE TABLE IF NOT EXISTS feedback (
    id          INTEGER PRIMARY KEY,
    item_id     INTEGER NOT NULL REFERENCES items(id),
    label       TEXT NOT NULL CHECK (label IN ('relevant', 'not_relevant')),
    embedding   BLOB,
    created_at  TEXT NOT NULL,
    UNIQUE(item_id)
);

-- One row per collection pass, so /pipeline-status can show trends.
CREATE TABLE IF NOT EXISTS runs (
    id            INTEGER PRIMARY KEY,
    started_at    TEXT NOT NULL,
    finished_at   TEXT,
    feeds_ok      INTEGER DEFAULT 0,
    feeds_failed  INTEGER DEFAULT 0,
    seen          INTEGER DEFAULT 0,
    inserted      INTEGER DEFAULT 0,
    note          TEXT
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init() -> sqlite3.Connection:
    conn = connect()
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
