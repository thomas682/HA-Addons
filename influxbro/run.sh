#!/usr/bin/env bash
export ADDON_VERSION="$(jq -r '.version // empty' /data/options.json 2>/dev/null || true)"
if [ -z "${ADDON_VERSION}" ] || [ "${ADDON_VERSION}" = "null" ]; then
  export ADDON_VERSION=""
fi
set -euo pipefail
OPTIONS_FILE="/data/options.json"
read_opt() { local key="$1"; jq -r ".${key} // empty" "$OPTIONS_FILE"; }
export DELETE_CONFIRM_PHRASE="$(read_opt delete_confirm_phrase)"
python /app/app.py
