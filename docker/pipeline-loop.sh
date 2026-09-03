#!/usr/bin/env bash
# Collection loop for the `pipeline` service.
#
# A plain loop rather than cron-in-a-container: one process, logs to stdout,
# and it dies loudly if something is wrong instead of failing silently into a
# mail spool nobody reads.
set -uo pipefail

INTERVAL="${COLLECT_INTERVAL:-14400}" # four hours, per the plan
: "${SCORE_ARGS:=}"                   # set to "--llm" to enable Haiku summaries

echo "pipeline: starting, interval ${INTERVAL}s, score args '${SCORE_ARGS}'"

# Feeds must be probed at least once before the first collection; on a fresh
# volume config/feeds.toml is baked into the image, so this is a no-op unless
# it is missing.
if [[ ! -f /app/config/feeds.toml ]]; then
  echo "pipeline: no config/feeds.toml, probing candidates"
  python /app/scripts/check_feeds.py --write || echo "pipeline: probe failed, continuing"
fi

while true; do
  started=$(date -u +%FT%TZ)
  echo "pipeline: cycle start ${started}"

  # A failing stage must not kill the loop — the next cycle may well succeed,
  # and a dead scheduler is worse than one bad pass.
  python -m nyhetsradar.collect || echo "pipeline: collect failed"
  python -m nyhetsradar.dedup || echo "pipeline: dedup failed"
  # shellcheck disable=SC2086 -- SCORE_ARGS is intentionally word-split
  python -m nyhetsradar.score ${SCORE_ARGS} || echo "pipeline: score failed"

  echo "pipeline: cycle done, sleeping ${INTERVAL}s"
  sleep "${INTERVAL}"
done
