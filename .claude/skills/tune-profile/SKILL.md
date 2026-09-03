---
name: tune-profile
description: Turn one specific bad result into a proposed edit to the leadership profile paragraph. Use when a single item was surfaced that shouldn't have been, or missed when it shouldn't have been.
disable-model-invocation: true
argument-hint: "[item id, URL, or a description of what went wrong]"
allowed-tools: Bash(sqlite3 data/news.db *), Read, Edit
---

Tune `config/profile.md` — the paragraph describing what leadership cares about and, more
importantly, what they don't. This text is where most of the first month's work happens.

Target: $ARGUMENTS

## Steps

1. Find the item. Pull its title, source, score, category, summary, and the model's own
   **why-it-matters sentence** — that sentence usually names the part of the profile text
   that misfired, in the model's own words.
2. Read the current `config/profile.md` and identify the specific clause responsible.
3. Decide which direction the profile is wrong:
   - **False positive** — the profile describes an interest too broadly, or omits a
     "not this" exclusion. Usually the fix is adding what leadership *doesn't* care about,
     which is the half of the paragraph people under-write.
   - **False negative** — an interest is missing or stated too narrowly.
4. Check the edit against recent items before proposing it. A clause that fixes this item
   and breaks four others is a worse paragraph. Say what else it would have changed.

## Rules

- **Edit the profile text, not the code.** If the item never reached the model, the profile
  is not the problem — say which stage dropped it and stop.
- Keep the paragraph readable prose. It is a description of a reader, not a rule list; a
  bulleted rulebook scores worse than a coherent description of what someone cares about.
- Change one thing. Two simultaneous edits make the next week's result unattributable.

## Output

The exact before and after text, what else in the recent set the change would have
affected, and a commit message in this shape:

```
profile: <what changed>

Prompted by: <the item and what went wrong>
Expected effect: <what should score differently now>
```

Apply the edit only if the user asks; otherwise leave it as a proposal.
