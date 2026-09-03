---
paths:
  - "pipeline/**/*.py"
  - "scripts/**/*.py"
  - "app.py"
---

# Pipeline rules

## Storage

The `items` table holds **title, feed snippet, link, source, published date** — and
nothing more. Never add a column for article body, full text, extracted content, or a
cached copy of the page. This is a copyright boundary and it went in on day one precisely
so it never has to be retrofitted.

If a task seems to need the body, it doesn't: the feed's own snippet is what the model
scores, and the link is what the reader clicks.

## Order of operations

Collection → dedup → keyword gate → model. The gate is not optional and not reorderable.

An item matching zero entities **and** zero themes must never reach the Anthropic API.
Any code path that scores an ungated item is a bug — it converts a near-zero API bill into
an open-ended one. When adding a scoring entry point, the gate check goes in it, not in
the caller.

## Dedup

`NbAiLab/nb-sbert-base` over title + snippet, cosine similarity above ~0.85, within a
rolling 7-day window. Keep one canonical item per cluster and record the rest as
additional coverage — don't discard them, the coverage count is signal.

Record the measured collapse ratio; it is a number worth reporting to stakeholders.

## Feedback

Every relevant / not-relevant click writes the label **with the item's embedding attached**.
Writing the label alone makes the row useless for phase 2, which needs a training set
that doesn't require reprocessing. This is the highest-value data the MVP produces.

## Model calls

- `claude-haiku-4-5`, batches of 15, via the Batch API (50% cheaper; latency doesn't matter)
- Structured outputs via `output_config={"format": {...}}` — never hand-parse JSON from prose
- No assistant prefill; no `output_config.effort` (errors on Haiku 4.5)
- Check `stop_reason` before reading `response.content`
- The scoring prompt's variable part is `config/profile.md`, loaded at call time — never
  inline that text into a Python string literal, or tuning stops being a config edit

## Scope

Do not add: Brønnøysund lookups, counterparty alerting, Teams push, story threading,
watchlists, a trained classifier, or semantic search. Those are phase 2–4. Embeddings
exist here for deduplication only.
