---
name: pipeline-status
description: Report the current state of the pipeline — volume, dedup collapse ratio, keyword gate pass rate, items surfaced per day, and feedback labels collected. Use to check health or before deciding what to tune.
allowed-tools: Bash(sqlite3 data/news.db *), Read
---

Read the pipeline's numbers out of SQLite. No changes, no proposals — just the state.

## Query

Against `data/news.db`, over the last 7 days unless told otherwise:

1. **Raw volume** — items collected per day. The step 2 question was whether this is 80/day
   or 800/day; the answer drives everything downstream.
2. **Collapse ratio** — items in, canonical items out, after dedup. If syndication is as
   heavy as expected this cuts volume by a third or more. This number is worth showing to
   whoever approves the project.
3. **Gate pass rate** — how many survivors matched at least one entity or theme.
4. **Scored** — how many reached the scorer, and the score distribution.
5. **Surfaced per day** — items above the dashboard's score threshold. **Target is under
   15.** A digest nobody finishes reading has failed regardless of recall.
6. **Feedback labels** — relevant/not-relevant counts, and how many have an embedding
   stored alongside. Phase 2 needs a few hundred; report progress toward that.
7. **API spend**, if the LLM scorer is enabled — scored item count × observed tokens, and
   whether calls went through the Batch API (half price).

## Report

The numbers, each with its trend against the prior week. Then one line naming the stage
that looks most out of line — but stop there. Diagnosing *why* is `relevance-analyst`'s
job, and proposing config edits is `/weekly-review`'s.

If a table doesn't exist yet, say which MVP step hasn't been built rather than guessing.
