---
paths:
  - "config/**"
---

# Config rules

`config/` is the tuning surface. Behaviour changes belong here, not in code — during the
pilot, editing this directory is the intended fix for almost every complaint about output.

## profile.md

The paragraph describing what leadership cares about and, more importantly, **what they
don't**. This is the primary knob; most of the first month's work happens in this file.

- Keep it prose. It describes a reader, not a rulebook — a bulleted rule list scores worse
  than a coherent description of someone's priorities.
- The exclusions matter as much as the inclusions, and are the half people under-write.
- **One change at a time.** Two simultaneous edits make the next week's result
  unattributable.
- Every edit gets a commit message saying what changed and which miss prompted it. The
  tuning history is meant to be readable a month later.

## feeds.toml

Dead feeds are **commented out, never deleted**, with the date and the observed failure.
The record of what was tried is the point — a deleted URL gets rediscovered and re-tried
by someone in three months.

## entities.toml / themes.toml

The keyword gate's vocabulary. Adding a term widens what reaches the model and costs money;
removing one narrows it and risks misses. Say which direction a change moves the volume.

Crude matching is intentional. This gate exists to keep the API bill near zero, not to be
accurate — accuracy is the model's job, one stage later.
