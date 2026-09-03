# Nyhetsradar

Norwegian property-sector news monitor for Selvaag Eiendom. Collects free RSS,
deduplicates near-identical coverage, filters on keywords, ranks what survives,
and serves a weekly brief.

Built to replace one clip report for one reader. It runs in parallel with the
paid clipping service for two weeks before anyone discusses cancelling anything.

## Quick start

```bash
uv sync
uv run scripts/check_feeds.py --write        # probe sources, write config/feeds.toml
uv run python -m nyhetsradar.collect         # fetch
uv run python -m nyhetsradar.dedup           # cluster duplicates
uv run python -m nyhetsradar.score           # gate + rank
uv run flask --app nyhetsradar.app run       # http://localhost:5000
```

No API key needed — the default scorer is keyword + recency + source breadth and
runs entirely offline. To add Norwegian summaries and a "why this matters"
paragraph, set `ANTHROPIC_API_KEY` in `.env` and run:

```bash
uv sync --extra llm
uv run python -m nyhetsradar.score --llm
```

## How it works

```
collect  →  dedup  →  gate  →  score  →  brief
```

- **collect** stores title, the feed's own snippet, link, source and date.
  Never article bodies — that is a copyright boundary, not an optimisation.
- **dedup** clusters near-identical headlines within a 7-day window. Conflicting
  figures veto a merge, so "Q1 2026" and "Q2 2026" stay separate stories.
- **gate** drops anything matching zero entities and zero themes before it can
  reach a paid API. Crude on purpose.
- **score** ranks the survivors. Own companies outweigh competitors, which
  outweigh places and themes; more sources carrying a story and more recent
  stories both rank higher.

## Sources

All free and public. 14 feeds at last probe.

The three most valuable trade publications — Estate Nyheter, Byggeindustrien and
Kommunal Rapport — have **removed their public RSS feeds**; every documented path
404s. They are reached instead through `site:`-scoped Google News queries, which
return same-day items. Re-run `scripts/check_feeds.py` whenever volume drops;
dead feeds stay commented in `config/candidates.toml`, never deleted.

## Tuning

Behaviour lives in `config/`, not in code.

| File | What it controls |
|---|---|
| `config/profile.md` | The leadership profile. **The primary knob.** |
| `config/entities.toml` | Own companies, competitors, places, institutions |
| `config/themes.toml` | Topic vocabulary |
| `config/candidates.toml` | Source list, probed into `config/feeds.toml` |
| `SCORE_THRESHOLD` | What counts as "over terskel" (default 50) |

One change at a time, so next week's result is attributable.

## Design

`design_handoff_nyhetsradar/` holds the design specification and a working
prototype. Only the **Ukens brief** screen is built; the handoff also specifies
article detail, admin and mobile screens.

Ignore `design_handoff_nyhetsradar/_ds/` — it is a generic design system the
prototype does not use, and building against it produces the wrong palette.

## Tests

```bash
uv run pytest
```

Covers the logic that decides what the reader sees: keyword matching, the gate,
and the duplicate rules. Several tests encode bugs found against real collected
data — read them before relaxing a threshold.
