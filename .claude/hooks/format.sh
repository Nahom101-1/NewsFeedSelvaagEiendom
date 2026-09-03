#!/usr/bin/env bash
# Format Python files with ruff after Claude edits them.
# Exits 0 always — a formatting failure should never block the edit.
set -uo pipefail

input=$(cat)
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')

[[ -z "$file_path" || "$file_path" != *.py || ! -f "$file_path" ]] && exit 0
command -v uv >/dev/null 2>&1 || exit 0

uv run ruff format "$file_path" >/dev/null 2>&1
uv run ruff check --fix "$file_path" >/dev/null 2>&1
exit 0
