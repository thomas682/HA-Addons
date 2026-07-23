#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."
timestamp=$(date -u +"%Y-%m-%d_%H-%M-%S_UTC")
short_sha=$(git rev-parse --short HEAD)
backup_dir="savefiles/AGENTS_backup_${timestamp}_manual_${short_sha}"
mkdir -p "$backup_dir"
cp AGENTS.md "$backup_dir/AGENTS.changed.md"
git show origin/main:AGENTS.md > "$backup_dir/AGENTS.main-before-change.md"
git diff --no-index "$backup_dir/AGENTS.main-before-change.md" "$backup_dir/AGENTS.changed.md" > "$backup_dir/AGENTS.diff" || true
printf 'Manual AGENTS backup: %s\n' "$backup_dir"
