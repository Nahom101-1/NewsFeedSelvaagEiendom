---
name: weekly-review
description: The MVP step 8 weekly tuning ritual — record the three pilot metrics, read the misses, and propose one profile edit. Run once a week during the pilot.
disable-model-invocation: true
argument-hint: "[week number, e.g. 2]"
allowed-tools: Bash(sqlite3 data/news.db *), Read, Grep, Glob
---

The weekly pilot loop. Expect week one to be noisy and week three to be decent.

## 1. The three numbers

Record for week $0 (or the last 7 days if no week given):

1. How many items the dashboard **surfaced**
2. How many the reader marked **relevant**
3. **How many things the paid clipping service caught that the dashboard missed**

Number three decides whether this project lives. If it isn't available from the DB, ask
the user for it rather than reporting the week without it.

Compare against the bar: reader prefers the dashboard, under 2 significant misses per
week, under 15 items surfaced per day.

## 2. Read the misses

Pull the items the reader marked not-relevant, and any known misses from number three
above. Delegate to the `relevance-analyst` subagent to establish which pipeline stage each
one failed at — source gap, dedup collapse, keyword gate, or score. Don't diagnose inline;
the analyst has the method and a clean context for it.

## 3. Propose exactly one change

One edit per week, so the effect is attributable. In priority order:

- **Profile text** (`config/profile.md`) — the primary knob. Most weeks this is the answer.
- **A keyword** in `config/entities.toml` or `config/themes.toml` — when items were gated
  out before reaching the scorer.
- **A feed** — when items were never collected at all. High miss counts mean *more
  sources, not more machine learning*.

Give the exact before/after text and the commit message naming the miss that prompted it.

**Do not propose architecture, schema, or model changes.** Every problem in weeks 1–3 is
a relevance problem. If you genuinely believe a code change is needed, say so in one
sentence and propose the config change anyway — the user decides whether to break the rule.

## 4. Output

A short written record, suitable to paste into the pilot log:

```
Week N
  Surfaced:        X/day avg
  Marked relevant: Y
  Misses vs clip:  Z
  Change:          <one line>
  Rationale:       <the miss that prompted it>
```

Then the proposed diff. Apply nothing without the user's go-ahead.
