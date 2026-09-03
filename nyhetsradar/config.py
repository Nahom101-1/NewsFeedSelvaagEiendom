"""Loading of the tuning surface in config/.

Behaviour lives in config, not in code. Nothing here caches across processes, so
editing a config file and re-running a pipeline step picks the change up.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"

# Load .env before anything reads os.environ, so ANTHROPIC_API_KEY and
# SCORE_THRESHOLD work from the file as well as from the shell.
load_dotenv(ROOT / ".env")

# Score at or above which a story is "over terskel" and shown in the brief.
# 50 was picked against real collected data: at 55 the brief showed 7 stories and
# cut obviously-relevant ones ("Obos og Selvaag topper salgsstatistikken") that
# scored 50-52. Tune against the under-15-per-day target, not by taste.
THRESHOLD = int(os.environ.get("SCORE_THRESHOLD", "50"))


def _flatten(table: dict) -> list[str]:
    """Collapse a grouped TOML table into one lowercase term list."""
    terms: list[str] = []
    for value in table.values():
        if isinstance(value, list):
            terms.extend(str(v).lower() for v in value)
    return terms


def feeds() -> list[dict]:
    path = CONFIG / "feeds.toml"
    if not path.exists():
        raise FileNotFoundError(
            "config/feeds.toml missing — run `uv run scripts/check_feeds.py --write` first"
        )
    return tomllib.loads(path.read_text()).get("feed", [])


def entities() -> dict[str, list[str]]:
    """Entity terms grouped by kind, lowercased. Groups carry different weights."""
    table = tomllib.loads((CONFIG / "entities.toml").read_text())
    return {group: [str(t).lower() for t in terms] for group, terms in table.items()}


def entity_terms() -> list[str]:
    return _flatten(tomllib.loads((CONFIG / "entities.toml").read_text()))


def theme_terms() -> list[str]:
    return _flatten(tomllib.loads((CONFIG / "themes.toml").read_text()))


def profile() -> str:
    """The leadership profile paragraph, passed to the LLM scorer verbatim."""
    return (CONFIG / "profile.md").read_text()
