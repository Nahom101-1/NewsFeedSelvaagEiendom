#!/usr/bin/env bash
# Surface pipeline state at session start so Claude knows which MVP step is live.
# Degrades silently before the DB exists.
set -uo pipefail

DB="${CLAUDE_PROJECT_DIR:-.}/data/news.db"
[[ -f "$DB" ]] || exit 0
command -v sqlite3 >/dev/null 2>&1 || exit 0

q() { sqlite3 "$DB" "$1" 2>/dev/null || echo "?"; }

items=$(q "SELECT count(*) FROM items;")
latest=$(q "SELECT max(collected_at) FROM items;")
labels=$(q "SELECT count(*) FROM feedback;")

printf 'Pipeline: %s items stored, last collection %s, %s feedback labels.\n' \
  "$items" "${latest:-never}" "$labels"
exit 0
