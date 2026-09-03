# CLAUDE.md — Nyhetsradar (NewsFeedSelvaagEiendom)

Norwegian property-sector news monitor for Selvaag Eiendom. Collects free RSS,
deduplicates near-identical coverage, gates on keywords, ranks, and serves a
weekly brief from a small Flask dashboard.

Interface language is **Norwegian**. Code, comments and commits are English.

## Where things are

This project lives at `Developer/projects/NewsFeedSelvaagEiendom/`. A stray
duplicate exists at `Developer/projects/nahom.no/NewsFeedSelvaagEiendom/` from a
misplaced folder move — it is not the project and should be deleted once
confirmed unneeded. `nahom.no` is a separate portfolio repo; nothing for this
project belongs inside it.

GitHub Actions workflows live at the **repo root** (`projects/.github/workflows/`),
not in this subdirectory — Actions only reads workflows from the root.

## Dev commands

```bash
uv sync                                        # install deps
uv sync --extra llm                            # + anthropic, for LLM scoring

uv run scripts/check_feeds.py                  # probe feeds, report health
uv run scripts/check_feeds.py --write          # rewrite config/feeds.toml

uv run python -m nyhetsradar.collect           # step 2: fetch into SQLite
uv run python -m nyhetsradar.dedup             # step 3: cluster duplicates
uv run python -m nyhetsradar.score             # steps 4-5: gate + keyword rank
uv run python -m nyhetsradar.score --llm       # + Haiku summaries (needs API key)

uv run flask --app nyhetsradar.app run --debug # step 6: dashboard on :5000
uv run ruff check . && uv run ruff format .
```

Cron, every four hours: `collect` → `dedup` → `score`.

## Stack

Python 3.11+ via **uv** (there is a `uv.lock`; do not switch to poetry/pipenv).
Flask + server-rendered Jinja, no build step, no bundler, no frontend framework.
SQLite at `data/news.db`. `feedparser` for RSS. Caddy in front for TLS and basic
auth. `anthropic` is an **optional** dependency — the pipeline runs without it.

## Sources — all free, and the trade press needs a workaround

**Finding from step 1 (2026-09-03), do not re-litigate without re-probing:** the
three most valuable trade publications — Estate Nyheter, Byggeindustrien
(bygg.no) and Kommunal Rapport — have **removed their public RSS feeds**. Every
documented path 404s and none advertise a `rel="alternate"` feed.

They are reachable instead through `site:`-scoped Google News RSS queries, which
return same-day items for free. Those are the `type = "bransje"` entries in
`config/feeds.toml`. If a publisher restores a real feed, prefer it — the direct
feed carries better snippets and a cleaner source name.

14 of 14 configured feeds were alive at last probe. Dead candidates stay
commented out in `config/candidates.toml` with the date and failure — never
delete them.

## Pipeline

```
collect → dedup → gate → score → brief
```

- **collect** — title, feed snippet, link, source, date. Google News titles have
  their trailing " - Publisher" stripped, and the real publisher is read from the
  entry's `source` element rather than recording everything as "Google News".
- **dedup** — title similarity, threshold 0.82, 7-day window. Currently 2%
  collapse, which is *correct* for a one-shot backfill spanning months; real
  syndication overlap appears once the cron is collecting the same day
  repeatedly. Do not lower the threshold to chase a bigger number — at 0.80,
  "Boligprisene steg 0,5 prosent i februar" merges with "falt 2,6 prosent i
  juli", which are different stories.
- **gate** — an item matching zero entities and zero themes never reaches the
  scorer. Crude on purpose; it exists to keep the API bill near zero.
- **score** — keyword + recency + cluster-size by default (no API key, no
  network). With `--llm`, top candidates additionally go to Haiku for a
  Norwegian summary and a "derfor er dette relevant" sentence.

## Hard constraints

Violating one is a bug even if the tests pass.

- **Never store article bodies.** The schema holds title, the feed's own snippet,
  link, source and date. This is a copyright boundary, in from day one so it
  never has to be retrofitted.
- **The gate runs before every API call.** A code path that scores an ungated
  item turns a near-zero bill into an open-ended one.
- **Dead feeds stay commented in config, never deleted.**
- **Feedback clicks store the embedding alongside the label.** Currently NULL
  because dedup is on title similarity; when `nb-sbert-base` lands, backfill it.
  A label without a vector is useless to phase 2.
- **Don't touch architecture during pilot weeks 1–3.** Every problem in that
  window is a relevance problem. The fix is config text.

## Tuning surface

Behaviour lives in `config/`, not in code.

- `config/profile.md` — the leadership profile. **Primary knob.** Most of the
  first month's work is here. One edit at a time; commit message names the miss.
- `config/entities.toml` — own companies, competitors, places, institutions.
  Groups carry different scoring weights.
- `config/themes.toml` — topic vocabulary.
- `config/candidates.toml` → `config/feeds.toml` — sources, via the prober.
- `SCORE_THRESHOLD` env var (default 55) — what counts as "over terskel".

## Frontend

`design_handoff_nyhetsradar/` is the design authority — a high-fidelity spec with
exact hex values, type scale, spacing and interaction states, plus a working
prototype (`Nyhetsradar.dc.html`).

- **Ignore `design_handoff_nyhetsradar/_ds/`.** It is a generic "Modernist"
  system with a red accent that the prototype does not import. Using it produces
  the wrong palette.
- Palette: petroleum `#00313B`, rust `#B7592E`, fromage `#FAF2CF`, paper
  `#FFFEF9`, sand `#E3DBCC`, mint `#85B590`.
- **Border radius 0 everywhere. No box-shadow anywhere.**
- Archivo and Source Serif 4 stand in for the licensed Selvaag Sans and Tiempos.
  Swap both in a real deployment; sizes and tracking carry over unchanged.
- Norwegian formatting: decimal comma, lowercase months, space thousands
  separator.

Only the **Ukens brief** screen is built. The handoff also specifies article
detail, admin, and mobile screens — not built yet.

## Scope

The design handoff describes the full product; the MVP is deliberately smaller.
Not built, and not to be built without a decision:

- **Watchlists** (per-role and per-person). The design centres on them; the MVP
  has a single implicit list.
- **SetFit classifier** and nearest-training-example explanations. Needs a few
  hundred labels that do not exist yet — the MVP's second job is generating them.
- Article detail and admin screens, Teams push, digest send, archive search.
- Brønnøysund counterparty alerting, story threading, absence detection, the
  land-banking map. Phases 2–4.

Embeddings, when they arrive, are for deduplication and the phase-2 training set
— not for semantic search.

## Success criteria

Track weekly during the pilot: items surfaced, items marked relevant, and **how
many things the paid clipping service caught that the dashboard missed**. The
third number decides whether this lives.

Done means: the reader prefers the dashboard 3 weeks of 4, fewer than 2
significant misses per week, and **under 15 items surfaced per day** — a digest
nobody finishes has failed regardless of recall.

If the miss count stays high, the answer is **more sources, not more machine
learning**.
