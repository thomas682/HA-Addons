#!/usr/bin/env bash
export ADDON_VERSION="$(jq -r '.version // empty' /data/options.json 2>/dev/null || true)"
if [ -z "${ADDON_VERSION}" ] || [ "${ADDON_VERSION}" = "null" ]; then
  export ADDON_VERSION=""
fi
set -euo pipefail
OPTIONS_FILE="/data/options.json"
read_opt() { local key="$1"; jq -r ".${key} // empty" "$OPTIONS_FILE"; }
export DELETE_CONFIRM_PHRASE="$(read_opt delete_confirm_phrase)"

# Expose /data/share under Home Assistant config tree so it is visible in the Filebrowser.
# Target: /config/influxbro
TARGET_SHARE_DIR="/config/influxbro"
SRC_SHARE_DIR="/data/share"

mkdir -p "${TARGET_SHARE_DIR}"

# Migrate existing /data/share contents into /config (best-effort), then replace with a symlink.
if [ -L "${SRC_SHARE_DIR}" ]; then
  true
else
  if [ -d "${SRC_SHARE_DIR}" ]; then
    shopt -s dotglob nullglob
    if [ -n "$(ls -A "${SRC_SHARE_DIR}" 2>/dev/null || true)" ]; then
      mv "${SRC_SHARE_DIR}"/* "${TARGET_SHARE_DIR}"/ 2>/dev/null || true
    fi
    rm -rf "${SRC_SHARE_DIR}" || true
  elif [ -e "${SRC_SHARE_DIR}" ]; then
    rm -f "${SRC_SHARE_DIR}" || true
  fi

  ln -s "${TARGET_SHARE_DIR}" "${SRC_SHARE_DIR}" || true
fi

python /app/app.py
