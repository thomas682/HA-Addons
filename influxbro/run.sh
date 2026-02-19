#!/usr/bin/env bash
export ADDON_VERSION="$(jq -r '.version' /data/options.json 2>/dev/null || echo dev)"
set -euo pipefail
OPTIONS_FILE="/data/options.json"
read_opt() { local key="$1"; jq -r ".${key} // empty" "$OPTIONS_FILE"; }
export ALLOW_DELETE="$(read_opt allow_delete)"
export DELETE_CONFIRM_PHRASE="$(read_opt delete_confirm_phrase)"
python /app/app.py
