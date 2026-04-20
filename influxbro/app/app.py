import csv
from collections import deque
import fnmatch
import gzip
import hashlib
import inspect
import io
import json
import logging
import logging.handlers
import math
import os
import re
import shutil
import socket
import select
import ssl
import sys
import subprocess
import tempfile
import threading
import time
import uuid
import urllib.error
import urllib.request
import urllib.parse
import zipfile
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from flask import Flask, Response, abort, g, jsonify, make_response, render_template, request, send_file
from influxdb_client import InfluxDBClient
from influxdb_client import Point
from influxdb_client import WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb import InfluxDBClient as InfluxDBClientV1

import yaml # pyright: ignore[reportMissingModuleSource]

CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "/config"))
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))

PROCESS_STARTED_AT = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
PROCESS_STARTED_MONO = time.monotonic()

APP_DIR = Path(__file__).resolve().parent
DEFAULT_BACKUP_DIR = CONFIG_DIR / "influxbro" / "backup"
OLD_DEFAULT_BACKUP_DIR = DATA_DIR / "backups"
FIXED_REPO_URL = "https://github.com/thomas682/HA-Addons"

# default; may be overridden via UI config
BACKUP_DIR = DEFAULT_BACKUP_DIR

GLOBAL_STATS_JOBS: dict[str, dict[str, Any]] = {}
GLOBAL_STATS_LOCK = threading.RLock()

HISTORY_LOCK = threading.RLock()
HISTORY_PATH = DATA_DIR / "influxbro_history.jsonl"

# Cache usage log (for UI + optional server log)
CACHE_USAGE_LOCK = threading.RLock()
CACHE_USAGE_MAX_MEM = 2000
CACHE_USAGE_MEM: "deque[dict[str, Any]]" = deque(maxlen=CACHE_USAGE_MAX_MEM)
CACHE_USAGE_PATH = DATA_DIR / "influxbro_cache_usage.jsonl"
UI_ACTIONS_LOCK = threading.RLock()
UI_ACTIONS_MAX_MEM = 200
UI_ACTIONS_MEM: "deque[dict[str, Any]]" = deque(maxlen=UI_ACTIONS_MAX_MEM)
UI_ACTIONS_PATH = DATA_DIR / "influxbro_ui_actions.jsonl"

TRACE_LOCK = threading.RLock()
TRACE_PATH = DATA_DIR / "influxbro_traces.json"
TRACE_ENABLED = True
TRACE_PERSIST = True
TRACE_MAX_ENTRIES = 1000
TRACE_MAX_DAYS = 14
TRACE_LAST_WRITE_MONO = 0.0
# Recents/LRU order of trace_ids (oldest -> newest). We keep it bounded manually so
# we can also evict TRACE_INDEX entries.
TRACE_MEM: "deque[str]" = deque()
TRACE_INDEX: dict[str, dict[str, Any]] = {}
ANALYSIS_HISTORY_LOCK = threading.RLock()
WORKLOG_MAX_ENTRIES = 2000
WORKLOG_MAX_DAYS = 14
WORKLOG_LAST_PRUNE_MONO = 0.0
ANALYSIS_HISTORY_MEM: "deque[dict[str, Any]]" = deque()
ANALYSIS_HISTORY_PATH = DATA_DIR / "influxbro_analysis_history.jsonl"
QUALITY_CLEANUP_LOG_PATH = DATA_DIR / "influxbro_quality_cleanup.jsonl"
MONITOR_LOCK = threading.RLock()
MONITOR_CFG_PATH = DATA_DIR / "influxbro_monitoring_config.json"
MONITOR_STATE_PATH = DATA_DIR / "influxbro_monitoring_state.json"
MONITOR_PENDING_PATH = DATA_DIR / "influxbro_monitoring_pending.json"
MONITOR_EVENTS_PATH = DATA_DIR / "influxbro_monitoring_events.jsonl"
JOBS_HISTORY_PATH = DATA_DIR / "influxbro_jobs_history.json"

# Timers state (last run timestamps, persisted under /data)
TIMERS_STATE_LOCK = threading.RLock()
TIMERS_STATE_PATH = DATA_DIR / "influxbro_timers_state.json"

# Influx connectivity status (best-effort, cached)
INFLUX_PING_LOCK = threading.RLock()
INFLUX_PING_CACHE: dict[str, Any] = {}

# UI state store (file-based; used to persist GUI selections across add-on restarts)
UI_STATE_LOCK = threading.RLock()
UI_STATE_PATH = DATA_DIR / "influxbro_ui_state.json"

APP_STATE_LOCK = threading.RLock()
APP_STATE_PATH = DATA_DIR / "influxbro_app_state.json"

# UI profiles (file-based; global active profile)
UI_PROFILES_LOCK = threading.RLock()
UI_PROFILES_DIR = DATA_DIR / "ui_profiles"
UI_PROFILE_ACTIVE_PATH = DATA_DIR / "ui_profile_active.json"

# Dashboard last graph pointer (file-based; restore across browser sessions)
DASH_LAST_LOCK = threading.RLock()
DASH_LAST_PATH = DATA_DIR / "influxbro_dashboard_last.json"

ANALYSIS_START_CACHE_LOCK = threading.RLock()
ANALYSIS_START_CACHE_PATH = DATA_DIR / "analysis_series_start_cache.json"

# toggled via config (configure_logging)
CACHE_USAGE_LOGGING = False

EXPORT_DIR = DATA_DIR / "exports"
IMPORT_DIR = DATA_DIR / "imports"


def export_dir_from_target(target: str | None) -> Path:
    """Resolve an export target directory (constrained under /data or /config)."""

    raw = str(target or "").strip()
    if not raw:
        return EXPORT_DIR
    try:
        p = Path(raw)
        if not p.is_absolute():
            # Relative paths live under /data.
            p = DATA_DIR / raw
        p = p.resolve()
        cfg_root = CONFIG_DIR.resolve()
        data_root = DATA_DIR.resolve()
        if _path_is_within(cfg_root, p) or _path_is_within(data_root, p):
            return p
    except Exception:
        pass
    return EXPORT_DIR

# Dashboard query cache (server-side, persisted under /data)
DASH_CACHE_DIR = DATA_DIR / "dash_cache"
DASH_CACHE_LOCK = threading.RLock()

# Analysis cache (server-side, persisted under /data)
ANALYSIS_CACHE_DIR = DATA_DIR / "analysis_cache"
ANALYSIS_CACHE_LOCK = threading.RLock()

DASH_CACHE_JOBS: dict[str, dict[str, Any]] = {}
DASH_CACHE_JOBS_LOCK = threading.RLock()

# Statistik cache (server-side, persisted under /data)
STATS_CACHE_DIR = DATA_DIR / "stats_cache"
STATS_CACHE_LOCK = threading.RLock()

# Per-series statistics cache for /api/stats (persistent under /data)
SERIES_STATS_CACHE_DIR = DATA_DIR / "series_stats_cache"
SERIES_STATS_CACHE_LOCK = threading.RLock()

RESTORE_COPY_JOBS: dict[str, dict[str, Any]] = {}
RESTORE_COPY_LOCK = threading.RLock()

COMBINE_JOBS: dict[str, dict[str, Any]] = {}
COMBINE_LOCK = threading.RLock()

ANALYSIS_CACHE_PATCH_JOBS: dict[str, dict[str, Any]] = {}
ANALYSIS_CACHE_PATCH_LOCK = threading.RLock()

# Nightly analysis refresh jobs
ANALYSIS_NIGHTLY_JOBS: dict[str, dict[str, Any]] = {}
ANALYSIS_NIGHTLY_LOCK = threading.RLock()

ANALYSIS_CACHE_CHECKPOINT_SECONDS = 3600
ANALYSIS_CACHE_PATCH_PADDING_SECONDS = 300
ANALYSIS_CACHE_PATCH_MAX_SPAN_SECONDS = 7200

BACKUP_JOBS: dict[str, dict[str, Any]] = {}
EXPORT_JOBS: dict[str, dict[str, Any]] = {}
BACKUP_LOCK = threading.RLock()
EXPORT_LOCK = threading.RLock()

FULLBACKUP_JOBS: dict[str, dict[str, Any]] = {}
FULLBACKUP_LOCK = threading.RLock()

FULLRESTORE_JOBS: dict[str, dict[str, Any]] = {}
FULLRESTORE_LOCK = threading.RLock()


def _req_ip() -> str:
    try:
        # access_route includes proxies; keep the chain for support.
        rt = list(getattr(request, "access_route", []) or [])
        if rt:
            return ", ".join(str(x) for x in rt if x)
    except Exception:
        pass
    try:
        return str(getattr(request, "remote_addr", "") or "")
    except Exception:
        return ""


def _req_ua() -> str:
    try:
        return str(request.headers.get("User-Agent") or "")[:200]
    except Exception:
        return ""

DEFAULT_INFLUX_YAML_PATH = "homeassistant/influx.yaml"
LAST_YAML_ERROR = None


def _load_secrets_for_config(cfg_file: Path) -> dict:
    """Load Home Assistant secrets.yaml near a given config file.

    Tries (in order):
    - <cfg_file_dir>/secrets.yaml
    - /config/secrets.yaml
    """

    cfg_root = CONFIG_DIR.resolve()
    candidates = [cfg_file.parent / "secrets.yaml", cfg_root / "secrets.yaml"]
    for p in candidates:
        try:
            if not p.exists():
                continue
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return {}


class _HALoader(yaml.SafeLoader):
    _ha_secrets: dict = {}
    pass


def _ha_multi_constructor(loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node):
    """Handle Home Assistant YAML tags like !secret without failing."""

    if tag_suffix == "secret" and isinstance(node, yaml.ScalarNode):
        key = loader.construct_scalar(node)
        secrets = getattr(loader, "_ha_secrets", {}) or {}
        return secrets.get(key, "")

    # Generic fallback for other tags: just construct the underlying value.
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


_HALoader.add_multi_constructor("!", _ha_multi_constructor)

def _resolve_cfg_path(path_str: str) -> Path:
    """
    Resolve a user-provided path to a file inside /config.

    Accepted inputs:
      - "homeassistant/influx.yaml"  -> /config/homeassistant/influx.yaml
      - "/config/homeassistant/influx.yaml" -> unchanged
      - "influx.yaml" -> /config/influx.yaml

    Any path traversal is rejected.
    """
    if not path_str:
        raise ValueError("influx_yaml_path is empty")

    p = Path(path_str)

    cfg_root = CONFIG_DIR.resolve()
    # Make relative paths relative to /config
    if not p.is_absolute():
        p = cfg_root / p

    rp = p.resolve()
    if cfg_root not in rp.parents and rp != cfg_root:
        raise ValueError("Path must stay within /config")

    return rp


def find_influx_yaml() -> tuple[str | None, list[str]]:
    """Find an `influx.yaml` under /config.

    Returns (best_relative_path, all_relative_matches).
    """

    cfg_root = CONFIG_DIR.resolve()

    # Prefer the canonical HA location first.
    preferred = [
        cfg_root / "homeassistant" / "influx.yaml",
        cfg_root / "influx.yaml",
    ]
    matches: list[Path] = []
    for p in preferred:
        try:
            if p.exists() and p.is_file():
                matches.append(p)
        except Exception:
            continue

    # Fallback: search under /config (keep it bounded).
    if not matches:
        try:
            for p in cfg_root.rglob("influx.yaml"):
                if p.is_file():
                    matches.append(p)
                if len(matches) >= 10:
                    break
        except Exception:
            pass

    rels: list[str] = []
    for p in matches:
        try:
            rp = p.resolve()
            if cfg_root in rp.parents:
                rels.append(str(rp.relative_to(cfg_root)))
        except Exception:
            continue

    best = rels[0] if rels else None
    return best, rels


def load_influx_yaml(influx_yaml_path: str):
    """
    Read Home Assistant's InfluxDB YAML config from a specific file path.

    Returns (detected_cfg_dict, source_path) or (None, None).
    """
    global LAST_YAML_ERROR
    LAST_YAML_ERROR = None

    try:
        fp = _resolve_cfg_path(influx_yaml_path)
        if not fp.exists():
            LAST_YAML_ERROR = "file not found"
            return None, None

        secrets = _load_secrets_for_config(fp)

        class _Loader(_HALoader):
            pass

        _Loader._ha_secrets = secrets
        data = yaml.load(fp.read_text(encoding="utf-8"), Loader=_Loader) or {}
        if not isinstance(data, dict):
            LAST_YAML_ERROR = "top-level YAML is not a mapping"
            return None, None

        # Sometimes configs are nested (e.g., {"influxdb": {...}})
        cfg_block = data.get("influxdb") if isinstance(data.get("influxdb"), dict) else data
        if not isinstance(cfg_block, dict):
            LAST_YAML_ERROR = "influxdb block is not a mapping"
            return None, None

        # Heuristic: must contain at least some typical keys
        if not any(k in cfg_block for k in ("host", "port", "token", "organization", "bucket", "database", "api_version")):
            LAST_YAML_ERROR = "no influxdb-like keys found"
            return None, None

        api_version_raw = cfg_block.get("api_version", 2)
        try:
            api_version = int(api_version_raw)
        except Exception:
            api_version = 2
        api_version = 1 if api_version == 1 else 2

        ssl = bool(cfg_block.get("ssl", False))
        scheme = "https" if ssl else "http"

        detected = {
            "influx_version": api_version,
            "scheme": scheme,
            "host": cfg_block.get("host", DEFAULT_CFG["host"]),
            "port": int(cfg_block.get("port") or DEFAULT_CFG["port"]),
        }

        if api_version == 2:
            detected.update({
                "token": cfg_block.get("token", ""),
                "admin_token": cfg_block.get("admin_token", cfg_block.get("adminToken", "")) or "",
                "org": cfg_block.get("organization", cfg_block.get("org", "")),
                "bucket": cfg_block.get("bucket", ""),
            })
        else:
            detected.update({
                "username": cfg_block.get("username", ""),
                "password": cfg_block.get("password", ""),
                "database": cfg_block.get("database", ""),
            })

        return detected, str(fp)
    except Exception as e:
        # Avoid leaking secrets; keep details minimal.
        LAST_YAML_ERROR = f"failed to read/parse YAML: {e.__class__.__name__}"
        return None, None


def _overlay_from_yaml(cfg_in: dict) -> tuple[dict, str | None]:
    """Overlay missing config values from influx.yaml (no persistence)."""

    path_str = (cfg_in.get("influx_yaml_path") or DEFAULT_INFLUX_YAML_PATH).strip()
    detected, src = load_influx_yaml(path_str)
    if not detected:
        return cfg_in, None

    merged = dict(cfg_in)

    # Only fill missing/empty values from YAML, do not override explicit UI inputs
    for k, v in detected.items():
        if k not in merged or merged.get(k) in (None, "", 0):
            merged[k] = v

    # Keep some additional fields in sync if YAML provided them and UI left defaults
    if merged.get("scheme") in (None, "") and detected.get("scheme"):
        merged["scheme"] = detected["scheme"]
    if merged.get("host") in (None, "") and detected.get("host"):
        merged["host"] = detected["host"]
    if merged.get("port") in (None, "", 0) and detected.get("port"):
        merged["port"] = detected["port"]

    return merged, src


def _overlay_from_yaml_if_enabled(cfg_in: dict) -> dict:
    """Overlay from YAML only after explicit user action in Config UI."""

    if not YAML_FALLBACK_ENABLED:
        return cfg_in

    merged, src = _overlay_from_yaml(cfg_in)
    if src:
        global LAST_AUTODETECT_SOURCE
        LAST_AUTODETECT_SOURCE = src

    # Normalize influx_version for runtime callers.
    # This is intentionally best-effort and does not persist anything.
    try:
        v = int(merged.get("influx_version", 2) or 2)
    except Exception:
        v = 2
    if v not in (1, 2):
        v = 2

    # Safety: if v1 is selected but no database is configured while v2 creds exist,
    # prefer v2 to avoid confusing "v1 requires database" errors.
    try:
        db = str(merged.get("database") or "").strip()
    except Exception:
        db = ""
    has_v2 = bool(merged.get("token")) and bool(merged.get("org")) and bool(merged.get("bucket"))
    if v != 2 and (not db) and has_v2:
        v = 2
    merged["influx_version"] = v
    return merged


app = Flask(__name__, template_folder=str(APP_DIR / "templates"))
RUNTIME_CFG_FILE = DATA_DIR / "influx_browser_config.json"

LOG_FILE = DATA_DIR / "influxbro.log"


def _redact_secrets(s: str) -> str:
    if not s:
        return ""
    out = s
    # Bearer tokens
    out = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)([^\s\"]+)", r"\1***", out)
    # Common key=value patterns
    out = re.sub(r"(?i)\b(token|admin_token|password|passwd|api_key|apikey|secret|private_key|public_key|access_key)\s*[:=]\s*([^\s,;\"]+)", r"\1=***", out)
    out = re.sub(r'(?i)(\b(?:token|admin_token|password|passwd|api_key|apikey|secret|private_key|public_key|access_key)\b\s*["\']?\s*[:=]\s*["\'])([^"\'\s]+)(["\'])', r'\1***\3', out)
    return out


class _RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            record.msg = _redact_secrets(str(msg))
            record.args = ()
        except Exception:
            # Keep record as-is.
            pass
        return True


_LOG_CONFIGURED = False
DETAILS_ENABLED = False
INFLUX_QUERY_LOGGING = False

LOG = logging.getLogger("influxbro")
DETAIL_LOG = logging.getLogger("influxbro.details")


@app.before_request
def _csrf_gate_api_requests():
    """Minimal CSRF hardening for state-changing API requests.

    The InfluxBro UI adds `X-InfluxBro-Request: 1` to same-origin /api/* calls.
    Without this header, cross-site form posts could trigger writes.

    Note: This does not replace authentication. It only raises the bar for CSRF.
    """

    try:
        # Unit tests use Flask's test_client without browser headers.
        # Keep the production guard in place, but allow tests to exercise endpoints.
        try:
            if os.environ.get("PYTEST_CURRENT_TEST"):
                return None
        except Exception:
            pass
        if request.method not in ("POST", "PUT", "DELETE", "PATCH"):
            return None
        p = str(request.path or "")
        if not p.startswith("/api/"):
            return None
        if str(request.headers.get("X-InfluxBro-Request") or "").strip() == "1":
            return None
        return jsonify({"ok": False, "error": "CSRF protection: missing X-InfluxBro-Request header"}), 403
    except Exception:
        # Fail open on unexpected errors to avoid breaking the UI.
        return None


def log_details(msg: str, *args: object) -> None:
    if not DETAILS_ENABLED:
        return
    try:
        DETAIL_LOG.debug(msg, *args)
    except Exception:
        return


def log_query(label: str, query: str) -> str:
    """Log an Influx query string under TRACE when enabled.

    Returns the (possibly trace-prefixed) query string.
    """

    q = (query or "").strip()
    if not q:
        return ""

    # Add trace correlation (if present).
    try:
        trace_id = str(getattr(g, "trace_id", "") or "")
        action = str(getattr(g, "trace_action", "") or "")
        span_id = str(getattr(g, "trace_span_id", "") or "")
        if trace_id:
            prefix = f"// trace_id={trace_id} action={action} span_id={span_id} label={label}"
            q = prefix + "\n" + q
    except Exception:
        pass

    # Store query in trace store (best effort), independent of log profile.
    try:
        _trace_add_query(label, q)
    except Exception:
        pass

    if DETAILS_ENABLED and INFLUX_QUERY_LOGGING:
        try:
            DETAIL_LOG.debug("%s:\n%s", label, q)
        except Exception:
            pass

    return q


def _cleanup_old_logs(max_age_days: int) -> None:
    if not max_age_days or max_age_days <= 0:
        return
    try:
        cutoff = time.time() - (max_age_days * 86400)
        for p in DATA_DIR.glob("influxbro.log*"):
            try:
                if p.is_file() and p.stat().st_mtime < cutoff:
                    p.unlink(missing_ok=True)
            except Exception:
                continue
    except Exception:
        return


def configure_logging(cfg: dict[str, Any]) -> None:
    """Configure logging to stdout (HA) and optional rotating logfile under /data."""

    global _LOG_CONFIGURED

    global DETAILS_ENABLED
    global INFLUX_QUERY_LOGGING
    global CACHE_USAGE_LOGGING

    try:
        profile = str(cfg.get("log_profile") or "").strip().lower()
    except Exception:
        profile = ""

    # Profiles:
    # - error: only errors
    # - debug: debug points
    # - trace: debug + internal query/details
    if profile in ("error", "errors", "only_errors", "fehler"):
        level_s = "ERROR"
        DETAILS_ENABLED = False
    elif profile in ("trace", "details", "verbose"):
        level_s = "DEBUG"
        DETAILS_ENABLED = True
    else:
        # default
        profile = "debug"
        level_s = "DEBUG"
        DETAILS_ENABLED = False

    level = getattr(logging, level_s, logging.DEBUG)

    log_to_file = bool(cfg.get("log_to_file", True))
    try:
        max_mb = int(cfg.get("log_max_mb", 5))
    except Exception:
        max_mb = 5
    if max_mb < 1:
        max_mb = 1
    if max_mb > 200:
        max_mb = 200

    try:
        backup_count = int(cfg.get("log_backup_count", 5))
    except Exception:
        backup_count = 5
    if backup_count < 1:
        backup_count = 1
    if backup_count > 50:
        backup_count = 50

    try:
        max_age_days = int(cfg.get("log_max_age_days", 14))
    except Exception:
        max_age_days = 14
    if max_age_days < 0:
        max_age_days = 0
    if max_age_days > 365:
        max_age_days = 365

    log_http_requests = bool(cfg.get("log_http_requests", False))
    INFLUX_QUERY_LOGGING = bool(cfg.get("log_influx_queries", False))
    CACHE_USAGE_LOGGING = bool(cfg.get("log_cache_usage", False))

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if log_to_file:
        _cleanup_old_logs(max_age_days)

    root = logging.getLogger()
    root.setLevel(level)

    # Remove old handlers to avoid duplicates on reconfigure.
    for h in list(root.handlers):
        try:
            root.removeHandler(h)
            h.close()
        except Exception:
            continue

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    red = _RedactFilter()

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(level)
    sh.setFormatter(fmt)
    sh.addFilter(red)
    root.addHandler(sh)

    if log_to_file:
        try:
            fh = logging.handlers.RotatingFileHandler(
                LOG_FILE,
                maxBytes=max_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding="utf-8",
            )
            fh.setLevel(level)
            fh.setFormatter(fmt)
            fh.addFilter(red)
            root.addHandler(fh)
        except Exception:
            # Keep stdout logging even if file handler fails.
            pass

    # Flask app logger: make it propagate to root handlers.
    try:
        app.logger.handlers = []
        app.logger.propagate = True
        app.logger.setLevel(level)
    except Exception:
        pass

    # Werkzeug request logs are very chatty; keep off by default.
    try:
        wz = logging.getLogger("werkzeug")
        if log_http_requests:
            wz.setLevel(level)
        else:
            wz.setLevel(logging.WARNING)
    except Exception:
        pass

    if not _LOG_CONFIGURED:
        _LOG_CONFIGURED = True
        logging.getLogger(__name__).info(
            "Logging configured (profile=%s, to_file=%s, level=%s, max_mb=%s, backups=%s, max_age_days=%s, http_requests=%s)",
            profile,
            log_to_file,
            level_s,
            max_mb,
            backup_count,
            max_age_days,
            log_http_requests,
        )

    try:
        _trace_configure(cfg)
    except Exception:
        pass

    try:
        _worklog_configure(cfg)
    except Exception:
        pass


def _trace_configure(cfg: dict[str, Any]) -> None:
    global TRACE_ENABLED
    global TRACE_PERSIST
    global TRACE_MAX_ENTRIES
    global TRACE_MAX_DAYS
    global TRACE_MEM

    TRACE_ENABLED = bool(cfg.get("trace_enabled", True))
    TRACE_PERSIST = bool(cfg.get("trace_persist", True))
    try:
        TRACE_MAX_ENTRIES = int(cfg.get("trace_max_entries", 1000) or 1000)
    except Exception:
        TRACE_MAX_ENTRIES = 1000
    TRACE_MAX_ENTRIES = max(100, min(20000, TRACE_MAX_ENTRIES))

    try:
        TRACE_MAX_DAYS = int(cfg.get("trace_max_days", 14) or 14)
    except Exception:
        TRACE_MAX_DAYS = 14
    TRACE_MAX_DAYS = max(1, min(3650, TRACE_MAX_DAYS))

    # Keep recents bounded and evict stale trace entries.
    with TRACE_LOCK:
        _trace_prune_locked()
        while len(TRACE_MEM) > TRACE_MAX_ENTRIES:
            old_tid = TRACE_MEM.popleft()
            try:
                TRACE_INDEX.pop(old_tid, None)
            except Exception:
                pass
        keep = set(TRACE_MEM)
        for tid in list(TRACE_INDEX.keys()):
            if tid not in keep:
                TRACE_INDEX.pop(tid, None)

    if TRACE_PERSIST:
        _trace_load_from_disk()


def _worklog_configure(cfg: dict[str, Any]) -> None:
    global WORKLOG_MAX_ENTRIES
    global WORKLOG_MAX_DAYS
    try:
        WORKLOG_MAX_ENTRIES = int(cfg.get("worklog_max_entries", WORKLOG_MAX_ENTRIES) or WORKLOG_MAX_ENTRIES)
    except Exception:
        WORKLOG_MAX_ENTRIES = 2000
    WORKLOG_MAX_ENTRIES = max(200, min(50000, WORKLOG_MAX_ENTRIES))

    try:
        WORKLOG_MAX_DAYS = int(cfg.get("worklog_max_days", WORKLOG_MAX_DAYS) or WORKLOG_MAX_DAYS)
    except Exception:
        WORKLOG_MAX_DAYS = 14
    WORKLOG_MAX_DAYS = max(1, min(3650, WORKLOG_MAX_DAYS))

    # Best-effort prune in-memory buffer to the new limits.
    with ANALYSIS_HISTORY_LOCK:
        _worklog_prune_mem_locked()


def _trace_load_from_disk() -> None:
    try:
        if not TRACE_PATH.exists():
            return
        raw = TRACE_PATH.read_text(encoding="utf-8", errors="replace")
        j = json.loads(raw or "null")
        if not isinstance(j, list):
            return
        with TRACE_LOCK:
            TRACE_MEM.clear()
            TRACE_INDEX.clear()
            items: list[dict[str, Any]] = []
            for it in j[-TRACE_MAX_ENTRIES:]:
                if not isinstance(it, dict):
                    continue
                tid = str(it.get("trace_id") or "").strip()
                if not tid:
                    continue
                TRACE_INDEX[tid] = it
                # normalize minimally so later updates are safe
                try:
                    _trace_get_or_create(tid)
                except Exception:
                    pass
                items.append({"trace_id": tid, "last_at": str(it.get("last_at") or "")})

            # Prefer recents by last_at, keep stable fallback order.
            items.sort(key=lambda d: str(d.get("last_at") or ""))
            for d in items[-TRACE_MAX_ENTRIES:]:
                TRACE_MEM.append(str(d.get("trace_id") or "").strip())

            # Enforce retention by age as well.
            _trace_prune_locked()
    except Exception:
        return


def _trace_save_to_disk() -> None:
    global TRACE_LAST_WRITE_MONO
    if not TRACE_PERSIST:
        return
    now = time.monotonic()
    # avoid heavy churn on frequent events
    if (now - TRACE_LAST_WRITE_MONO) < 0.8:
        return
    TRACE_LAST_WRITE_MONO = now
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with TRACE_LOCK:
            _trace_prune_locked()
            # Persist in recent/LRU order.
            items = []
            for tid in list(TRACE_MEM)[-TRACE_MAX_ENTRIES:]:
                tr = TRACE_INDEX.get(tid)
                if isinstance(tr, dict):
                    items.append(tr)
        tmp = TRACE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=True), encoding="utf-8")
        tmp.replace(TRACE_PATH)
    except Exception:
        return


def _trace_ctx() -> dict[str, str]:
    try:
        return {
            "trace_id": str(getattr(g, "trace_id", "") or ""),
            "action": str(getattr(g, "trace_action", "") or ""),
            "span_id": str(getattr(g, "trace_span_id", "") or ""),
        }
    except Exception:
        return {"trace_id": "", "action": "", "span_id": ""}


def _trace_get_or_create(trace_id: str, page: str = "", action: str = "", started_at: str = "") -> dict[str, Any]:
    tid = str(trace_id or "").strip()
    if not tid:
        return {}
    with TRACE_LOCK:
        tr = TRACE_INDEX.get(tid)
        if isinstance(tr, dict):
            _trace_normalize(tr, tid, page=page, action=action, started_at=started_at)
            return tr
        tr = {
            "trace_id": tid,
            "page": str(page or ""),
            "action": str(action or ""),
            "started_at": started_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "last_at": started_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "running",
            "dur_ms": None,
            "counts": {"ui_events": 0, "api_spans": 0, "client_spans": 0, "queries": 0},
            "ui_events": [],
            "spans": [],
            "client_spans": [],
            "queries": [],
            "errors": [],
        }
        TRACE_INDEX[tid] = tr
        # add to recents
        try:
            _trace_recent_touch_locked(tid)
        except Exception:
            pass
        return tr


def _trace_parse_iso(iso: str) -> datetime | None:
    s = str(iso or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _trace_normalize(tr: dict[str, Any], tid: str, page: str = "", action: str = "", started_at: str = "") -> None:
    # Minimal shape normalization to handle older persisted traces.
    tr["trace_id"] = str(tr.get("trace_id") or tid)
    if page and not str(tr.get("page") or "").strip():
        tr["page"] = str(page)
    if action and not str(tr.get("action") or "").strip():
        tr["action"] = str(action)
    if started_at and not str(tr.get("started_at") or "").strip():
        tr["started_at"] = str(started_at)
    if not str(tr.get("started_at") or "").strip():
        tr["started_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if not str(tr.get("last_at") or "").strip():
        tr["last_at"] = str(tr.get("started_at") or "")

    counts = tr.get("counts")
    if not isinstance(counts, dict):
        counts = {}
    for k in ("ui_events", "api_spans", "client_spans", "queries"):
        try:
            counts[k] = int(counts.get(k, 0) or 0)
        except Exception:
            counts[k] = 0
    tr["counts"] = counts

    for k in ("ui_events", "spans", "client_spans", "queries", "errors"):
        if not isinstance(tr.get(k), list):
            tr[k] = []

    st = str(tr.get("status") or "running")
    if st not in ("running", "ok", "err"):
        st = "running"
    tr["status"] = st


def _trace_recent_touch_locked(tid: str) -> None:
    # TRACE_LOCK must be held.
    while True:
        try:
            TRACE_MEM.remove(tid)
        except ValueError:
            break
        except Exception:
            break
    TRACE_MEM.append(tid)
    while len(TRACE_MEM) > TRACE_MAX_ENTRIES:
        old_tid = TRACE_MEM.popleft()
        try:
            TRACE_INDEX.pop(old_tid, None)
        except Exception:
            pass


def _trace_prune_locked(now_dt: datetime | None = None) -> None:
    """Prune trace store by age and max entries.

    TRACE_LOCK must be held.
    """

    try:
        now = now_dt or datetime.now(timezone.utc)
        cutoff = now - timedelta(days=int(TRACE_MAX_DAYS or 14))
    except Exception:
        cutoff = None

    if cutoff is not None:
        keep_ids: list[str] = []
        for tid in list(TRACE_MEM):
            tr = TRACE_INDEX.get(tid)
            if not isinstance(tr, dict):
                continue
            last = _trace_parse_iso(str(tr.get("last_at") or "")) or _trace_parse_iso(str(tr.get("started_at") or ""))
            if last and last < cutoff:
                continue
            keep_ids.append(tid)

        TRACE_MEM.clear()
        for tid in keep_ids:
            TRACE_MEM.append(tid)

        keep_set = set(keep_ids)
        for tid in list(TRACE_INDEX.keys()):
            if tid not in keep_set:
                TRACE_INDEX.pop(tid, None)

    while len(TRACE_MEM) > TRACE_MAX_ENTRIES:
        old_tid = TRACE_MEM.popleft()
        try:
            TRACE_INDEX.pop(old_tid, None)
        except Exception:
            pass


def _trace_summary(tr: dict[str, Any]) -> dict[str, Any]:
    out = {
        "trace_id": str(tr.get("trace_id") or ""),
        "started_at": tr.get("started_at"),
        "last_at": tr.get("last_at"),
        "status": tr.get("status"),
        "page": tr.get("page"),
        "action": tr.get("action"),
        "dur_ms": tr.get("dur_ms"),
        "counts": tr.get("counts") or {},
    }
    # Ensure counts is JSON-safe and small.
    try:
        c = out["counts"]
        if not isinstance(c, dict):
            c = {}
        out["counts"] = {
            "ui_events": int(c.get("ui_events", 0) or 0),
            "api_spans": int(c.get("api_spans", 0) or 0),
            "client_spans": int(c.get("client_spans", 0) or 0),
            "queries": int(c.get("queries", 0) or 0),
        }
    except Exception:
        out["counts"] = {"ui_events": 0, "api_spans": 0, "client_spans": 0, "queries": 0}
    return out


def _trace_touch(tr: dict[str, Any]) -> None:
    # TRACE_LOCK must be held.
    try:
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        tr["last_at"] = now_iso
        try:
            t0 = _trace_parse_iso(str(tr.get("started_at") or ""))
            t1 = _trace_parse_iso(now_iso)
            if t0 and t1:
                tr["dur_ms"] = int(max(0.0, (t1 - t0).total_seconds() * 1000.0))
        except Exception:
            pass
        _trace_recent_touch_locked(str(tr.get("trace_id") or "").strip())
    except Exception:
        return


def _trace_add_ui_event(page: str, ui: str, text: str, extra: Any) -> None:
    if not TRACE_ENABLED:
        return
    trace_id = ""
    action = ""
    started_at = ""
    if isinstance(extra, dict):
        trace_id = str(extra.get("trace_id") or "").strip()
        action = str(extra.get("action") or extra.get("ui") or "").strip()
        started_at = str(extra.get("started_at") or "").strip()
    if not trace_id:
        return
    tr = _trace_get_or_create(trace_id, page=page, action=action, started_at=started_at)
    if not tr:
        return
    with TRACE_LOCK:
        _trace_normalize(tr, str(tr.get("trace_id") or ""), page=page, action=action, started_at=started_at)
        _trace_touch(tr)
        tr["counts"]["ui_events"] = int(tr["counts"].get("ui_events", 0) or 0) + 1
        safe_extra: Any = extra
        if isinstance(extra, dict):
            # keep small and non-sensitive
            safe_extra = {str(k)[:40]: _redact_secrets(str(v)[:200]) for k, v in list(extra.items())[:25]}
        tr["ui_events"].append({
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "page": page,
            "ui": ui,
            "text": text,
            "extra": safe_extra,
        })
    _trace_save_to_disk()


def _trace_add_span(span: dict[str, Any]) -> None:
    if not TRACE_ENABLED:
        return
    tid = str(span.get("trace_id") or "").strip()
    if not tid:
        return
    tr = _trace_get_or_create(tid, page=str(span.get("page") or ""), action=str(span.get("action") or ""), started_at=str(span.get("started_at") or ""))
    if not tr:
        return
    with TRACE_LOCK:
        _trace_normalize(tr, str(tr.get("trace_id") or ""), page=str(span.get("page") or ""), action=str(span.get("action") or ""), started_at=str(span.get("started_at") or ""))
        _trace_touch(tr)
        tr["counts"]["api_spans"] = int(tr["counts"].get("api_spans", 0) or 0) + 1
        tr["spans"].append(span)
        # update status/dur
        try:
            if span.get("status") == "err":
                tr["status"] = "err"
        except Exception:
            pass
    _trace_save_to_disk()


def _trace_add_client_span(span: dict[str, Any]) -> None:
    if not TRACE_ENABLED:
        return
    tid = str(span.get("trace_id") or "").strip()
    if not tid:
        return
    tr = _trace_get_or_create(tid, page=str(span.get("page") or ""), action=str(span.get("action") or ""), started_at=str(span.get("started_at") or ""))
    if not tr:
        return
    with TRACE_LOCK:
        _trace_normalize(tr, str(tr.get("trace_id") or ""), page=str(span.get("page") or ""), action=str(span.get("action") or ""), started_at=str(span.get("started_at") or ""))
        _trace_touch(tr)
        tr["counts"]["client_spans"] = int(tr["counts"].get("client_spans", 0) or 0) + 1
        tr["client_spans"].append(span)
    _trace_save_to_disk()


def _trace_add_query(label: str, query: str) -> None:
    if not TRACE_ENABLED:
        return
    ctx = _trace_ctx()
    tid = str(ctx.get("trace_id") or "").strip()
    if not tid:
        return
    tr = _trace_get_or_create(tid, page="", action=str(ctx.get("action") or ""), started_at="")
    if not tr:
        return
    q = _redact_secrets(str(query or ""))
    with TRACE_LOCK:
        _trace_normalize(tr, str(tr.get("trace_id") or ""), action=str(ctx.get("action") or ""))
        _trace_touch(tr)
        tr["counts"]["queries"] = int(tr["counts"].get("queries", 0) or 0) + 1
        tr["queries"].append({
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "label": str(label or "")[:120],
            "span_id": str(ctx.get("span_id") or ""),
            "query": q[:200000],
        })
    _trace_save_to_disk()


@app.before_request
def _trace_before_request() -> None:
    if not TRACE_ENABLED:
        return
    try:
        g.trace_id = str(request.headers.get("X-InfluxBro-Trace-Id") or "").strip()
        g.trace_span_id = str(request.headers.get("X-InfluxBro-Span-Id") or "").strip()
        g.trace_action = str(request.headers.get("X-InfluxBro-Action") or "").strip()
        g.trace_started_at = str(request.headers.get("X-InfluxBro-Trace-Started-At") or "").strip()
        g.trace_page = str(request.headers.get("X-InfluxBro-Trace-Page") or "").strip()
        g._trace_req_t0 = time.monotonic()
    except Exception:
        return


@app.after_request
def _trace_after_request(resp: Response) -> Response:
    if not TRACE_ENABLED:
        return resp
    try:
        tid = str(getattr(g, "trace_id", "") or "").strip()
        if not tid:
            return resp
        t0 = float(getattr(g, "_trace_req_t0", 0.0) or 0.0)
        dur_ms = int(max(0.0, (time.monotonic() - t0) * 1000.0)) if t0 else None
        span = {
            "trace_id": tid,
            "span_id": str(getattr(g, "trace_span_id", "") or ""),
            "action": str(getattr(g, "trace_action", "") or ""),
            "page": str(getattr(g, "trace_page", "") or ""),
            "started_at": str(getattr(g, "trace_started_at", "") or ""),
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "kind": "http.request",
            "method": str(request.method or ""),
            "path": str(request.path or ""),
            "status_code": int(resp.status_code),
            "dur_ms": dur_ms,
            "status": "ok" if int(resp.status_code) < 400 else "err",
        }
        _trace_add_span(span)
    except Exception:
        return resp
    return resp

def env_bool(key: str, default: bool) -> bool:
    v = os.environ.get(key, str(default)).lower()
    return v in ("1", "true", "yes", "on")

# Kept for backward compatibility; do not rely on this env var.
_ALLOW_DELETE_ENV = env_bool("ALLOW_DELETE", False)

LAST_AUTODETECT_SOURCE = None
YAML_FALLBACK_ENABLED = False

DEFAULT_CFG = {
    "influx_version": 2,
    "scheme": "http",
    "host": "a0d7b954-influxdb",
    "port": 8086,
    "verify_ssl": True,
    "timeout_seconds": 10,
    "influx_yaml_path": DEFAULT_INFLUX_YAML_PATH,
    # v2
    "token": "",
    # v2 admin token (native backup/restore); never exposed
    "admin_token": "",
    "org": "",
    "bucket": "",
    # v1
    "username": "",
    "password": "",
    "database": "",

    # UI defaults
    "ui_table_visible_rows": 20,
    "ui_outlier_visible_rows": 10,
    "ui_table_row_height_px": 13,
    # Picker / S-Picker highlight
    "ui_picker_outline_auto": True,
    "ui_picker_outline_light_bg": "#FF00AA",
    "ui_picker_outline_dark_bg": "#00E5FF",
    "ui_analysis_cache_hidden_color": "#b0b0b0",
    "ui_analysis_cache_missing_color": "#b00020",
    "ui_backup_table_row_height_px": 13,
    "ui_backup_visible_rows": 24,
    "ui_restore_visible_rows": 24,
    "ui_edit_neighbors_n": 5,
    "ui_edit_details_visible_rows": 12,
    "ui_edit_graph_buffer_minutes": 30,
    "ui_edit_graph_max_points": 50000,
    # Dashboard graph context (raw-window preview): extend the visible raw range by before/after buffer.
    "ui_graph_ctx_before_minutes": 60,
    "ui_graph_ctx_after_minutes": 60,
    "ui_query_max_points": 5000,
    "ui_raw_max_points": 20000,
    "ui_raw_center_max_points": 2000,
    "ui_raw_center_range_default": 100,
    "ui_raw_center_min_points": 10,
    "ui_query_manual_max_points": 200000,
    "ui_decimals": 3,

    # Dashboard graph: highlight around detected jumps (in coarse intervals)
    "ui_graph_jump_padding_intervals": 1,

    "ui_font_size_px": 14,
    "ui_font_small_px": 11,
    "ui_popup_pre_font_px": 10,
    "ui_popup_history_font_px": 10,
    "ui_pagecard_title_px": 30,
    "ui_page_search_highlight_color": "#FF9900",
    "ui_page_search_highlight_width_px": 5,
    "ui_page_search_highlight_duration_ms": 8000,
    "ui_status_font_px": 12,
    "ui_status_show_sysinfo": False,
    "ui_status_bar_height_px": 38,
    "ui_status_bar_bg": "#FFFFFF",
    "ui_status_bar_fg": "#111111",
    "ui_checkbox_scale": 0.85,
    # Section title row (details > summary): optional overrides
    # Allowed: "" (default), "transparent"/"inherit", or "#RRGGBB"
    # Defaults chosen for better readability.
    "ui_section_title_bg": "#3287a8",
    "ui_section_title_fg": "#FFFFFF",
    "ui_section_title_font_px": 13,
    "ui_section_level2_bg": "#8BA293",
    "ui_section_level2_fg": "#FFFFFF",
    "ui_section_level2_font_px": 12,
    "ui_section_level3_bg": "#B8B17F",
    "ui_section_level3_fg": "#FFFFFF",
    "ui_section_level3_font_px": 11,
    "ui_filter_label_width_px": 170,
    "ui_filter_control_width_px": 320,
    "ui_filter_search_width_px": 160,

    # Selection fields (master template for filter/time selection)
    "ui_sel_field_font_px": 13,
    "ui_sel_label_font_px": 12,
    "ui_sel_desc_font_px": 11,
    "ui_sel_auto_width": True,
    "ui_sel_width_px": 260,

    # Outlier search limit (max results returned in raw outlier search)
    "ui_raw_outlier_search_limit": 5000,

    # Max visible outliers per type in the outlier table (analysis still computes all)
    "ui_raw_outlier_display_limit_per_type": 100,

    # Outlier context rows (rows shown before/after outlier in raw table)
    "ui_raw_outlier_context_rows": 10,

    # Target chunk duration for adaptive outlier search (milliseconds)
    "ui_raw_target_chunk_ms": 5000,

    # Max analysis age when range=all (years)
    "ui_analysis_max_age_years": 5,

    # Jobs UI colors (used by Jobs & Cache table)
    "ui_job_color_running": "#eef3ff",
    "ui_job_color_done": "#eefaf1",
    "ui_job_color_error": "#fff0f0",
    "ui_job_color_cancelled": "#f6f6f6",

    # Safety: auto-cancel jobs after N seconds (0 = disabled)
    "jobs_max_runtime_seconds": 3600,

    # Restore
    "restore_preview_lines": 5,

    # Import transformation rules: one rule per line, format `source;target;factor`
    "import_measurement_transforms": "W;kW;0.001\nkW;W;1000\nkW;MW;0.001\nMW;kW;1000\nWh;kWh;0.001\nkWh;Wh;1000\nkWh;MWh;0.001\nMWh;kWh;1000",

    # Tooltips
    "ui_tooltips_enabled": True,

    # Backups (must live under /config or /data)
    "backup_dir": str(DEFAULT_BACKUP_DIR),
    # Refuse creating a backup if free space is below this threshold (0 = disabled)
    "backup_min_free_mb": 10,
    # Safety budget: keep at least this much space free for caches (/data) (0 = disabled)
    "storage_budget_mb": 5,
    # One-time migration marker when moving from the old default (/data/backups)
    "backup_migrated_to_config": False,

    # Outlier scan defaults (max jump per point)
    # Based on a typical household connection: 3-phase 400V, 35A -> ~24.2kW; use 30kW as practical ceiling.
    "outlier_max_step_w": 30000,
    "outlier_max_step_kw": 30,
    # Energy deltas depend on sampling interval; defaults assume coarse (hour-ish) steps.
    "outlier_max_step_wh": 30000,
    "outlier_max_step_kwh": 30,
    # A time gap above this threshold is treated as measurement gap instead of a normal step jump.
    "outlier_gap_seconds_default": 300,

    # Point-based context around relevant boundaries/outliers.
    # Used for:
    # - Raw-Fenster around detected outliers (N points before/after)
    # - Future boundary buffering (cache append / dirty repair)
    "outlier_context_before_points": 10,
    "outlier_context_after_points": 10,

    # Optional default bounds for outlier scan (empty = disabled)
    "outlier_bounds_min_default": "",
    "outlier_bounds_max_default": "",

    # Fault-phase search: number of valid values until leaving a fault phase.
    "outlier_recovery_valid_streak_default": 2,

    # Additional unit thresholds (one per line): unit=max_step
    # Example: 
    #   °C=2
    #   bar=0.3
    "outlier_max_step_units": "",

    # Logging (stdout + optional /data log file)
    "log_to_file": True,
    # Log profiles (standard-ish): error, debug, trace
    "log_profile": "debug",
    # Backward-compat / advanced (ignored if log_profile is set)
    "log_level": "DEBUG",
    "log_max_mb": 5,
    "log_backup_count": 5,
    "log_max_age_days": 14,
    "bugreport_log_history_hours": 1,
    "log_http_requests": False,
    "log_influx_queries": False,
    "log_cache_usage": False,

    # Tracing / Performanceanalyse (persistent action log)
    "trace_enabled": True,
    "trace_persist": True,
    "trace_max_entries": 1000,
    "trace_max_days": 14,

    # Performanceanalyse: correlation heuristics
    "perf_corr_causal_gap_ms": 8,
    "perf_corr_timer_gap_ms": 1000,
    # Performanceanalyse: correlation dep graph zoom
    # 0 = auto-fit (x+y), otherwise percent scaling (global)
    "perf_corr_dep_zoom_pct": 0,

    # Worklog (Analyse/Statistik/Raw Operations; persistent under /data)
    "worklog_max_entries": 2000,
    "worklog_max_days": 14,

    # Dashboard query cache (server-side, persisted under /data)
    "dash_cache_enabled": True,
    "dash_cache_auto_update": True,
    # Refresh schedule:
    # - mode=hours: refresh entries after N hours
    # - mode=daily: refresh once per day at dash_cache_refresh_daily_at (local time)
    # - mode=weekly: refresh once per week at dash_cache_refresh_weekday + dash_cache_refresh_daily_at
    # - mode=manual: never becomes stale by schedule (still may be updated when dirty/mismatch)
    "dash_cache_refresh_mode": "hours",
    "dash_cache_refresh_hours": 6,
    "dash_cache_refresh_daily_at": "00:00:00",
    "dash_cache_refresh_weekday": 0,
    # Cache size limits (best-effort eviction)
    "dash_cache_max_items": 40,
    "dash_cache_max_mb": 50,
    # If enabled, Dashboard may enqueue background updates when serving stale cache.
    "dash_cache_update_on_use_if_stale": True,

    # Statistik cache (server-side, persisted under /data)
    "stats_cache_enabled": True,
    "stats_cache_auto_update": True,
    # Refresh schedule:
    # - mode=hours: refresh entries after N hours
    # - mode=daily: refresh once per day at stats_cache_refresh_daily_at (local time)
    # - mode=weekly: refresh once per week at stats_cache_refresh_weekday + stats_cache_refresh_daily_at
    # - mode=manual: never becomes stale by schedule (still may be updated when dirty/mismatch)
    "stats_cache_refresh_mode": "daily",
    "stats_cache_refresh_hours": 24,
    "stats_cache_refresh_daily_at": "03:00:00",
    "stats_cache_refresh_weekday": 0,
    # Cache size limits (best-effort eviction)
    "stats_cache_max_items": 10,
    "stats_cache_max_mb": 50,

    # Timer Job: stats_full (global statistics full load)
    "stats_full_refresh_mode": "manual",
    "stats_full_refresh_hours": 24,
    "stats_full_refresh_daily_at": "03:00:00",
    "stats_full_refresh_weekday": 0,
    # Safety cap for scheduled full stats scans (prevents querying from epoch / huge ranges)
    "stats_full_max_days": 3650,

    # Timer Job: analysis_nightly (nightly refresh of analysis cache for known series)
    "analysis_nightly_enabled": True,
    "analysis_nightly_auto_update": True,
    "analysis_nightly_refresh_mode": "daily",
    "analysis_nightly_refresh_hours": 24,
    "analysis_nightly_refresh_daily_at": "03:30:00",
    "analysis_nightly_refresh_weekday": 0,
    # Time window covered by nightly refresh (stop=now, start=now-window)
    "analysis_nightly_window_hours": 24,

    # Data quality / long-term buckets
    "quality_raw_bucket": "homeassistant_raw_30d",
    "quality_clean_bucket": "homeassistant_clean_180d",
    "quality_rollup_bucket": "homeassistant_rollup",
    "quality_retention_raw_days": 30,
    "quality_retention_clean_days": 180,
    "quality_retention_rollup_days": 1825,
    "quality_timezone": "Europe/Berlin",
    "quality_lateness_minutes": 10,
    "quality_auto_create_buckets": True,
    "quality_auto_create_tasks": False,
    "quality_rules_json": "",
    "quality_rollup_levels_json": "",
    "quality_cleanup_plan_json": "",

}


def _strip_trace_prefix(query: str) -> str:
    """Remove a leading // trace_id=... prefix line from a stored query.

    This prevents cached queries from carrying an older trace_id into new traces.
    """

    try:
        q = str(query or "")
    except Exception:
        return ""
    if not q.strip():
        return ""
    try:
        lines = q.splitlines()
        while lines and str(lines[0] or "").lstrip().startswith("// trace_id="):
            lines.pop(0)
        return "\n".join(lines).lstrip("\n")
    except Exception:
        return q


def _process_rss_bytes() -> int | None:
    """Best-effort current process RSS (bytes)."""

    # Linux: /proc
    try:
        p = Path("/proc/self/status")
        if p.exists():
            for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if ln.startswith("VmRSS:"):
                    # VmRSS:   12345 kB
                    parts = ln.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        return int(parts[1]) * 1024
    except Exception:
        pass

    # Fallback: resource (max RSS, platform-dependent units)
    try:
        import resource

        ru = resource.getrusage(resource.RUSAGE_SELF)
        v = int(getattr(ru, "ru_maxrss", 0) or 0)
        if v <= 0:
            return None
        # Linux: KB; macOS: bytes
        if sys.platform == "darwin":
            return v
        return v * 1024
    except Exception:
        return None


def _fmt_bytes(n: int | None) -> str | None:
    if n is None:
        return None
    try:
        x = float(n)
    except Exception:
        return None
    if x < 0:
        x = 0
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if x < 1024 or unit == "TB":
            return f"{x:.1f} {unit}" if unit != "B" else f"{int(x)} B"
        x /= 1024
    return None


def writes_enabled(cfg: dict[str, Any]) -> bool:
    """Backward-compat only.

    Historically, writes/deletes were gated by a Settings toggle. This toggle is
    removed; we keep this helper to avoid breaking older clients.
    """

    return True


def _history_append(entry: dict[str, Any]) -> None:
    try:
        entry = dict(entry or {})
        if "id" not in entry:
            entry["id"] = uuid.uuid4().hex
        if "at" not in entry:
            entry["at"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        line = json.dumps(entry, ensure_ascii=True, separators=(",", ":"))
        with HISTORY_LOCK:
            try:
                HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            with HISTORY_PATH.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        # History is best-effort; never break runtime due to logging.
        return


def _history_read_all() -> list[dict[str, Any]]:
    try:
        if not HISTORY_PATH.exists():
            return []
        with HISTORY_LOCK:
            raw = HISTORY_PATH.read_text(encoding="utf-8", errors="replace")
        out: list[dict[str, Any]] = []
        for ln in (raw or "").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                j = json.loads(ln)
            except Exception:
                continue
            if isinstance(j, dict):
                out.append(j)
        return out
    except Exception:
        return []


def _history_series_matches(
    item: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
) -> bool:
    try:
        series = item.get("series") or {}
        if str(series.get("measurement") or "").strip() != str(measurement or "").strip():
            return False
        if str(series.get("field") or "").strip() != str(field or "").strip():
            return False
        want_eid = str(entity_id or "").strip()
        have_eid = str(series.get("entity_id") or "").strip()
        if want_eid != have_eid:
            return False
        want_fn = str(friendly_name or "").strip()
        have_fn = str(series.get("friendly_name") or "").strip()
        if want_fn != have_fn:
            return False
        return True
    except Exception:
        return False


def _history_time_key(value: Any) -> str:
    try:
        raw = str(value or "").strip()
        if not raw:
            return ""
        return _parse_iso_datetime(raw).isoformat()
    except Exception:
        return ""


def _history_trigger_meta(item: dict[str, Any]) -> dict[str, str]:
    try:
        return {
            "trigger_page": str(item.get("trigger_page") or "").strip(),
            "trigger_source": str(item.get("trigger_source") or "").strip(),
            "trigger_action": str(item.get("trigger_action") or "").strip(),
            "trigger_button": str(item.get("trigger_button") or "").strip(),
        }
    except Exception:
        return {
            "trigger_page": "",
            "trigger_source": "",
            "trigger_action": "",
            "trigger_button": "",
        }


def _timers_state_load() -> dict[str, Any]:
    try:
        if not TIMERS_STATE_PATH.exists():
            return {}
        with TIMERS_STATE_LOCK:
            raw = TIMERS_STATE_PATH.read_text(encoding="utf-8", errors="replace")
        j = json.loads(raw) if raw else {}
        return j if isinstance(j, dict) else {}
    except Exception:
        return {}


def _timers_state_save(state: dict[str, Any]) -> None:
    try:
        with TIMERS_STATE_LOCK:
            try:
                TIMERS_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            TIMERS_STATE_PATH.write_text(json.dumps(state or {}, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        return


def _timers_state_get(timer_id: str) -> dict[str, Any]:
    try:
        tid = str(timer_id or "").strip()
        if not tid:
            return {}
        st = _timers_state_load()
        v = st.get(tid)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _timer_event_append(timer_id: str, kind: str, extra: dict[str, Any] | None = None) -> None:
    """Append a small per-timer history ring buffer under /data (best-effort)."""

    try:
        tid = str(timer_id or "").strip()
        if not tid:
            return
        k = str(kind or "").strip() or "event"
        st = _timers_state_load()
        cur = st.get(tid)
        cur = cur if isinstance(cur, dict) else {}
        xs = cur.get("events")
        xs = xs if isinstance(xs, list) else []
        ent: dict[str, Any] = {
            "at": _utc_now_iso_ms(),
            "kind": k,
        }
        if extra and isinstance(extra, dict):
            for kk, vv in extra.items():
                ent[str(kk)] = vv
        xs.append(ent)
        if len(xs) > 80:
            xs = xs[-80:]
        cur["events"] = xs
        st[tid] = cur
        _timers_state_save(st)
    except Exception:
        return


def _timer_mark_started(timer_id: str, job_id: str | None = None) -> None:
    try:
        tid = str(timer_id or "").strip()
        if not tid:
            return
        st = _timers_state_load()
        cur = st.get(tid)
        cur = cur if isinstance(cur, dict) else {}
        cur["last_started_at"] = _utc_now_iso_ms()
        cur["last_job_id"] = str(job_id or "").strip() or None
        cur["last_state"] = "running"
        st[tid] = cur
        _timers_state_save(st)
        _timer_event_append(tid, "started", {"job_id": cur.get("last_job_id")})
    except Exception:
        return


def _timer_mark_finished(timer_id: str, state: str, extra: dict[str, Any] | None = None) -> None:
    try:
        tid = str(timer_id or "").strip()
        if not tid:
            return
        st_s = str(state or "").strip().lower()
        if st_s not in ("done", "error", "cancelled"):
            st_s = "done"
        st = _timers_state_load()
        cur = st.get(tid)
        cur = cur if isinstance(cur, dict) else {}
        cur["last_run_at"] = _utc_now_iso_ms()
        cur["last_state"] = st_s

        # Optional: enrich UI status with duration/error.
        try:
            if extra and isinstance(extra, dict):
                if "duration_ms" in extra and extra.get("duration_ms") is not None:
                    cur["last_duration_ms"] = int(max(0, int(extra.get("duration_ms") or 0)))
                if "error" in extra and extra.get("error"):
                    # Never persist secrets/tokens into UI-facing timer status.
                    cur["last_error"] = _redact_secrets(str(extra.get("error") or "")).strip()[:500]
                elif st_s != "error":
                    # Clear stale error on successful runs.
                    cur.pop("last_error", None)
        except Exception:
            pass
        st[tid] = cur
        _timers_state_save(st)
        ev_extra: dict[str, Any] = {"state": st_s, "job_id": cur.get("last_job_id")}
        try:
            if extra and isinstance(extra, dict):
                if extra.get("duration_ms") is not None:
                    ev_extra["duration_ms"] = int(max(0, int(extra.get("duration_ms") or 0)))
                if extra.get("error"):
                    ev_extra["error"] = _redact_secrets(str(extra.get("error") or "")).strip()[:500]
        except Exception:
            pass
        _timer_event_append(tid, "finished", ev_extra)
    except Exception:
        return


def _ui_state_load() -> dict[str, str]:
    try:
        if not UI_STATE_PATH.exists():
            return {}
        with UI_STATE_LOCK:
            raw = UI_STATE_PATH.read_text(encoding="utf-8", errors="replace")
        j = json.loads(raw) if raw else {}
        if not isinstance(j, dict):
            return {}
        out: dict[str, str] = {}
        for k, v in j.items():
            if not isinstance(k, str):
                continue
            if isinstance(v, str):
                out[k] = v
            elif v is None:
                continue
            else:
                # keep as JSON string
                try:
                    out[k] = json.dumps(v, ensure_ascii=True)
                except Exception:
                    continue
        return out
    except Exception:
        return {}


def _ui_state_save(state: dict[str, str]) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with UI_STATE_LOCK:
            UI_STATE_PATH.write_text(
                json.dumps(state or {}, indent=2, sort_keys=True, ensure_ascii=True),
                encoding="utf-8",
            )
    except Exception:
        return


def _app_state_load() -> dict[str, Any]:
    try:
        if not APP_STATE_PATH.exists():
            return {}
        with APP_STATE_LOCK:
            raw = APP_STATE_PATH.read_text(encoding="utf-8", errors="replace")
        j = json.loads(raw) if raw else {}
        return j if isinstance(j, dict) else {}
    except Exception:
        return {}


def _app_state_save(state: dict[str, Any]) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with APP_STATE_LOCK:
            APP_STATE_PATH.write_text(
                json.dumps(state or {}, indent=2, sort_keys=True, ensure_ascii=True),
                encoding="utf-8",
            )
    except Exception:
        return


def _ui_state_key_ok(key: str) -> bool:
    # keep keys bounded; do not allow very large / binary keys
    try:
        k = str(key or "")
    except Exception:
        return False
    if not k or len(k) > 240:
        return False
    # allow common chars used in existing localStorage keys
    return bool(re.match(r"^[a-zA-Z0-9_\-:\./]+$", k))


def _ui_state_val_ok(val: str) -> bool:
    try:
        v = str(val or "")
    except Exception:
        return False
    return len(v) <= 10000


def _profile_id_from_label(label: str) -> str:
    raw = str(label or "").strip()
    if not raw:
        return ""
    # ASCII-only, file-safe id
    out = re.sub(r"[^a-zA-Z0-9_-]+", "_", raw).strip("_")
    return out[:48]


def _profile_id_ok(pid: str) -> bool:
    p = str(pid or "").strip()
    if not p or len(p) > 48:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", p))


def _ui_items_snapshot(prefix: str = "influxbro") -> dict[str, str]:
    st = _ui_state_load()
    out: dict[str, str] = {}
    pref = str(prefix or "")
    for k, v in st.items():
        try:
            if not isinstance(k, str) or not isinstance(v, str):
                continue
            if pref and not k.startswith(pref):
                continue
            lk = k.lower()
            if "token" in lk or "password" in lk or "delete_confirm" in lk or "confirm_phrase" in lk:
                continue
            out[k] = v
        except Exception:
            continue
    return out


def _profiles_ensure_defaults() -> None:
    try:
        with UI_PROFILES_LOCK:
            UI_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
            existing = [p for p in UI_PROFILES_DIR.iterdir() if p.is_file() and p.suffix == ".json"]
            if existing:
                if not UI_PROFILE_ACTIVE_PATH.exists():
                    # pick first existing
                    try:
                        pid = existing[0].stem
                        UI_PROFILE_ACTIVE_PATH.write_text(
                            json.dumps({"active": pid, "updated_at": _utc_now_iso_ms()}, indent=2, sort_keys=True),
                            encoding="utf-8",
                        )
                    except Exception:
                        pass
                return

            # Create defaults from current state (best-effort)
            items = _ui_items_snapshot(prefix="influxbro")
            for lbl in ("PC", "MOBIL"):
                pid = _profile_id_from_label(lbl)
                if not pid:
                    continue
                path = UI_PROFILES_DIR / f"{pid}.json"
                payload = {
                    "id": pid,
                    "label": lbl,
                    "updated_at": _utc_now_iso_ms(),
                    "items": items,
                }
                try:
                    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
                except Exception:
                    continue

            if not UI_PROFILE_ACTIVE_PATH.exists():
                try:
                    UI_PROFILE_ACTIVE_PATH.write_text(
                        json.dumps({"active": "PC", "updated_at": _utc_now_iso_ms()}, indent=2, sort_keys=True),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
    except Exception:
        return


def _profile_path(pid: str) -> Path:
    return UI_PROFILES_DIR / f"{pid}.json"


def _profile_load(pid: str) -> dict[str, Any] | None:
    try:
        if not _profile_id_ok(pid):
            return None
        path = _profile_path(pid)
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8", errors="replace")
        j = json.loads(raw) if raw else None
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def _profile_save(pid: str, label: str, items: dict[str, str]) -> None:
    try:
        if not _profile_id_ok(pid):
            return
        UI_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        safe_items: dict[str, str] = {}
        for k, v in (items or {}).items():
            if not isinstance(k, str) or not isinstance(v, str):
                continue
            if not _ui_state_key_ok(k) or not _ui_state_val_ok(v):
                continue
            lk = k.lower()
            if "token" in lk or "password" in lk or "delete_confirm" in lk or "confirm_phrase" in lk:
                continue
            safe_items[k] = v
        payload = {
            "id": pid,
            "label": str(label or pid).strip() or pid,
            "updated_at": _utc_now_iso_ms(),
            "items": safe_items,
        }
        _profile_path(pid).write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
            encoding="utf-8",
        )
    except Exception:
        return


def _profile_list() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        UI_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted([p for p in UI_PROFILES_DIR.iterdir() if p.is_file() and p.suffix == ".json"], key=lambda p: p.name)
        for p in files:
            try:
                pid = p.stem
                j = _profile_load(pid) or {}
                label = str(j.get("label") or pid)
                updated_at = j.get("updated_at")
                items = j.get("items") if isinstance(j.get("items"), dict) else {}
                out.append({
                    "id": pid,
                    "label": label,
                    "updated_at": updated_at,
                    "count": len(items),
                })
            except Exception:
                continue
    except Exception:
        return []
    return out


def _active_profile_get() -> str | None:
    try:
        if not UI_PROFILE_ACTIVE_PATH.exists():
            return None
        raw = UI_PROFILE_ACTIVE_PATH.read_text(encoding="utf-8", errors="replace")
        j = json.loads(raw) if raw else {}
        if not isinstance(j, dict):
            return None
        pid = str(j.get("active") or "").strip()
        return pid if _profile_id_ok(pid) else None
    except Exception:
        return None


def _active_profile_set(pid: str) -> None:
    try:
        if not _profile_id_ok(pid):
            return
        UI_PROFILE_ACTIVE_PATH.write_text(
            json.dumps({"active": pid, "updated_at": _utc_now_iso_ms()}, indent=2, sort_keys=True, ensure_ascii=True),
            encoding="utf-8",
        )
    except Exception:
        return


def _dash_last_save(payload: dict[str, Any]) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with DASH_LAST_LOCK:
            DASH_LAST_PATH.write_text(
                json.dumps(payload or {}, indent=2, sort_keys=True, ensure_ascii=True),
                encoding="utf-8",
            )
    except Exception:
        return


def _dash_last_load() -> dict[str, Any] | None:
    try:
        if not DASH_LAST_PATH.exists():
            return None
        with DASH_LAST_LOCK:
            raw = DASH_LAST_PATH.read_text(encoding="utf-8", errors="replace")
        j = json.loads(raw) if raw else None
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def _dash_last_set_from_query(
    body: dict[str, Any],
    cache_id: str,
    key: dict[str, Any] | None,
) -> None:
    try:
        if not cache_id:
            return
        measurement = str(body.get("measurement") or "").strip()
        field = str(body.get("field") or "").strip()
        if not measurement or not field:
            return
        payload = {
            "v": 1,
            "at": _utc_now_iso_ms(),
            "cache_id": str(cache_id),
            "key": key if isinstance(key, dict) else None,
            "selection": {
                "measurement": measurement,
                "field": field,
                "entity_id": str(body.get("entity_id") or "").strip() or None,
                "friendly_name": str(body.get("friendly_name") or "").strip() or None,
                "range": str(body.get("range") or "").strip() or None,
                "start": str(body.get("start") or "").strip() or None,
                "stop": str(body.get("stop") or "").strip() or None,
                "unit": str(body.get("unit") or "").strip() or None,
                "detail_mode": str(body.get("detail_mode") or "").strip() or None,
                "manual_density_pct": body.get("manual_density_pct"),
            },
        }
        _dash_last_save(payload)
    except Exception:
        return

def load_cfg():
    # NOTE: No automatic autodetect at startup.
    # Autodetect is only triggered by explicit user action in the Config UI.
    global LAST_AUTODETECT_SOURCE
    LAST_AUTODETECT_SOURCE = None

    cfg = dict(DEFAULT_CFG)
    if RUNTIME_CFG_FILE.exists():
        try:
            disk = json.loads(RUNTIME_CFG_FILE.read_text(encoding="utf-8")) or {}
            if isinstance(disk, dict):
                cfg.update(disk)
        except Exception:
            pass

    # Normalize influx_version for all runtime callers.
    # This is intentionally best-effort and does not persist anything.
    try:
        v = int(cfg.get("influx_version", 2) or 2)
    except Exception:
        v = 2
    if v not in (1, 2):
        v = 2
    try:
        db = str(cfg.get("database") or "").strip()
    except Exception:
        db = ""
    has_v2 = bool(cfg.get("token")) and bool(cfg.get("org")) and bool(cfg.get("bucket"))
    if v != 2 and (not db) and has_v2:
        # Safety: prefer v2 to avoid confusing "v1 requires database" errors.
        v = 2
    cfg["influx_version"] = v
    return cfg


def _path_is_within(root: Path, p: Path) -> bool:
    try:
        rr = root.resolve()
        rp = p.resolve()
        return rp == rr or rr in rp.parents
    except Exception:
        return False


def _maybe_migrate_backups(cfg: dict[str, Any], target_dir: Path) -> None:
    """One-time migrate backups from old default (/data/backups) to /config.

    This is used to make backups visible in the HA file browser (under /config).
    """

    try:
        if not _path_is_within(CONFIG_DIR, target_dir):
            return
        # Only migrate when we're using the new default.
        if target_dir.resolve() != DEFAULT_BACKUP_DIR.resolve():
            return
        if bool(cfg.get("backup_migrated_to_config")):
            return

        src = OLD_DEFAULT_BACKUP_DIR
        if not src.exists() or not src.is_dir():
            cfg["backup_migrated_to_config"] = True
            save_cfg(cfg)
            return

        files = [p for p in src.iterdir() if p.is_file()]
        if not files:
            cfg["backup_migrated_to_config"] = True
            save_cfg(cfg)
            try:
                shutil.rmtree(src, ignore_errors=True)
            except Exception:
                pass
            return

        target_dir.mkdir(parents=True, exist_ok=True)

        for p in files:
            dst = target_dir / p.name
            if dst.exists():
                try:
                    if dst.stat().st_size == p.stat().st_size:
                        p.unlink(missing_ok=True)
                        continue
                except Exception:
                    pass
                # Avoid overwriting: copy with a suffix
                stem = p.name
                n = 1
                while True:
                    cand = target_dir / f"{stem}.dup{n}"
                    if not cand.exists():
                        dst = cand
                        break
                    n += 1

            shutil.copy2(p, dst)
            # Only delete source if destination exists and is non-empty (best-effort)
            try:
                if dst.exists() and dst.stat().st_size >= 0:
                    p.unlink(missing_ok=True)
            except Exception:
                pass

        # Remove old directory (user requested delete)
        try:
            shutil.rmtree(src, ignore_errors=True)
        except Exception:
            pass

        # Ensure persisted config points to the new path
        cfg["backup_dir"] = str(DEFAULT_BACKUP_DIR)
        cfg["backup_migrated_to_config"] = True
        save_cfg(cfg)
    except Exception:
        # Never break normal operation due to migration issues
        return


def backup_dir(cfg: dict[str, Any] | None = None) -> Path:
    """Return the configured backup directory (constrained under /config or /data)."""

    try:
        c = cfg or load_cfg()
        raw = str(c.get("backup_dir") or "").strip()
    except Exception:
        c = cfg or {}
        raw = ""

    # Treat the old default as legacy; keep behavior aligned with the new default.
    if raw in (str(OLD_DEFAULT_BACKUP_DIR), "/data/backups"):
        raw = ""

    if not raw:
        target = BACKUP_DIR
    else:
        try:
            p = Path(raw)
            if not p.is_absolute():
                # Relative paths live under /config.
                p = CONFIG_DIR / raw
            p = p.resolve()
            cfg_root = CONFIG_DIR.resolve()
            data_root = DATA_DIR.resolve()
            if _path_is_within(cfg_root, p) or _path_is_within(data_root, p):
                target = p
            else:
                target = BACKUP_DIR
        except Exception:
            target = BACKUP_DIR

    # Migrate old default backups to /config when applicable.
    # Use persisted runtime config (do not persist YAML overlays).
    try:
        _maybe_migrate_backups(load_cfg(), target)
    except Exception:
        pass
    return target


def _backup_disk_usage_bytes(cfg: dict[str, Any]) -> dict[str, int] | None:
    """Return disk usage for the backup directory (best-effort)."""

    try:
        bdir = backup_dir(cfg)
        bdir.mkdir(parents=True, exist_ok=True)
        du = shutil.disk_usage(str(bdir))
        return {"total": int(du.total), "used": int(du.used), "free": int(du.free)}
    except Exception:
        return None


def _addon_data_usage_bytes() -> int | None:
    """Return total bytes used under /data for this add-on (best-effort)."""

    try:
        total = 0
        root = DATA_DIR
        if not root.exists():
            return 0
        for base, _, files in os.walk(str(root)):
            for fn in files:
                try:
                    p = os.path.join(base, fn)
                    total += int(os.path.getsize(p) or 0)
                except Exception:
                    continue
        return int(total)
    except Exception:
        return None


def _backup_require_free_space(cfg: dict[str, Any]) -> tuple[bool, str | None]:
    """Return (ok, error_message) according to backup_min_free_mb."""

    try:
        min_mb = int(cfg.get("backup_min_free_mb", 0) or 0)
    except Exception:
        min_mb = 0
    if min_mb <= 0:
        return True, None

    du = _backup_disk_usage_bytes(cfg)
    if not du:
        return True, None
    free = int(du.get("free") or 0)
    if free >= min_mb * 1024 * 1024:
        return True, None
    free_mb = int(free / 1024 / 1024)
    return False, f"Nicht genug freier Speicher fuer Backup. Frei: {free_mb} MB; erforderlich: {min_mb} MB"


# Configure logging early from persisted config.
try:
    configure_logging(load_cfg())
except Exception:
    # Worst case: Flask still logs to stderr.
    pass


def save_cfg(cfg: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_CFG_FILE.write_text(json.dumps(cfg, indent=2, sort_keys=True), encoding="utf-8")


def _utc_now_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _meta_add_event(meta: dict[str, Any], kind: str, note: str | None = None, at: str | None = None) -> None:
    """Append a small timestamped event to a cache/job meta dict (best-effort)."""

    try:
        xs = meta.get("events")
        events: list[dict[str, Any]] = xs if isinstance(xs, list) else []
        events = [e for e in events if isinstance(e, dict)]
        events.append({
            "at": str(at or _utc_now_iso_ms()),
            "kind": str(kind or "event"),
            "note": (str(note)[:400] if note else ""),
        })
        # Keep meta small.
        if len(events) > 60:
            events = events[-60:]
        meta["events"] = events
    except Exception:
        return


def _cache_usage_append(cfg: dict[str, Any] | None, entry: dict[str, Any]) -> None:
    """Append a cache usage entry for the UI and (optionally) the server log."""

    try:
        e = dict(entry or {})
        e.setdefault("at", _utc_now_iso_ms())
        e.setdefault("id", uuid.uuid4().hex)
        # keep small and safe
        for k in list(e.keys()):
            lk = str(k).lower()
            if "token" in lk or "password" in lk or "confirm_phrase" in lk:
                e.pop(k, None)
        # cap large strings
        for k in ("kind", "page", "step", "cache_id", "run_id", "note", "series_key"):
            if k in e and e[k] is not None:
                e[k] = str(e[k])[:400]
        with CACHE_USAGE_LOCK:
            CACHE_USAGE_MEM.append(e)
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with CACHE_USAGE_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(e, ensure_ascii=True) + "\n")
        except Exception:
            pass

        try:
            if CACHE_USAGE_LOGGING and bool(cfg or {}):
                # Keep log line compact.
                LOG.info(
                    "cache_usage kind=%s page=%s run_id=%s cache_id=%s step=%s dur_ms=%s note=%s",
                    e.get("kind"),
                    e.get("page"),
                    e.get("run_id"),
                    e.get("cache_id"),
                    e.get("step"),
                    e.get("dur_ms"),
                    (str(e.get("note") or "")[:200]),
                )
        except Exception:
            pass
    except Exception:
        return


def _cache_usage_tail(limit: int = 500) -> list[dict[str, Any]]:
    try:
        lim = int(limit or 500)
    except Exception:
        lim = 500
    lim = min(5000, max(1, lim))
    with CACHE_USAGE_LOCK:
        xs = list(CACHE_USAGE_MEM)
    if xs:
        return xs[-lim:]
    # Cold start: best-effort tail from file.
    try:
        if CACHE_USAGE_PATH.exists():
            lines = CACHE_USAGE_PATH.read_text(encoding="utf-8").splitlines()
            out: list[dict[str, Any]] = []
            for ln in lines[-lim:]:
                try:
                    j = json.loads(ln)
                    if isinstance(j, dict):
                        out.append(j)
                except Exception:
                    continue
            return out
    except Exception:
        pass
    return []


def _ui_action_append(entry: dict[str, Any]) -> None:
    """Append a compact UI action record for support and bug reports."""

    try:
        e = dict(entry or {})
        e.setdefault("at", _utc_now_iso_ms())
        e.setdefault("id", uuid.uuid4().hex)
        for k in list(e.keys()):
            lk = str(k).lower()
            if "token" in lk or "password" in lk or "confirm_phrase" in lk:
                e.pop(k, None)
        for k in ("page", "ui", "text"):
            if k in e and e[k] is not None:
                e[k] = str(e[k])[:200]
        extra = e.get("extra")
        if isinstance(extra, dict):
            safe_extra: dict[str, str] = {}
            for k, v in list(extra.items())[:10]:
                safe_extra[str(k)[:40]] = str(v)[:120]
            e["extra"] = safe_extra
        elif extra is not None:
            e["extra"] = str(extra)[:200]

        with UI_ACTIONS_LOCK:
            UI_ACTIONS_MEM.append(e)
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with UI_ACTIONS_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(e, ensure_ascii=True) + "\n")
        except Exception:
            pass

        try:
            extra_s = json.dumps(e.get("extra"), ensure_ascii=True)[:300] if e.get("extra") is not None else ""
        except Exception:
            extra_s = str(e.get("extra") or "")[:300]
        try:
            LOG.info(
                "ui_action at=%s page=%s ui=%s text=%s extra=%s",
                e.get("at"),
                e.get("page"),
                e.get("ui"),
                e.get("text"),
                extra_s,
            )
        except Exception:
            pass
    except Exception:
        return


def _ui_action_tail(limit: int = 5) -> list[dict[str, Any]]:
    try:
        lim = min(100, max(1, int(limit or 5)))
    except Exception:
        lim = 5
    with UI_ACTIONS_LOCK:
        xs = list(UI_ACTIONS_MEM)
    if xs:
        return xs[-lim:]
    try:
        if UI_ACTIONS_PATH.exists():
            lines = UI_ACTIONS_PATH.read_text(encoding="utf-8").splitlines()
            out: list[dict[str, Any]] = []
            for ln in lines[-lim:]:
                try:
                    j = json.loads(ln)
                    if isinstance(j, dict):
                        out.append(j)
                except Exception:
                    continue
            return out
    except Exception:
        pass
    return []


def _analysis_history_append(entry: dict[str, Any]) -> None:
    try:
        # Apply retention settings (configured via Settings).
        cutoff_dt: datetime | None = None
        try:
            cutoff_dt = datetime.now(timezone.utc) - timedelta(days=int(WORKLOG_MAX_DAYS or 14))
        except Exception:
            cutoff_dt = None

        e = dict(entry or {})
        e.setdefault("at", _utc_now_iso_ms())
        e.setdefault("id", uuid.uuid4().hex)
        for k in list(e.keys()):
            lk = str(k).lower()
            if "token" in lk or "password" in lk or "confirm_phrase" in lk:
                e.pop(k, None)
        for k in (
            "kind",
            "step",
            "page",
            "measurement",
            "field",
            "entity_id",
            "friendly_name",
            "detail",
            "status",
            "trace_id",
        ):
            if k in e and e[k] is not None:
                e[k] = str(e[k])[:2000]
        try:
            if e.get("dur_ms") is not None:
                e["dur_ms"] = int(max(0, int(e.get("dur_ms") or 0)))
        except Exception:
            pass
        with ANALYSIS_HISTORY_LOCK:
            ANALYSIS_HISTORY_MEM.append(e)
            _worklog_prune_mem_locked(cutoff_dt=cutoff_dt)
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with ANALYSIS_HISTORY_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(e, ensure_ascii=True) + "\n")
        except Exception:
            pass

        # Best-effort disk pruning (avoid churn).
        try:
            _worklog_prune_disk_best_effort(cutoff_dt=cutoff_dt)
        except Exception:
            pass
    except Exception:
        return


def _worklog_prune_mem_locked(cutoff_dt: datetime | None = None) -> None:
    """Prune in-memory worklog buffer.

    ANALYSIS_HISTORY_LOCK must be held.
    """

    try:
        max_entries = int(WORKLOG_MAX_ENTRIES or 2000)
    except Exception:
        max_entries = 2000
    max_entries = max(200, min(50000, max_entries))

    if cutoff_dt is not None:
        while ANALYSIS_HISTORY_MEM:
            try:
                first = ANALYSIS_HISTORY_MEM[0]
                at = _trace_parse_iso(str(first.get("at") or ""))
                if at and at < cutoff_dt:
                    ANALYSIS_HISTORY_MEM.popleft()
                    continue
            except Exception:
                break
            break

    while len(ANALYSIS_HISTORY_MEM) > max_entries:
        try:
            ANALYSIS_HISTORY_MEM.popleft()
        except Exception:
            break


def _worklog_prune_disk_best_effort(cutoff_dt: datetime | None = None) -> None:
    global WORKLOG_LAST_PRUNE_MONO

    # Avoid frequent full-file rewrites.
    now = time.monotonic()
    if (now - float(WORKLOG_LAST_PRUNE_MONO or 0.0)) < 8.0:
        return
    WORKLOG_LAST_PRUNE_MONO = now

    try:
        if not ANALYSIS_HISTORY_PATH.exists():
            return
    except Exception:
        return

    try:
        max_entries = int(WORKLOG_MAX_ENTRIES or 2000)
    except Exception:
        max_entries = 2000
    max_entries = max(200, min(50000, max_entries))

    try:
        lines = ANALYSIS_HISTORY_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return

    if not lines:
        return

    # Fast path: already within entry limit and no age cutoff.
    if cutoff_dt is None and len(lines) <= max_entries:
        return

    out: list[str] = []
    for ln in lines:
        try:
            j = json.loads(ln)
        except Exception:
            continue
        if not isinstance(j, dict):
            continue
        if cutoff_dt is not None:
            at = _trace_parse_iso(str(j.get("at") or ""))
            if at and at < cutoff_dt:
                continue
        out.append(json.dumps(j, ensure_ascii=True))

    if len(out) > max_entries:
        out = out[-max_entries:]

    try:
        tmp = ANALYSIS_HISTORY_PATH.with_suffix(".tmp")
        tmp.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
        tmp.replace(ANALYSIS_HISTORY_PATH)
    except Exception:
        return


def _worklog_append_op(
    *,
    purpose: str,
    op: str,
    status: str,
    detail: str,
    measurement: str = "",
    field: str = "",
    entity_id: str = "",
    friendly_name: str = "",
    window_start: str = "",
    window_stop: str = "",
    source: str = "",
    reason_code: str = "",
    reason_label: str = "",
    duration_ms: int | None = None,
    counts: dict[str, Any] | None = None,
    cache: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Append a structured worklog entry (for non-expert diagnostics)."""

    try:
        ex: dict[str, Any] = {}
        ex["purpose"] = str(purpose or "")[:40]
        ex["op"] = str(op or "")[:80]
        if window_start:
            ex["window_start"] = str(window_start)
        if window_stop:
            ex["window_stop"] = str(window_stop)
        if source:
            ex["source"] = str(source)[:20]
        if reason_code:
            ex["reason_code"] = str(reason_code)[:60]
        if reason_label:
            ex["reason_label"] = str(reason_label)[:240]
        if duration_ms is not None:
            try:
                ex["duration_ms"] = int(duration_ms)
            except Exception:
                ex["duration_ms"] = duration_ms
        if isinstance(counts, dict) and counts:
            ex["counts"] = {str(k)[:40]: counts[k] for k in list(counts.keys())[:30]}
        if isinstance(cache, dict) and cache:
            safe_cache = {}
            for k, v in list(cache.items())[:30]:
                lk = str(k).lower()
                if "token" in lk or "password" in lk:
                    continue
                safe_cache[str(k)[:40]] = v
            ex["cache"] = safe_cache
        if isinstance(extra, dict) and extra:
            safe_extra = {}
            for k, v in list(extra.items())[:40]:
                lk = str(k).lower()
                if "token" in lk or "password" in lk:
                    continue
                safe_extra[str(k)[:40]] = v
            ex.update(safe_extra)

        _analysis_history_append({
            "kind": "worklog",
            "step": f"{str(purpose or '')}.{str(op or '')}".strip("."),
            "page": str(purpose or "dashboard")[:40],
            "measurement": str(measurement or "")[:200],
            "field": str(field or "")[:200],
            "entity_id": str(entity_id or "")[:200],
            "friendly_name": str(friendly_name or "")[:200],
            "detail": str(detail or "")[:4000],
            "status": str(status or "")[:40],
            "extra": ex,
            "ip": _req_ip(),
            "ua": _req_ua(),
        })
    except Exception:
        return


def _analysis_history_tail(limit: int = 500) -> list[dict[str, Any]]:
    try:
        lim = min(5000, max(1, int(limit or 500)))
    except Exception:
        lim = 500
    cutoff_dt: datetime | None = None
    try:
        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=int(WORKLOG_MAX_DAYS or 14))
    except Exception:
        cutoff_dt = None

    with ANALYSIS_HISTORY_LOCK:
        _worklog_prune_mem_locked(cutoff_dt=cutoff_dt)
        xs = list(ANALYSIS_HISTORY_MEM)
    if xs:
        return xs[-lim:]
    try:
        if ANALYSIS_HISTORY_PATH.exists():
            lines = ANALYSIS_HISTORY_PATH.read_text(encoding="utf-8").splitlines()
            out: list[dict[str, Any]] = []
            max_entries = lim
            try:
                max_entries = min(max_entries, int(WORKLOG_MAX_ENTRIES or max_entries))
            except Exception:
                pass

            for ln in lines[-max_entries:]:
                try:
                    j = json.loads(ln)
                    if isinstance(j, dict):
                        if cutoff_dt is not None:
                            at = _trace_parse_iso(str(j.get("at") or ""))
                            if at and at < cutoff_dt:
                                continue
                        out.append(j)
                except Exception:
                    continue
            return out
    except Exception:
        pass
    return []


MONITOR_REASON_LABELS = {
    "steigt_zu_stark": "steigt zu stark",
    "faellt_zu_stark": "faellt zu stark",
    "ausserhalb_min_max": "ausserhalb Min/Max",
    "ungueltiger_wert": "ungueltiger Wert",
    "fault_active": "fault_active",
}


def _monitor_default_config() -> dict[str, Any]:
    return {
        "global": {
            "critical_repeat_threshold": 3,
            "default_recovery_valid_streak": 2,
        },
        "monitors": [],
    }


def _monitor_normalize_item(item: dict[str, Any], cfg_global: dict[str, Any] | None = None) -> dict[str, Any]:
    g = cfg_global if isinstance(cfg_global, dict) else {}
    key = str(item.get("key") or item.get("id") or "").strip()
    if not key:
        raise ValueError("key required")

    def _flt(name: str) -> float | None:
        val = item.get(name)
        if val in (None, ""):
            return None
        try:
            out = float(val)
        except Exception:
            return None
        return out if math.isfinite(out) else None

    def _int(name: str, default: int) -> int:
        try:
            return max(0, int(item.get(name, default)))
        except Exception:
            return default

    def _bool(name: str, default: bool = False) -> bool:
        raw = item.get(name, default)
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in ("1", "true", "yes", "on")

    correction = item.get("correction_map") if isinstance(item.get("correction_map"), dict) else {}
    out = {
        "key": key,
        "label": str(item.get("label") or key).strip(),
        "enabled": _bool("enabled", True),
        "min_value": _flt("min_value"),
        "max_value": _flt("max_value"),
        "max_rise": _flt("max_rise"),
        "max_fall": _flt("max_fall"),
        "invalid_zero": _bool("invalid_zero", True),
        "mode": str(item.get("mode") or "pending").strip().lower() or "pending",
        "recovery_mode": str(item.get("recovery_mode") or "range").strip().lower() or "range",
        "recovery_band_abs": _flt("recovery_band_abs"),
        "recovery_valid_streak": _int("recovery_valid_streak", int(g.get("default_recovery_valid_streak") or 2)),
        "critical_repeat_threshold": _int("critical_repeat_threshold", int(g.get("critical_repeat_threshold") or 3)),
        "correction_map": {},
    }
    if out["mode"] not in ("auto", "pending"):
        out["mode"] = "pending"
    if out["recovery_mode"] not in ("range", "last_valid_band"):
        out["recovery_mode"] = "range"
    for reason in MONITOR_REASON_LABELS:
        action = str(correction.get(reason) or item.get(f"correction_{reason}") or "last_valid").strip().lower() or "last_valid"
        if action not in ("last_valid", "delete", "clamp", "none"):
            action = "last_valid"
        out["correction_map"][reason] = action
    return out


def _monitor_load_config() -> dict[str, Any]:
    base = _monitor_default_config()
    try:
        if not MONITOR_CFG_PATH.exists():
            return base
        raw = MONITOR_CFG_PATH.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw) if raw else {}
        if not isinstance(data, dict):
            return base
        g = data.get("global") if isinstance(data.get("global"), dict) else {}
        monitors_raw = data.get("monitors") if isinstance(data.get("monitors"), list) else []
        monitors = []
        for item in monitors_raw:
            if not isinstance(item, dict):
                continue
            try:
                monitors.append(_monitor_normalize_item(item, g))
            except Exception:
                continue
        base["global"].update(g)
        base["monitors"] = monitors
        return base
    except Exception:
        return base


def _monitor_save_config(data: dict[str, Any]) -> dict[str, Any]:
    cfg = _monitor_default_config()
    g = data.get("global") if isinstance(data.get("global"), dict) else {}
    cfg["global"]["critical_repeat_threshold"] = max(1, int(g.get("critical_repeat_threshold") or 3))
    cfg["global"]["default_recovery_valid_streak"] = max(1, int(g.get("default_recovery_valid_streak") or 2))
    monitors_raw = data.get("monitors") if isinstance(data.get("monitors"), list) else []
    seen: set[str] = set()
    monitors = []
    for item in monitors_raw:
        if not isinstance(item, dict):
            continue
        mon = _monitor_normalize_item(item, cfg["global"])
        if mon["key"] in seen:
            continue
        seen.add(mon["key"])
        monitors.append(mon)
    cfg["monitors"] = monitors
    with MONITOR_LOCK:
        MONITOR_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
        MONITOR_CFG_PATH.write_text(json.dumps(cfg, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    return cfg


def _monitor_load_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        raw = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw) if raw else default
        return data if isinstance(data, type(default)) else default
    except Exception:
        return default


def _monitor_save_json(path: Path, data: Any) -> None:
    with MONITOR_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")


def _monitor_load_state() -> dict[str, Any]:
    return _monitor_load_json(MONITOR_STATE_PATH, {})


def _monitor_save_state(state: dict[str, Any]) -> None:
    _monitor_save_json(MONITOR_STATE_PATH, state)


def _analysis_load_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        raw = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw) if raw else default
        return data if isinstance(data, type(default)) else default
    except Exception:
        return default


def _analysis_save_json(path: Path, data: Any) -> None:
    with ANALYSIS_START_CACHE_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")


def _analysis_series_key(measurement: str, field: str, entity_id: str | None, friendly_name: str | None) -> str:
    return "|".join([
        str(measurement or "").strip(),
        str(field or "").strip(),
        str(entity_id or "").strip(),
        str(friendly_name or "").strip(),
    ])


def _analysis_start_cache_load() -> dict[str, Any]:
    return _analysis_load_json(ANALYSIS_START_CACHE_PATH, {})


def _analysis_start_cache_save(data: dict[str, Any]) -> None:
    _analysis_save_json(ANALYSIS_START_CACHE_PATH, data)


def _monitor_load_pending() -> list[dict[str, Any]]:
    return _monitor_load_json(MONITOR_PENDING_PATH, [])


def _monitor_save_pending(rows: list[dict[str, Any]]) -> None:
    _monitor_save_json(MONITOR_PENDING_PATH, rows)


def _monitor_event_append(entry: dict[str, Any]) -> None:
    try:
        e = dict(entry or {})
        e.setdefault("id", uuid.uuid4().hex)
        e.setdefault("at", _utc_now_iso_ms())
        with MONITOR_LOCK:
            MONITOR_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with MONITOR_EVENTS_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(e, ensure_ascii=True) + "\n")
    except Exception:
        return


def _monitor_events_read(limit: int = 500) -> list[dict[str, Any]]:
    try:
        lim = min(5000, max(1, int(limit or 500)))
    except Exception:
        lim = 500
    try:
        if not MONITOR_EVENTS_PATH.exists():
            return []
        lines = MONITOR_EVENTS_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
        out: list[dict[str, Any]] = []
        for ln in lines[-lim:]:
            try:
                j = json.loads(ln)
            except Exception:
                continue
            if isinstance(j, dict):
                out.append(j)
        return out
    except Exception:
        return []


def _monitor_get_item(cfg: dict[str, Any], key: str) -> dict[str, Any] | None:
    want = str(key or "").strip()
    for item in cfg.get("monitors", []):
        if isinstance(item, dict) and str(item.get("key") or "").strip() == want:
            return item
    return None


def _monitor_detect_reason(item: dict[str, Any], last_valid: float | None, value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "ungueltiger_wert"
    if bool(item.get("invalid_zero", True)) and value == 0:
        return "ungueltiger_wert"
    min_value = item.get("min_value")
    max_value = item.get("max_value")
    if min_value is not None and value < float(min_value):
        return "ausserhalb_min_max"
    if max_value is not None and value > float(max_value):
        return "ausserhalb_min_max"
    if last_valid is not None:
        max_rise = item.get("max_rise")
        max_fall = item.get("max_fall")
        if max_rise is not None and (value - last_valid) > float(max_rise):
            return "steigt_zu_stark"
        if max_fall is not None and (last_valid - value) > float(max_fall):
            return "faellt_zu_stark"
    return ""


def _monitor_recovery_ok(item: dict[str, Any], state: dict[str, Any], value: float | None) -> bool:
    if value is None or not math.isfinite(value):
        return False
    if _monitor_detect_reason(item, state.get("last_valid_value"), value):
        return False
    mode = str(item.get("recovery_mode") or "range")
    if mode == "last_valid_band":
        last_valid = state.get("last_valid_value")
        band = item.get("recovery_band_abs")
        if last_valid is None or band is None:
            return False
        try:
            return abs(float(value) - float(last_valid)) <= abs(float(band))
        except Exception:
            return False
    return True


def _monitor_suggest_value(item: dict[str, Any], state: dict[str, Any], value: float | None, reason: str) -> tuple[str, float | None]:
    action = str((item.get("correction_map") or {}).get(reason) or "last_valid")
    if action == "delete":
        return action, None
    if action == "clamp" and value is not None and math.isfinite(value):
        lo = item.get("min_value")
        hi = item.get("max_value")
        out = float(value)
        if lo is not None:
            out = max(out, float(lo))
        if hi is not None:
            out = min(out, float(hi))
        return action, out
    if action == "none":
        return action, value
    last_valid = state.get("last_valid_value")
    try:
        return "last_valid", None if last_valid is None else float(last_valid)
    except Exception:
        return "last_valid", None


def _monitor_recount_pending(state: dict[str, Any], key: str) -> None:
    pending = _monitor_load_pending()
    open_count = len([p for p in pending if isinstance(p, dict) and str(p.get("key") or "") == key and str(p.get("status") or "open") == "open"])
    cur = state.get(key) if isinstance(state.get(key), dict) else {}
    cur["pending_count"] = open_count
    state[key] = cur


def _monitor_evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    cfg = _monitor_load_config()
    key = str(payload.get("key") or "").strip()
    if not key:
        raise ValueError("key required")
    item = _monitor_get_item(cfg, key)
    if not item or not bool(item.get("enabled", True)):
        raise ValueError("monitor not found")

    at = str(payload.get("at") or _utc_now_iso_ms()).strip() or _utc_now_iso_ms()
    raw_in = payload.get("raw_value")
    try:
        value = float(raw_in)
        if not math.isfinite(value):
            value = None
    except Exception:
        value = None

    state_all = _monitor_load_state()
    state = state_all.get(key) if isinstance(state_all.get(key), dict) else {}
    status = str(state.get("status") or "normal")
    last_valid = state.get("last_valid_value")
    try:
        last_valid_num = None if last_valid is None else float(last_valid)
    except Exception:
        last_valid_num = None

    detected_reason = _monitor_detect_reason(item, last_valid_num, value)
    reason = detected_reason
    outlier = False
    recovered = False

    if status in ("fault_active", "recovering"):
        if _monitor_recovery_ok(item, state, value):
            streak = int(state.get("recovery_streak") or 0) + 1
            need = max(1, int(item.get("recovery_valid_streak") or 1))
            if streak >= need:
                status = "normal"
                recovered = True
                reason = ""
                state["fault_ended_at"] = at
                state["recovery_streak"] = 0
            else:
                status = "recovering"
                state["recovery_streak"] = streak
                reason = "fault_active"
                outlier = True
        else:
            status = "fault_active"
            state["recovery_streak"] = 0
            reason = detected_reason or "fault_active"
            outlier = True
    elif detected_reason:
        status = "fault_active"
        state["fault_started_at"] = at
        state["recovery_streak"] = 0
        reason = detected_reason
        outlier = True

    correction_action = "none"
    corrected_value = value
    correction_status = "none"
    pending_entry = None

    if outlier:
        state["fault_count"] = int(state.get("fault_count") or 0) + 1
        state["total_outliers"] = int(state.get("total_outliers") or 0) + 1
        correction_action, corrected_value = _monitor_suggest_value(item, state, value, reason)
        if str(item.get("mode") or "pending") == "auto":
            correction_status = "auto_applied"
        else:
            correction_status = "pending"
            pending = _monitor_load_pending()
            pending_entry = {
                "id": uuid.uuid4().hex,
                "key": key,
                "label": item.get("label") or key,
                "at": at,
                "reason": reason,
                "reason_label": MONITOR_REASON_LABELS.get(reason, reason),
                "raw_value": raw_in,
                "suggested_action": correction_action,
                "suggested_value": corrected_value,
                "status": "open",
            }
            pending.append(pending_entry)
            _monitor_save_pending(pending)
    else:
        state["fault_count"] = 0

    threshold = max(1, int(item.get("critical_repeat_threshold") or 3))
    critical = int(state.get("fault_count") or 0) >= threshold
    state.update({
        "status": status,
        "fault_active": status != "normal",
        "critical": critical,
        "last_reason": reason,
        "last_reason_label": MONITOR_REASON_LABELS.get(reason, reason),
        "last_raw_value": raw_in,
        "last_corrected_value": corrected_value,
        "last_event_at": at,
        "correction_action": correction_action,
        "correction_status": correction_status,
    })
    if not outlier and value is not None:
        state["last_valid_value"] = value
        state["last_valid_at"] = at
        state["last_corrected_value"] = value
    state_all[key] = state
    _monitor_recount_pending(state_all, key)
    _monitor_save_state(state_all)

    if outlier:
        _monitor_event_append({
            "kind": "outlier",
            "key": key,
            "label": item.get("label") or key,
            "at": at,
            "reason": reason,
            "reason_label": MONITOR_REASON_LABELS.get(reason, reason),
            "raw_value": raw_in,
            "corrected_value": corrected_value,
            "correction_action": correction_action,
            "correction_status": correction_status,
            "fault_active": bool(state.get("fault_active")),
            "critical": critical,
        })
    elif recovered:
        _monitor_event_append({
            "kind": "recovery",
            "key": key,
            "label": item.get("label") or key,
            "at": at,
            "raw_value": raw_in,
            "corrected_value": value,
            "fault_active": False,
            "critical": critical,
        })

    return {
        "key": key,
        "label": item.get("label") or key,
        "at": at,
        "status": status,
        "outlier": outlier,
        "recovered": recovered,
        "reason": reason,
        "reason_label": MONITOR_REASON_LABELS.get(reason, reason),
        "correction_action": correction_action,
        "corrected_value": corrected_value,
        "correction_status": correction_status,
        "critical": critical,
        "pending": pending_entry,
        "state": state_all.get(key),
    }


def _monitor_template_snapshot() -> dict[str, Any]:
    cfg = _monitor_load_config()
    state_all = _monitor_load_state()
    pending = _monitor_load_pending()
    items = []
    for mon in cfg.get("monitors", []):
        if not isinstance(mon, dict):
            continue
        key = str(mon.get("key") or "").strip()
        st = state_all.get(key) if isinstance(state_all.get(key), dict) else {}
        pend = len([p for p in pending if isinstance(p, dict) and str(p.get("key") or "") == key and str(p.get("status") or "open") == "open"])
        items.append({
            "key": key,
            "label": mon.get("label") or key,
            "raw_value": st.get("last_raw_value"),
            "corrected_value": st.get("last_corrected_value"),
            "last_valid_value": st.get("last_valid_value"),
            "last_reason": st.get("last_reason"),
            "last_reason_label": st.get("last_reason_label"),
            "outlier_flag": bool(st.get("last_reason")),
            "critical_flag": bool(st.get("critical")),
            "pending_count": pend,
            "fault_active_flag": bool(st.get("fault_active")),
            "status": st.get("status") or "normal",
            "event_count": int(st.get("total_outliers") or 0),
            "last_event_at": st.get("last_event_at"),
        })
    critical_items = [it for it in items if it.get("critical_flag")]
    open_pending = [p for p in pending if isinstance(p, dict) and str(p.get("status") or "open") == "open"]
    return {
        "items": items,
        "global": {
            "outlier_count": len(_monitor_events_read(5000)),
            "pending_count": len(open_pending),
            "critical_count": len(critical_items),
        },
        "critical": critical_items,
        "pending": open_pending,
    }


def _cache_usage_clear() -> None:
    try:
        with CACHE_USAGE_LOCK:
            CACHE_USAGE_MEM.clear()
        try:
            if CACHE_USAGE_PATH.exists():
                CACHE_USAGE_PATH.unlink()
        except Exception:
            pass
    except Exception:
        return


def _dash_cache_meta_path(cache_id: str) -> Path:
    return DASH_CACHE_DIR / f"{cache_id}.meta.json"


def _dash_cache_data_path(cache_id: str) -> Path:
    return DASH_CACHE_DIR / f"{cache_id}.data.json.gz"


def _dash_cache_cfg_fp(cfg: dict[str, Any]) -> str:
    """A stable fingerprint for the active Influx connection + query-relevant settings.

    Must not include secrets.
    """

    try:
        influx_v = int(cfg.get("influx_version", 2) or 2)
    except Exception:
        influx_v = 2
    base = {
        "influx_version": influx_v,
        "scheme": str(cfg.get("scheme") or ""),
        "host": str(cfg.get("host") or ""),
        "port": int(cfg.get("port") or 0),
        "org": str(cfg.get("org") or "") if influx_v == 2 else "",
        "bucket": str(cfg.get("bucket") or "") if influx_v == 2 else "",
        "database": str(cfg.get("database") or "") if influx_v != 2 else "",
        "ui_query_max_points": int(cfg.get("ui_query_max_points", 5000) or 5000),
        "ui_query_manual_max_points": int(cfg.get("ui_query_manual_max_points", 200000) or 200000),
    }
    raw = json.dumps(base, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _dash_cache_key(
    cfg: dict[str, Any],
    body: dict[str, Any],
    measurement: str,
    field: str,
    range_key: str,
    entity_id: str | None,
    friendly_name: str | None,
    unit: str,
    detail_mode: str,
    manual_density_pct: int,
    start_dt: datetime | None,
    stop_dt: datetime | None,
) -> dict[str, Any]:
    # Keep the key stable for relative ranges (e.g. 24h, 7d) so it can be refreshed in-place.
    start_iso = _dt_to_rfc3339_utc(start_dt) if (start_dt and stop_dt) else None
    stop_iso = _dt_to_rfc3339_utc(stop_dt) if (start_dt and stop_dt) else None
    return {
        "v": 1,
        "kind": "dashboard_query",
        "cfg_fp": _dash_cache_cfg_fp(cfg),
        "measurement": str(measurement or ""),
        "field": str(field or ""),
        "entity_id": str(entity_id) if entity_id else None,
        "friendly_name": str(friendly_name) if friendly_name else None,
        "range": str(range_key or ""),
        "start": start_iso,
        "stop": stop_iso,
        "detail_mode": str(detail_mode or "dynamic"),
        "manual_density_pct": int(manual_density_pct or 100),
        "unit": str(unit or ""),
        # Include a few knobs that influence the response shape.
        "ui_query_max_points": int(cfg.get("ui_query_max_points", 5000) or 5000),
        "ui_query_manual_max_points": int(cfg.get("ui_query_manual_max_points", 200000) or 200000),
        # Keep original payload markers for reproducibility (best-effort)
        "payload_start": body.get("start") or body.get("start_time"),
        "payload_stop": body.get("stop") or body.get("end") or body.get("stop_time"),
    }


def _dash_cache_id(key: dict[str, Any]) -> str:
    raw = json.dumps(key, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _analysis_cache_meta_path(cache_id: str) -> Path:
    return ANALYSIS_CACHE_DIR / f"{cache_id}.meta.json"


def _analysis_cache_data_path(cache_id: str) -> Path:
    return ANALYSIS_CACHE_DIR / f"{cache_id}.data.json.gz"


def _analysis_cache_cfg_fp(cfg: dict[str, Any]) -> str:
    return _dash_cache_cfg_fp(cfg)


def _analysis_cache_series_key(measurement: str, field: str, entity_id: str | None, friendly_name: str | None) -> str:
    return "|".join([
        str(measurement or "").strip(),
        str(field or "").strip(),
        str(entity_id or "").strip(),
        str(friendly_name or "").strip(),
    ])


def _analysis_cache_key(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    start_iso: str,
    stop_iso: str,
) -> dict[str, Any]:
    return {
        "v": 1,
        "kind": "analysis_cache_segment",
        "cfg_fp": _analysis_cache_cfg_fp(cfg),
        "measurement": str(measurement or "").strip(),
        "field": str(field or "").strip(),
        "entity_id": str(entity_id or "").strip() or None,
        "friendly_name": str(friendly_name or "").strip() or None,
        "start": str(start_iso or "").strip(),
        "stop": str(stop_iso or "").strip(),
        "search_types": ["bounds", "counter", "decrease", "fault_phase", "null", "zero"],
    }


def _analysis_cache_id(key: dict[str, Any]) -> str:
    raw = json.dumps(key, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _analysis_cache_checkpoint_interval_seconds(cfg: dict[str, Any] | None = None) -> int:
    try:
        val = int((cfg or {}).get("analysis_cache_checkpoint_seconds") or ANALYSIS_CACHE_CHECKPOINT_SECONDS)
    except Exception:
        val = ANALYSIS_CACHE_CHECKPOINT_SECONDS
    return max(300, val)


def _analysis_cache_state_snapshot(
    last_time: str | None,
    last_value: Any,
    counter_base_value: Any,
    scan_state: dict[str, Any] | None,
) -> dict[str, Any]:
    out = {
        "last_time": str(last_time or "") or None,
        "last_value": last_value,
        "counter_base_value": counter_base_value,
        "scan_state": dict(scan_state or {}) if isinstance(scan_state, dict) else None,
    }
    return out


def _analysis_cache_state_equal(left: dict[str, Any] | None, right: dict[str, Any] | None) -> bool:
    l = left if isinstance(left, dict) else {}
    r = right if isinstance(right, dict) else {}
    try:
        return json.dumps(l, sort_keys=True, ensure_ascii=True, default=str) == json.dumps(r, sort_keys=True, ensure_ascii=True, default=str)
    except Exception:
        return False


def _analysis_cache_payload_checkpoints(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cps = payload.get("checkpoints") if isinstance(payload.get("checkpoints"), list) else []
    out: list[dict[str, Any]] = []
    for cp in cps:
        if not isinstance(cp, dict):
            continue
        at = str(cp.get("at") or "").strip()
        if not at:
            continue
        item = dict(cp)
        item["at"] = at
        out.append(item)
    out.sort(key=lambda x: str(x.get("at") or ""))
    return out


def _analysis_cache_segment_changes(meta: dict[str, Any], limit: int = 200) -> list[dict[str, Any]]:
    start_dt, stop_dt = _analysis_cache_meta_span(meta)
    if not start_dt or not stop_dt:
        return []
    updated_at = _parse_iso_datetime(str(meta.get("updated_at") or "")) or datetime.fromtimestamp(0, tz=timezone.utc)
    return _history_changes_for_window(
        str(meta.get("measurement") or ""),
        str(meta.get("field") or ""),
        str(meta.get("entity_id") or "") or None,
        str(meta.get("friendly_name") or "") or None,
        start_dt,
        stop_dt,
        updated_at,
        limit=limit,
    )


def _analysis_cache_load_meta(cache_id: str) -> dict[str, Any] | None:
    try:
        p = _analysis_cache_meta_path(cache_id)
        if not p.exists():
            return None
        with ANALYSIS_CACHE_LOCK:
            j = json.loads(p.read_text(encoding="utf-8"))
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def _analysis_cache_write_meta(meta: dict[str, Any]) -> None:
    try:
        ANALYSIS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_id = str(meta.get("id") or "").strip()
        if not cache_id:
            return
        p = _analysis_cache_meta_path(cache_id)
        raw = json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=True)
        with ANALYSIS_CACHE_LOCK:
            p.write_text(raw, encoding="utf-8")
    except Exception:
        return


def _analysis_cache_load_payload(cache_id: str) -> dict[str, Any] | None:
    try:
        p = _analysis_cache_data_path(cache_id)
        if not p.exists():
            return None
        with ANALYSIS_CACHE_LOCK:
            with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
                j = json.loads(f.read() or "{}")
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def _analysis_cache_write_payload(cache_id: str, payload: dict[str, Any]) -> int:
    try:
        ANALYSIS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        p = _analysis_cache_data_path(cache_id)
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        with ANALYSIS_CACHE_LOCK:
            with gzip.open(p, "wt", encoding="utf-8") as f:
                f.write(raw)
        try:
            return int(p.stat().st_size)
        except Exception:
            return 0
    except Exception:
        return 0


def _analysis_cache_list_meta() -> list[dict[str, Any]]:
    try:
        if not ANALYSIS_CACHE_DIR.exists():
            LOG.info("analysis_cache_list_meta files_found=0 meta_loaded=0 dir_exists=False")
            return []
        file_count = len(list(ANALYSIS_CACHE_DIR.glob("*.meta.json")))
        out: list[dict[str, Any]] = []
        for p in sorted(ANALYSIS_CACHE_DIR.glob("*.meta.json")):
            try:
                j = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(j, dict):
                    out.append(j)
            except Exception:
                continue
        LOG.info("analysis_cache_list_meta files_found=%d meta_loaded=%d", file_count, len(out))
        return out
    except Exception:
        return []


def _analysis_cache_delete_id(cache_id: str) -> None:
    try:
        _analysis_cache_meta_path(cache_id).unlink(missing_ok=True)
    except Exception:
        pass
    try:
        _analysis_cache_data_path(cache_id).unlink(missing_ok=True)
    except Exception:
        pass


def _analysis_cache_store_segment(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    start_iso: str,
    stop_iso: str,
    rows: list[dict[str, Any]],
    scanned: int,
    *,
    checkpoints: list[dict[str, Any]] | None = None,
    final_state: dict[str, Any] | None = None,
    windows_meta: dict[str, Any] | None = None,
    patch_status: str | None = None,
    patch_error: str | None = None,
    patch_info: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    try:
        key = _analysis_cache_key(cfg, measurement, field, entity_id, friendly_name, start_iso, stop_iso)
        cache_id = _analysis_cache_id(key)
        LOG.info(
            "analysis_cache_store_segment start cache_id=%s series_key=%s start=%s stop=%s rows=%d scanned=%d",
            cache_id,
            _analysis_cache_series_key(measurement, field, entity_id, friendly_name),
            start_iso,
            stop_iso,
            len(rows),
            scanned,
        )
        now = _utc_now_iso_ms()
        payload = {
            "ok": True,
            "rows": rows,
            "scanned": int(scanned or 0),
            "checkpoints": checkpoints if isinstance(checkpoints, list) else [],
            "final_state": final_state if isinstance(final_state, dict) else {},
            "meta": {
                "covered_start": start_iso,
                "covered_stop": stop_iso,
                "outlier_count": len(rows),
                "checkpoint_count": len(checkpoints if isinstance(checkpoints, list) else []),
            },
        }
        if isinstance(windows_meta, dict) and windows_meta:
            try:
                payload["meta"]["windows_n_before"] = int(windows_meta.get("n_before") or 0) or None
            except Exception:
                payload["meta"]["windows_n_before"] = None
            try:
                payload["meta"]["windows_n_after"] = int(windows_meta.get("n_after") or 0) or None
            except Exception:
                payload["meta"]["windows_n_after"] = None
            try:
                payload["meta"]["windows_algo_v"] = int(windows_meta.get("algo_v") or 0) or None
            except Exception:
                payload["meta"]["windows_algo_v"] = None
            payload["meta"]["windows_computed_at"] = str(windows_meta.get("computed_at") or "").strip() or None
        bytes_written = _analysis_cache_write_payload(cache_id, payload)
        if bytes_written <= 0:
            LOG.error(
                "analysis_cache_store_segment payload write failed measurement=%s field=%s cache_id=%s",
                measurement,
                field,
                cache_id,
            )
            return None
        LOG.info(
            "analysis_cache_store_segment payload_written cache_id=%s bytes=%d data_path=%s",
            cache_id,
            bytes_written,
            str(_analysis_cache_data_path(cache_id)),
        )
        prev = _analysis_cache_load_meta(cache_id) or {}
        patch_meta = dict(patch_info or {}) if isinstance(patch_info, dict) else {}
        meta = {
            "v": 1,
            "id": cache_id,
            "key": key,
            "series_key": _analysis_cache_series_key(measurement, field, entity_id, friendly_name),
            "measurement": str(measurement or "").strip(),
            "field": str(field or "").strip(),
            "entity_id": str(entity_id or "").strip() or None,
            "friendly_name": str(friendly_name or "").strip() or None,
            "covered_start": start_iso,
            "covered_stop": stop_iso,
            "updated_at": now,
            "created_at": str(prev.get("created_at") or now),
            "last_used_at": now,
            "bytes": bytes_written,
            "outlier_count": len(rows),
            "scanned": int(scanned or 0),
            "dirty": False,
            "dirty_reason": None,
            "dirty_at": None,
            "patch_status": str(patch_status or "ok"),
            "patch_error": str(patch_error or "") or None,
            "last_patch_at": now if patch_status else None,
            "last_patch_mode": str(patch_meta.get("mode") or ("initial_build" if not patch_status else str(patch_status or "ok"))),
            "last_patch_start": patch_meta.get("start_iso") or start_iso,
            "last_patch_stop": patch_meta.get("stop_iso") or stop_iso,
            "last_patch_checkpoint_at": patch_meta.get("checkpoint_at"),
            "last_patch_context_before": patch_meta.get("context_before_time"),
            "last_patch_context_after": patch_meta.get("context_after_time"),
            "last_patch_change_start": patch_meta.get("change_start"),
            "last_patch_change_stop": patch_meta.get("change_stop"),
            "checkpoint_count": len(checkpoints if isinstance(checkpoints, list) else []),
            "search_types": ["bounds", "counter", "decrease", "fault_phase", "null", "zero"],
        }
        _analysis_cache_write_meta(meta)
        LOG.info(
            "analysis_cache_store_segment meta_written cache_id=%s meta_path=%s updated_at=%s outlier_count=%d",
            cache_id,
            str(_analysis_cache_meta_path(cache_id)),
            now,
            len(rows),
        )
        meta_path = _analysis_cache_meta_path(cache_id)
        data_path = _analysis_cache_data_path(cache_id)
        if not meta_path.exists() or not data_path.exists():
            LOG.error(
                "analysis_cache_store_segment files missing after write measurement=%s field=%s cache_id=%s meta_exists=%s data_exists=%s",
                measurement,
                field,
                cache_id,
                meta_path.exists(),
                data_path.exists(),
            )
            return None
        stored_meta = _analysis_cache_load_meta(cache_id)
        stored_payload = _analysis_cache_load_payload(cache_id)
        if not stored_meta or not stored_payload or not bool(stored_payload.get("ok")):
            LOG.error(
                "analysis_cache_store_segment verification failed measurement=%s field=%s cache_id=%s meta_ok=%s payload_ok=%s",
                measurement,
                field,
                cache_id,
                bool(stored_meta),
                bool(stored_payload and bool(stored_payload.get("ok"))),
            )
            return None
        LOG.info(
            "analysis_cache_store_segment verified cache_id=%s meta_ok=%s payload_ok=%s series_key=%s",
            cache_id,
            bool(stored_meta),
            bool(stored_payload and bool(stored_payload.get("ok"))),
            str(meta.get("series_key") or ""),
        )
        return stored_meta
    except Exception as e:
        LOG.error(
            "analysis_cache_store_segment exception measurement=%s field=%s start=%s stop=%s error=%s",
            measurement,
            field,
            start_iso,
            stop_iso,
            e,
            exc_info=True,
        )
        return None


def _dash_cache_load_meta(cache_id: str) -> dict[str, Any] | None:
    try:
        p = _dash_cache_meta_path(cache_id)
        if not p.exists():
            return None
        with DASH_CACHE_LOCK:
            j = json.loads(p.read_text(encoding="utf-8"))
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def _dash_cache_write_meta(meta: dict[str, Any]) -> None:
    try:
        DASH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_id = str(meta.get("id") or "").strip()
        if not cache_id:
            return
        p = _dash_cache_meta_path(cache_id)
        raw = json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=True)
        with DASH_CACHE_LOCK:
            p.write_text(raw, encoding="utf-8")
    except Exception:
        return


def _dash_cache_load_payload(cache_id: str) -> dict[str, Any] | None:
    try:
        p = _dash_cache_data_path(cache_id)
        if not p.exists():
            return None
        with DASH_CACHE_LOCK:
            with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
                j = json.loads(f.read() or "{}")
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def _dash_cache_write_payload(cache_id: str, payload: dict[str, Any]) -> int:
    try:
        DASH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        p = _dash_cache_data_path(cache_id)
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        with DASH_CACHE_LOCK:
            with gzip.open(p, "wt", encoding="utf-8") as f:
                f.write(raw)
        try:
            return int(p.stat().st_size)
        except Exception:
            return 0
    except Exception:
        return 0


def _dash_cache_list_meta() -> list[dict[str, Any]]:
    try:
        if not DASH_CACHE_DIR.exists():
            return []
        out: list[dict[str, Any]] = []
        for p in sorted(DASH_CACHE_DIR.glob("*.meta.json")):
            try:
                j = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(j, dict):
                    out.append(j)
            except Exception:
                continue
        return out
    except Exception:
        return []


def _dash_cache_ts(meta: dict[str, Any], key: str) -> float:
    try:
        v = str(meta.get(key) or "").strip()
        if not v:
            return 0.0
        return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _dash_cache_enforce_limits(cfg: dict[str, Any]) -> None:
    """Best-effort eviction by LRU (last_used_at) then updated_at."""

    try:
        max_items = int(cfg.get("dash_cache_max_items", 40) or 40)
    except Exception:
        max_items = 40
    if max_items < 0:
        max_items = 0
    try:
        max_mb = int(cfg.get("dash_cache_max_mb", 50) or 50)
    except Exception:
        max_mb = 50
    if max_mb < 0:
        max_mb = 0
    max_bytes = max_mb * 1024 * 1024

    items = _dash_cache_list_meta()
    if not items:
        return

    # Compute total bytes (meta.bytes is best-effort).
    total = 0
    for m in items:
        try:
            total += int(m.get("bytes") or 0)
        except Exception:
            continue

    def sort_key(m: dict[str, Any]) -> tuple[float, float]:
        # older first
        return (_dash_cache_ts(m, "last_used_at") or _dash_cache_ts(m, "updated_at"), _dash_cache_ts(m, "updated_at"))

    items.sort(key=sort_key)

    def delete_one(cache_id: str) -> None:
        try:
            _dash_cache_meta_path(cache_id).unlink(missing_ok=True)
        except Exception:
            pass
        try:
            _dash_cache_data_path(cache_id).unlink(missing_ok=True)
        except Exception:
            pass

    # Enforce item count
    if max_items == 0:
        for m in items:
            cid = str(m.get("id") or "").strip()
            if cid:
                delete_one(cid)
        return

    while len(items) > max_items:
        m = items.pop(0)
        cid = str(m.get("id") or "").strip()
        if cid:
            delete_one(cid)

    # Enforce bytes
    if max_bytes <= 0:
        return
    if total <= max_bytes:
        return
    for m in list(items):
        if total <= max_bytes:
            break
        cid = str(m.get("id") or "").strip()
        if not cid:
            continue
        try:
            total -= int(m.get("bytes") or 0)
        except Exception:
            pass
        delete_one(cid)
    return


def _dash_cache_mark_dirty_series(
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    reason: str,
) -> int:
    """Mark matching cache entries as dirty (best-effort). Returns number marked."""

    want_m = str(measurement or "").strip()
    want_f = str(field or "").strip()
    want_e = str(entity_id or "").strip() if entity_id else ""
    want_n = str(friendly_name or "").strip() if friendly_name else ""
    if not want_m or not want_f:
        return 0

    marked = 0
    for meta in _dash_cache_list_meta():
        try:
            key = meta.get("key") if isinstance(meta.get("key"), dict) else {}
            if str(key.get("measurement") or "") != want_m:
                continue
            if str(key.get("field") or "") != want_f:
                continue
            if want_e and str(key.get("entity_id") or "") != want_e:
                continue
            if want_n and str(key.get("friendly_name") or "") != want_n:
                continue
            if bool(meta.get("dirty")):
                continue
            meta["dirty"] = True
            meta["dirty_reason"] = str(reason or "").strip() or "changed"
            meta["dirty_at"] = _utc_now_iso_ms()
            _meta_add_event(meta, "dirty", str(meta.get("dirty_reason") or ""), at=str(meta.get("dirty_at") or ""))
            _dash_cache_write_meta(meta)
            marked += 1
        except Exception:
            continue
    return marked


def _dash_cache_mark_dirty_id(cache_id: str, reason: str) -> bool:
    try:
        cid = str(cache_id or "").strip()
        if not cid:
            return False
        meta = _dash_cache_load_meta(cid)
        if not meta:
            return False
        meta["dirty"] = True
        meta["dirty_reason"] = str(reason or "").strip() or "changed"
        meta["dirty_at"] = _utc_now_iso_ms()
        _meta_add_event(meta, "dirty", str(meta.get("dirty_reason") or ""), at=str(meta.get("dirty_at") or ""))
        _dash_cache_write_meta(meta)
        return True
    except Exception:
        return False


def _dash_cache_store(
    cache_id: str,
    key: dict[str, Any],
    payload: dict[str, Any],
    trigger_page: str | None = None,
) -> dict[str, Any] | None:
    """Persist payload and write/update meta. Returns meta."""

    try:
        now = _utc_now_iso_ms()
        rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
        row_count = len(rows)
        first_time = None
        last_time = None
        try:
            if row_count:
                first_time = str(rows[0].get("time") or "") if isinstance(rows[0], dict) else None
                last_time = str(rows[-1].get("time") or "") if isinstance(rows[-1], dict) else None
        except Exception:
            first_time = None
            last_time = None

        bytes_written = _dash_cache_write_payload(cache_id, payload)
        meta = _dash_cache_load_meta(cache_id) or {}
        created = str(meta.get("created_at") or "").strip() or now
        created_trigger = str(meta.get("trigger_page") or "").strip() or str(trigger_page or "").strip() or "dashboard"

        # Keep a stable small meta file for list views.
        covered_start = None
        covered_stop = None
        outlier_count = None
        query_ms_original = None
        source_cache_ids = []
        cache_strategy = None
        try:
            m = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
            covered_start = str(m.get("covered_start") or "").strip() or first_time
            covered_stop = str(m.get("covered_stop") or "").strip() or last_time
            js = m.get("jump_spans") if isinstance(m.get("jump_spans"), list) else []
            outlier_count = int(m.get("outlier_count") or len(js) or 0)
            if m.get("query_ms_original") is not None:
                query_ms_original = int(m.get("query_ms_original") or 0)
            src_ids = m.get("source_cache_ids") if isinstance(m.get("source_cache_ids"), list) else []
            source_cache_ids = [str(x) for x in src_ids if str(x).strip()][:8]
            cache_strategy = str(m.get("cache_strategy") or "").strip() or None
        except Exception:
            covered_start = first_time
            covered_stop = last_time

        out = {
            "v": 1,
            "id": cache_id,
            "key": key,
            "created_at": created,
            "trigger_page": created_trigger,
            "updated_at": now,
            "last_used_at": now,
            "row_count": row_count,
            "first_time": first_time,
            "last_time": last_time,
            "covered_start": covered_start,
            "covered_stop": covered_stop,
            "total_points": None,
            "outlier_count": outlier_count,
            "query_ms_original": query_ms_original,
            "cache_strategy": cache_strategy,
            "source_cache_ids": source_cache_ids,
            "bytes": bytes_written,
            "dirty": False,
            "dirty_reason": None,
            "dirty_at": None,
            "mismatch": False,
            "last_check_at": meta.get("last_check_at"),
            "last_check_ok": meta.get("last_check_ok"),
            "last_check_note": meta.get("last_check_note"),
            "last_update_at": now,
            "last_update_note": meta.get("last_update_note"),
            "events": meta.get("events") if isinstance(meta.get("events"), list) else [],
        }
        try:
            m = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
            tp = m.get("total_points") if isinstance(m, dict) else None
            if isinstance(tp, (int, float)):
                out["total_points"] = int(tp)
        except Exception:
            pass

        try:
            _meta_add_event(out, "store", f"rows={row_count} trigger={created_trigger}", at=now)
        except Exception:
            pass

        _dash_cache_write_meta(out)
        try:
            _dash_cache_enforce_limits(load_cfg())
        except Exception:
            pass
        return out
    except Exception:
        return None


def _dash_cache_touch_used(cache_id: str) -> None:
    try:
        meta = _dash_cache_load_meta(cache_id)
        if not meta:
            return
        now = _utc_now_iso_ms()
        meta["last_used_at"] = now
        _meta_add_event(meta, "used", None, at=now)
        _dash_cache_write_meta(meta)
        try:
            cfg = load_cfg()
            _cache_usage_append(cfg, {
                "kind": "dash_cache_used",
                "page": str(meta.get("trigger_page") or "dashboard"),
                "cache_id": str(cache_id),
                "step": "touch_used",
                "rows": meta.get("row_count"),
                "bytes": meta.get("bytes"),
            })
        except Exception:
            pass
    except Exception:
        return


def _dash_cache_signature(key: dict[str, Any]) -> tuple[str, str, str, str, str, str, int, str]:
    return (
        str(key.get("cfg_fp") or "").strip(),
        str(key.get("measurement") or "").strip(),
        str(key.get("field") or "").strip(),
        str(key.get("entity_id") or "").strip(),
        str(key.get("friendly_name") or "").strip(),
        str(key.get("detail_mode") or "dynamic").strip().lower(),
        int(key.get("manual_density_pct") or 100),
        str(key.get("unit") or "").strip(),
    )


def _dash_cache_requested_range(range_key: str, start_dt: datetime | None, stop_dt: datetime | None) -> tuple[datetime, datetime]:
    if start_dt and stop_dt:
        return start_dt, stop_dt
    return parse_range_to_datetimes(range_key)


def _dash_cache_meta_span(meta: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    try:
        start_raw = str(meta.get("covered_start") or meta.get("first_time") or "").strip()
        stop_raw = str(meta.get("covered_stop") or meta.get("last_time") or "").strip()
        start_dt = _parse_iso_datetime(start_raw) if start_raw else None
        stop_dt = _parse_iso_datetime(stop_raw) if stop_raw else None
        if start_dt and stop_dt and stop_dt > start_dt:
            return start_dt, stop_dt
    except Exception:
        pass
    try:
        key = meta.get("key") if isinstance(meta.get("key"), dict) else {}
        _, _, range_key, _, _, _, _, _, start_dt, stop_dt = _dash_cache_key_to_params(key)
        if start_dt and stop_dt and stop_dt > start_dt:
            return start_dt, stop_dt
    except Exception:
        pass
    return None, None


def _dash_cache_row_in_window(row: dict[str, Any], start_dt: datetime, stop_dt: datetime) -> bool:
    try:
        ts = _parse_iso_datetime(str(row.get("time") or ""))
        return start_dt <= ts <= stop_dt
    except Exception:
        return False


def _dash_cache_filter_rows(rows: list[dict[str, Any]], start_dt: datetime, stop_dt: datetime) -> list[dict[str, Any]]:
    return [r for r in rows if isinstance(r, dict) and _dash_cache_row_in_window(r, start_dt, stop_dt)]


def _dash_cache_merge_rows(row_groups: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for rows in row_groups:
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            ts = str(row.get("time") or "").strip()
            if not ts:
                continue
            merged[ts] = row
    out = list(merged.values())
    out.sort(key=lambda r: str(r.get("time") or ""))
    return out


def _dash_cache_merge_spans(spans: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    valid = [(a, b) for a, b in spans if a and b and b > a]
    valid.sort(key=lambda x: x[0])
    merged: list[tuple[datetime, datetime]] = []
    for a, b in valid:
        if not merged:
            merged.append((a, b))
            continue
        la, lb = merged[-1]
        if a <= lb:
            merged[-1] = (la, max(lb, b))
        else:
            merged.append((a, b))
    return merged


def _dash_cache_gap_ranges(start_dt: datetime, stop_dt: datetime, covered: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    gaps: list[tuple[datetime, datetime]] = []
    cur = start_dt
    for a, b in _dash_cache_merge_spans(covered):
        if b <= start_dt or a >= stop_dt:
            continue
        aa = max(start_dt, a)
        bb = min(stop_dt, b)
        if aa > cur:
            gaps.append((cur, aa))
        if bb > cur:
            cur = bb
    if cur < stop_dt:
        gaps.append((cur, stop_dt))
    return [(a, b) for a, b in gaps if b > a]


def _dash_cache_series_key(measurement: str, field: str, entity_id: str | None, friendly_name: str | None, detail_mode: str) -> str:
    return "|".join([
        str(measurement or "").strip(),
        str(field or "").strip(),
        str(entity_id or "").strip(),
        str(friendly_name or "").strip(),
        str(detail_mode or "dynamic").strip().lower(),
    ])


def _history_changes_for_window(
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    start_dt: datetime,
    stop_dt: datetime,
    since_dt: datetime,
    limit: int = 50,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for it in reversed(_history_read_all()):
        if not isinstance(it, dict):
            continue
        if not _history_series_matches(it, measurement, field, entity_id, friendly_name):
            continue
        action = str(it.get("action") or "").strip().lower()
        if action not in ("overwrite", "delete"):
            continue
        try:
            changed_at = _parse_iso_datetime(str(it.get("at") or ""))
            value_at = _parse_iso_datetime(str(it.get("time") or ""))
        except Exception:
            continue
        if changed_at < since_dt:
            continue
        if value_at < start_dt or value_at > stop_dt:
            continue
        trigger = _history_trigger_meta(it)
        out.append({
            "id": str(it.get("id") or ""),
            "at": str(it.get("at") or ""),
            "time": str(it.get("time") or ""),
            "action": action,
            "old_value": it.get("old_value"),
            "new_value": it.get("new_value"),
            "reason": str(it.get("reason") or ""),
            **trigger,
        })
        if len(out) >= limit:
            break
    return out


def _dash_cache_reference_ms(series_key: str, desired_span_s: float, kind: str = "dash_db_query") -> int | None:
    vals: list[int] = []
    tol = max(60.0, desired_span_s * 0.25)
    for row in reversed(_cache_usage_tail(2000)):
        if not isinstance(row, dict):
            continue
        if str(row.get("kind") or "") != kind:
            continue
        if str(row.get("series_key") or "") != series_key:
            continue
        try:
            span_s = float(row.get("requested_span_s") or 0)
            dur_ms = int(row.get("dur_ms") or 0)
        except Exception:
            continue
        if dur_ms <= 0:
            continue
        if span_s > 0 and abs(span_s - desired_span_s) > tol:
            continue
        vals.append(dur_ms)
        if len(vals) >= 5:
            break
    if not vals:
        return None
    return int(sum(vals) / len(vals))


def _dash_cache_plan(
    cfg: dict[str, Any],
    body: dict[str, Any],
    measurement: str,
    field: str,
    range_key: str,
    entity_id: str | None,
    friendly_name: str | None,
    unit: str,
    detail_mode: str,
    manual_density_pct: int,
    start_dt: datetime | None,
    stop_dt: datetime | None,
    *,
    max_segments: int = 8,
) -> dict[str, Any]:
    req_start, req_stop = _dash_cache_requested_range(range_key, start_dt, stop_dt)
    key = _dash_cache_key(
        cfg,
        body,
        measurement,
        field,
        range_key,
        entity_id,
        friendly_name,
        unit,
        detail_mode,
        manual_density_pct,
        start_dt,
        stop_dt,
    )
    exact_cache_id = _dash_cache_id(key)
    signature = _dash_cache_signature(key)
    candidates: list[dict[str, Any]] = []
    for meta in _dash_cache_list_meta():
        try:
            key2 = meta.get("key") if isinstance(meta.get("key"), dict) else {}
            if _dash_cache_signature(key2) != signature:
                continue
            if bool(meta.get("dirty")) or bool(meta.get("mismatch")):
                continue
            cache_id = str(meta.get("id") or "").strip()
            if not cache_id:
                continue
            payload = _dash_cache_load_payload(cache_id)
            if not payload or not bool(payload.get("ok")):
                continue
            rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
            if not rows:
                continue
            cov_start, cov_stop = _dash_cache_meta_span(meta)
            if not cov_start or not cov_stop:
                continue
            use_start = max(req_start, cov_start)
            use_stop = min(req_stop, cov_stop)
            if use_stop <= use_start:
                continue
            filtered_rows = _dash_cache_filter_rows(rows, use_start, use_stop)
            if not filtered_rows:
                continue
            candidates.append({
                "cache_id": cache_id,
                "meta": meta,
                "payload": payload,
                "covered_start": cov_start,
                "covered_stop": cov_stop,
                "use_start": use_start,
                "use_stop": use_stop,
                "filtered_rows": filtered_rows,
                "covered_seconds": (use_stop - use_start).total_seconds(),
            })
        except Exception:
            continue

    candidates.sort(key=lambda c: (float(c.get("covered_seconds") or 0.0), _dash_cache_ts(c.get("meta") or {}, "updated_at")), reverse=True)
    selected: list[dict[str, Any]] = []
    covered: list[tuple[datetime, datetime]] = []
    for cand in candidates:
        if len(selected) >= max_segments:
            break
        gaps_before = _dash_cache_gap_ranges(req_start, req_stop, covered)
        if not gaps_before:
            break
        adds = False
        for ga, gb in gaps_before:
            if min(gb, cand["use_stop"]) > max(ga, cand["use_start"]):
                adds = True
                break
        if not adds:
            continue
        selected.append(cand)
        covered.append((cand["use_start"], cand["use_stop"]))

    gaps = _dash_cache_gap_ranges(req_start, req_stop, covered)
    exact = False
    for seg in selected:
        if str(seg.get("cache_id") or "") == exact_cache_id and not gaps and len(selected) == 1:
            exact = True
            break

    earliest_created = None
    for seg in selected:
        try:
            created = _parse_iso_datetime(str((seg.get("meta") or {}).get("created_at") or ""))
        except Exception:
            created = None
        if created and (earliest_created is None or created < earliest_created):
            earliest_created = created
    changes = _history_changes_for_window(measurement, field, entity_id, friendly_name, req_start, req_stop, earliest_created, limit=50) if earliest_created else []

    desired_span_s = max(1.0, (req_stop - req_start).total_seconds())
    series_key = _dash_cache_series_key(measurement, field, entity_id, friendly_name, detail_mode)
    full_ref_ms = _dash_cache_reference_ms(series_key, desired_span_s, kind="dash_db_query")
    cache_ref_ms = _dash_cache_reference_ms(series_key, desired_span_s, kind="dash_cache_hit")
    if cache_ref_ms is None:
        cache_ref_ms = _dash_cache_reference_ms(series_key, desired_span_s, kind="dash_cache_partial_hit")
    gap_fraction = sum((b - a).total_seconds() for a, b in gaps) / desired_span_s
    estimated_total_ms = None
    estimated_savings_ms = None
    if full_ref_ms is not None:
        base_cache_ms = int(cache_ref_ms or 25)
        estimated_total_ms = int((len(selected) * base_cache_ms) + (full_ref_ms * gap_fraction) + (len(selected) * 15))
        estimated_savings_ms = max(0, full_ref_ms - estimated_total_ms)

    cached_outlier_count = 0
    for seg in selected:
        try:
            m = seg.get("payload", {}).get("meta") if isinstance(seg.get("payload"), dict) else {}
            cached_outlier_count += int(m.get("outlier_count") or len(m.get("jump_spans") or []))
        except Exception:
            continue

    return {
        "request": {
            "start": _dt_to_rfc3339_utc(req_start),
            "stop": _dt_to_rfc3339_utc(req_stop),
            "range": range_key,
        },
        "exact_cache_id": exact_cache_id,
        "exact": exact,
        "has_cache": bool(selected),
        "segments": selected,
        "gaps": gaps,
        "series_key": series_key,
        "full_reference_ms": full_ref_ms,
        "estimated_total_ms": estimated_total_ms,
        "estimated_savings_ms": estimated_savings_ms,
        "changes": changes,
        "cached_outlier_count": cached_outlier_count,
    }


def _analysis_cache_meta_span(meta: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    try:
        start_raw = str(meta.get("covered_start") or "").strip()
        stop_raw = str(meta.get("covered_stop") or "").strip()
        start_dt = _parse_iso_datetime(start_raw) if start_raw else None
        stop_dt = _parse_iso_datetime(stop_raw) if stop_raw else None
        if start_dt and stop_dt and stop_dt > start_dt:
            return start_dt, stop_dt
    except Exception:
        pass
    return None, None


def _analysis_cache_payload_rows_in_window(payload: dict[str, Any], start_dt: datetime, stop_dt: datetime) -> list[dict[str, Any]]:
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    return [r for r in rows if isinstance(r, dict) and _dash_cache_row_in_window(r, start_dt, stop_dt)]


def _analysis_type_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "counter": 0,
        "decrease": 0,
        "bounds": 0,
        "fault_phase": 0,
        "null": 0,
        "zero": 0,
        "ignored": 0,
    }
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        for t in row.get("types") if isinstance(row.get("types"), list) else []:
            key = str(t or "").strip()
            if key in counts:
                counts[key] += 1
    return counts


def _analysis_outlier_times(rows: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        ts = str(row.get("time") or "").strip()
        if not ts or ts in seen:
            continue
        seen.add(ts)
        out.append(ts)
    out.sort()
    return out


def _analysis_outlier_details(rows: list[dict[str, Any]], limit: int = 500) -> list[dict[str, Any]]:
    """Return compact outlier details for timeline tooltip rendering."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        ts = str(row.get("time") or "").strip()
        if not ts or ts in seen:
            continue
        seen.add(ts)
        types_raw = row.get("types") if isinstance(row.get("types"), list) else []
        types_s = [str(t or "").strip() for t in types_raw if str(t or "").strip()]
        detail: dict[str, Any] = {"time": ts, "types": types_s}
        val = row.get("value")
        if val is not None:
            try:
                detail["value"] = float(val)
            except (TypeError, ValueError):
                detail["value"] = str(val)
        out.append(detail)
        if len(out) >= limit:
            break
    out.sort(key=lambda d: str(d.get("time") or ""))
    return out


def _analysis_cache_resolve_segment_reuse(
    cfg: dict[str, Any],
    meta: dict[str, Any],
    use_start: datetime,
    use_stop: datetime,
) -> dict[str, Any]:
    cache_id = str(meta.get("id") or "").strip()
    payload = _analysis_cache_load_payload(cache_id) or {}
    updated_at = _parse_iso_datetime(str(meta.get("updated_at") or "")) or datetime.fromtimestamp(0, tz=timezone.utc)
    changed = _history_changes_for_window(
        str(meta.get("measurement") or ""),
        str(meta.get("field") or ""),
        str(meta.get("entity_id") or "") or None,
        str(meta.get("friendly_name") or "") or None,
        use_start,
        use_stop,
        updated_at,
        limit=200,
    )
    patch_status = str(meta.get("patch_status") or "ok")
    explicitly_dirty = bool(meta.get("dirty")) or patch_status in ("patch_pending", "patch_failed", "patch_not_safe")
    repair_reason: str | None = None
    repair_error: str | None = None
    reused_after_repair = False
    if changed or explicitly_dirty:
        try:
            repair = _analysis_cache_patch_meta(cfg, meta)
        except Exception as e:
            repair = {"ok": False, "patched": False, "reason": "patch_failed", "error": str(e) or e.__class__.__name__}
        repair_reason = str(repair.get("reason") or "") or None
        repair_error = str(repair.get("error") or "") or None
        meta = _analysis_cache_load_meta(cache_id) or dict(meta)
        payload = _analysis_cache_load_payload(cache_id) or payload
        updated_at = _parse_iso_datetime(str(meta.get("updated_at") or "")) or datetime.fromtimestamp(0, tz=timezone.utc)
        changed = _history_changes_for_window(
            str(meta.get("measurement") or ""),
            str(meta.get("field") or ""),
            str(meta.get("entity_id") or "") or None,
            str(meta.get("friendly_name") or "") or None,
            use_start,
            use_stop,
            updated_at,
            limit=200,
        )
        patch_status = str(meta.get("patch_status") or "ok")
        explicitly_dirty = bool(meta.get("dirty")) or patch_status in ("patch_pending", "patch_failed", "patch_not_safe")
        reused_after_repair = bool(repair_reason) and not changed and not explicitly_dirty and bool(payload.get("ok"))
    dirty_reason = str(meta.get("dirty_reason") or ("history_change" if changed else "")).strip() or None
    return {
        "cache_id": cache_id,
        "meta": meta,
        "payload": payload,
        "changes": changed,
        "patch_status": patch_status,
        "dirty_reason": dirty_reason,
        "usable": bool(payload.get("ok")) and not changed and not explicitly_dirty,
        "reused_after_repair": reused_after_repair,
        "repair_reason": repair_reason,
        "repair_error": repair_error,
    }


def _analysis_cache_plan(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    start_dt: datetime,
    stop_dt: datetime,
    *,
    max_segments: int = 64,
) -> dict[str, Any]:
    req_start = start_dt
    req_stop = stop_dt
    series_key = _analysis_cache_series_key(measurement, field, entity_id, friendly_name)
    candidates: list[dict[str, Any]] = []
    dirty_ranges: list[tuple[datetime, datetime]] = []
    dirty_changes: list[dict[str, Any]] = []
    repaired_segments: list[dict[str, Any]] = []
    blocked_segments: list[dict[str, Any]] = []
    for meta in _analysis_cache_list_meta():
        try:
            key = meta.get("key") if isinstance(meta.get("key"), dict) else {}
            if str(meta.get("series_key") or "") != series_key:
                continue
            cache_id = str(meta.get("id") or "").strip()
            if not cache_id:
                continue
            payload = _analysis_cache_load_payload(cache_id)
            if not payload or not bool(payload.get("ok")):
                continue
            cov_start, cov_stop = _analysis_cache_meta_span(meta)
            if not cov_start or not cov_stop:
                continue
            use_start = max(req_start, cov_start)
            use_stop = min(req_stop, cov_stop)
            if use_stop <= use_start:
                continue
            resolved = _analysis_cache_resolve_segment_reuse(cfg, meta, use_start, use_stop)
            meta = resolved.get("meta") if isinstance(resolved.get("meta"), dict) else meta
            payload = resolved.get("payload") if isinstance(resolved.get("payload"), dict) else payload
            changed = resolved.get("changes") if isinstance(resolved.get("changes"), list) else []
            if bool(resolved.get("reused_after_repair")):
                repaired_segments.append({
                    "cache_id": cache_id,
                    "start": _dt_to_rfc3339_utc(use_start),
                    "stop": _dt_to_rfc3339_utc(use_stop),
                    "repair_reason": str(resolved.get("repair_reason") or "patched"),
                })
            if not bool(resolved.get("usable")):
                dirty_ranges.append((use_start, use_stop))
                for ch in changed:
                    item = dict(ch)
                    item["cache_id"] = cache_id
                    dirty_changes.append(item)
                blocked_segments.append({
                    "cache_id": cache_id,
                    "start": _dt_to_rfc3339_utc(use_start),
                    "stop": _dt_to_rfc3339_utc(use_stop),
                    "patch_status": str(resolved.get("patch_status") or "ok"),
                    "dirty_reason": str(resolved.get("dirty_reason") or "history_change"),
                    "change_count": len(changed),
                    "repair_reason": resolved.get("repair_reason"),
                    "repair_error": resolved.get("repair_error"),
                })
                continue
            filtered_rows = _analysis_cache_payload_rows_in_window(payload, use_start, use_stop)
            candidates.append({
                "cache_id": cache_id,
                "meta": meta,
                "payload": payload,
                "use_start": use_start,
                "use_stop": use_stop,
                "covered_seconds": (use_stop - use_start).total_seconds(),
                "filtered_rows": filtered_rows,
            })
        except Exception:
            continue
    candidates.sort(key=lambda c: (float(c.get("covered_seconds") or 0.0), _dash_cache_ts(c.get("meta") or {}, "updated_at")), reverse=True)
    selected: list[dict[str, Any]] = []
    covered: list[tuple[datetime, datetime]] = []
    for cand in candidates:
        if len(selected) >= max_segments:
            break
        gaps_before = _dash_cache_gap_ranges(req_start, req_stop, covered + dirty_ranges)
        if not gaps_before:
            break
        adds = False
        for ga, gb in gaps_before:
            if min(gb, cand["use_stop"]) > max(ga, cand["use_start"]):
                adds = True
                break
        if not adds:
            continue
        selected.append(cand)
        covered.append((cand["use_start"], cand["use_stop"]))
    gaps = _dash_cache_gap_ranges(req_start, req_stop, covered + dirty_ranges)
    cached_outlier_count = 0
    for seg in selected:
        try:
            cached_outlier_count += int((seg.get("meta") or {}).get("outlier_count") or 0)
        except Exception:
            continue
    LOG.info(
        "analysis_cache_plan series_key=%s selected=%d gaps=%d dirty_ranges=%d dirty_changes=%d",
        series_key,
        len(selected),
        len(gaps),
        len(dirty_ranges),
        len(dirty_changes),
    )
    LOG.info(
        "analysis_cache_plan selected_ids=%s dirty_cache_ids=%s",
        [str(s.get("cache_id") or "") for s in selected],
        list({str(ch.get("cache_id") or "") for ch in dirty_changes if ch.get("cache_id")}),
    )
    return {
        "request": {
            "start": _dt_to_rfc3339_utc(req_start),
            "stop": _dt_to_rfc3339_utc(req_stop),
        },
        "has_cache": bool(selected),
        "segments": selected,
        "gaps": gaps,
        "dirty_ranges": dirty_ranges,
        "changes": dirty_changes,
        "repaired_segments": repaired_segments,
        "blocked_segments": blocked_segments,
        "cached_outlier_count": cached_outlier_count,
        "series_key": series_key,
    }


def _analysis_cache_group_list(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for meta in _analysis_cache_list_meta():
        try:
            series_key = str(meta.get("series_key") or "").strip()
            if not series_key:
                continue
            group = groups.get(series_key)
            if not group:
                group = {
                    "series_key": series_key,
                    "measurement": meta.get("measurement"),
                    "field": meta.get("field"),
                    "entity_id": meta.get("entity_id"),
                    "friendly_name": meta.get("friendly_name"),
                    "segments": [],
                    "bytes": 0,
                    "outlier_count": 0,
                }
                groups[series_key] = group
            start_dt, stop_dt = _analysis_cache_meta_span(meta)
            if not start_dt or not stop_dt:
                continue
            changed = _history_changes_for_window(
                str(meta.get("measurement") or ""),
                str(meta.get("field") or ""),
                str(meta.get("entity_id") or "") or None,
                str(meta.get("friendly_name") or "") or None,
                start_dt,
                stop_dt,
                _parse_iso_datetime(str(meta.get("updated_at") or "")) or datetime.fromtimestamp(0, tz=timezone.utc),
                limit=50,
            )
            group["segments"].append({
                "cache_id": str(meta.get("id") or ""),
                "start": str(meta.get("covered_start") or ""),
                "stop": str(meta.get("covered_stop") or ""),
                "updated_at": meta.get("updated_at"),
                "outlier_count": int(meta.get("outlier_count") or 0),
                "bytes": int(meta.get("bytes") or 0),
                "dirty": bool(changed) or bool(meta.get("dirty")),
                "dirty_reason": meta.get("dirty_reason"),
                "dirty_at": meta.get("dirty_at"),
                "patch_status": str(meta.get("patch_status") or "ok"),
                "patch_error": meta.get("patch_error"),
                "checkpoint_count": int(meta.get("checkpoint_count") or 0),
                "last_patch_mode": meta.get("last_patch_mode"),
                "last_patch_at": meta.get("last_patch_at"),
                "last_patch_start": meta.get("last_patch_start"),
                "last_patch_stop": meta.get("last_patch_stop"),
                "last_patch_checkpoint_at": meta.get("last_patch_checkpoint_at"),
                "last_patch_context_before": meta.get("last_patch_context_before"),
                "last_patch_context_after": meta.get("last_patch_context_after"),
                "changes": changed,
                "meta_path": f"analysis_cache/{str(meta.get('id') or '')}.meta.json",
                "data_path": f"analysis_cache/{str(meta.get('id') or '')}.data.json.gz",
            })
            group["bytes"] = int(group.get("bytes") or 0) + int(meta.get("bytes") or 0)
            group["outlier_count"] = int(group.get("outlier_count") or 0) + int(meta.get("outlier_count") or 0)
        except Exception:
            continue
    out = list(groups.values())
    for group in out:
        segs = group.get("segments") if isinstance(group.get("segments"), list) else []
        segs.sort(key=lambda s: str(s.get("start") or ""))
        group["segment_count"] = len(segs)
        group["dirty_segment_count"] = len([s for s in segs if bool(s.get("dirty"))])
        group["patch_pending_count"] = len([s for s in segs if str(s.get("patch_status") or "") == "patch_pending"])
        group["patch_failed_count"] = len([s for s in segs if str(s.get("patch_status") or "") in ("patch_failed", "patch_not_safe")])
        group["checkpoint_count"] = sum(int(s.get("checkpoint_count") or 0) for s in segs)
        group["covered_start"] = segs[0].get("start") if segs else None
        group["covered_stop"] = segs[-1].get("stop") if segs else None
        group["updated_at"] = max((str(s.get("updated_at") or "") for s in segs), default=None)
        group["paths"] = [str(s.get("data_path") or "") for s in segs if str(s.get("data_path") or "")]
    out.sort(key=lambda g: str(g.get("updated_at") or ""), reverse=True)
    LOG.info(
        "analysis_cache_group_list groups=%d series=%s",
        len(out),
        [str(g.get("series_key") or "") for g in out[:20]],
    )
    return out


def _analysis_cache_fetch_segment_result(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    start_iso: str,
    stop_iso: str,
    *,
    prev_time: str | None = None,
    prev_value: Any = None,
    counter_base_value: Any = None,
    scan_state: dict[str, Any] | None = None,
    return_checkpoints: bool = False,
) -> dict[str, Any]:
    body0 = {
        "measurement": str(measurement or ""),
        "field": str(field or ""),
        "entity_id": str(entity_id or ""),
        "friendly_name": str(friendly_name or ""),
        "start": str(start_iso or ""),
        "stop": str(stop_iso or ""),
        "search_types": ["bounds", "counter", "decrease", "fault_phase", "null", "zero"],
        "limit": int(cfg.get("ui_raw_outlier_search_limit", 5000) or 5000),
        "return_checkpoints": bool(return_checkpoints),
        "checkpoint_seconds": _analysis_cache_checkpoint_interval_seconds(cfg),
    }
    if prev_time:
        body0["prev_time"] = str(prev_time)
    if prev_value is not None:
        body0["prev_value"] = prev_value
    if counter_base_value is not None:
        body0["counter_base_value"] = counter_base_value
    if isinstance(scan_state, dict) and scan_state:
        body0["scan_state"] = scan_state
    with app.test_request_context("/api/outliers", method="POST", json=body0):
        resp = api_outliers()
    response = make_response(resp)
    if response.status_code >= 400:
        err_payload = response.get_json(silent=True) or {}
        err_text = err_payload.get("error") if isinstance(err_payload, dict) else str(err_payload)
        raise _ApiError(err_text or f"rebuild failed: {response.status_code}", 500)
    data = response.get_json(silent=True) or {}
    if not data.get("ok"):
        raise _ApiError(str(data.get("error") or "rebuild failed"), 500)
    return data


def _analysis_cache_fetch_neighbor_points(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    center_dt: datetime,
    start_dt: datetime,
    stop_dt: datetime,
    *,
    n_before: int = 2,
    n_after: int = 2,
) -> dict[str, list[dict[str, Any]]]:
    if int(cfg.get("influx_version", 2)) != 2:
        return {"older": [], "newer": []}
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return {"older": [], "newer": []}
    n_before = max(1, min(int(n_before or 2), 5000))
    n_after = max(1, min(int(n_after or 2), 5000))
    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    center = _dt_to_rfc3339_utc(center_dt)
    extra = flux_tag_filter(entity_id, friendly_name)
    q_older = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> filter(fn: (r) => r._time < time(v: "{center}"))
  |> keep(columns: ["_time", "_value"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {n_before})
'''
    q_newer = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> filter(fn: (r) => r._time > time(v: "{center}"))
  |> keep(columns: ["_time", "_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: {n_after})
'''
    older: list[dict[str, Any]] = []
    newer: list[dict[str, Any]] = []
    try:
        with v2_client(cfg) as client:
            qapi = client.query_api()
            for table in qapi.query(q_older, org=cfg["org"]) or []:
                for rec in getattr(table, "records", []) or []:
                    ts = rec.get_time()
                    if isinstance(ts, datetime):
                        older.append({"time": _dt_to_rfc3339_utc_ms(ts), "value": rec.get_value()})
            for table in qapi.query(q_newer, org=cfg["org"]) or []:
                for rec in getattr(table, "records", []) or []:
                    ts = rec.get_time()
                    if isinstance(ts, datetime):
                        newer.append({"time": _dt_to_rfc3339_utc_ms(ts), "value": rec.get_value()})
    except Exception as e:
        LOG.warning("analysis_cache_fetch_neighbor_points failed center=%s error=%s", center, e)
        return {"older": [], "newer": []}
    older.reverse()
    return {"older": older, "newer": newer}


def _analysis_cache_patch_window(
    cfg: dict[str, Any],
    meta: dict[str, Any],
    payload: dict[str, Any],
    changes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    cps = _analysis_cache_payload_checkpoints(payload)
    if not changes:
        return None
    times = []
    for ch in changes:
        try:
            times.append(_parse_iso_datetime(str(ch.get("time") or "")))
        except Exception:
            continue
    times = [t for t in times if isinstance(t, datetime)]
    if not times:
        return None
    first_dt = min(times)
    last_dt = max(times)
    start_dt = _parse_iso_datetime(str(meta.get("covered_start") or ""))
    stop_dt = _parse_iso_datetime(str(meta.get("covered_stop") or ""))
    if start_dt is None or stop_dt is None:
        return None
    # Prefer point-based context around the change window. This aligns with the UI settings
    # and scales better across different sampling rates.
    try:
        ctx_before = int(cfg.get("outlier_context_before_points", 10) or 10)
    except Exception:
        ctx_before = 10
    try:
        ctx_after = int(cfg.get("outlier_context_after_points", 10) or 10)
    except Exception:
        ctx_after = 10
    ctx_before = max(1, min(5000, ctx_before))
    ctx_after = max(1, min(5000, ctx_after))
    series = {
        "measurement": str(meta.get("measurement") or ""),
        "field": str(meta.get("field") or ""),
        "entity_id": str(meta.get("entity_id") or "") or None,
        "friendly_name": str(meta.get("friendly_name") or "") or None,
    }
    first_neighbors = _analysis_cache_fetch_neighbor_points(
        cfg,
        series["measurement"],
        series["field"],
        series["entity_id"],
        series["friendly_name"],
        first_dt,
        start_dt,
        stop_dt,
        n_before=max(2, ctx_before + 2),
        n_after=max(1, ctx_after),
    )
    last_neighbors = first_neighbors if last_dt == first_dt else _analysis_cache_fetch_neighbor_points(
        cfg,
        series["measurement"],
        series["field"],
        series["entity_id"],
        series["friendly_name"],
        last_dt,
        start_dt,
        stop_dt,
        n_before=max(1, ctx_before),
        n_after=max(1, ctx_after),
    )
    older_first = first_neighbors.get("older") if isinstance(first_neighbors.get("older"), list) else []
    newer_last = last_neighbors.get("newer") if isinstance(last_neighbors.get("newer"), list) else []

    # older_first is returned in ascending order (oldest -> newest)
    prev_neighbor = older_first[-1] if older_first else None
    # Context window start: N points before the change center (best-effort)
    # If we have fewer context points than requested, prefer the closest neighbor
    # to keep patch windows small and deterministic.
    ctx_start_point = older_first[-(ctx_before + 1)] if len(older_first) >= (ctx_before + 1) else (older_first[-1] if older_first else None)
    # Seed point: one point before ctx_start_point, best-effort (may be missing)
    if len(older_first) >= (ctx_before + 2):
        prev_seed_point = older_first[-(ctx_before + 2)]
    elif len(older_first) >= 2:
        prev_seed_point = older_first[-2]
    else:
        prev_seed_point = None
    # newer_last is ascending order (oldest -> newest), so the N-th after point is at index ctx_after-1
    ctx_after_point = newer_last[min(len(newer_last) - 1, max(0, ctx_after - 1))] if newer_last else None
    next_neighbor = newer_last[0] if newer_last else None

    ctx_start_dt = _parse_iso_datetime(str((ctx_start_point or {}).get("time") or "")) if isinstance(ctx_start_point, dict) else None
    ctx_after_dt = _parse_iso_datetime(str((ctx_after_point or {}).get("time") or "")) if isinstance(ctx_after_point, dict) else None
    fallback_start = max(start_dt, ctx_start_dt or first_dt)
    fallback_stop = min(stop_dt, ctx_after_dt or last_dt)
    prev_cp = None
    next_cp = None
    for cp in cps:
        try:
            cp_dt = _parse_iso_datetime(str(cp.get("at") or ""))
        except Exception:
            continue
        if cp_dt <= first_dt:
            prev_cp = cp
        if cp_dt >= last_dt and next_cp is None:
            next_cp = cp
            break
    prev_neighbor_dt = _parse_iso_datetime(str((prev_neighbor or {}).get("time") or "")) if isinstance(prev_neighbor, dict) else None
    next_neighbor_dt = _parse_iso_datetime(str((next_neighbor or {}).get("time") or "")) if isinstance(next_neighbor, dict) else None
    patch_start = _parse_iso_datetime(str(prev_cp.get("at") or "")) if isinstance(prev_cp, dict) else (ctx_start_dt or prev_neighbor_dt or fallback_start)
    patch_stop = _parse_iso_datetime(str(next_cp.get("at") or "")) if isinstance(next_cp, dict) else ((ctx_after_dt + timedelta(milliseconds=1)) if ctx_after_dt else ((next_neighbor_dt + timedelta(milliseconds=1)) if next_neighbor_dt else fallback_stop))
    mode = "checkpoint"
    if not isinstance(prev_cp, dict) and not isinstance(next_cp, dict):
        mode = "neighbor_context" if (prev_neighbor_dt or next_neighbor_dt) else "fallback_time"
    elif not isinstance(prev_cp, dict) or not isinstance(next_cp, dict):
        mode = "checkpoint_mixed_neighbor" if (prev_neighbor_dt or next_neighbor_dt) else "checkpoint_mixed_fallback"
    if patch_start is None or patch_stop is None or patch_stop <= patch_start:
        return None
    if (patch_stop - patch_start).total_seconds() > ANALYSIS_CACHE_PATCH_MAX_SPAN_SECONDS:
        patch_start = fallback_start
        patch_stop = fallback_stop
        mode = "fallback_points"
    if patch_stop <= patch_start:
        return None
    if (patch_stop - patch_start).total_seconds() > ANALYSIS_CACHE_PATCH_MAX_SPAN_SECONDS:
        return None
    prev_seed_time = prev_cp.get("last_time") if isinstance(prev_cp, dict) else ((prev_seed_point or {}).get("time") if isinstance(prev_seed_point, dict) else None)
    prev_seed_value = prev_cp.get("last_value") if isinstance(prev_cp, dict) else ((prev_seed_point or {}).get("value") if isinstance(prev_seed_point, dict) else None)
    return {
        "start_dt": patch_start,
        "stop_dt": patch_stop,
        "start_iso": _dt_to_rfc3339_utc_ms(patch_start),
        "stop_iso": _dt_to_rfc3339_utc_ms(patch_stop),
        "prev_time": prev_seed_time,
        "prev_value": prev_seed_value,
        "counter_base_value": prev_cp.get("counter_base_value") if isinstance(prev_cp, dict) else None,
        "scan_state": prev_cp.get("scan_state") if isinstance(prev_cp, dict) else None,
        "mode": mode,
        "checkpoint_at": prev_cp.get("at") if isinstance(prev_cp, dict) else None,
        "context_before_time": (ctx_start_point or {}).get("time") if isinstance(ctx_start_point, dict) else ((prev_neighbor or {}).get("time") if isinstance(prev_neighbor, dict) else None),
        "context_after_time": (ctx_after_point or {}).get("time") if isinstance(ctx_after_point, dict) else ((next_neighbor or {}).get("time") if isinstance(next_neighbor, dict) else None),
        "context_before_points": int(ctx_before),
        "context_after_points": int(ctx_after),
        "change_start": _dt_to_rfc3339_utc_ms(first_dt),
        "change_stop": _dt_to_rfc3339_utc_ms(last_dt),
    }


def _analysis_cache_merge_rows_with_patch(
    existing_rows: list[dict[str, Any]],
    patch_rows: list[dict[str, Any]],
    start_dt: datetime,
    stop_dt: datetime,
) -> list[dict[str, Any]]:
    kept = [r for r in existing_rows if isinstance(r, dict) and not _dash_cache_row_in_window(r, start_dt, stop_dt)]
    merged = kept + [r for r in patch_rows if isinstance(r, dict)]
    merged.sort(key=lambda r: str(r.get("time") or ""))
    return merged


def _analysis_cache_patch_meta(cfg: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    payload = _analysis_cache_load_payload(str(meta.get("id") or "")) or {}
    changes = _analysis_cache_segment_changes(meta, limit=500)
    if not changes:
        meta2 = dict(meta)
        meta2["dirty"] = False
        meta2["dirty_reason"] = None
        meta2["dirty_at"] = None
        meta2["patch_status"] = "ok"
        meta2["patch_error"] = None
        meta2["last_patch_at"] = _utc_now_iso_ms()
        _analysis_cache_write_meta(meta2)
        return {"ok": True, "cache_id": str(meta.get("id") or ""), "patched": False, "reason": "clean"}
    window = _analysis_cache_patch_window(cfg, meta, payload, changes)
    if not window:
        meta2 = dict(meta)
        meta2["dirty"] = True
        meta2["dirty_reason"] = "patch_window_too_large"
        meta2["dirty_at"] = _utc_now_iso_ms()
        meta2["patch_status"] = "patch_not_safe"
        meta2["patch_error"] = "patch window too large or checkpoint missing"
        meta2["last_patch_at"] = _utc_now_iso_ms()
        meta2["last_patch_mode"] = "patch_not_safe"
        _analysis_cache_write_meta(meta2)
        return {"ok": False, "cache_id": str(meta.get("id") or ""), "patched": False, "reason": "patch_not_safe"}
    data = _analysis_cache_fetch_segment_result(
        cfg,
        str(meta.get("measurement") or ""),
        str(meta.get("field") or ""),
        str(meta.get("entity_id") or "") or None,
        str(meta.get("friendly_name") or "") or None,
        str(window.get("start_iso") or ""),
        str(window.get("stop_iso") or ""),
        prev_time=str(window.get("prev_time") or "") or None,
        prev_value=window.get("prev_value"),
        counter_base_value=window.get("counter_base_value"),
        scan_state=window.get("scan_state") if isinstance(window.get("scan_state"), dict) else None,
        return_checkpoints=True,
    )
    merged_rows = _analysis_cache_merge_rows_with_patch(
        payload.get("rows") if isinstance(payload.get("rows"), list) else [],
        data.get("rows") if isinstance(data.get("rows"), list) else [],
        window["start_dt"],
        window["stop_dt"],
    )
    existing_cps = _analysis_cache_payload_checkpoints(payload)
    patch_start_iso = str(window.get("start_iso") or "")
    patch_stop_iso = str(window.get("stop_iso") or "")
    kept_cps = [cp for cp in existing_cps if not (patch_start_iso <= str(cp.get("at") or "") <= patch_stop_iso)]
    new_cps = [cp for cp in (data.get("checkpoints") if isinstance(data.get("checkpoints"), list) else []) if isinstance(cp, dict)]
    merged_cps = kept_cps + new_cps
    merged_cps.sort(key=lambda cp: str(cp.get("at") or ""))
    merged_meta = _analysis_cache_store_segment(
        cfg,
        str(meta.get("measurement") or ""),
        str(meta.get("field") or ""),
        str(meta.get("entity_id") or "") or None,
        str(meta.get("friendly_name") or "") or None,
        str(meta.get("covered_start") or ""),
        str(meta.get("covered_stop") or ""),
        merged_rows,
        int((payload.get("scanned") or 0)) + int(data.get("scanned") or 0),
        checkpoints=merged_cps,
        final_state=_analysis_cache_state_snapshot(
            data.get("last_time") or (payload.get("final_state") or {}).get("last_time"),
            data.get("last_value") if "last_value" in data else (payload.get("final_state") or {}).get("last_value"),
            data.get("counter_base_value") if "counter_base_value" in data else (payload.get("final_state") or {}).get("counter_base_value"),
            data.get("scan_state") if isinstance(data.get("scan_state"), dict) else (payload.get("final_state") if isinstance(payload.get("final_state"), dict) else {}).get("scan_state"),
        ),
        patch_status="ok",
        patch_info=window,
    )
    if not merged_meta:
        raise _ApiError("analysis cache patch store failed", 500)
    return {"ok": True, "cache_id": str(meta.get("id") or ""), "patched": True, "reason": "patched"}


def _analysis_cache_fetch_segment(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    start_iso: str,
    stop_iso: str,
) -> tuple[list[dict[str, Any]], int]:
    data = _analysis_cache_fetch_segment_result(cfg, measurement, field, entity_id, friendly_name, start_iso, stop_iso)
    return data.get("rows") if isinstance(data.get("rows"), list) else [], int(data.get("scanned") or 0)


def _analysis_cache_patch_job_public(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": job.get("id"),
        "state": job.get("state"),
        "message": job.get("message"),
        "started_at": job.get("started_at"),
        "updated_at": job.get("updated_at"),
        "finished_at": job.get("finished_at"),
        "elapsed": _job_elapsed_hms(job),
        "current": job.get("current") or "",
        "series_key": job.get("series_key") or "",
        "patched": int(job.get("patched") or 0),
        "skipped": int(job.get("skipped") or 0),
        "cancelled": bool(job.get("cancelled")),
        "error": job.get("error"),
        "ready": job.get("state") in ("done", "error", "cancelled"),
    }


def _analysis_cache_patch_job_thread(job_id: str, cfg: dict[str, Any], series_key: str) -> None:
    def set_state(state: str, msg: str, current: str | None = None) -> None:
        with ANALYSIS_CACHE_PATCH_LOCK:
            if job_id not in ANALYSIS_CACHE_PATCH_JOBS:
                return
            ANALYSIS_CACHE_PATCH_JOBS[job_id]["state"] = state
            ANALYSIS_CACHE_PATCH_JOBS[job_id]["message"] = msg
            ANALYSIS_CACHE_PATCH_JOBS[job_id]["updated_at"] = _utc_now_iso_ms()
            if current is not None:
                ANALYSIS_CACHE_PATCH_JOBS[job_id]["current"] = current
            if state in ("done", "error", "cancelled"):
                _job_set_finished(ANALYSIS_CACHE_PATCH_JOBS[job_id])

    try:
        metas = [m for m in _analysis_cache_list_meta() if str(m.get("series_key") or "") == series_key]
        patched = 0
        skipped = 0
        for meta in metas:
            with ANALYSIS_CACHE_PATCH_LOCK:
                if bool((ANALYSIS_CACHE_PATCH_JOBS.get(job_id) or {}).get("cancelled")):
                    set_state("cancelled", "Patchjob abgebrochen")
                    return
            cid = str(meta.get("id") or "")
            set_state("running", "Analysecache wird lokal repariert...", current=cid)
            try:
                res = _analysis_cache_patch_meta(cfg, meta)
                if bool(res.get("patched")):
                    patched += 1
                else:
                    skipped += 1
            except Exception as e:
                meta2 = dict(meta)
                meta2["dirty"] = True
                meta2["dirty_reason"] = "patch_failed"
                meta2["dirty_at"] = _utc_now_iso_ms()
                meta2["patch_status"] = "patch_failed"
                meta2["patch_error"] = str(e) or e.__class__.__name__
                meta2["last_patch_at"] = _utc_now_iso_ms()
                _analysis_cache_write_meta(meta2)
                skipped += 1
        with ANALYSIS_CACHE_PATCH_LOCK:
            if job_id in ANALYSIS_CACHE_PATCH_JOBS:
                ANALYSIS_CACHE_PATCH_JOBS[job_id]["patched"] = patched
                ANALYSIS_CACHE_PATCH_JOBS[job_id]["skipped"] = skipped
        set_state("done", f"Patchjob fertig: {patched} Segment(e) gepatcht, {skipped} uebersprungen.")
    except Exception as e:
        with ANALYSIS_CACHE_PATCH_LOCK:
            if job_id in ANALYSIS_CACHE_PATCH_JOBS:
                ANALYSIS_CACHE_PATCH_JOBS[job_id]["error"] = str(e) or e.__class__.__name__
        set_state("error", str(e) or e.__class__.__name__)


def _analysis_cache_queue_patch_job(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    reason: str,
) -> str | None:
    series_key = _analysis_cache_series_key(measurement, field, entity_id, friendly_name)
    if not series_key.strip():
        return None
    with ANALYSIS_CACHE_PATCH_LOCK:
        for job in ANALYSIS_CACHE_PATCH_JOBS.values():
            if str(job.get("series_key") or "") != series_key:
                continue
            if str(job.get("state") or "") not in ("running", "pending"):
                continue
            return str(job.get("id") or "") or None
        job_id = uuid.uuid4().hex
        ANALYSIS_CACHE_PATCH_JOBS[job_id] = {
            "id": job_id,
            "series_key": series_key,
            "measurement": measurement,
            "field": field,
            "entity_id": entity_id,
            "friendly_name": friendly_name,
            "reason": reason,
            "state": "pending",
            "message": "Patchjob wird gestartet...",
            "started_at": _utc_now_iso_ms(),
            "updated_at": _utc_now_iso_ms(),
            "started_mono": time.monotonic(),
            "patched": 0,
            "skipped": 0,
            "cancelled": False,
            "error": None,
        }
    t = threading.Thread(target=_analysis_cache_patch_job_thread, args=(job_id, dict(cfg), series_key), daemon=True)
    t.start()
    return job_id


def _analysis_cache_mark_dirty_series(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    reason: str,
) -> str | None:
    now = _utc_now_iso_ms()
    touched = False
    for meta in _analysis_cache_list_meta():
        if str(meta.get("measurement") or "") != str(measurement or ""):
            continue
        if str(meta.get("field") or "") != str(field or ""):
            continue
        if (str(meta.get("entity_id") or "") or None) != (str(entity_id or "") or None):
            continue
        if (str(meta.get("friendly_name") or "") or None) != (str(friendly_name or "") or None):
            continue
        meta2 = dict(meta)
        meta2["dirty"] = True
        meta2["dirty_reason"] = str(reason or "manual_change")
        meta2["dirty_at"] = now
        meta2["patch_status"] = "patch_pending"
        meta2["patch_error"] = None
        _analysis_cache_write_meta(meta2)
        touched = True
    if not touched:
        return None
    return _analysis_cache_queue_patch_job(cfg, measurement, field, entity_id, friendly_name, reason)


def _analysis_cache_merge_group(cfg: dict[str, Any], metas: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(metas) < 2:
        return None
    metas = sorted(metas, key=lambda m: str(m.get("covered_start") or ""))
    first = metas[0]
    key0 = first.get("key") if isinstance(first.get("key"), dict) else {}
    measurement = str(key0.get("measurement") or first.get("measurement") or "")
    field = str(key0.get("field") or first.get("field") or "")
    entity_id = str(key0.get("entity_id") or first.get("entity_id") or "") or None
    friendly_name = str(key0.get("friendly_name") or first.get("friendly_name") or "") or None
    all_rows: list[dict[str, Any]] = []
    total_scanned = 0
    now = _utc_now_iso_ms()
    for meta in metas:
        start_iso = str(meta.get("covered_start") or "")
        stop_iso = str(meta.get("covered_stop") or "")
        start_dt, stop_dt = _analysis_cache_meta_span(meta)
        updated_at = _parse_iso_datetime(str(meta.get("updated_at") or "")) or datetime.fromtimestamp(0, tz=timezone.utc)
        changed = _history_changes_for_window(measurement, field, entity_id, friendly_name, start_dt, stop_dt, updated_at, limit=500) if start_dt and stop_dt else []
        if changed:
            rows, scanned = _analysis_cache_fetch_segment(cfg, measurement, field, entity_id, friendly_name, start_iso, stop_iso)
        else:
            payload = _analysis_cache_load_payload(str(meta.get("id") or "")) or {}
            rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
            scanned = int(payload.get("scanned") or meta.get("scanned") or 0)
        all_rows.extend([r for r in rows if isinstance(r, dict)])
        total_scanned += int(scanned or 0)
    merged_by_time: dict[str, dict[str, Any]] = {}
    for row in all_rows:
        merged_by_time[str(row.get("time") or "")] = row
    merged_rows = list(merged_by_time.values())
    merged_rows.sort(key=lambda r: str(r.get("time") or ""))
    merged_meta = _analysis_cache_store_segment(
        cfg,
        measurement,
        field,
        entity_id,
        friendly_name,
        str(metas[0].get("covered_start") or ""),
        str(metas[-1].get("covered_stop") or ""),
        merged_rows,
        total_scanned,
    )
    if not merged_meta:
        return None
    merged_meta["updated_at"] = now
    merged_meta["combined_from"] = [str(m.get("id") or "") for m in metas]
    _analysis_cache_write_meta(merged_meta)
    for meta in metas:
        _analysis_cache_delete_id(str(meta.get("id") or ""))
    return merged_meta


def _analysis_cache_contiguous_groups(metas: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    ordered = sorted(metas, key=lambda m: str(m.get("covered_start") or ""))
    groups: list[list[dict[str, Any]]] = []
    cur: list[dict[str, Any]] = []
    cur_stop: datetime | None = None
    for meta in ordered:
        start_dt, stop_dt = _analysis_cache_meta_span(meta)
        if not start_dt or not stop_dt:
            continue
        if not cur:
            cur = [meta]
            cur_stop = stop_dt
            continue
        if cur_stop and start_dt <= cur_stop:
            cur.append(meta)
            if stop_dt > cur_stop:
                cur_stop = stop_dt
        elif cur_stop and abs((start_dt - cur_stop).total_seconds()) <= 1:
            cur.append(meta)
            cur_stop = stop_dt
        else:
            groups.append(cur)
            cur = [meta]
            cur_stop = stop_dt
    if cur:
        groups.append(cur)
    return groups


def _dash_cache_is_stale(cfg: dict[str, Any], meta: dict[str, Any]) -> bool:
    try:
        mode = str(cfg.get("dash_cache_refresh_mode") or "hours").strip().lower()
        if mode not in ("hours", "daily", "weekly", "manual"):
            mode = "hours"

        updated_ts = _dash_cache_ts(meta, "updated_at")
        if updated_ts <= 0:
            return True

        if mode == "manual":
            return False

        now_ts = datetime.now(timezone.utc).timestamp()

        if mode == "hours":
            try:
                h = int(cfg.get("dash_cache_refresh_hours", 6) or 6)
            except Exception:
                h = 6
            if h <= 0:
                return False
            return (now_ts - updated_ts) >= float(h * 3600)

        # daily/weekly
        at = str(cfg.get("dash_cache_refresh_daily_at") or "00:00:00").strip() or "00:00:00"
        hh, mm, ss = _timer_parse_hms(at, (0, 0, 0))
        wd = _timer_parse_weekday(cfg.get("dash_cache_refresh_weekday"), default=0)

        now_local = datetime.now().astimezone()
        last_local = datetime.fromtimestamp(updated_ts, tz=timezone.utc).astimezone(now_local.tzinfo)
        boundary = _timer_last_boundary_local(now_local, mode=mode, hh=hh, mm=mm, ss=ss, weekday=wd)
        if not boundary:
            return False
        return last_local < boundary
    except Exception:
        return False


def _dash_cache_key_to_params(key: dict[str, Any]) -> tuple[
    str,
    str,
    str,
    str | None,
    str | None,
    str,
    str,
    int,
    datetime | None,
    datetime | None,
]:
    measurement = str(key.get("measurement") or "").strip()
    field = str(key.get("field") or "").strip()
    range_key = str(key.get("range") or "24h")
    entity_id = str(key.get("entity_id") or "").strip() or None
    friendly_name = str(key.get("friendly_name") or "").strip() or None
    unit = str(key.get("unit") or "").strip()
    detail_mode = str(key.get("detail_mode") or "dynamic").strip().lower()
    if detail_mode not in ("dynamic", "manual"):
        detail_mode = "dynamic"
    try:
        manual_density_pct = int(key.get("manual_density_pct") or 100)
    except Exception:
        manual_density_pct = 100
    manual_density_pct = min(100, max(1, manual_density_pct))

    start_dt = None
    stop_dt = None
    try:
        s = str(key.get("start") or "").strip()
        e = str(key.get("stop") or "").strip()
        if s and e:
            start_dt = _parse_iso_datetime(s)
            stop_dt = _parse_iso_datetime(e)
    except Exception:
        start_dt = None
        stop_dt = None

    return (
        measurement,
        field,
        range_key,
        entity_id,
        friendly_name,
        unit,
        detail_mode,
        manual_density_pct,
        start_dt,
        stop_dt,
    )


def _dash_cache_db_signature(cfg: dict[str, Any], key: dict[str, Any]) -> dict[str, Any]:
    """Best-effort signature for DB state in the cache's time window.

    Returns: {total_points, first_time, last_time}
    """

    (
        measurement,
        field,
        range_key,
        entity_id,
        friendly_name,
        _,
        _,
        _,
        start_dt,
        stop_dt,
    ) = _dash_cache_key_to_params(key)

    if not measurement or not field:
        return {"total_points": None, "first_time": None, "last_time": None}

    if int(cfg.get("influx_version", 2)) == 2:
        if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
            return {"total_points": None, "first_time": None, "last_time": None}

        extra = flux_tag_filter(entity_id, friendly_name)
        range_clause = _flux_range_clause(range_key, start_dt, stop_dt)
        base = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"])
'''

        def _count(qapi) -> int | None:
            try:
                qcnt = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_value"])
  |> count(column: "_value")
'''
                for rec in qapi.query_stream(qcnt, org=cfg["org"]):
                    v = rec.get_value()
                    if isinstance(v, (int, float)):
                        return int(v)
            except Exception:
                return None
            return None

        def _first_last(qapi, which: str) -> str | None:
            try:
                suffix = "first" if which == "first" else "last"
                q = base + f"  |> {suffix}()\n"
                for rec in qapi.query_stream(q, org=cfg["org"]):
                    ts = rec.get_time()
                    if isinstance(ts, datetime):
                        return _dt_to_rfc3339_utc_ms(ts)
                    break
            except Exception:
                return None
            return None

        with v2_client(cfg, timeout_seconds_override=min(8, int(cfg.get("timeout_seconds") or 10))) as c:
            qapi = c.query_api()
            total = _count(qapi)
            first_time = _first_last(qapi, "first")
            last_time = _first_last(qapi, "last")
            return {"total_points": total, "first_time": first_time, "last_time": last_time}

    # v1
    if not cfg.get("database"):
        return {"total_points": None, "first_time": None, "last_time": None}
    try:
        c = v1_client(cfg)
        tag_where = influxql_tag_filter(entity_id, friendly_name)
        time_where = _influxql_time_where(range_key, start_dt, stop_dt)

        total = None
        try:
            qcnt = f'SELECT COUNT("{field}") AS c FROM "{measurement}" WHERE {time_where}{tag_where}'
            res = c.query(qcnt)
            for _, pts in res.items():
                for p in pts:
                    v = p.get("c")
                    if isinstance(v, (int, float)):
                        total = int(v)
                        break
                if total is not None:
                    break
        except Exception:
            total = None

        def _one(which: str) -> str | None:
            try:
                fn = "FIRST" if which == "first" else "LAST"
                q = f'SELECT {fn}("{field}") AS v FROM "{measurement}" WHERE {time_where}{tag_where}'
                res = c.query(q)
                for _, pts in res.items():
                    for p in pts:
                        ts = p.get("time")
                        if ts:
                            return str(ts)
            except Exception:
                return None
            return None

        return {"total_points": total, "first_time": _one("first"), "last_time": _one("last")}
    except Exception:
        return {"total_points": None, "first_time": None, "last_time": None}


def _dash_cache_job_public(job: dict[str, Any]) -> dict[str, Any]:
    return _job_public(job)


def _dash_cache_job_thread(job_id: str, action: str, cache_id: str) -> None:
    def set_state(state: str, msg: str) -> None:
        timer_id = None
        extra = None
        with DASH_CACHE_JOBS_LOCK:
            if job_id in DASH_CACHE_JOBS:
                DASH_CACHE_JOBS[job_id]["state"] = state
                DASH_CACHE_JOBS[job_id]["message"] = msg
                if state in ("done", "error", "cancelled"):
                    _job_set_finished(DASH_CACHE_JOBS[job_id])
                    timer_id = DASH_CACHE_JOBS[job_id].get("timer_id")
                    try:
                        started_mono = float(DASH_CACHE_JOBS[job_id].get("started_mono") or 0.0)
                    except Exception:
                        started_mono = 0.0
                    dur_ms = int(max(0.0, (time.monotonic() - started_mono) * 1000.0)) if started_mono > 0 else None
                    err = str(DASH_CACHE_JOBS[job_id].get("error") or "").strip() or None
                    if state == "error" and not err:
                        err = str(msg or "").strip() or None
                    extra = {"duration_ms": dur_ms, "error": err}
        if timer_id and state in ("done", "error", "cancelled"):
            _timer_mark_finished(str(timer_id), state, extra=extra)

    def set_error(msg: str) -> None:
        with DASH_CACHE_JOBS_LOCK:
            if job_id in DASH_CACHE_JOBS:
                DASH_CACHE_JOBS[job_id]["error"] = msg

    try:
        trigger_page = None
        with DASH_CACHE_JOBS_LOCK:
            j = DASH_CACHE_JOBS.get(job_id) or {}
            trigger_page = j.get("trigger_page")
            if bool(j.get("cancelled")):
                set_state("cancelled", "Abgebrochen")
                return

        cfg = _overlay_from_yaml_if_enabled(load_cfg())

        def is_cancelled() -> bool:
            with DASH_CACHE_JOBS_LOCK:
                j2 = DASH_CACHE_JOBS.get(job_id) or {}
                if bool(j2.get("cancelled")):
                    return True
                try:
                    max_s = int(cfg.get("jobs_max_runtime_seconds", 0) or 0)
                except Exception:
                    max_s = 0
                if max_s <= 0:
                    return False
                try:
                    started_mono = float(j2.get("started_mono") or 0.0)
                except Exception:
                    started_mono = 0.0
                if started_mono > 0 and (time.monotonic() - started_mono) >= float(max_s):
                    DASH_CACHE_JOBS[job_id]["cancelled"] = True
                    try:
                        LOG.warning("job_auto_cancel type=dash_cache job_id=%s reason=max_runtime_seconds exceeded (%s)", job_id, max_s)
                    except Exception:
                        pass
                    return True
                return False
        meta = _dash_cache_load_meta(cache_id)
        if not meta:
            set_state("error", "Cache nicht gefunden")
            set_error("cache not found")
            return
        key = meta.get("key") if isinstance(meta.get("key"), dict) else None
        if not key:
            set_state("error", "Cache-Key fehlt")
            set_error("cache key missing")
            return

        now = _utc_now_iso_ms()

        if is_cancelled():
            set_state("cancelled", "Abgebrochen")
            return

        if action == "delete":
            try:
                _dash_cache_meta_path(cache_id).unlink(missing_ok=True)
            except Exception:
                pass
            try:
                _dash_cache_data_path(cache_id).unlink(missing_ok=True)
            except Exception:
                pass
            set_state("done", "Cache geloescht")
            return

        if action == "check":
            set_state("running", "Pruefe Cache...")
            sig = _dash_cache_db_signature(cfg, key)
            mismatch = False
            note = []
            try:
                if meta.get("total_points") is not None and sig.get("total_points") is not None:
                    if int(meta.get("total_points") or 0) != int(sig.get("total_points") or 0):
                        mismatch = True
                        note.append("count")
            except Exception:
                pass
            try:
                if meta.get("first_time") and sig.get("first_time") and str(meta.get("first_time")) != str(sig.get("first_time")):
                    mismatch = True
                    note.append("first")
            except Exception:
                pass
            try:
                if meta.get("last_time") and sig.get("last_time") and str(meta.get("last_time")) != str(sig.get("last_time")):
                    mismatch = True
                    note.append("last")
            except Exception:
                pass

            meta["last_check_at"] = now
            meta["last_check_ok"] = (not mismatch)
            meta["last_check_note"] = ("ok" if not mismatch else ("changed: " + ",".join(note)))
            meta["mismatch"] = bool(mismatch)
            _meta_add_event(meta, "check", str(meta.get("last_check_note") or ""), at=now)
            _dash_cache_write_meta(meta)
            set_state("done", "Pruefung fertig")
            return

        # update
        set_state("running", "Aktualisiere Cache...")
        (
            measurement,
            field,
            range_key,
            entity_id,
            friendly_name,
            unit,
            detail_mode,
            manual_density_pct,
            start_dt,
            stop_dt,
        ) = _dash_cache_key_to_params(key)
        payload = _query_payload(
            cfg,
            measurement,
            field,
            range_key,
            entity_id,
            friendly_name,
            unit,
            detail_mode,
            manual_density_pct,
            start_dt,
            stop_dt,
        )
        _dash_cache_store(cache_id, key, payload, trigger_page=str(trigger_page or "").strip() or None)
        meta2 = _dash_cache_load_meta(cache_id) or meta
        meta2["last_update_at"] = now
        meta2["last_update_note"] = "updated"
        meta2["dirty"] = False
        meta2["dirty_reason"] = None
        meta2["dirty_at"] = None
        meta2["mismatch"] = False
        _meta_add_event(meta2, "update", "updated", at=now)
        _dash_cache_write_meta(meta2)
        set_state("done", "Cache aktualisiert")
    except _ApiError as e:
        try:
            meta = _dash_cache_load_meta(cache_id) or {}
            meta["last_update_at"] = _utc_now_iso_ms()
            meta["last_update_note"] = f"error: {e.message}"
            _dash_cache_write_meta(meta)
        except Exception:
            pass
        set_error(str(e.message))
        set_state("error", "Fehler")
    except Exception as e:
        msg = _short_influx_error(e)
        try:
            meta = _dash_cache_load_meta(cache_id) or {}
            meta["last_update_at"] = _utc_now_iso_ms()
            meta["last_update_note"] = f"error: {msg}"
            _dash_cache_write_meta(meta)
        except Exception:
            pass
        set_error(msg)
        set_state("error", "Fehler")


def _dash_cache_start_job(
    action: str,
    cache_id: str,
    trigger_page: str | None = None,
    timer_id: str | None = None,
) -> str:
    job_id = uuid.uuid4().hex
    ip = _req_ip()
    ua = _req_ua()
    job = {
        "id": job_id,
        "state": "queued",
        "message": "Start...",
        "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "started_mono": time.monotonic(),
        "trigger_page": trigger_page,
        "trigger_ip": ip,
        "trigger_ua": ua,
        "timer_id": str(timer_id or "").strip() or None,
        "cache_id": cache_id,
        "action": action,
    }
    with DASH_CACHE_JOBS_LOCK:
        DASH_CACHE_JOBS[job_id] = job
        # Cleanup old jobs
        cutoff = time.monotonic() - 6 * 3600
        old = [k for k, v in DASH_CACHE_JOBS.items() if float(v.get("started_mono") or 0) < cutoff]
        for k in old:
            if k != job_id:
                DASH_CACHE_JOBS.pop(k, None)
    try:
        LOG.info(
            "job_start type=dash_cache job_id=%s action=%s cache_id=%s timer_id=%s ip=%s ua=%s",
            job_id,
            action,
            cache_id,
            str(timer_id or "") if timer_id else "",
            ip,
            ua,
        )
    except Exception:
        pass
    t = threading.Thread(target=_dash_cache_job_thread, args=(job_id, action, cache_id), daemon=True)
    t.start()
    return job_id


def _stats_cache_meta_path(cache_id: str) -> Path:
    return STATS_CACHE_DIR / f"{cache_id}.meta.json"


def _stats_cache_data_path(cache_id: str) -> Path:
    return STATS_CACHE_DIR / f"{cache_id}.data.json.gz"


def _series_stats_cache_meta_path(cache_id: str) -> Path:
    return SERIES_STATS_CACHE_DIR / f"{cache_id}.meta.json"


def _series_stats_cache_data_path(cache_id: str) -> Path:
    return SERIES_STATS_CACHE_DIR / f"{cache_id}.data.json"


def _series_stats_cache_id(key: dict[str, Any]) -> str:
    try:
        raw = json.dumps(key or {}, sort_keys=True, ensure_ascii=True)
    except Exception:
        raw = str(key or "")
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _series_stats_cache_load_meta(cache_id: str) -> dict[str, Any] | None:
    try:
        p = _series_stats_cache_meta_path(cache_id)
        if not p.exists():
            return None
        with SERIES_STATS_CACHE_LOCK:
            return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _series_stats_cache_write_meta(meta: dict[str, Any]) -> None:
    try:
        SERIES_STATS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_id = str(meta.get("id") or "").strip()
        if not cache_id:
            return
        p = _series_stats_cache_meta_path(cache_id)
        with SERIES_STATS_CACHE_LOCK:
            p.write_text(json.dumps(meta, ensure_ascii=True), encoding="utf-8")
    except Exception:
        return


def _series_stats_cache_load_payload(cache_id: str) -> dict[str, Any] | None:
    try:
        p = _series_stats_cache_data_path(cache_id)
        if not p.exists():
            return None
        with SERIES_STATS_CACHE_LOCK:
            return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _series_stats_cache_write_payload(cache_id: str, payload: dict[str, Any]) -> int:
    try:
        SERIES_STATS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(payload, ensure_ascii=True)
        p = _series_stats_cache_data_path(cache_id)
        with SERIES_STATS_CACHE_LOCK:
            p.write_text(raw, encoding="utf-8")
        return len(raw.encode("utf-8"))
    except Exception:
        return 0


def _series_stats_cache_list_meta() -> list[dict[str, Any]]:
    try:
        if not SERIES_STATS_CACHE_DIR.exists():
            return []
        out = []
        for p in sorted(SERIES_STATS_CACHE_DIR.glob("*.meta.json")):
            try:
                m = json.loads(p.read_text(encoding="utf-8", errors="replace"))
                if isinstance(m, dict):
                    out.append(m)
            except Exception:
                continue
        return out
    except Exception:
        return []


def _series_stats_cache_touch_used(cache_id: str) -> None:
    try:
        meta = _series_stats_cache_load_meta(cache_id)
        if not meta:
            return
        meta["last_used_at"] = _utc_now_iso_ms()
        _series_stats_cache_write_meta(meta)
    except Exception:
        return


def _stats_cache_cfg_fp(cfg: dict[str, Any]) -> str:
    """Stable fingerprint for the active Influx connection (no secrets)."""

    try:
        influx_v = int(cfg.get("influx_version", 2) or 2)
    except Exception:
        influx_v = 2
    base = {
        "influx_version": influx_v,
        "scheme": str(cfg.get("scheme") or ""),
        "host": str(cfg.get("host") or ""),
        "port": int(cfg.get("port") or 0),
        "org": str(cfg.get("org") or "") if influx_v == 2 else "",
        "bucket": str(cfg.get("bucket") or "") if influx_v == 2 else "",
        "database": str(cfg.get("database") or "") if influx_v != 2 else "",
        "verify_ssl": bool(cfg.get("verify_ssl", True)),
        "timeout_seconds": int(cfg.get("timeout_seconds", 10) or 10),
    }
    raw = json.dumps(base, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _stats_cache_key(
    cfg: dict[str, Any],
    body: dict[str, Any],
    start_dt: datetime,
    stop_dt: datetime,
    field_filter: str | None,
    measurement_filter: str | None,
    entity_id_filter: str | None,
    friendly_name_filter: str | None,
    columns: list[str] | None,
    page_limit: int,
) -> dict[str, Any]:
    range_key = str(body.get("range") or "").strip().lower()
    if not range_key:
        range_key = "custom"
    if range_key not in ("custom", "all", "this_year", "12mo", "24mo"):
        # allow 24h/30d/... as-is
        range_key = range_key

    cols = [str(x) for x in (columns or []) if x]
    cols = sorted(set(cols))

    # Keep key stable for relative ranges.
    start_iso = _dt_to_rfc3339_utc(start_dt) if range_key == "custom" else None
    stop_iso = _dt_to_rfc3339_utc(stop_dt) if range_key == "custom" else None

    return {
        "v": 2,
        "kind": "global_stats",
        "cfg_fp": _stats_cache_cfg_fp(cfg),
        "range": range_key,
        "start": start_iso,
        "stop": stop_iso,
        "field_filter": str(field_filter or "") or None,
        "measurement": str(measurement_filter or "") or None,
        "entity_id": str(entity_id_filter or "") or None,
        "friendly_name": str(friendly_name_filter or "") or None,
        "columns": cols,
        "page_limit": int(page_limit or 200),
        # keep original payload markers for debugging
        "payload_start": body.get("start") or body.get("start_time"),
        "payload_stop": body.get("stop") or body.get("end") or body.get("stop_time"),
    }


def _stats_cache_append_supported(range_key: str) -> bool:
    rk = str(range_key or "").strip().lower()
    return rk in ("all", "this_year")


def _stats_cache_sliding_supported(range_key: str) -> bool:
    rk = str(range_key or "").strip().lower()
    return rk in ("24h", "7d", "30d", "90d", "180d", "365d", "12mo", "24mo")


def _stats_row_identity(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("measurement") or ""),
        str(row.get("field") or ""),
        str(row.get("entity_id") or ""),
        str(row.get("friendly_name") or ""),
    )


def _stats_row_sum(row: dict[str, Any]) -> float | None:
    try:
        if row.get("__sum") is not None:
            return float(row.get("__sum"))
    except Exception:
        pass
    try:
        count = int(row.get("count") or 0)
        mean = row.get("mean")
        if count > 0 and mean is not None:
            return float(mean) * float(count)
    except Exception:
        pass
    return None


def _stats_cache_merge_rows(base_rows: list[dict[str, Any]], delta_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for src in base_rows or []:
        if isinstance(src, dict):
            merged[_stats_row_identity(src)] = dict(src)

    for src in delta_rows or []:
        if not isinstance(src, dict):
            continue
        key = _stats_row_identity(src)
        cur = merged.get(key)
        if not cur:
            merged[key] = dict(src)
            continue

        out = dict(cur)

        try:
            c0 = int(cur.get("count") or 0)
            c1 = int(src.get("count") or 0)
            if c0 or c1:
                out["count"] = c0 + c1
        except Exception:
            pass

        s0 = _stats_row_sum(cur)
        s1 = _stats_row_sum(src)
        if s0 is not None or s1 is not None:
            total_sum = float(s0 or 0.0) + float(s1 or 0.0)
            out["__sum"] = total_sum
            try:
                total_count = int(out.get("count") or 0)
                if total_count > 0:
                    out["mean"] = total_sum / float(total_count)
            except Exception:
                pass

        try:
            if cur.get("min") is None:
                out["min"] = src.get("min")
            elif src.get("min") is not None:
                out["min"] = min(float(cur.get("min")), float(src.get("min")))
        except Exception:
            pass
        try:
            if cur.get("max") is None:
                out["max"] = src.get("max")
            elif src.get("max") is not None:
                out["max"] = max(float(cur.get("max")), float(src.get("max")))
        except Exception:
            pass

        try:
            ct = _parse_iso_datetime(str(cur.get("oldest_time") or ""))
            st = _parse_iso_datetime(str(src.get("oldest_time") or ""))
            if st and (not ct or st < ct):
                out["oldest_time"] = _dt_to_rfc3339_utc(st)
        except Exception:
            pass

        try:
            ct = _parse_iso_datetime(str(cur.get("newest_time") or ""))
            st = _parse_iso_datetime(str(src.get("newest_time") or ""))
            if st and (not ct or st >= ct):
                out["newest_time"] = _dt_to_rfc3339_utc(st)
                if "last_value" in src:
                    out["last_value"] = src.get("last_value")
        except Exception:
            pass

        merged[key] = out

    return sorted(merged.values(), key=lambda r: int(r.get("count") or 0), reverse=True)


def _stats_cache_discover_series_span(
    cfg: dict[str, Any],
    start_dt: datetime,
    stop_dt: datetime,
    field_filter: str | None,
    measurement_filter: str | None,
    entity_id_filter: str | None,
    friendly_name_filter: str | None,
) -> list[dict[str, Any]]:
    ff = str(field_filter or "").strip()
    mf = str(measurement_filter or "").strip()
    eid_f = str(entity_id_filter or "").strip()
    fn_f = str(friendly_name_filter or "").strip()
    cfg_local = dict(cfg)
    try:
        cfg_local["timeout_seconds"] = min(max(int(cfg_local.get("timeout_seconds", 10)), 10), 60)
    except Exception:
        cfg_local["timeout_seconds"] = 60

    min_chunk_seconds = 5 * 60

    def _run(a: datetime, b: datetime) -> list[dict[str, Any]]:
        s_iso = _dt_to_rfc3339_utc(a)
        e_iso = _dt_to_rfc3339_utc(b)
        ff_clause = f"|> filter(fn: (r) => r._field == {_flux_str(ff)})" if ff else ""
        mf_clause = f"|> filter(fn: (r) => r._measurement == {_flux_str(mf)})" if mf else ""
        tag_clause = ""
        if eid_f:
            tag_clause += f"|> filter(fn: (r) => r.entity_id == {_flux_str(eid_f)})\n"
        if fn_f:
            tag_clause += f"|> filter(fn: (r) => r.friendly_name == {_flux_str(fn_f)})\n"
        q = f'''
from(bucket: "{cfg_local["bucket"]}")
  |> range(start: time(v: "{s_iso}"), stop: time(v: "{e_iso}"))
  |> filter(fn: (r) => exists r._measurement and exists r._field)
  {mf_clause}
  {ff_clause}
  {tag_clause.strip()}
  |> map(fn: (r) => ({{ r with entity_id: if exists r.entity_id then string(v: r.entity_id) else "", friendly_name: if exists r.friendly_name then string(v: r.friendly_name) else "" }}))
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_time","_value"])
  |> group(columns: ["_measurement","_field","entity_id","friendly_name"])
  |> last()
'''
        out: list[dict[str, Any]] = []
        with v2_client(cfg_local) as c:
            qapi = c.query_api()
            for rec in qapi.query_stream(q, org=cfg_local["org"]):
                vals = getattr(rec, "values", {}) or {}
                newest = rec.get_time() or vals.get("_time")
                out.append({
                    "measurement": str(vals.get("_measurement") or ""),
                    "field": str(vals.get("_field") or ""),
                    "entity_id": str(vals.get("entity_id") or ""),
                    "friendly_name": str(vals.get("friendly_name") or ""),
                    "newest_time": _as_rfc3339(newest),
                    "last_value": rec.get_value(),
                })
        return out

    def _split(a: datetime, b: datetime) -> list[dict[str, Any]]:
        span_s = max(0.0, (b - a).total_seconds())
        try:
            return _run(a, b)
        except Exception as e:
            s = str(e).lower()
            timeout = ("timed out" in s) or ("timeout" in s) or ("read timed out" in s)
            if timeout and span_s > min_chunk_seconds:
                mid = a + timedelta(seconds=(span_s / 2.0))
                return _split(a, mid) + _split(mid, b)
            raise

    if stop_dt <= start_dt:
        return []
    return _split(start_dt, stop_dt)


def _stats_cache_id(key: dict[str, Any]) -> str:
    raw = json.dumps(key, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _stats_cache_load_meta(cache_id: str) -> dict[str, Any] | None:
    try:
        p = _stats_cache_meta_path(cache_id)
        if not p.exists():
            return None
        with STATS_CACHE_LOCK:
            j = json.loads(p.read_text(encoding="utf-8"))
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def _stats_cache_write_meta(meta: dict[str, Any]) -> None:
    try:
        STATS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    try:
        cache_id = str(meta.get("id") or "").strip()
        if not cache_id:
            return
        p = _stats_cache_meta_path(cache_id)
        raw = json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=True)
        with STATS_CACHE_LOCK:
            p.write_text(raw, encoding="utf-8")
    except Exception:
        return


def _stats_cache_load_payload(cache_id: str) -> dict[str, Any] | None:
    try:
        p = _stats_cache_data_path(cache_id)
        if not p.exists():
            return None
        with STATS_CACHE_LOCK:
            raw = gzip.decompress(p.read_bytes()).decode("utf-8", errors="replace")
        j = json.loads(raw)
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def _stats_cache_write_payload(cache_id: str, payload: dict[str, Any]) -> int:
    try:
        STATS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    try:
        p = _stats_cache_data_path(cache_id)
        raw = json.dumps(payload, sort_keys=False, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        comp = gzip.compress(raw)
        with STATS_CACHE_LOCK:
            p.write_bytes(comp)
        return len(comp)
    except Exception:
        return 0


def _stats_cache_list_meta() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        if not STATS_CACHE_DIR.exists():
            return []
        for p in sorted(STATS_CACHE_DIR.glob("*.meta.json")):
            try:
                j = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(j, dict):
                    out.append(j)
            except Exception:
                continue
    except Exception:
        return []
    return out


def _stats_cache_ts(meta: dict[str, Any], key: str) -> float:
    try:
        s = str(meta.get(key) or "").strip()
        if not s:
            return 0.0
        dt = _parse_iso_datetime(s)
        if not dt:
            return 0.0
        return dt.timestamp()
    except Exception:
        return 0.0


def _stats_cache_is_stale(cfg: dict[str, Any], meta: dict[str, Any]) -> bool:
    try:
        mode = str(cfg.get("stats_cache_refresh_mode") or "daily").strip().lower()
        if mode not in ("hours", "daily", "weekly", "manual"):
            mode = "daily"

        updated_ts = _stats_cache_ts(meta, "updated_at")
        if updated_ts <= 0:
            return True

        if mode == "manual":
            return False

        now_ts = datetime.now(timezone.utc).timestamp()
        if mode == "hours":
            try:
                h = int(cfg.get("stats_cache_refresh_hours", 24) or 24)
            except Exception:
                h = 24
            if h <= 0:
                return False
            return (now_ts - updated_ts) >= float(h * 3600)

        at = str(cfg.get("stats_cache_refresh_daily_at") or "03:00:00").strip() or "03:00:00"
        hh, mm, ss = _timer_parse_hms(at, (3, 0, 0))
        wd = _timer_parse_weekday(cfg.get("stats_cache_refresh_weekday"), default=0)

        now_local = datetime.now().astimezone()
        last_local = datetime.fromtimestamp(updated_ts, tz=timezone.utc).astimezone(now_local.tzinfo)
        boundary = _timer_last_boundary_local(now_local, mode=mode, hh=hh, mm=mm, ss=ss, weekday=wd)
        if not boundary:
            return False
        return last_local < boundary
    except Exception:
        return False


def _stats_cache_touch_used(cache_id: str) -> None:
    try:
        meta = _stats_cache_load_meta(cache_id)
        if not meta:
            return
        now = _utc_now_iso_ms()
        meta["last_used_at"] = now
        _meta_add_event(meta, "used", None, at=now)
        _stats_cache_write_meta(meta)
        try:
            cfg = load_cfg()
            _cache_usage_append(cfg, {
                "kind": "stats_cache_used",
                "page": str(meta.get("trigger_page") or "stats"),
                "cache_id": str(cache_id),
                "step": "touch_used",
                "rows": meta.get("row_count"),
                "bytes": meta.get("bytes"),
            })
        except Exception:
            pass
    except Exception:
        return


def _stats_cache_enforce_limits(cfg: dict[str, Any]) -> None:
    try:
        try:
            max_items = int(cfg.get("stats_cache_max_items", 10) or 10)
        except Exception:
            max_items = 10
        if max_items < 0:
            max_items = 0

        try:
            max_mb = int(cfg.get("stats_cache_max_mb", 50) or 50)
        except Exception:
            max_mb = 50
        if max_mb < 0:
            max_mb = 0
        max_bytes = max_mb * 1024 * 1024

        items = _stats_cache_list_meta()
        if not items:
            return

        def score(m: dict[str, Any]) -> tuple[float, float]:
            return (_stats_cache_ts(m, "last_used_at") or _stats_cache_ts(m, "updated_at"), _stats_cache_ts(m, "updated_at"))

        items.sort(key=score)
        total = 0
        for m in items:
            try:
                total += int(m.get("bytes") or 0)
            except Exception:
                pass

        # Evict LRU until limits satisfied.
        while items and ((max_items > 0 and len(items) > max_items) or (max_bytes > 0 and total > max_bytes) or (max_items == 0) or (max_bytes == 0)):
            m = items.pop(0)
            cid = str(m.get("id") or "").strip()
            if not cid:
                continue
            try:
                total -= int(m.get("bytes") or 0)
            except Exception:
                pass
            try:
                _stats_cache_meta_path(cid).unlink(missing_ok=True)
            except Exception:
                pass
            try:
                _stats_cache_data_path(cid).unlink(missing_ok=True)
            except Exception:
                pass
    except Exception:
        return


def _stats_cache_mark_dirty_series(
    measurement: str | None,
    field: str | None,
    entity_id: str | None,
    friendly_name: str | None,
    reason: str,
) -> None:
    try:
        for meta in _stats_cache_list_meta():
            try:
                k = meta.get("key") or {}
                if not isinstance(k, dict) or str(k.get("kind") or "") != "global_stats":
                    continue

                mf = str(k.get("measurement") or "").strip()
                if mf and measurement and mf != str(measurement):
                    continue
                ff = str(k.get("field_filter") or "").strip()
                if ff and field and ff != str(field):
                    continue
                eidf = str(k.get("entity_id") or "").strip()
                if eidf and entity_id and eidf != str(entity_id):
                    continue
                fnf = str(k.get("friendly_name") or "").strip()
                if fnf and friendly_name and fnf != str(friendly_name):
                    continue

                meta["dirty"] = True
                meta["dirty_reason"] = str(reason or "")[:80]
                meta["dirty_at"] = _utc_now_iso_ms()
                _meta_add_event(meta, "dirty", str(meta.get("dirty_reason") or ""), at=str(meta.get("dirty_at") or ""))
                _stats_cache_write_meta(meta)
            except Exception:
                continue

        # Also mark per-series total stats cache entries dirty.
        for meta in _series_stats_cache_list_meta():
            try:
                k = meta.get("key") or {}
                if not isinstance(k, dict) or str(k.get("kind") or "") != "series_stats_total":
                    continue

                mf = str(k.get("measurement") or "").strip()
                if measurement and mf and mf != str(measurement):
                    continue
                ff = str(k.get("field") or "").strip()
                if field and ff and ff != str(field):
                    continue
                eidf = str(k.get("entity_id") or "").strip()
                if entity_id and eidf and eidf != str(entity_id):
                    continue
                fnf = str(k.get("friendly_name") or "").strip()
                if friendly_name and fnf and fnf != str(friendly_name):
                    continue

                meta["dirty"] = True
                meta["dirty_reason"] = str(reason or "")[:80]
                meta["dirty_at"] = _utc_now_iso_ms()
                _meta_add_event(meta, "dirty", str(meta.get("dirty_reason") or ""), at=str(meta.get("dirty_at") or ""))
                _series_stats_cache_write_meta(meta)
            except Exception:
                continue
    except Exception:
        return


def _stats_cache_range_to_datetimes(range_key: str) -> tuple[datetime, datetime]:
    """Match stats.html timeFilter() behavior (best-effort)."""

    now_utc = datetime.now(timezone.utc)
    rk = (range_key or "").strip().lower()
    if not rk:
        rk = "30d"
    if rk == "all":
        return datetime(1970, 1, 1, tzinfo=timezone.utc), now_utc
    if rk == "this_year":
        now_local = datetime.now().astimezone()
        start_local = now_local.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start_local.astimezone(timezone.utc), now_utc
    if rk == "12mo":
        return now_utc - timedelta(days=365), now_utc
    if rk == "24mo":
        return now_utc - timedelta(days=730), now_utc

    m = re.match(r"^(\d+)([hd])$", rk)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        delta = timedelta(days=n) if unit == "d" else timedelta(hours=n)
        return now_utc - delta, now_utc

    md = re.match(r"^(\d+)d$", rk)
    if md:
        n = int(md.group(1))
        return now_utc - timedelta(days=n), now_utc

    # fallback: support existing parse_range_to_datetimes for h/d
    try:
        return parse_range_to_datetimes(rk)
    except Exception:
        return now_utc - timedelta(days=30), now_utc


def _parse_range_key(range_key: str) -> tuple[int, str]:
    s = (range_key or "").strip().lower()
    if not s:
        return 24, "h"
    # Special keys are handled by callers.
    if s in ("all", "alle", "inf", "infinite", "infinity"):
        return 24, "h"
    num = ""
    unit = ""
    for ch in s:
        if ch.isdigit() and not unit:
            num += ch
        else:
            unit += ch
    try:
        n = int(num or "0")
    except Exception:
        n = 0
    u = unit or "h"
    if u not in ("h", "d"):
        u = "h"
    if n <= 0:
        n = 24
        u = "h"
    return n, u


def range_to_flux(range_key: str) -> str:
    s = (range_key or "").strip().lower()
    if s in ("all", "alle", "inf", "infinite", "infinity"):
        return 'time(v: "1970-01-01T00:00:00Z")'
    n, u = _parse_range_key(range_key)
    return f"-{n}{u}"


def range_to_influxql(range_key: str) -> str:
    s = (range_key or "").strip().lower()
    if s in ("all", "alle", "inf", "infinite", "infinity"):
        return "0h"
    n, u = _parse_range_key(range_key)
    return f"{n}{u}"


def parse_range_to_datetimes(range_key: str) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    s = (range_key or "").strip().lower()
    if s in ("all", "alle", "inf", "infinite", "infinity"):
        return datetime(1970, 1, 1, tzinfo=timezone.utc), now
    n, u = _parse_range_key(range_key)
    delta = timedelta(hours=n) if u == "h" else timedelta(days=n)
    return now - delta, now


def _parse_iso_datetime(s: str) -> datetime:
    """Parse an ISO datetime string into a timezone-aware UTC datetime.

    Accepts strings like:
      - 2026-02-23T10:00:00Z
      - 2026-02-23T10:00:00+00:00
      - 2026-02-23T10:00:00.123Z
    """

    v = (s or "").strip()
    if not v:
        raise ValueError("empty datetime")
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        raise ValueError("datetime must include timezone")
    return dt.astimezone(timezone.utc)


def _get_start_stop_from_payload(payload: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    start_raw = payload.get("start") or payload.get("start_time")
    stop_raw = payload.get("stop") or payload.get("end") or payload.get("stop_time")
    if not start_raw and not stop_raw:
        return None, None

    if not (start_raw and stop_raw):
        raise ValueError("start and stop required")

    start_dt = _parse_iso_datetime(str(start_raw))
    stop_dt = _parse_iso_datetime(str(stop_raw))
    if stop_dt <= start_dt:
        raise ValueError("stop must be after start")
    return start_dt, stop_dt


def _dt_to_rfc3339_utc(dt: datetime) -> str:
    s = dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    return s.replace("+00:00", "Z")


def _dt_to_rfc3339_utc_ms(dt: datetime) -> str:
    """RFC3339 UTC with millisecond precision."""

    s = dt.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    return s.replace("+00:00", "Z")


_UI_LOCAL_TS_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2}):(\d{2})\.(\d{3})$")


def _tz_from_client(tz_name: str | None, tz_offset_minutes: int | None):
    """Return a tzinfo based on client timezone.

    Prefers an IANA timezone name. Falls back to a fixed offset.
    """

    name = (tz_name or "").strip()
    if name:
        try:
            return ZoneInfo(name)
        except Exception:
            pass
    try:
        if tz_offset_minutes is not None:
            return timezone(timedelta(minutes=int(tz_offset_minutes)))
    except Exception:
        pass
    return timezone.utc


def _parse_ui_local_ts(s: str, tz_name: str | None, tz_offset_minutes: int | None) -> datetime:
    """Parse UI local timestamp (dd.mm.yyyy HH:MM:SS.mmm) into UTC datetime."""

    v = (s or "").strip()
    m = _UI_LOCAL_TS_RE.match(v)
    if not m:
        raise ValueError("invalid local timestamp format")
    dd, mm, yyyy, hh, mi, ss, ms = (int(x) for x in m.groups())
    tz = _tz_from_client(tz_name, tz_offset_minutes)
    dt = datetime(yyyy, mm, dd, hh, mi, ss, ms * 1000, tzinfo=tz)
    return dt.astimezone(timezone.utc)


def _fmt_ui_local_ts(dt_utc: datetime, tz_name: str | None, tz_offset_minutes: int | None) -> str:
    """Format UTC datetime into UI local timestamp (dd.mm.yyyy HH:MM:SS.mmm)."""

    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    tz = _tz_from_client(tz_name, tz_offset_minutes)
    d = dt_utc.astimezone(tz)
    return (
        f"{d.day:02d}.{d.month:02d}.{d.year:04d} "
        f"{d.hour:02d}:{d.minute:02d}:{d.second:02d}.{int(d.microsecond/1000):03d}"
    )


def _flux_range_clause(range_key: str, start: datetime | None, stop: datetime | None) -> str:
    if start and stop:
        s = _dt_to_rfc3339_utc(start)
        e = _dt_to_rfc3339_utc(stop)
        return f'|> range(start: time(v: "{s}"), stop: time(v: "{e}"))'
    rk = (range_key or "").strip().lower()
    if rk in ("all", "alle", "inf", "infinite", "infinity"):
        return '|> range(start: time(v: "1970-01-01T00:00:00Z"))'
    return f"|> range(start: {range_to_flux(range_key)})"


def _selector_range_key(range_key: str | None, start: datetime | None, stop: datetime | None) -> str:
    """Selector range selection.

    Note: This repo now defaults selector endpoints to full history when no
    explicit time filter is provided, to keep source resolution consistent.
    If this becomes too expensive for large buckets, clients should pass an
    explicit `range=` value.
    """

    if start and stop:
        return str(range_key or "24h")
    rk = str(range_key or "").strip()
    return rk if rk else "all"


def _log_selector_debug(kind: str, payload: dict[str, Any]) -> None:
    try:
        safe = json.dumps(payload, ensure_ascii=True)
    except Exception:
        safe = str(payload)
    try:
        LOG.debug("selector_debug kind=%s payload=%s", kind, safe)
    except Exception:
        pass


def _parse_import_measurement_transforms(cfg: dict[str, Any]) -> dict[tuple[str, str], float]:
    raw = str(cfg.get("import_measurement_transforms") or "")
    out: dict[tuple[str, str], float] = {}
    for ln in raw.splitlines():
        s = str(ln or "").strip()
        if not s or s.startswith("#"):
            continue
        src = dst = ""
        factor_txt = ""
        parts = [p.strip() for p in re.split(r"[;,]", s) if p.strip()]
        if len(parts) >= 3:
            src, dst, factor_txt = parts[0], parts[1], parts[2]
        else:
            m = re.match(r"^(.*?)\s*(?:=>|->|>)\s*(.*?)\s*=\s*([-+0-9.eE]+)$", s)
            if m:
                src, dst, factor_txt = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if not src or not dst or not factor_txt:
            continue
        try:
            out[(src, dst)] = float(factor_txt)
        except Exception:
            continue
    return out


def _import_column_map(header: list[str]) -> dict[str, str]:
    canon = {_canon_col(c): c for c in header if c is not None}
    alias = {
        "timestamp": "time",
        "datetime": "time",
        "date": "time",
        "value": "value",
        "val": "value",
        "state": "value",
        "measurement": "_measurement",
        "_measurement": "_measurement",
        "field": "_field",
        "_field": "_field",
        "entityid": "entity_id",
        "entity_id": "entity_id",
        "friendlyname": "friendly_name",
        "friendly_name": "friendly_name",
    }
    need = ["time", "value", "entity_id", "friendly_name", "_measurement", "_field"]
    col_map: dict[str, str] = {}
    for want in need:
        if want in canon:
            col_map[want] = canon[want]
            continue
        for k, w in alias.items():
            if w != want:
                continue
            if k in canon:
                col_map[want] = canon[k]
                break
    return col_map


def _prepare_import_rows(
    path: Path,
    delimiter: str | None,
    tz_name: str | None,
    tz_offset_minutes: int | None,
) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln for ln in (raw or "").splitlines() if ln.strip()]
    data_lines = [ln for ln in lines if not ln.lstrip().startswith("#")]
    if not data_lines:
        raise ValueError("empty file")

    delim = str(delimiter or "").strip()
    if len(delim) != 1:
        delim = _detect_delimiter(_strip_utf8_bom(data_lines[0]))

    header_raw = _strip_utf8_bom(data_lines[0])
    header = next(csv.reader([header_raw], delimiter=delim), [])
    col_map = _import_column_map(header)
    need = ["time", "value", "entity_id", "friendly_name", "_measurement", "_field"]
    missing = [k for k in need if k not in col_map]
    if missing:
        raise ValueError("missing column(s): " + ", ".join(missing))

    reader = csv.DictReader(data_lines, delimiter=delim)
    cols = reader.fieldnames or []
    parsed_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    error_samples: list[dict[str, Any]] = []
    errors: dict[str, int] = {}
    source_measurements: list[str] = []
    source_fields: list[str] = []
    source_entity_ids: list[str] = []
    source_friendly_names: list[str] = []
    issue_counts = {"entity_id": 0, "friendly_name": 0}
    oldest_utc: datetime | None = None
    newest_utc: datetime | None = None

    def add_unique(xs: list[str], value: str) -> None:
        if value and value not in xs:
            xs.append(value)

    for row in reader:
        try:
            t_local = str(row.get(col_map["time"]) or "").strip()
            dt_utc = _parse_ui_local_ts(t_local, tz_name, tz_offset_minutes)
            val_raw = row.get(col_map["value"])
            value = float(val_raw)
            src_measurement = str(row.get(col_map["_measurement"]) or "").strip()
            src_field = str(row.get(col_map["_field"]) or "").strip()
            src_entity = str(row.get(col_map["entity_id"]) or "").strip()
            src_friendly = str(row.get(col_map["friendly_name"]) or "").strip()
            parsed = {
                "time": t_local,
                "dt_utc": dt_utc,
                "value": value,
                "value_raw": str(val_raw or "").strip(),
                "entity_id": src_entity,
                "friendly_name": src_friendly,
                "_measurement": src_measurement,
                "_field": src_field,
            }
            parsed_rows.append(parsed)
            if len(sample_rows) < 3:
                sample_rows.append({k: parsed[k] for k in ("time", "value_raw", "entity_id", "friendly_name", "_measurement", "_field")})
            add_unique(source_measurements, src_measurement)
            add_unique(source_fields, src_field)
            add_unique(source_entity_ids, src_entity)
            add_unique(source_friendly_names, src_friendly)
            if not src_entity:
                issue_counts["entity_id"] = int(issue_counts.get("entity_id", 0) or 0) + 1
            if not src_friendly:
                issue_counts["friendly_name"] = int(issue_counts.get("friendly_name", 0) or 0) + 1
            if oldest_utc is None or dt_utc < oldest_utc:
                oldest_utc = dt_utc
            if newest_utc is None or dt_utc > newest_utc:
                newest_utc = dt_utc
        except Exception as e:
            key = "row"
            msg = str(e)
            if "time" in msg:
                key = "time"
            elif "value" in msg:
                key = "value"
            errors[key] = int(errors.get(key, 0) or 0) + 1
            if len(error_samples) < 3:
                error_samples.append({
                    "reason": key,
                    "time": str(row.get(col_map.get("time", "")) or "").strip(),
                    "value": str(row.get(col_map.get("value", "")) or "").strip(),
                    "raw": {k: row.get(k) for k in list(row.keys())[:10]},
                })

    return {
        "delimiter": delim,
        "columns": cols,
        "column_map": col_map,
        "parsed_rows": parsed_rows,
        "sample": sample_rows,
        "errors": errors,
        "error_samples": error_samples,
        "count": len(parsed_rows),
        "oldest_utc": oldest_utc,
        "newest_utc": newest_utc,
        "source_measurements": source_measurements,
        "source_fields": source_fields,
        "source_entity_ids": source_entity_ids,
        "source_friendly_names": source_friendly_names,
        "issue_counts": issue_counts,
    }


def _build_import_transform_plan(
    cfg: dict[str, Any],
    parsed_rows: list[dict[str, Any]],
    target_measurement: str,
    target_field: str,
    target_entity_id: str | None,
    target_friendly_name: str | None,
) -> dict[str, Any]:
    transforms = _parse_import_measurement_transforms(cfg)
    source_measurements: list[str] = []
    source_fields: list[str] = []
    source_entities: list[str] = []
    source_friendly: list[str] = []
    for row in parsed_rows:
        for xs, key in (
            (source_measurements, "_measurement"),
            (source_fields, "_field"),
            (source_entities, "entity_id"),
            (source_friendly, "friendly_name"),
        ):
            val = str(row.get(key) or "").strip()
            if val and val not in xs:
                xs.append(val)

    measurement_factors: dict[str, float] = {}
    missing_measurement_rules: list[str] = []
    for src in source_measurements:
        if src == target_measurement:
            measurement_factors[src] = 1.0
            continue
        factor = transforms.get((src, target_measurement))
        if factor is None:
            missing_measurement_rules.append(src)
            continue
        measurement_factors[src] = factor

    measurement_status = "ok"
    measurement_message = "Quelle und Ziel sind identisch."
    if missing_measurement_rules:
        measurement_status = "error"
        measurement_message = "Keine Transformationsregel fuer: " + ", ".join(missing_measurement_rules)
    elif any(abs(v - 1.0) > 1e-12 for v in measurement_factors.values()):
        measurement_status = "transform"
        measurement_message = "Transformation mit Faktor aus Einstellungen verfuegbar."

    field_status = "ok"
    field_message = "Quelle und Ziel sind identisch."
    bad_fields = [src for src in source_fields if src != target_field]
    if bad_fields:
        field_status = "error"
        field_message = "Quelle passt nicht zum Ziel-Feld: " + ", ".join(bad_fields)

    entity_status = "ok" if target_entity_id else "warn"
    entity_message = "Wird auf Ziel-entity_id gesetzt." if target_entity_id else "Keine Ziel-entity_id gesetzt - Quellwert bleibt erhalten."
    friendly_status = "ok" if target_friendly_name else "warn"
    friendly_message = "Wird auf Ziel-friendly_name gesetzt." if target_friendly_name else "Kein Ziel-friendly_name gesetzt - Quellwert bleibt erhalten."
    value_status = "ok"
    value_message = "Numerischer Import moeglich."
    if measurement_status == "transform":
        value_status = "transform"
        value_message = "Numerischer Wert wird mit Measurement-Faktor umgerechnet."
    elif measurement_status == "error":
        value_status = "error"
        value_message = "Wert kann ohne Measurement-Transformationsregel nicht sicher umgerechnet werden."

    return {
        "compatible": measurement_status != "error" and field_status != "error",
        "measurement_factors": measurement_factors,
        "source_measurements": source_measurements,
        "source_fields": source_fields,
        "source_entity_ids": source_entities,
        "source_friendly_names": source_friendly,
        "checks": {
            "measurement": {"status": measurement_status, "message": measurement_message, "source": source_measurements, "target": target_measurement},
            "field": {"status": field_status, "message": field_message, "source": source_fields, "target": target_field},
            "entity_id": {"status": entity_status, "message": entity_message, "source": source_entities[:10], "target": target_entity_id},
            "friendly_name": {"status": friendly_status, "message": friendly_message, "source": source_friendly[:10], "target": target_friendly_name},
            "value": {"status": value_status, "message": value_message, "target": target_field},
        },
    }


def _transform_import_preview_rows(
    parsed_rows: list[dict[str, Any]],
    plan: dict[str, Any],
    target_measurement: str,
    target_field: str,
    target_entity_id: str | None,
    target_friendly_name: str | None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    factors = dict(plan.get("measurement_factors") or {})
    for row in parsed_rows[: max(0, int(limit))]:
        src_measurement = str(row.get("_measurement") or "")
        factor = float(factors.get(src_measurement, 1.0) or 1.0)
        value = float(row.get("value") or 0.0) * factor
        out.append({
            "time": row.get("time"),
            "value": value,
            "entity_id": target_entity_id or str(row.get("entity_id") or ""),
            "friendly_name": target_friendly_name or str(row.get("friendly_name") or ""),
            "_measurement": target_measurement,
            "_field": target_field,
            "source_measurement": src_measurement,
            "source_field": row.get("_field"),
            "factor": factor,
        })
    return out


def _flux_range_clause_for_scope(
    scope: str,
    range_key: str,
    start: datetime | None,
    stop: datetime | None,
) -> str:
    s = (scope or "current").strip().lower()
    if s in ("current", "range"):
        return _flux_range_clause(range_key, start, stop)
    if s in ("1y", "1yr", "year"):
        return "|> range(start: -365d)"
    if s in ("inf", "infinite", "all"):
        return '|> range(start: time(v: "1970-01-01T00:00:00Z"))'
    return _flux_range_clause(range_key, start, stop)


def _influxql_time_where(range_key: str, start: datetime | None, stop: datetime | None) -> str:
    if start and stop:
        s = _dt_to_rfc3339_utc(start)
        e = _dt_to_rfc3339_utc(stop)
        return f"time >= '{s}' AND time <= '{e}'"
    rk = (range_key or "").strip().lower()
    if rk in ("all", "alle", "inf", "infinite", "infinity"):
        return "1=1"
    dur = range_to_influxql(range_key)
    return f"time > now() - {dur}"


def _influxql_time_where_for_scope(
    scope: str,
    range_key: str,
    start: datetime | None,
    stop: datetime | None,
) -> str:
    s = (scope or "current").strip().lower()
    if s in ("current", "range"):
        return _influxql_time_where(range_key, start, stop)
    if s in ("1y", "1yr", "year"):
        return "time > now() - 365d"
    if s in ("inf", "infinite", "all"):
        return "1=1"
    return _influxql_time_where(range_key, start, stop)


def _flux_escape(v: str) -> str:
    return (v or "").replace("\\", "\\\\").replace('"', "\\\"")


def _flux_str(v: str) -> str:
    return f'"{_flux_escape(v)}"'


def _short_influx_error(e: Exception) -> str:
    s = str(e) or e.__class__.__name__
    s_l = s.lower()

    # Special-case missing permissions for native v2 backup/restore.
    # Influx CLI needs to read metadata (incl. authorizations) -> requires an all-access token.
    try:
        if ("unauthorized" in s_l or "401" in s_l) and ("read:authorizations" in s_l or "authorizations" in s_l):
            return (
                "401 Unauthorized: Token hat nicht genug Rechte fuer Native v2 FullBackup/FullRestore (metadata).\n"
                "Loesung: In InfluxDB einen All-Access Token fuer die Org erstellen und in InfluxBro unter "
                "Einstellungen -> InfluxDB v2 -> admin_token speichern.\n\n"
                f"Original: {s}"
            )
    except Exception:
        pass

    def _is_timeout(x: object) -> bool:
        try:
            if isinstance(x, TimeoutError):
                return True
        except Exception:
            pass
        try:
            msg = (str(x) or "").lower()
        except Exception:
            msg = ""
        return ("read timed out" in msg) or ("timed out" in msg) or ("timeout" in msg)

    # Special-case timeouts with a helpful hint.
    try:
        if _is_timeout(e) or _is_timeout(getattr(e, "__cause__", None)) or _is_timeout(getattr(e, "__context__", None)):
            try:
                cfg = _overlay_from_yaml_if_enabled(load_cfg())
                host = str(cfg.get("host") or "").strip()
                port = int(cfg.get("port") or 8086)
                timeout_s = int(cfg.get("timeout_seconds") or 10)
                target = (f"{host}:{port}" if host else "InfluxDB")
                return (
                    f"Timeout beim Zugriff auf {target} nach {timeout_s}s. "
                    "Tipp: Einstellungen -> Verbindung -> timeout_seconds erhoehen (z.B. 30/60) "
                    "oder Zeitraum reduzieren.\n\n"
                    f"Original: {s}"
                )
            except Exception:
                return (
                    "Timeout beim Zugriff auf InfluxDB. Tipp: timeout_seconds erhoehen oder Zeitraum reduzieren.\n\n"
                    f"Original: {s}"
                )
    except Exception:
        pass

    # Special-case server panic strings (InfluxDB internal error).
    try:
        if "panic:" in s_l:
            return "InfluxDB interner Fehler (panic). Bitte InfluxDB Logs pruefen.\n\n" + s
    except Exception:
        pass

    # Try to extract the JSON {"message":"..."} part from influxdb-client exception strings.
    m = re.search(r'"message"\s*:\s*"((?:\\.|[^"])*)"', s)
    if m:
        raw = m.group(1)
        try:
            # Unescape JSON string content (handles embedded \" quotes correctly).
            return json.loads('"' + raw + '"')
        except Exception:
            return raw
    return s


def flux_tag_filter(entity_id: str | None, friendly_name: str | None) -> str:
    extra = ""
    if entity_id:
        extra += f" and r.entity_id == {_flux_str(entity_id)}"
    if friendly_name:
        extra += f" and r.friendly_name == {_flux_str(friendly_name)}"
    return extra


def _influxql_escape(v: str) -> str:
    return (v or "").replace("\\", "\\\\").replace("'", "\\'")


def influxql_tag_filter(entity_id: str | None, friendly_name: str | None) -> str:
    out = ""
    if entity_id:
        out += f' AND "entity_id"=\'{_influxql_escape(entity_id)}\''
    if friendly_name:
        out += f' AND "friendly_name"=\'{_influxql_escape(friendly_name)}\''
    return out


def _influx_url(cfg: dict) -> str:
    return cfg.get("url") or f'{cfg.get("scheme","http")}://{cfg.get("host","localhost")}:{int(cfg.get("port",8086))}'


def _influx_cli_env(cfg: dict, *, token: str) -> dict[str, str]:
    env = dict(os.environ)
    env["INFLUX_HOST"] = _influx_url(cfg)
    env["INFLUX_ORG"] = str(cfg.get("org") or "")
    env["INFLUX_TOKEN"] = str(token or "")
    if not bool(cfg.get("verify_ssl", True)):
        env["INFLUX_SKIP_VERIFY"] = "true"
    return env


def _ha_platform() -> str:
    """Return the Home Assistant build platform (BUILD_ARCH) if available."""

    v = str(os.environ.get("INFLUXBRO_BUILD_ARCH") or os.environ.get("BUILD_ARCH") or "").strip()
    if v:
        return v

    # Fallback (container runtime arch, best-effort).
    try:
        return str(getattr(os.uname(), "machine", "") or "").strip() or "unknown"
    except Exception:
        return "unknown"


def _influx_cli_available() -> bool:
    try:
        return shutil.which("influx") is not None
    except Exception:
        return False


@contextmanager
def v2_admin_client(cfg: dict, timeout_seconds_override: int | None = None):
    """Context-managed InfluxDB v2 client using admin_token (if present)."""

    token = str(cfg.get("admin_token") or "").strip() or str(cfg.get("token") or "").strip()
    url = _influx_url(cfg)
    org = cfg.get("org")
    ts = timeout_seconds_override if timeout_seconds_override is not None else int(cfg.get("timeout_seconds", 10))
    timeout_ms = int(ts) * 1000
    verify_ssl = bool(cfg.get("verify_ssl", True))
    client = InfluxDBClient(url=url, token=token, org=org, timeout=timeout_ms, verify_ssl=verify_ssl)
    try:
        yield client
    finally:
        try:
            client.close()
        except Exception:
            pass


@contextmanager
def v2_client(cfg: dict, timeout_seconds_override: int | None = None):
    """Context-managed InfluxDB v2 client."""
    url = _influx_url(cfg)
    token = cfg.get("token")
    org = cfg.get("org")
    ts = timeout_seconds_override if timeout_seconds_override is not None else int(cfg.get("timeout_seconds", 10))
    timeout_ms = int(ts) * 1000
    verify_ssl = bool(cfg.get("verify_ssl", True))

    client = InfluxDBClient(url=url, token=token, org=org, timeout=timeout_ms, verify_ssl=verify_ssl)
    try:
        yield client
    finally:
        try:
            client.close()
        except Exception:
            pass


def v1_client(cfg: dict):
    """Create an InfluxDB v1 client (caller is responsible for closing if needed)."""
    host = cfg.get("host", "localhost")
    port = int(cfg.get("port", 8086))
    username = cfg.get("username") or None
    password = cfg.get("password") or None
    database = cfg.get("database") or None
    ssl = (cfg.get("scheme") == "https")
    verify_ssl = bool(cfg.get("verify_ssl", True))

    return InfluxDBClientV1(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        ssl=ssl,
        verify_ssl=verify_ssl,
        timeout=int(cfg.get("timeout_seconds", 10)),
    )
    
def _initial_suggestions(cfg: dict[str, Any]) -> dict[str, list[str]]:
    suggestions: dict[str, list[str]] = {"measurements": [], "friendly_name": [], "entity_id": []}
    try:
        cfg_eff = _overlay_from_yaml_if_enabled(cfg)
        if int(cfg_eff.get("influx_version", 2)) != 2:
            return suggestions
        if not (cfg_eff.get("token") and cfg_eff.get("org") and cfg_eff.get("bucket")):
            return suggestions
        with v2_client(cfg_eff) as c:
            qapi = c.query_api()

            qm = f'import "influxdata/influxdb/schema"\nschema.measurements(bucket: "{cfg_eff["bucket"]}")'
            ms = []
            for t in qapi.query(qm, org=cfg_eff["org"]):
                for r in t.records:
                    ms.append(str(r.get_value()))
            suggestions["measurements"] = sorted(set(ms))

            for tag in ("friendly_name", "entity_id"):
                q = f'import "influxdata/influxdb/schema"\nschema.tagValues(bucket: "{cfg_eff["bucket"]}", tag: "{tag}", start: -30d)'
                vals = []
                for t in qapi.query(q, org=cfg_eff["org"]):
                    for r in t.records:
                        vals.append(str(r.get_value()))
                suggestions[tag] = sorted(set(vals))
    except Exception:
        return {"measurements": [], "friendly_name": [], "entity_id": []}
    return suggestions


@app.get("/")
def index():
    cfg = load_cfg()
    suggestions = _initial_suggestions(cfg)

    return render_template(
        "index.html",
        cfg=cfg,
        allow_delete=True,
        nav="dashboard",
        suggestions=suggestions,
    )


@app.get("/stats")
def stats_page():
    cfg = load_cfg()
    return render_template("stats.html", cfg=cfg, allow_delete=True, nav="stats", suggestions=_initial_suggestions(cfg))


@app.get("/quality")
def quality_page():
    cfg = load_cfg()
    return render_template("quality.html", cfg=cfg, allow_delete=True, nav="quality")


@app.get("/logs")
def logs_page():
    cfg = load_cfg()
    return render_template("logs.html", cfg=cfg, allow_delete=True, nav="logs")


@app.get("/performance")
def performance_page():
    cfg = load_cfg()
    return render_template("performance.html", cfg=cfg, allow_delete=True, nav="performance")


@app.get("/jobs")
def jobs_page():
    cfg = load_cfg()
    return render_template("jobs.html", cfg=cfg, allow_delete=True, nav="jobs")


@app.get("/history")
def history_page():
    cfg = load_cfg()
    return render_template(
        "history.html",
        cfg=cfg,
        allow_delete=True,
        nav="history",
    )


@app.get("/monitor")
def monitor_page():
    cfg = load_cfg()
    return render_template(
        "monitor.html",
        cfg=cfg,
        allow_delete=True,
        nav="monitor",
    )


@app.get("/backup")
def backup_page():
    cfg = load_cfg()
    return render_template("backup.html", cfg=cfg, allow_delete=True, nav="backup")


@app.get("/restore")
def restore_page():
    cfg = load_cfg()
    return render_template(
        "restore.html",
        cfg=cfg,
        allow_delete=True,
        nav="restore",
    )


@app.get("/combine")
def combine_page():
    cfg = load_cfg()
    return render_template("combine.html", cfg=cfg, allow_delete=True, nav="combine")


@app.get("/export")
def export_page():
    cfg = load_cfg()
    return render_template("export.html", cfg=cfg, allow_delete=True, nav="export", suggestions=_initial_suggestions(cfg))


@app.get("/import")
def import_page():
    cfg = load_cfg()
    return render_template(
        "import.html",
        cfg=cfg,
        allow_delete=True,
        nav="import",
    )


@app.get("/info")
def info_page():
    cfg = load_cfg()
    changelog = ""
    try:
        changelog = (APP_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    except Exception:
        changelog = ""
    return render_template(
        "info.html",
        cfg=cfg,
        allow_delete=True,
        nav="changelog",
        repo_url=FIXED_REPO_URL,
        changelog_text=changelog,
    )


@app.get("/dbinfo")
def dbinfo_page():
    cfg = load_cfg()
    return render_template(
        "dbinfo.html",
        cfg=cfg,
        allow_delete=True,
        nav="dbinfo",
        repo_url=FIXED_REPO_URL,
    )


@app.get("/manual")
def manual_page():
    cfg = load_cfg()
    manual = ""
    try:
        manual = (APP_DIR / "MANUAL.md").read_text(encoding="utf-8")
    except Exception:
        manual = ""
    return render_template(
        "manual.html",
        cfg=cfg,
        allow_delete=True,
        nav="manual",
        manual_text=manual,
    )


@app.get("/api/manual_asset")
def manual_asset():
    rel = str(request.args.get("path") or "").strip()
    if not rel:
        return jsonify({"ok": False, "error": "path required"}), 400

    addon_root = APP_DIR.parent.resolve()
    images_root = (addon_root / "images").resolve()
    target = (addon_root / rel).resolve()

    try:
        target.relative_to(images_root)
    except Exception:
        LOG.warning("manual_asset blocked path=%s", rel)
        abort(404)

    if not target.is_file():
        LOG.warning("manual_asset missing path=%s", rel)
        abort(404)

    return send_file(target)


@app.get("/profiles")
def profiles_page():
    cfg = load_cfg()
    return render_template("profiles.html", cfg=cfg, allow_delete=True, nav="profiles")

@app.get("/config")
def config_page():
    cfg = load_cfg()
    return render_template(
        "config.html",
        cfg=cfg,
        allow_delete=True,
        autodetect_source=LAST_AUTODETECT_SOURCE,
        nav="settings",
    )


@app.post("/api/load_influx_yaml")
def api_load_influx_yaml():
    """
    Load InfluxDB settings from a specific Home Assistant YAML config file (default: /config/homeassistant/influx.yaml).

    Does NOT persist anything. UI must call /api/config (POST) to save.
    """
    body = request.get_json(force=True) or {}
    cfg = load_cfg()
    path_str = (body.get("influx_yaml_path") or cfg.get("influx_yaml_path") or DEFAULT_INFLUX_YAML_PATH).strip()

    detected, src = load_influx_yaml(path_str)
    if not detected:
        detail = f" ({LAST_YAML_ERROR})" if LAST_YAML_ERROR else ""
        return jsonify({"ok": False, "error": f"Keine influx.yaml gefunden/lesbar unter: {path_str}{detail}", "source": None, "config": None})

    # Remember last source for UI display (runtime only)
    global LAST_AUTODETECT_SOURCE
    LAST_AUTODETECT_SOURCE = src

    # Enable YAML fallback for this runtime session (explicit user action)
    global YAML_FALLBACK_ENABLED
    YAML_FALLBACK_ENABLED = True

    return jsonify({"ok": True, "source": src, "config": detected})


@app.get("/api/find_influx_yaml")
def api_find_influx_yaml():
    best, matches = find_influx_yaml()
    if not best:
        return jsonify({"ok": False, "error": "Keine influx.yaml unter /config gefunden.", "path": None, "matches": []})

    # Remember last source for UI display (runtime only)
    global LAST_AUTODETECT_SOURCE
    LAST_AUTODETECT_SOURCE = str(_resolve_cfg_path(best))

    return jsonify({"ok": True, "path": best, "matches": matches, "resolved": LAST_AUTODETECT_SOURCE})

@app.get("/api/config")
def api_get_config():
    cfg = load_cfg()
    redacted = dict(cfg)
    if redacted.get("token"):
        redacted["token"] = "********"
    if redacted.get("admin_token"):
        redacted["admin_token"] = "********"
    if redacted.get("password"):
        redacted["password"] = "********"
    return jsonify({
        "ok": True,
        "config": redacted,
        # Backward-compat keys; writes are always enabled.
        "allow_delete": True,
        "writes_enabled": True,
        "autodetect_source": LAST_AUTODETECT_SOURCE,
    })


@app.get("/api/config_defaults")
def api_get_config_defaults():
    """Returns DEFAULT_CFG for UI (without secrets)."""

    defaults = dict(DEFAULT_CFG)
    defaults["token"] = ""
    defaults["admin_token"] = ""
    defaults["password"] = ""
    return jsonify({"ok": True, "defaults": defaults})


def _api_doc_group(path: str) -> tuple[str, str, str, str]:
    """Returns (group, role, role_label, role_color_cssvar) for an API path."""

    p = str(path or "")
    if p.startswith("/api/backup") or p.startswith("/api/fullbackup") or p.startswith("/api/restore") or p.startswith("/api/backups"):
        return ("Backup/Restore", "system", "\U0001F4E6 Backup", "var(--orange)")
    if p.startswith("/api/cache/") or p.startswith("/api/stats_cache") or p.startswith("/api/dash_cache"):
        return ("Cache", "analysis", "\U0001F9E0 Cache", "var(--cyan)")
    if p.startswith("/api/analysis_cache/") or p.startswith("/api/analysis") or p.startswith("/api/outlier"):
        return ("Analyse", "analysis", "\U0001F50D Analyse", "var(--cyan)")
    if p.startswith("/api/trace") or p.startswith("/api/perf"):
        return ("Tracing", "tracking", "\U0001F4CA Trace", "var(--green)")
    if p.startswith("/api/ui_") or p.startswith("/api/ui") or p.startswith("/api/client"):
        return ("UI/Client", "tracking", "\U0001F5A5\uFE0F UI", "var(--green)")
    if p.startswith("/api/sys") or p.startswith("/api/storage"):
        return ("System", "system", "\U0001F5A5\uFE0F System", "var(--orange)")
    if p.startswith("/api/config"):
        return ("Konfiguration", "system", "\u2699\uFE0F Config", "var(--orange)")
    if p.startswith("/api/import") or p.startswith("/api/export"):
        return ("Import/Export", "system", "\U0001F4E4 I/O", "var(--orange)")
    return ("API", "query", "\U0001F517 API", "var(--accent)")


def _api_doc_summary(method: str, path: str) -> str:
    m = str(method or "").upper()
    p = str(path or "")
    if m == "GET":
        return f"Liest Daten/Status fuer {p}."
    if m == "POST":
        return f"Fuehrt eine Aktion aus oder berechnet Daten fuer {p}."
    if m == "DELETE":
        return f"Loescht Ressource(n) unter {p}."
    if m == "PUT":
        return f"Aktualisiert Ressource(n) unter {p}."
    return f"Endpoint {m} {p}."


def _api_doc_description(method: str, path: str, keys_body: list[str], keys_args: list[str]) -> str:
    """Generate a beginner-friendly + pro-friendly description from code hints."""

    m = str(method or "").upper()
    p = str(path or "")
    group, role, role_label, _ = _api_doc_group(p)
    body = ", ".join([f"<code>{k}</code>" for k in keys_body[:8]])
    args = ", ".join([f"<code>{k}</code>" for k in keys_args[:8]])
    intro = (
        f"<strong>Einsteiger:</strong> Dieser Endpoint gehoert zur Gruppe <strong>{group}</strong> und macht "
        f"eine klar abgegrenzte Teilaufgabe (wie ein Werkzeug im Werkzeugkasten)."
    )
    pro = (
        f"<strong>Profi:</strong> {role_label} ({role}) Handler fuer <code>{m} {p}</code>. "
        f"Die Antwort ist typischerweise ein JSON-Envelope mit <code>ok</code> sowie endpoint-spezifischen Daten."
    )
    hints = []
    if keys_args:
        hints.append(f"Query-Parameter (gesehen im Code): {args}.")
    if keys_body and m in ("POST", "PUT", "DELETE"):
        hints.append(f"JSON-Body-Felder (gesehen im Code): {body}.")
    if not hints:
        hints.append("Keine Parameter/Keys konnten automatisch aus dem Code extrahiert werden.")
    return intro + "<br>" + pro + "<br>" + " ".join(hints)


def _extract_keys_from_source(src: str) -> tuple[list[str], list[str]]:
    """Best-effort extraction of request body / query arg keys from handler source."""

    try:
        s = str(src or "")
    except Exception:
        return ([], [])

    # body.get("...")
    body_keys = []
    try:
        for m in re.finditer(r"\bbody\.get\(\s*['\"]([^'\"]+)['\"]", s):
            body_keys.append(m.group(1))
    except Exception:
        body_keys = []

    # request.args.get("...")
    args_keys = []
    try:
        for m in re.finditer(r"\brequest\.args\.get\(\s*['\"]([^'\"]+)['\"]", s):
            args_keys.append(m.group(1))
    except Exception:
        args_keys = []

    def _uniq(xs: list[str]) -> list[str]:
        out: list[str] = []
        seen = set()
        for x in xs:
            k = str(x or "").strip()
            if not k or k in seen:
                continue
            seen.add(k)
            out.append(k)
        return out

    return (_uniq(body_keys), _uniq(args_keys))


@app.get("/api/api_docs")
def api_api_docs():
    """Returns best-effort API docs for all registered /api routes."""

    allowed = {"GET", "POST", "PUT", "DELETE"}
    routes: list[dict[str, Any]] = []
    for rule in app.url_map.iter_rules():
        try:
            path = str(rule.rule)
            if not path.startswith("/api/"):
                continue
            if path.startswith("/api/static"):
                continue
            methods = sorted([m for m in (rule.methods or set()) if m in allowed])
            if not methods:
                continue
            routes.append({
                "path": path,
                "methods": methods,
                "endpoint": str(rule.endpoint or ""),
            })
        except Exception:
            continue

    docs: list[dict[str, Any]] = []
    for r in sorted(routes, key=lambda x: (x.get("path") or "", ",".join(x.get("methods") or []))):
        path = str(r.get("path") or "")
        endpoint_name = str(r.get("endpoint") or "")
        fn = app.view_functions.get(endpoint_name)
        src = ""
        try:
            if fn:
                src = inspect.getsource(fn)
        except Exception:
            src = ""
        keys_body, keys_args = _extract_keys_from_source(src)

        for method in r.get("methods") or []:
            group, role, role_label, role_color = _api_doc_group(path)
            doc_id = (f"{str(method).lower()}-" + path.strip("/").replace("/", "-")).replace("--", "-")
            docs.append({
                "id": doc_id,
                "method": method,
                "path": path,
                "summary": _api_doc_summary(method, path),
                "description": _api_doc_description(method, path, keys_body, keys_args),
                "group": group,
                "tags": [role, group.lower().replace("/", "-"), str(method).lower()],
                "role": role,
                "roleLabel": role_label,
                "roleColor": role_color,
                "authRequired": False,
                "request": {
                    "contentType": "application/json" if str(method).upper() in ("POST", "PUT", "DELETE") else "(none)",
                    "queryKeys": keys_args,
                    "bodyKeys": keys_body,
                },
                "response": {
                    "contentType": "application/json",
                    "statusCodes": [
                        {"code": 200, "desc": "ok"},
                        {"code": 400, "desc": "Request/Parameter Fehler"},
                        {"code": 500, "desc": "Interner Fehler"},
                    ],
                },
            })

    routes_method_count = 0
    try:
        routes_method_count = sum(len(r.get("methods") or []) for r in routes)
    except Exception:
        routes_method_count = len(docs)

    return jsonify({
        "ok": True,
        "docs": docs,
        "routes_count": int(routes_method_count),
        "docs_count": int(len(docs)),
    })


@app.get("/api/config_export")
def api_config_export():
    """Exports the current settings as a JSON file."""

    cfg = load_cfg()
    txt = json.dumps(cfg, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    resp = make_response(txt)
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=\"influxbro_settings.json\""
    return resp


@app.get("/api/influx_admin_test")
def api_influx_admin_test():
    """Best-effort test whether the configured admin_token has sufficient rights.

    Returns ok:true when a minimal authorizations call succeeds, otherwise an error message.
    """
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    admin_token = str(cfg.get("admin_token") or "").strip()
    if not admin_token:
        return jsonify({"ok": False, "error": "admin_token missing in settings"}), 400

    try:
        with v2_admin_client(cfg, timeout_seconds_override=min(8, int(cfg.get("timeout_seconds") or 10))) as c:
            try:
                # Do a minimal authorizations call; avoid passing params for broad compatibility.
                c.authorizations_api().find_authorizations()  # type: ignore[attr-defined]
            except Exception as e:
                try:
                    LOG.warning("influx_admin_test_failed err=%s", _short_influx_error(e))
                except Exception:
                    pass
                return jsonify({"ok": False, "error": _short_influx_error(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 400

    return jsonify({"ok": True})


def _resolve_host_ip(host: str) -> str | None:
    h = (host or "").strip()
    if not h:
        return None
    try:
        return socket.gethostbyname(h)
    except Exception:
        return None


def _http_get_json(url: str, verify_ssl: bool, timeout_s: int) -> tuple[int, dict[str, Any] | None, str | None]:
    """Best-effort JSON GET; returns (status, json, error)."""

    req = urllib.request.Request(url, method="GET")
    ctx = None
    try:
        if url.lower().startswith("https://") and not verify_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
    except Exception:
        ctx = None

    try:
        with urllib.request.urlopen(req, timeout=timeout_s, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = int(getattr(resp, "status", 200))
            try:
                data = json.loads(raw) if raw else None
            except Exception:
                data = None
            return status, data if isinstance(data, dict) else None, None
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return int(getattr(e, "code", 0) or 0), None, body or (str(e) or "HTTPError")
    except Exception as e:
        return 0, None, str(e) or e.__class__.__name__


def _http_get_text(url: str, verify_ssl: bool, timeout_s: int) -> tuple[int, str | None, str | None]:
    """Best-effort text GET; returns (status, text, error)."""

    req = urllib.request.Request(url, method="GET")
    ctx = None
    try:
        if url.lower().startswith("https://") and not verify_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
    except Exception:
        ctx = None

    try:
        with urllib.request.urlopen(req, timeout=timeout_s, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = int(getattr(resp, "status", 200))
            return status, raw, None
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return int(getattr(e, "code", 0) or 0), None, body or (str(e) or "HTTPError")
    except Exception as e:
        return 0, None, str(e) or e.__class__.__name__


@app.get("/api/influx_info")
def api_influx_info():
    """Return best-effort diagnostics about the configured InfluxDB."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    scheme = str(cfg.get("scheme") or "http").strip() or "http"
    host = str(cfg.get("host") or "").strip()
    port = int(cfg.get("port") or 8086)
    verify_ssl = bool(cfg.get("verify_ssl", True))
    timeout_s = int(cfg.get("timeout_seconds") or 10)
    base_url = str(cfg.get("url") or f"{scheme}://{host}:{port}").strip()

    info: dict[str, Any] = {
        "url": base_url,
        "host": host,
        "ip": _resolve_host_ip(host),
        "verify_ssl": verify_ssl,
        "timeout_seconds": timeout_s,
        "influx_version": None,
        "health": None,
        "health_http_status": None,
        "health_error": None,
        "bucket_count": None,
        "database_count": None,
        "ha_database": (cfg.get("bucket") if int(cfg.get("influx_version", 2)) == 2 else cfg.get("database")) or None,
        "note": "Hinweis: Speicherplatz/Freiplatz/Memory der InfluxDB sind ueber die Influx HTTP API nicht verlaesslich abrufbar. Anzeige ist best-effort.",
    }

    # Health endpoint (v2 + some v1 builds)
    try:
        st, js, err = _http_get_json(base_url.rstrip("/") + "/health", verify_ssl=verify_ssl, timeout_s=min(8, timeout_s))
        info["health_http_status"] = int(st) if st else None
        if js:
            info["health"] = str(js.get("status") or "") or (f"HTTP {st}" if st else None)
            info["influx_version"] = str(js.get("version") or js.get("build") or "") or None
        elif err:
            info["health"] = (f"HTTP {st}" if st else None) or ""
            info["health_error"] = str(err)
    except Exception:
        pass

    # Buckets (InfluxDB v2)
    try:
        if int(cfg.get("influx_version", 2)) == 2 and cfg.get("token") and cfg.get("org") and cfg.get("bucket"):
            with v2_client(cfg, timeout_seconds_override=min(8, timeout_s)) as c:
                b = c.buckets_api().find_buckets(org=cfg.get("org"))
                buckets = getattr(b, "buckets", None) or []
                info["bucket_count"] = int(len(buckets))
    except Exception:
        info["bucket_count"] = None

    # Databases (InfluxDB v1)
    try:
        if int(cfg.get("influx_version", 2)) != 2 and cfg.get("database"):
            c = v1_client(cfg)
            res = c.query("SHOW DATABASES")
            dbs = []
            try:
                for _, points in res.items():
                    for p in points:
                        n = p.get("name")
                        if n:
                            dbs.append(str(n))
            except Exception:
                dbs = []
            info["database_count"] = int(len(dbs)) if dbs else None
    except Exception:
        info["database_count"] = None

    return jsonify({"ok": True, "info": info})


@app.get("/api/influx_metrics")
def api_influx_metrics():
    """Best-effort Prometheus metrics from InfluxDB (/metrics).

    This endpoint intentionally returns only a small KPI subset.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    scheme = str(cfg.get("scheme") or "http").strip() or "http"
    host = str(cfg.get("host") or "").strip()
    port = int(cfg.get("port") or 8086)
    verify_ssl = bool(cfg.get("verify_ssl", True))
    timeout_s = int(cfg.get("timeout_seconds") or 10)
    base_url = str(cfg.get("url") or f"{scheme}://{host}:{port}").strip()
    url = base_url.rstrip("/") + "/metrics"

    st, raw, err = _http_get_text(url, verify_ssl=verify_ssl, timeout_s=min(8, timeout_s))
    if not raw:
        return jsonify({
            "ok": False,
            "error": (str(err) if err else (f"HTTP {st}" if st else "unavailable")),
            "status": int(st) if st else None,
        }), 502

    # Parse a few known Go/Influx metrics.
    want_scalar = {
        "go_goroutines",
        "go_memstats_alloc_bytes",
        "go_memstats_heap_inuse_bytes",
        "go_memstats_heap_idle_bytes",
        "go_memstats_next_gc_bytes",
        "go_gc_duration_seconds_sum",
        "go_gc_duration_seconds_count",
    }
    scalars: dict[str, float] = {}
    gc_p99_s = None

    # best-effort request counters
    req_total = 0.0
    req_seen = False

    line_re = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+([-+0-9.eE]+)")
    for ln in (raw or "").splitlines():
        s = (ln or "").strip()
        if not s or s.startswith("#"):
            continue
        m = line_re.match(s)
        if not m:
            continue
        name = m.group(1)
        labels = m.group(2) or ""
        v_raw = m.group(3)
        try:
            val = float(v_raw)
        except Exception:
            continue

        if name in want_scalar and not labels:
            scalars[name] = val
            continue

        # go_gc_duration_seconds{quantile="0.99"}
        if name == "go_gc_duration_seconds" and "quantile=\"0.99\"" in labels:
            gc_p99_s = val
            continue

        # InfluxDB request counters are not stable across versions; sum a few common names.
        if name in ("influxdb_http_api_requests_total", "http_requests_total"):
            req_total += val
            req_seen = True

    # Derived KPIs
    gc_avg_ms = None
    try:
        ssum = float(scalars.get("go_gc_duration_seconds_sum") or 0.0)
        cnt = float(scalars.get("go_gc_duration_seconds_count") or 0.0)
        if cnt > 0:
            gc_avg_ms = (ssum / cnt) * 1000.0
    except Exception:
        gc_avg_ms = None

    out = {
        "ok": True,
        "status": int(st) if st else None,
        "kpi": {
            "goroutines": int(scalars.get("go_goroutines")) if "go_goroutines" in scalars else None,
            "ram_alloc_bytes": int(scalars.get("go_memstats_alloc_bytes")) if "go_memstats_alloc_bytes" in scalars else None,
            "heap_inuse_bytes": int(scalars.get("go_memstats_heap_inuse_bytes")) if "go_memstats_heap_inuse_bytes" in scalars else None,
            "heap_idle_bytes": int(scalars.get("go_memstats_heap_idle_bytes")) if "go_memstats_heap_idle_bytes" in scalars else None,
            "next_gc_bytes": int(scalars.get("go_memstats_next_gc_bytes")) if "go_memstats_next_gc_bytes" in scalars else None,
            "gc_pause_avg_ms": gc_avg_ms,
            "gc_pause_p99_ms": (float(gc_p99_s) * 1000.0) if gc_p99_s is not None else None,
            "gc_runs": int(scalars.get("go_gc_duration_seconds_count")) if "go_gc_duration_seconds_count" in scalars else None,
            "http_requests_total": int(req_total) if req_seen else None,
        },
    }
    return jsonify(out)


@app.get("/api/v2/buckets")
def api_v2_buckets():
    """Return bucket names for InfluxDB v2 (best-effort)."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    try:
        influx_v = int(cfg.get("influx_version", 2) or 2)
    except Exception:
        influx_v = 2
    if influx_v != 2:
        return jsonify({"ok": False, "error": "influx_version must be 2"}), 400

    org = str(cfg.get("org") or "").strip()
    if not org:
        return jsonify({"ok": False, "error": "org required"}), 400

    token = str(cfg.get("admin_token") or cfg.get("token") or "").strip()
    if not token:
        return jsonify({"ok": False, "error": "token required"}), 400

    try:
        with v2_admin_client(cfg, timeout_seconds_override=min(10, int(cfg.get("timeout_seconds") or 10))) as c:
            b = c.buckets_api().find_buckets(org=org)
            buckets = getattr(b, "buckets", None) or []
            names = []
            for buck in buckets:
                try:
                    n = str(getattr(buck, "name", "") or "").strip()
                    if n:
                        names.append(n)
                except Exception:
                    continue
            names = sorted(set(names))
            return jsonify({"ok": True, "buckets": names})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


def _quality_default_rules() -> list[dict[str, Any]]:
    return [
        {
            "enabled": True,
            "pattern": "sensor.*_energy*",
            "type": "counter",
            "min": 0,
            "max": None,
            "max_delta": 30,
            "invalid_policy": "carry_last",
            "reset_allowed": False,
            "rollup": True,
            "rollup_levels": "15m,1h,1d",
        },
        {
            "enabled": True,
            "pattern": "sensor.*power*",
            "type": "gauge",
            "min": 0,
            "max": 30000,
            "max_delta": 30000,
            "invalid_policy": "drop",
            "reset_allowed": False,
            "rollup": True,
            "rollup_levels": "15m,1h",
        },
        {
            "enabled": True,
            "pattern": "binary_sensor.*",
            "type": "binary",
            "min": None,
            "max": None,
            "max_delta": None,
            "invalid_policy": "drop",
            "reset_allowed": False,
            "rollup": True,
            "rollup_levels": "1h,1d",
        },
    ]


def _quality_default_rollup_levels() -> list[dict[str, Any]]:
    return [
        {"name": "15m", "source_after_days": 30, "every": "1h", "window": "15m", "mode_counter": "last", "mode_gauge": "mean"},
        {"name": "1h", "source_after_days": 90, "every": "6h", "window": "1h", "mode_counter": "last", "mode_gauge": "mean"},
        {"name": "1d", "source_after_days": 365, "every": "24h", "window": "1d", "mode_counter": "last", "mode_gauge": "mean"},
    ]


def _quality_parse_json_or_default(raw: str, default: Any) -> Any:
    try:
        txt = str(raw or "").strip()
        if not txt:
            return default
        val = json.loads(txt)
        return val if isinstance(val, type(default)) else default
    except Exception:
        return default


def _quality_cfg_view(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_bucket": str(cfg.get("quality_raw_bucket") or DEFAULT_CFG["quality_raw_bucket"]),
        "clean_bucket": str(cfg.get("quality_clean_bucket") or DEFAULT_CFG["quality_clean_bucket"]),
        "rollup_bucket": str(cfg.get("quality_rollup_bucket") or DEFAULT_CFG["quality_rollup_bucket"]),
        "retention_raw_days": int(cfg.get("quality_retention_raw_days") or DEFAULT_CFG["quality_retention_raw_days"]),
        "retention_clean_days": int(cfg.get("quality_retention_clean_days") or DEFAULT_CFG["quality_retention_clean_days"]),
        "retention_rollup_days": int(cfg.get("quality_retention_rollup_days") or DEFAULT_CFG["quality_retention_rollup_days"]),
        "timezone": str(cfg.get("quality_timezone") or DEFAULT_CFG["quality_timezone"]),
        "lateness_minutes": int(cfg.get("quality_lateness_minutes") or DEFAULT_CFG["quality_lateness_minutes"]),
        "auto_create_buckets": bool(cfg.get("quality_auto_create_buckets", True)),
        "auto_create_tasks": bool(cfg.get("quality_auto_create_tasks", False)),
        "rules": _quality_parse_json_or_default(cfg.get("quality_rules_json") or "", _quality_default_rules()),
        "rollups": _quality_parse_json_or_default(cfg.get("quality_rollup_levels_json") or "", _quality_default_rollup_levels()),
        "cleanup_plan": _quality_parse_json_or_default(cfg.get("quality_cleanup_plan_json") or "", {}),
    }


def _quality_influx_request(cfg: dict[str, Any], method: str, path: str, payload: Any | None = None) -> tuple[int, Any]:
    token = str(cfg.get("admin_token") or cfg.get("token") or "").strip()
    if not token:
        raise RuntimeError("token required")
    url = _influx_url(cfg).rstrip("/") + path
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, headers=headers, method=method.upper(), data=data)
    try:
        with urllib.request.urlopen(req, timeout=min(20, int(cfg.get("timeout_seconds") or 10))) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = int(getattr(resp, "status", 200) or 200)
            try:
                return status, json.loads(raw) if raw else {}
            except Exception:
                return status, raw
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        try:
            return int(getattr(e, "code", 0) or 0), json.loads(body) if body else {}
        except Exception:
            return int(getattr(e, "code", 0) or 0), body


def _quality_org_id(cfg: dict[str, Any]) -> str:
    org = str(cfg.get("org") or "").strip()
    if not org:
        raise RuntimeError("org required")
    st, js = _quality_influx_request(cfg, "GET", "/api/v2/orgs?org=" + urllib.parse.quote(org))
    orgs = js.get("orgs") if isinstance(js, dict) else None
    if st < 200 or st >= 300 or not isinstance(orgs, list) or not orgs:
        raise RuntimeError("org lookup failed")
    oid = str((orgs[0] or {}).get("id") or "").strip()
    if not oid:
        raise RuntimeError("org id missing")
    return oid


def _quality_bucket_retention(days: int) -> list[dict[str, Any]]:
    try:
        d = int(days or 0)
    except Exception:
        d = 0
    if d <= 0:
        return []
    return [{"type": "expire", "everySeconds": int(d) * 86400}]


def _quality_bucket_specs(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    q = _quality_cfg_view(cfg)
    return [
        {"name": q["raw_bucket"], "retention_days": q["retention_raw_days"], "kind": "raw"},
        {"name": q["clean_bucket"], "retention_days": q["retention_clean_days"], "kind": "clean"},
        {"name": q["rollup_bucket"], "retention_days": q["retention_rollup_days"], "kind": "rollup"},
    ]


def _quality_list_buckets(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    org = str(cfg.get("org") or "").strip()
    st, js = _quality_influx_request(cfg, "GET", "/api/v2/buckets?org=" + urllib.parse.quote(org))
    if st < 200 or st >= 300 or not isinstance(js, dict):
        raise RuntimeError("bucket listing failed")
    out = []
    for item in js.get("buckets") or []:
        if not isinstance(item, dict):
            continue
        rules = item.get("retentionRules") if isinstance(item.get("retentionRules"), list) else []
        days = None
        try:
            if rules:
                every = int((rules[0] or {}).get("everySeconds") or 0)
                days = int(round(every / 86400)) if every > 0 else None
        except Exception:
            days = None
        out.append({"id": str(item.get("id") or ""), "name": str(item.get("name") or ""), "retention_days": days})
    return out


def _quality_apply_buckets(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    oid = _quality_org_id(cfg)
    existing = {str(b.get("name") or ""): b for b in _quality_list_buckets(cfg)}
    out = []
    for spec in _quality_bucket_specs(cfg):
        name = str(spec.get("name") or "").strip()
        if not name:
            continue
        payload = {"name": name, "orgID": oid, "retentionRules": _quality_bucket_retention(int(spec.get("retention_days") or 0))}
        if name in existing and str(existing[name].get("id") or ""):
            st, _ = _quality_influx_request(cfg, "PATCH", "/api/v2/buckets/" + urllib.parse.quote(str(existing[name]["id"])), payload)
            if st < 200 or st >= 300:
                raise RuntimeError(f"bucket update failed: {name}")
            out.append({"name": name, "action": "updated"})
        else:
            st, _ = _quality_influx_request(cfg, "POST", "/api/v2/buckets", payload)
            if st < 200 or st >= 300:
                raise RuntimeError(f"bucket create failed: {name}")
            out.append({"name": name, "action": "created"})
    return out


def _quality_task_flux(cfg: dict[str, Any], level: dict[str, Any], quality_cfg: dict[str, Any]) -> str:
    clean_bucket = str(quality_cfg.get("clean_bucket") or "")
    rollup_bucket = str(quality_cfg.get("rollup_bucket") or "")
    org = str(cfg.get("org") or "")
    window = str(level.get("window") or "15m")
    every = str(level.get("every") or "1h")
    return (
        f'option task = {{name: "InfluxBro Rollup {window}", every: {every}, offset: 1m}}\n'
        f'from(bucket: "{clean_bucket}")\n'
        f'  |> range(start: -task.every)\n'
        f'  |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)\n'
        f'  |> to(bucket: "{rollup_bucket}", org: "{org}")\n'
    )


def _quality_apply_tasks(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    oid = _quality_org_id(cfg)
    qcfg = _quality_cfg_view(cfg)
    out = []
    for level in qcfg.get("rollups") or []:
        if not isinstance(level, dict):
            continue
        name = f'InfluxBro Rollup {str(level.get("window") or level.get("name") or "")}'
        payload = {
            "orgID": oid,
            "status": "active",
            "description": f'InfluxBro Rollup {str(level.get("name") or "")}',
            "flux": _quality_task_flux(cfg, level, qcfg),
        }
        st, _ = _quality_influx_request(cfg, "POST", "/api/v2/tasks", payload)
        if st < 200 or st >= 300:
            raise RuntimeError(f"task create failed: {name}")
        out.append({"name": name, "action": "created"})
    return out


def _quality_rule_matches(rule: dict[str, Any], entity_id: str, measurement: str) -> bool:
    pat = str(rule.get("pattern") or "").strip()
    if not pat:
        return False
    target = entity_id or measurement
    return fnmatch.fnmatch(target, pat)


def _quality_load_entity_catalog(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        with v2_client(cfg) as c:
            q = f'''
import "influxdata/influxdb/schema"
schema.tagValues(bucket: "{cfg["bucket"]}", tag: "entity_id", start: -30d)
'''
            ids = []
            for rec in c.query_api().query_stream(q, org=cfg["org"]):
                v = str(rec.get_value() or "").strip()
                if v:
                    ids.append(v)
            ids = sorted(set(ids))[:2000]
            for eid in ids:
                out.append({"entity_id": eid, "measurement": "", "friendly_name": ""})
    except Exception:
        return []
    return out


def _quality_cleanup_analyse(cfg: dict[str, Any], start_dt: datetime, stop_dt: datetime, dry_run: bool) -> dict[str, Any]:
    qcfg = _quality_cfg_view(cfg)
    rules = [r for r in (qcfg.get("rules") or []) if isinstance(r, dict) and bool(r.get("enabled", True))]
    raw_bucket = str(qcfg.get("raw_bucket") or "").strip()
    clean_bucket = str(qcfg.get("clean_bucket") or "").strip()
    if not raw_bucket or not clean_bucket:
        raise RuntimeError("raw/clean bucket required")
    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    q = f'''
from(bucket: "{raw_bucket}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => exists r._measurement and exists r._field)
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_time","_value"])
  |> group(columns: ["_measurement","_field","entity_id","friendly_name"])
  |> sort(columns: ["_time"])
'''
    summary = {"series": 0, "points": 0, "corrected": 0, "dropped": 0, "written": 0}
    lines = []
    with v2_client(cfg) as c:
        qapi = c.query_api()
        wapi = c.write_api(write_options=SYNCHRONOUS) if not dry_run else None
        series_rows: dict[tuple[str, str, str, str], list[Any]] = {}
        for rec in qapi.query_stream(q, org=cfg["org"]):
            vals = getattr(rec, "values", {}) or {}
            key = (str(vals.get("_measurement") or ""), str(vals.get("_field") or ""), str(vals.get("entity_id") or ""), str(vals.get("friendly_name") or ""))
            series_rows.setdefault(key, []).append(rec)
        for (measurement, field, entity_id, friendly_name), recs in series_rows.items():
            rule = next((r for r in rules if _quality_rule_matches(r, entity_id, measurement)), None)
            if not rule:
                continue
            summary["series"] += 1
            last_valid = None
            write_batch = []
            for rec in recs:
                summary["points"] += 1
                dt = rec.get_time()
                raw_val = rec.get_value()
                typ = str(rule.get("type") or "gauge")
                invalid_policy = str(rule.get("invalid_policy") or "drop")
                out_val = raw_val
                valid = True
                try:
                    if typ in ("counter", "gauge"):
                        num = float(raw_val)
                        mn = rule.get("min")
                        mx = rule.get("max")
                        if mn is not None and num < float(mn):
                            valid = False
                        if mx is not None and num > float(mx):
                            valid = False
                        max_delta = rule.get("max_delta")
                        if max_delta not in (None, "", 0) and last_valid is not None and abs(num - float(last_valid)) > float(max_delta):
                            valid = False
                        if typ == "counter" and last_valid is not None and not bool(rule.get("reset_allowed")) and num < float(last_valid):
                            valid = False
                        if valid:
                            out_val = num
                    elif typ == "binary":
                        sval = str(raw_val).strip().lower()
                        if sval in ("1", "true", "on", "open"):
                            out_val = 1
                        elif sval in ("0", "false", "off", "closed"):
                            out_val = 0
                        else:
                            valid = False
                    else:
                        sval = str(raw_val).strip()
                        if not sval:
                            valid = False
                        out_val = sval
                except Exception:
                    valid = False
                if not valid:
                    if invalid_policy == "carry_last" and last_valid is not None:
                        out_val = last_valid
                        summary["corrected"] += 1
                    else:
                        summary["dropped"] += 1
                        continue
                else:
                    if out_val != raw_val:
                        summary["corrected"] += 1
                last_valid = out_val
                if not dry_run and wapi is not None and isinstance(dt, datetime):
                    p = Point(str(measurement)).field(str(field), out_val).time(dt, WritePrecision.NS)
                    if entity_id:
                        p = p.tag("entity_id", entity_id)
                    if friendly_name:
                        p = p.tag("friendly_name", friendly_name)
                    write_batch.append(p)
            if write_batch and not dry_run and wapi is not None:
                wapi.write(bucket=clean_bucket, org=cfg["org"], record=write_batch, write_precision=WritePrecision.NS)
                summary["written"] += len(write_batch)
            lines.append({"measurement": measurement, "field": field, "entity_id": entity_id, "friendly_name": friendly_name, "points": len(recs)})
    try:
        QUALITY_CLEANUP_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        QUALITY_CLEANUP_LOG_PATH.open("a", encoding="utf-8").write(json.dumps({"at": _utc_now_iso_ms(), "dry_run": dry_run, "summary": summary}) + "\n")
    except Exception:
        pass
    return {"summary": summary, "series": lines[:200], "query": q}


@app.get("/api/quality/config")
def api_quality_config_get():
    return jsonify({"ok": True, "config": _quality_cfg_view(load_cfg())})


@app.post("/api/quality/config")
def api_quality_config_set():
    body = request.get_json(force=True) or {}
    cfg = load_cfg()
    allowed = {
        "quality_raw_bucket", "quality_clean_bucket", "quality_rollup_bucket",
        "quality_retention_raw_days", "quality_retention_clean_days", "quality_retention_rollup_days",
        "quality_timezone", "quality_lateness_minutes", "quality_auto_create_buckets", "quality_auto_create_tasks",
        "quality_rules_json", "quality_rollup_levels_json", "quality_cleanup_plan_json",
    }
    for k in allowed:
        if k in body:
            cfg[k] = body.get(k)
    save_cfg(cfg)
    return jsonify({"ok": True, "config": _quality_cfg_view(cfg)})


@app.get("/api/quality/buckets/status")
def api_quality_buckets_status():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    qcfg = _quality_cfg_view(cfg)
    try:
        buckets = _quality_list_buckets(cfg)
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e), "config": qcfg}), 500
    return jsonify({"ok": True, "config": qcfg, "buckets": buckets, "desired": _quality_bucket_specs(cfg)})


@app.post("/api/quality/buckets/apply")
def api_quality_buckets_apply():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    try:
        actions = _quality_apply_buckets(cfg)
        return jsonify({"ok": True, "actions": actions})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/quality/tasks/apply")
def api_quality_tasks_apply():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    try:
        actions = _quality_apply_tasks(cfg)
        return jsonify({"ok": True, "actions": actions})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.get("/api/quality/catalog")
def api_quality_catalog():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    return jsonify({"ok": True, "entities": _quality_load_entity_catalog(cfg)})


@app.post("/api/quality/rules/preview")
def api_quality_rules_preview():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    rules = body.get("rules") if isinstance(body.get("rules"), list) else _quality_cfg_view(cfg).get("rules")
    entities = _quality_load_entity_catalog(cfg)
    out = []
    for rule in rules or []:
        if not isinstance(rule, dict):
            continue
        matches = [e for e in entities if _quality_rule_matches(rule, str(e.get("entity_id") or ""), str(e.get("measurement") or ""))]
        out.append({"pattern": str(rule.get("pattern") or ""), "count": len(matches), "matches": matches[:20]})
    return jsonify({"ok": True, "preview": out})


@app.post("/api/quality/query_preview")
def api_quality_query_preview():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    bucket = str(body.get("bucket") or cfg.get("quality_clean_bucket") or cfg.get("bucket") or "").strip()
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "value").strip()
    entity_id = str(body.get("entity_id") or "").strip()
    mode = str(body.get("mode") or "single").strip().lower()
    if not bucket or not measurement:
        return jsonify({"ok": False, "error": "bucket und measurement erforderlich"}), 400
    extra = f' and r.entity_id == {_flux_str(entity_id)}' if entity_id else ''
    if mode == "graph":
        q = f'''
from(bucket: "{bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> keep(columns: ["_time","_value"])
  |> limit(n: 300)
'''
    else:
        q = f'''
from(bucket: "{bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> last()
'''
    rows = []
    with v2_client(cfg) as c:
        for rec in c.query_api().query_stream(q, org=cfg["org"]):
            rows.append({"time": _as_rfc3339(rec.get_time()), "value": rec.get_value()})
    return jsonify({"ok": True, "query": q, "rows": rows[:300]})


@app.post("/api/quality/cleanup_preview")
def api_quality_cleanup_preview():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    t0 = time.monotonic()
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
        out = _quality_cleanup_analyse(cfg, start_dt, stop_dt, True)
        return jsonify({"ok": True, **out})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/quality/cleanup_run")
def api_quality_cleanup_run():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
        out = _quality_cleanup_analyse(cfg, start_dt, stop_dt, False)
        return jsonify({"ok": True, **out})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.get("/api/quality/log")
def api_quality_log():
    rows = []
    try:
        if QUALITY_CLEANUP_LOG_PATH.exists():
            for ln in QUALITY_CLEANUP_LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-100:]:
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    continue
    except Exception:
        rows = []
    return jsonify({"ok": True, "rows": rows})


_ENTITY_ID_RE = re.compile(r"^[A-Za-z0-9_]+\.[A-Za-z0-9_]+$")


def _supervisor_token() -> str:
    return (os.environ.get("SUPERVISOR_TOKEN") or "").strip()


def _supervisor_get(path: str, timeout_s: int = 8) -> tuple[int, str]:
    """GET from Supervisor API.

    Returns: (status_code, text)
    """

    token = _supervisor_token()
    if not token:
        return 0, "SUPERVISOR_TOKEN not set"

    url = "http://supervisor" + (path if path.startswith("/") else ("/" + path))
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = int(getattr(resp, "status", 200))
            return status, raw
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return int(getattr(e, "code", 0) or 0), body or (str(e) or "HTTPError")
    except Exception as e:
        return 0, str(e) or e.__class__.__name__


def _resolve_ha_entity_id(raw_entity_id: str) -> tuple[str | None, str | None]:
    """Resolve entity_id.

    If raw value has no domain (no '.'), treat as object_id and probe common domains.

    Returns: (resolved_entity_id, error)
    """

    v = (raw_entity_id or "").strip()
    if not v:
        return None, "entity_id required"

    if "." in v:
        return v, None if _ENTITY_ID_RE.match(v) else "invalid entity_id"

    # object_id only
    obj = v
    domains = ["sensor", "binary_sensor", "switch", "number", "input_number"]
    for d in domains:
        cand = f"{d}.{obj}"
        if not _ENTITY_ID_RE.match(cand):
            continue
        status, txt = _supervisor_get("/core/api/states/" + urllib.parse.quote(cand, safe=""), timeout_s=6)
        if status == 200 and txt:
            return cand, None
    return None, "invalid entity_id"


@app.get("/api/ha_entity")
def api_ha_entity():
    """Fetch entity metadata from Home Assistant Core.

    Uses Supervisor to call: /core/api/states/<entity_id>
    """

    raw = (request.args.get("entity_id") or "").strip()
    resolved, rerr = _resolve_ha_entity_id(raw)
    if not resolved:
        return jsonify({"ok": True, "available": False, "error": rerr or "invalid entity_id", "entity": None})

    try:
        status, txt = _supervisor_get("/core/api/states/" + urllib.parse.quote(resolved, safe=""), timeout_s=8)
        if status != 200:
            return jsonify({"ok": True, "available": False, "error": f"HTTP {status}" if status else txt, "entity": None})

        raw_txt = txt
        raw = raw_txt
        data = json.loads(raw) if raw else {}
        attrs = (data.get("attributes") or {}) if isinstance(data, dict) else {}

        entity = {
            "entity_id": data.get("entity_id") if isinstance(data, dict) else resolved,
            "state": data.get("state") if isinstance(data, dict) else None,
            "friendly_name": attrs.get("friendly_name"),
            "device_class": attrs.get("device_class"),
            "state_class": attrs.get("state_class"),
            "unit_of_measurement": attrs.get("unit_of_measurement"),
            "icon": attrs.get("icon"),
            "last_changed": data.get("last_changed") if isinstance(data, dict) else None,
            "last_updated": data.get("last_updated") if isinstance(data, dict) else None,
            "resolved_entity_id": resolved,
        }
        return jsonify({"ok": True, "available": True, "entity": entity, "error": None})
    except Exception as e:
        return jsonify({"ok": True, "available": False, "error": str(e) or e.__class__.__name__, "entity": None})


@app.get("/api/ha_debug")
def api_ha_debug():
    """Small diagnostics for HA connectivity.

    Does not expose the Supervisor token.
    """

    token_present = bool((os.environ.get("SUPERVISOR_TOKEN") or "").strip())
    out: dict[str, Any] = {
        "ok": True,
        "token_present": token_present,
        "supervisor_core_api": {"ok": False, "status": None, "error": None},
    }

    if not token_present:
        out["supervisor_core_api"]["error"] = "SUPERVISOR_TOKEN not set"
        return jsonify(out)

    token = (os.environ.get("SUPERVISOR_TOKEN") or "").strip()
    try:
        url = "http://supervisor/core/api/"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            out["supervisor_core_api"]["ok"] = True
            out["supervisor_core_api"]["status"] = getattr(resp, "status", 200)
    except urllib.error.HTTPError as e:
        out["supervisor_core_api"]["status"] = e.code
        out["supervisor_core_api"]["error"] = f"HTTP {e.code} {getattr(e, 'reason', '')}".strip()
    except Exception as e:
        out["supervisor_core_api"]["error"] = str(e) or e.__class__.__name__

    return jsonify(out)


@app.get("/api/logs")
def api_logs():
    """Fetch InfluxBro add-on logs via Supervisor."""

    def _unwrap(txt: str) -> str:
        raw = (txt or "").strip()
        if not raw:
            return ""
        if not (raw.startswith("{") or raw.startswith("[")):
            return txt
        try:
            data = json.loads(raw)
        except Exception:
            return txt
        if isinstance(data, dict):
            d = data.get("data")
            if isinstance(d, str):
                return d
            if isinstance(d, dict):
                for k in ("content", "logs", "result", "stdout", "text"):
                    v = d.get(k)
                    if isinstance(v, str):
                        return v
            # Some endpoints return the body directly
            for k in ("result", "content", "logs", "stdout", "text"):
                v = data.get(k)
                if isinstance(v, str):
                    return v
        return txt

    def _short_err_body(txt: str) -> str:
        t = (txt or "").strip().replace("\n", " ")
        return (t[:240] + "...") if len(t) > 240 else t

    def _extract_slug(txt: str) -> str | None:
        raw = _unwrap(txt)
        try:
            data = json.loads(raw) if raw else {}
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        d = data.get("data") if "data" in data else data
        if not isinstance(d, dict):
            return None
        for k in ("slug", "addon", "add_on", "addon_slug"):
            v = d.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None

    try:
        tail = int(request.args.get("tail", "2000"))
    except Exception:
        tail = 2000
    if tail < 0:
        tail = 0
    if tail > 20000:
        tail = 20000

    sup_lines = min(max(tail, 0), 5000)
    q = f"?lines={sup_lines}" if sup_lines else ""
    # Try self first. Some Supervisor versions return 500 for self/logs; fall back to explicit slug.
    candidates = [
        "/addons/self/logs" + q,
        "/addons/self/logs",
    ]

    status = 0
    txt = ""
    used = ""
    for p in candidates:
        st, out = _supervisor_get(p, timeout_s=10)
        if st == 200 and out:
            status, txt, used = st, out, p
            break
        status, txt, used = st, out, p

    if status == 500:
        # Try to resolve slug and re-run logs with explicit addon id.
        st_info, info_txt = _supervisor_get("/addons/self/info", timeout_s=8)
        if st_info == 200 and info_txt:
            slug = _extract_slug(info_txt)
            if slug:
                for p in (f"/addons/{slug}/logs" + q, f"/addons/{slug}/logs"):
                    st, out = _supervisor_get(p, timeout_s=10)
                    if st == 200 and out:
                        status, txt, used = st, out, p
                        break
                    status, txt, used = st, out, p

    if status != 200:
        msg = _short_err_body(txt)
        return jsonify({
            "ok": False,
            "error": f"Logs not available: HTTP {status} ({used}) {msg}".strip(),
        }), 502

    txt = _unwrap(txt)
    lines = (txt or "").splitlines()
    if tail and len(lines) > tail:
        lines = lines[-tail:]
    return jsonify({"ok": True, "text": "\n".join(lines)})


@app.get("/api/logfile")
def api_logfile():
    """Fetch InfluxBro logfile from /data (rotating)."""

    try:
        tail = int(request.args.get("tail", "2000"))
    except Exception:
        tail = 2000
    if tail < 0:
        tail = 0
    if tail > 20000:
        tail = 20000

    try:
        if not LOG_FILE.exists():
            return jsonify({"ok": True, "text": ""})
        txt = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500

    lines = (txt or "").splitlines()
    if tail and len(lines) > tail:
        lines = lines[-tail:]
    return jsonify({"ok": True, "text": "\n".join(lines)})


@app.get("/api/log_excerpt")
def api_log_excerpt():
    """Return a best-effort excerpt of recent log lines.

    This is used by the UI error popup to show a quick context snippet.
    """

    try:
        minutes = int(request.args.get("minutes", "5"))
    except Exception:
        minutes = 5
    minutes = min(120, max(1, minutes))

    # Read a bounded tail; RotatingFileHandler caps file size anyway.
    try:
        tail = int(request.args.get("tail", "8000"))
    except Exception:
        tail = 8000
    tail = min(20000, max(200, tail))

    try:
        if not LOG_FILE.exists():
            return jsonify({"ok": True, "text": ""})
        txt = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500

    lines = (txt or "").splitlines()
    if tail and len(lines) > tail:
        lines = lines[-tail:]

    cutoff = datetime.now() - timedelta(minutes=minutes)

    # logging.Formatter default asctime: "YYYY-MM-DD HH:MM:SS,mmm"
    ts_re = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:,(\d{3}))?\s")

    def _parse_dt(line: str) -> datetime | None:
        m = ts_re.match(line or "")
        if not m:
            return None
        base = m.group(1)
        ms = m.group(2)
        try:
            dt = datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
            if ms and ms.isdigit():
                dt = dt.replace(microsecond=int(ms) * 1000)
            return dt
        except Exception:
            return None

    # Walk from bottom to find the earliest included timestamped line.
    start_idx = 0
    found = False
    for i in range(len(lines) - 1, -1, -1):
        dt = _parse_dt(lines[i])
        if dt is None:
            continue
        if dt >= cutoff:
            start_idx = i
            found = True
            continue
        # first older timestamp => stop
        if found:
            start_idx = i + 1
        break

    out = lines[start_idx:] if lines else []
    return jsonify({"ok": True, "text": "\n".join(out), "minutes": minutes})


@app.get("/api/logs_diag")
def api_logs_diag():
    """Diagnostics for Supervisor logs access.

    Helps debug 403/404 by listing candidate paths and status codes.
    Does not expose the Supervisor token.
    """

    def _unwrap(txt: str) -> str:
        raw = (txt or "").strip()
        if not raw:
            return ""
        if not (raw.startswith("{") or raw.startswith("[")):
            return txt
        try:
            data = json.loads(raw)
        except Exception:
            return txt
        if isinstance(data, dict):
            d = data.get("data")
            if isinstance(d, str):
                return d
            if isinstance(d, dict):
                for k in ("content", "logs", "result", "stdout", "text"):
                    v = d.get(k)
                    if isinstance(v, str):
                        return v
            for k in ("result", "content", "logs", "stdout", "text"):
                v = data.get(k)
                if isinstance(v, str):
                    return v
        return txt

    def _snip(s: str, n: int = 200) -> str:
        t = (s or "").replace("\r", "").strip()
        t = t.replace("\n", " ")
        return (t[:n] + "...") if len(t) > n else t

    def _extract_slug(txt: str) -> str | None:
        raw = _unwrap(txt)
        try:
            data = json.loads(raw) if raw else {}
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        d = data.get("data") if "data" in data else data
        if not isinstance(d, dict):
            return None
        for k in ("slug", "addon", "add_on", "addon_slug"):
            v = d.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None

    token_present = bool(_supervisor_token())
    try:
        lines = int(request.args.get("lines", "80"))
    except Exception:
        lines = 80
    if lines < 0:
        lines = 0
    if lines > 500:
        lines = 500

    q = f"?lines={lines}" if lines else ""
    candidates = [
        "/addons/self/logs" + q,
        "/addons/self/logs",
    ]

    slug: str | None = None
    st_info, info_txt = _supervisor_get("/addons/self/info", timeout_s=8)
    if st_info == 200 and info_txt:
        slug = _extract_slug(info_txt)
        if slug:
            candidates.extend([
                f"/addons/{slug}/logs" + q,
                f"/addons/{slug}/logs",
            ])

    checks: list[dict[str, Any]] = []
    for p in candidates:
        st, out = _supervisor_get(p, timeout_s=8)
        checks.append({
            "path": p,
            "status": st,
            "ok": st == 200,
            "body": _snip(out),
            "unwrapped": _snip(_unwrap(out)),
        })

    return jsonify({
        "ok": True,
        "token_present": token_present,
        "self_info": {"status": st_info, "slug": slug, "body": _snip(info_txt)},
        "checks": checks,
    })


def _json_best_effort(txt: str) -> dict[str, Any] | None:
    try:
        data = json.loads(txt) if txt else None
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _github_repo_base(url: str) -> str:
    """Return https://github.com/<owner>/<repo> from a configured URL (best-effort)."""

    raw = (url or "").strip()
    if not raw:
        return ""
    # Accept URLs like:
    # - https://github.com/owner/repo
    # - https://github.com/owner/repo/tree/main/influxbro
    m = re.search(r"github\.com/([^/]+)/([^/]+)", raw)
    if not m:
        return ""
    owner = (m.group(1) or "").strip()
    repo = (m.group(2) or "").strip()
    # Strip suffixes like .git
    repo = repo[:-4] if repo.lower().endswith(".git") else repo
    if not owner or not repo:
        return ""
    return f"https://github.com/{owner}/{repo}"


@app.get("/api/bugreport_meta")
def api_bugreport_meta():
    """Small metadata for pre-filling a GitHub bug report (no secrets)."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    repo_base = _github_repo_base(FIXED_REPO_URL)
    # Prefer the advanced bugreport template if present.
    new_issue_url = (repo_base + "/issues/new") if repo_base else ""

    # Home Assistant versions (Supervisor API; best-effort)
    ha_core_ver = None
    ha_supervisor_ver = None
    ha_os_ver = None
    ha_arch = None
    ha_installation_type = None
    try:
        st, txt = _supervisor_get("/core/api/config", timeout_s=6)
        j = _json_best_effort(txt)
        if st == 200 and j:
            ha_core_ver = j.get("version")
    except Exception:
        pass
    try:
        st, txt = _supervisor_get("/supervisor/info", timeout_s=6)
        j = _json_best_effort(txt)
        d = (j.get("data") if isinstance(j, dict) else None) if j else None
        if st == 200 and isinstance(d, dict):
            ha_supervisor_ver = d.get("version")
            ha_arch = d.get("arch") or d.get("architecture")
            ha_installation_type = d.get("installation_type")
    except Exception:
        pass
    try:
        st, txt = _supervisor_get("/os/info", timeout_s=6)
        j = _json_best_effort(txt)
        d = (j.get("data") if isinstance(j, dict) else None) if j else None
        if st == 200 and isinstance(d, dict):
            ha_os_ver = d.get("version")
    except Exception:
        pass

    influx_ver = None
    try:
        j = api_influx_info().get_json()  # type: ignore[attr-defined]
        info = (j.get("info") if isinstance(j, dict) else None) if j else None
        if isinstance(info, dict):
            influx_ver = info.get("influx_version")
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "addon_version": ADDON_VERSION,
        "repo_url": repo_base or repo_cfg,
        "github_repo_base": repo_base,
        "github_new_issue_url": new_issue_url,
        "ha": {
            "core": ha_core_ver,
            "supervisor": ha_supervisor_ver,
            "os": ha_os_ver,
            "arch": ha_arch,
            "installation_type": ha_installation_type,
            "platform": _ha_platform(),
        },
        "influx": {
            "version": influx_ver,
        },
        "recent_actions": _ui_action_tail(5),
    })


def _md_code_block(lang: str, s: str) -> str:
    # Avoid breaking markdown fences.
    t = (s or "").replace("```", "` ` `")
    return f"```{lang}\n{t}\n```\n"


@app.post("/api/debug_report")
def api_debug_report():
    """Export a GitHub-friendly debug report as Markdown.

    This is intended for user bug reports. It must not include secrets.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    bugreport_log_hours = int(cfg.get("bugreport_log_history_hours", 1) or 1)
    bugreport_log_hours = max(1, min(168, bugreport_log_hours))

    try:
        tail = int(body.get("tail") or 2000)
    except Exception:
        tail = 2000
    tail = min(20000, max(0, tail))

    # Client-provided context (best-effort)
    client = body.get("client") if isinstance(body.get("client"), dict) else {}
    issue = body.get("issue") if isinstance(body.get("issue"), dict) else {}

    def _safe_obj(x: Any, max_len: int = 20000) -> str:
        try:
            s = json.dumps(x, indent=2, sort_keys=True, ensure_ascii=True)
        except Exception:
            s = str(x)
        s = _redact_secrets(s)
        if len(s) > max_len:
            s = s[:max_len] + "\n... (truncated)"
        return s

    def _cfg_redacted(c: dict[str, Any]) -> dict[str, Any]:
        r = dict(c)
        if r.get("token"):
            r["token"] = "********"
        if r.get("admin_token"):
            r["admin_token"] = "********"
        if r.get("password"):
            r["password"] = "********"
        return r

    def _tail_file(path: Path, want: int) -> str:
        try:
            if not path.exists():
                return ""
            txt = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"ERROR reading {path}: {e}"
        lines = (txt or "").splitlines()
        if want and len(lines) > want:
            lines = lines[-want:]
        return _redact_secrets("\n".join(lines))

    def _parse_log_dt(raw: str) -> datetime | None:
        s = str(raw or "").strip()
        if not s:
            return None
        patterns = [
            r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)",
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d{3,6})?)",
        ]
        for pat in patterns:
            m = re.match(pat, s)
            if not m:
                continue
            token = str(m.group(1) or "").replace(",", ".")
            if token.endswith("Z"):
                token = token[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(token)
            except Exception:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        return None

    def _filter_log_text_since(txt: str, hours: int) -> str:
        lines = (txt or "").splitlines()
        if not lines:
            return ""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max(1, int(hours or 1)))
        out: list[str] = []
        keep = False
        for line in lines:
            dt = _parse_log_dt(line)
            if dt is not None:
                keep = dt >= cutoff
            if keep:
                out.append(line)
        return _redact_secrets("\n".join(out))

    def _snip_text(s: str, n: int = 200) -> str:
        try:
            t = (s or "").replace("\r", "").strip()
            t = t.replace("\n", " ")
            return (t[:n] + "...") if len(t) > n else t
        except Exception:
            return (s or "")[:n]

    # Home Assistant versions (Supervisor API)
    ha_core = {"ok": False}
    ha_supervisor = {"ok": False}
    ha_os = {"ok": False}
    try:
        st, txt = _supervisor_get("/core/api/config", timeout_s=8)
        j = _json_best_effort(txt)
        if st == 200 and j:
            ha_core = {"ok": True, "status": st, "version": j.get("version"), "time_zone": j.get("time_zone")}
        else:
            ha_core = {"ok": False, "status": st, "error": _snip_text(txt)}
    except Exception as e:
        ha_core = {"ok": False, "error": str(e) or e.__class__.__name__}

    try:
        st, txt = _supervisor_get("/supervisor/info", timeout_s=8)
        j = _json_best_effort(txt)
        d = (j.get("data") if isinstance(j, dict) else None) if j else None
        if st == 200 and isinstance(d, dict):
            ha_supervisor = {"ok": True, "status": st, "version": d.get("version"), "healthy": d.get("healthy")}
        else:
            ha_supervisor = {"ok": False, "status": st}
    except Exception as e:
        ha_supervisor = {"ok": False, "error": str(e) or e.__class__.__name__}

    try:
        st, txt = _supervisor_get("/os/info", timeout_s=8)
        j = _json_best_effort(txt)
        d = (j.get("data") if isinstance(j, dict) else None) if j else None
        if st == 200 and isinstance(d, dict):
            ha_os = {"ok": True, "status": st, "version": d.get("version"), "board": d.get("board")}
        else:
            ha_os = {"ok": False, "status": st}
    except Exception as e:
        ha_os = {"ok": False, "error": str(e) or e.__class__.__name__}

    # Server-side diagnostics (reuse existing endpoints best-effort)
    try:
        ha_debug = api_ha_debug().get_json()  # type: ignore[attr-defined]
    except Exception:
        ha_debug = None
    try:
        influx_info = api_influx_info().get_json()  # type: ignore[attr-defined]
    except Exception:
        influx_info = None
    try:
        logs_diag = api_logs_diag().get_json()  # type: ignore[attr-defined]
    except Exception:
        logs_diag = None
    try:
        jobs = api_jobs().get_json()  # type: ignore[attr-defined]
    except Exception:
        jobs = None
    try:
        caches = api_cache_list().get_json()  # type: ignore[attr-defined]
    except Exception:
        caches = None

    logfile_txt = _filter_log_text_since(_tail_file(LOG_FILE, tail), bugreport_log_hours)

    sup_txt = ""
    try:
        st, txt = _supervisor_get(f"/addons/self/logs?lines={tail}", timeout_s=12)
        if st == 200:
            # Try unwrap similar to api_logs
            sup_txt = txt
            try:
                j = _json_best_effort(txt)
                if j and isinstance(j.get("data"), str):
                    sup_txt = str(j.get("data") or "")
            except Exception:
                sup_txt = txt
            sup_txt = _filter_log_text_since(sup_txt, bugreport_log_hours)
        else:
            sup_txt = f"HTTP {st}: {txt}"
    except Exception as e:
        sup_txt = f"ERROR: {e}"

    exported_at = _utc_now_iso_ms()
    addon_ver = ADDON_VERSION

    # Build Markdown
    lines: list[str] = []
    lines.append(f"# InfluxBro Debug Report\n")
    lines.append(f"Exported at: `{exported_at}`\n")
    lines.append(f"Add-on version: `{addon_ver}`\n")

    title = str(issue.get("title") or "").strip()
    desc = str(issue.get("description") or "").strip()
    steps = str(issue.get("steps") or "").strip()
    func_name = str(issue.get("function") or "").strip()
    if title or desc or steps or func_name:
        lines.append("## User Report\n")
        if title:
            lines.append(f"- Title: {title}\n")
        if func_name:
            lines.append(f"- Function: {func_name}\n")
        if desc:
            lines.append("\n**Description**\n\n" + desc + "\n")
        if steps:
            lines.append("\n**Steps to reproduce**\n\n" + steps + "\n")

    lines.append("## Versions\n")
    lines.append(_md_code_block("json", _safe_obj({"ha_core": ha_core, "ha_supervisor": ha_supervisor, "ha_os": ha_os})))

    lines.append("## Client Context\n")
    lines.append(_md_code_block("json", _safe_obj(client)))

    lines.append("## Recent UI Actions\n")
    lines.append(_md_code_block("json", _safe_obj(_ui_action_tail(20))))

    lines.append("## Add-on Config (redacted)\n")
    lines.append(_md_code_block("json", _safe_obj(_cfg_redacted(cfg))))

    lines.append("## Diagnostics\n")
    lines.append(_md_code_block("json", _safe_obj({"ha_debug": ha_debug, "logs_diag": logs_diag, "influx_info": influx_info})))

    lines.append("## Jobs\n")
    lines.append(_md_code_block("json", _safe_obj(jobs)))

    lines.append("## Dashboard Cache\n")
    lines.append(_md_code_block("json", _safe_obj(caches)))

    lines.append(f"## Logfile (letzte {bugreport_log_hours}h)\n")
    lines.append(_md_code_block("text", logfile_txt))

    lines.append(f"## Supervisor Logs (letzte {bugreport_log_hours}h)\n")
    lines.append(_md_code_block("text", sup_txt))

    md = "\n".join(lines)
    fn = f"influxbro_debug_report_{addon_ver}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.md"
    resp = make_response(md)
    resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
    resp.headers["Content-Disposition"] = f"attachment; filename=\"{fn}\""
    return resp


def _backup_safe(s: str) -> str:
    out = re.sub(r"[^A-Za-z0-9_.-]+", "_", (s or "").strip())
    out = out.strip("_.-")
    return out[:80] if out else "backup"


def _backup_files(dir_path: Path, backup_id: str) -> tuple[Path, Path]:
    stem = _backup_safe(backup_id)
    return dir_path / f"{stem}.json", dir_path / f"{stem}.lp"


def _backup_zip_path(dir_path: Path, backup_id: str) -> Path:
    stem = _backup_safe(backup_id)
    return dir_path / f"{stem}.zip"


def _backup_pack_zip(dir_path: Path, backup_id: str, meta_path: Path, lp_path: Path) -> Path:
    """Pack meta+lp into a zip next to them (best-effort).

    Creates `<stem>.zip` and then removes the original files.
    Keeps legacy files only if zipping fails.
    """

    zpath = _backup_zip_path(dir_path, backup_id)
    tmp = zpath.with_suffix(zpath.suffix + ".tmp")
    try:
        if tmp.exists():
            tmp.unlink()
    except Exception:
        pass

    with zipfile.ZipFile(tmp, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        if meta_path.exists():
            z.write(meta_path, arcname=meta_path.name)
        if lp_path.exists():
            z.write(lp_path, arcname=lp_path.name)

    try:
        tmp.replace(zpath)
    except Exception:
        # Fallback: try unlink then rename
        try:
            if zpath.exists():
                zpath.unlink()
        except Exception:
            pass
        tmp.replace(zpath)

    # Remove originals after the zip is in place.
    for p in (meta_path, lp_path):
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    return zpath


def _backup_pack_zip_tree(
    dir_path: Path,
    backup_id: str,
    *,
    meta_path: Path,
    payload_dir: Path,
    payload_arc_prefix: str,
) -> Path:
    """Pack meta JSON + a payload directory into a zip next to them (best-effort).

    Creates `<stem>.zip` and then removes the original meta file + payload directory.
    """

    zpath = _backup_zip_path(dir_path, backup_id)
    tmp = zpath.with_suffix(zpath.suffix + ".tmp")
    try:
        if tmp.exists():
            tmp.unlink()
    except Exception:
        pass

    with zipfile.ZipFile(tmp, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        if meta_path.exists():
            z.write(meta_path, arcname=meta_path.name)

        pref = (payload_arc_prefix or "payload").strip("/")
        root = payload_dir
        if root.exists() and root.is_dir():
            for base, _dirs, files in os.walk(str(root)):
                for fn in files:
                    try:
                        p = Path(base) / fn
                        if not p.is_file():
                            continue
                        rel = str(p.relative_to(root)).replace("\\", "/")
                        arc = f"{pref}/{rel}" if rel else pref
                        z.write(p, arcname=arc)
                    except Exception:
                        continue

    try:
        tmp.replace(zpath)
    except Exception:
        try:
            if zpath.exists():
                zpath.unlink()
        except Exception:
            pass
        tmp.replace(zpath)

    try:
        if meta_path.exists():
            meta_path.unlink()
    except Exception:
        pass
    try:
        if payload_dir.exists() and payload_dir.is_dir():
            shutil.rmtree(payload_dir, ignore_errors=True)
    except Exception:
        pass
    return zpath


def _backup_create_range(
    cfg: dict[str, Any],
    *,
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    start_dt: datetime,
    stop_dt: datetime,
    display_name: str,
) -> str:
    """Create a range backup ZIP for a specific series; returns backup_id.

    Best-effort helper used by combine for rollback safety.
    """

    ok_free, msg = _backup_require_free_space(cfg)
    if not ok_free:
        raise RuntimeError(msg)

    measurement = str(measurement or "").strip()
    field = str(field or "").strip()
    entity_id = str(entity_id or "").strip() or None
    friendly_name = str(friendly_name or "").strip() or None
    if not measurement or not field:
        raise ValueError("measurement and field required")
    if not entity_id and not friendly_name:
        raise ValueError("entity_id or friendly_name required")
    if not (start_dt and stop_dt):
        raise ValueError("start_dt and stop_dt required")

    if int(cfg.get("influx_version", 2)) != 2:
        raise RuntimeError("range backup supports InfluxDB v2 only")
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        raise RuntimeError("InfluxDB v2 requires token, org, bucket")

    bdir = backup_dir(cfg)
    bdir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_kind = "range"
    display = str(display_name or friendly_name or entity_id or f"{measurement}_{field}")
    backup_id = _backup_safe(display) + "__" + backup_kind + "__" + ts
    meta_path, lp_path = _backup_files(bdir, backup_id)
    if _backup_zip_path(bdir, backup_id).exists() or meta_path.exists() or lp_path.exists():
        raise RuntimeError("backup id collision")

    extra = flux_tag_filter(entity_id, friendly_name)
    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> sort(columns: ["_time"])
'''

    count = 0
    oldest: datetime | None = None
    newest: datetime | None = None
    with v2_client(cfg) as c:
        qapi = c.query_api()
        with lp_path.open("w", encoding="utf-8") as f:
            for rec in qapi.query_stream(q, org=cfg["org"]):
                try:
                    t = rec.get_time()
                    v = rec.get_value()
                    m = rec.values.get("_measurement") or measurement
                    fld = rec.values.get("_field") or field
                    if v is None:
                        continue
                    p = Point(str(m))
                    for k, tv in (rec.values or {}).items():
                        if k in ("result", "table"):
                            continue
                        if str(k).startswith("_"):
                            continue
                        if tv is None:
                            continue
                        p = p.tag(str(k), str(tv))
                    p = p.field(str(fld), v)
                    if isinstance(t, datetime):
                        p = p.time(t, WritePrecision.NS)
                    lp = p.to_line_protocol()
                    if lp:
                        f.write(lp)
                        f.write("\n")
                        count += 1
                        if isinstance(t, datetime):
                            if oldest is None or t < oldest:
                                oldest = t
                            if newest is None or t > newest:
                                newest = t
                except Exception:
                    continue

    bytes_size = int(lp_path.stat().st_size) if lp_path.exists() else 0
    meta = {
        "id": backup_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "kind": backup_kind,
        "display_name": display,
        "measurement": measurement,
        "field": field,
        "entity_id": entity_id,
        "friendly_name": friendly_name,
        "start": start,
        "stop": stop,
        "point_count": count,
        "bytes": bytes_size,
        "oldest_time": _dt_to_rfc3339_utc(oldest) if oldest else None,
        "newest_time": _dt_to_rfc3339_utc(newest) if newest else None,
    }
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
    _backup_pack_zip(bdir, backup_id, meta_path, lp_path)
    return backup_id


def _fullbackup_files(dir_path: Path, backup_id: str) -> tuple[Path, Path]:
    # Stored in the same directory as normal backups, but distinguished by meta.kind == 'db_full'.
    stem = _backup_safe(backup_id)
    return dir_path / f"{stem}.json", dir_path / f"{stem}.lp"


def _norm_unit(u: str) -> str:
    return (u or "").strip().lower().replace(" ", "")


def _parse_unit_step_map(raw: str) -> dict[str, float]:
    out: dict[str, float] = {}
    txt = raw or ""
    for ln in txt.splitlines():
        s = (ln or "").strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        # allow inline comments
        if "#" in s:
            s = s.split("#", 1)[0].strip()
        if not s:
            continue
        if "=" in s:
            a, b = s.split("=", 1)
        elif ":" in s:
            a, b = s.split(":", 1)
        else:
            # fallback: split on whitespace
            parts = s.split()
            if len(parts) < 2:
                continue
            a, b = parts[0], parts[1]
        unit = _norm_unit(a)
        if not unit:
            continue
        try:
            v = float(str(b).strip())
        except Exception:
            continue
        out[unit] = v
    return out


def _outlier_max_step(cfg: dict[str, Any], measurement: str, unit: str) -> float:
    m = _norm_unit(measurement)
    u = _norm_unit(unit)
    try:
        custom = _parse_unit_step_map(str(cfg.get("outlier_max_step_units") or ""))
        if m and m in custom:
            return float(custom[m])
        if u and u in custom:
            return float(custom[u])
    except Exception:
        pass
    if u in ("w", "watt"):
        return float(cfg.get("outlier_max_step_w", 30000))
    if u in ("kw", "kilowatt"):
        return float(cfg.get("outlier_max_step_kw", 30))
    if u in ("wh", "watt-hour", "watthour", "watthours"):
        return float(cfg.get("outlier_max_step_wh", 30000))
    if u in ("kwh", "kilowatt-hour", "kilowatthour", "kilowatthours"):
        return float(cfg.get("outlier_max_step_kwh", 30))
    # fallback
    return float(cfg.get("outlier_max_step_w", 30000))


def _outlier_gap_seconds(cfg: dict[str, Any]) -> float:
    try:
        return float(cfg.get("outlier_gap_seconds_default", 300) or 300)
    except Exception:
        return 300.0


def _outlier_bounds_defaults(cfg: dict[str, Any]) -> tuple[float | None, float | None]:
    def _opt_num(key: str) -> float | None:
        try:
            raw = cfg.get(key)
            s = "" if raw is None else str(raw).strip()
            if not s:
                return None
            return float(s)
        except Exception:
            return None

    return _opt_num("outlier_bounds_min_default"), _opt_num("outlier_bounds_max_default")


def _flux_tag_filter_from_tags(tags: dict[str, str]) -> str:
    """Build a safe Flux tag filter expression from a tag dict."""

    extra = ""
    if not isinstance(tags, dict):
        return extra
    for k, v in (tags or {}).items():
        key = str(k or "").strip()
        if not key:
            continue
        # keep this conservative; Flux identifiers can't be arbitrary.
        if not re.match(r"^[a-zA-Z0-9_]+$", key):
            continue
        extra += f" and r.{key} == {_flux_str(str(v or ''))}"
    return extra


def _neighbors_v2(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    dt: datetime,
    extra_filter: str,
) -> dict[str, Any]:
    """Return best-effort prev/next neighbor points around dt."""

    windows_s = [3600, 6 * 3600, 24 * 3600, 7 * 24 * 3600]
    prev: tuple[datetime, float] | None = None
    nxt: tuple[datetime, float] | None = None

    with v2_client(cfg) as c:
        qapi = c.query_api()
        for win_s in windows_s:
            start = _dt_to_rfc3339_utc_full(dt - timedelta(seconds=int(win_s)))
            stop = _dt_to_rfc3339_utc_full(dt + timedelta(seconds=int(win_s)))
            q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra_filter})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: 1000)
'''
            try:
                tables = qapi.query(q, org=cfg["org"])
            except Exception:
                continue
            rows: list[tuple[datetime, float]] = []
            for t in tables or []:
                for rec in getattr(t, "records", []) or []:
                    ts = rec.get_time()
                    val = rec.get_value()
                    if not isinstance(ts, datetime):
                        continue
                    if isinstance(val, bool) or not isinstance(val, (int, float)):
                        continue
                    rows.append((ts.astimezone(timezone.utc), float(val)))
            if not rows:
                continue
            rows.sort(key=lambda x: x[0])
            for ts, val in rows:
                if ts < dt:
                    prev = (ts, val)
                elif ts > dt and nxt is None:
                    nxt = (ts, val)
            if prev is not None or nxt is not None:
                break

    out: dict[str, Any] = {}
    if prev is not None:
        out["prev_time"] = _dt_to_rfc3339_utc_ms(prev[0])
        out["prev_value"] = prev[1]
    if nxt is not None:
        out["next_time"] = _dt_to_rfc3339_utc_ms(nxt[0])
        out["next_value"] = nxt[1]
    return out


def _neighbors_v1(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    ts: datetime,
    tag_where: str,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not cfg.get("database"):
        return out
    c = v1_client(cfg)
    try:
        t = _dt_to_rfc3339_utc(ts)
        # previous
        q_prev = f'SELECT "{field}" FROM "{measurement}" WHERE time < \'{t}\'{tag_where} ORDER BY time DESC LIMIT 1'
        res = c.query(q_prev)
        for _, pts in (res or {}).items():
            for p in pts or []:
                try:
                    out["prev_time"] = str(p.get("time") or "")
                    out["prev_value"] = float(p.get(field))
                except Exception:
                    pass
            break
        # next
        q_next = f'SELECT "{field}" FROM "{measurement}" WHERE time > \'{t}\'{tag_where} ORDER BY time ASC LIMIT 1'
        res = c.query(q_next)
        for _, pts in (res or {}).items():
            for p in pts or []:
                try:
                    out["next_time"] = str(p.get("time") or "")
                    out["next_value"] = float(p.get(field))
                except Exception:
                    pass
            break
    finally:
        try:
            c.close()
        except Exception:
            pass
    return out


def _check_outlier_edit_rules(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    ts: datetime,
    new_value: float,
    unit: str,
    tags: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Best-effort rule check used for write guardrails."""

    min_v, max_v = _outlier_bounds_defaults(cfg)
    step_th = 0.0
    try:
        step_th = float(_outlier_max_step(cfg, measurement, unit))
    except Exception:
        step_th = 0.0
    if step_th < 0:
        step_th = 0.0

    violations: list[dict[str, Any]] = []

    if min_v is not None and new_value < float(min_v):
        violations.append({
            "rule": "bounds_min",
            "detail": f"new_value={new_value} < min={min_v}",
            "min": float(min_v),
            "new_value": float(new_value),
        })
    if max_v is not None and new_value > float(max_v):
        violations.append({
            "rule": "bounds_max",
            "detail": f"new_value={new_value} > max={max_v}",
            "max": float(max_v),
            "new_value": float(new_value),
        })

    neighbors: dict[str, Any] = {}
    try:
        if int(cfg.get("influx_version", 2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return {"ok": True, "violations": [], "meta": {"skipped": "missing_v2_cfg"}}
            extra = _flux_tag_filter_from_tags(tags or {}) if tags else flux_tag_filter(entity_id, friendly_name)
            neighbors = _neighbors_v2(cfg, measurement, field, ts.astimezone(timezone.utc), extra)
        else:
            tag_where = influxql_tag_filter(entity_id, friendly_name)
            neighbors = _neighbors_v1(cfg, measurement, field, ts, tag_where)
    except Exception:
        neighbors = {}

    if step_th and neighbors:
        try:
            if "prev_value" in neighbors:
                dv = abs(float(new_value) - float(neighbors["prev_value"]))
                if dv > step_th:
                    violations.append({
                        "rule": "max_step_prev",
                        "detail": f"abs(new-prev)={dv} > max_step={step_th}",
                        "max_step": float(step_th),
                        "delta": float(dv),
                        "prev_time": neighbors.get("prev_time"),
                        "prev_value": neighbors.get("prev_value"),
                        "new_value": float(new_value),
                    })
        except Exception:
            pass
        try:
            if "next_value" in neighbors:
                dv = abs(float(new_value) - float(neighbors["next_value"]))
                if dv > step_th:
                    violations.append({
                        "rule": "max_step_next",
                        "detail": f"abs(new-next)={dv} > max_step={step_th}",
                        "max_step": float(step_th),
                        "delta": float(dv),
                        "next_time": neighbors.get("next_time"),
                        "next_value": neighbors.get("next_value"),
                        "new_value": float(new_value),
                    })
        except Exception:
            pass

    return {
        "ok": True,
        "violations": violations,
        "meta": {
            "unit": str(unit or ""),
            "max_step": float(step_th or 0.0),
            "bounds_min": min_v,
            "bounds_max": max_v,
            **neighbors,
        },
    }


def _list_backups(dir_path: Path, include_db_full: bool = False) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not dir_path.exists():
        return out

    # Prefer packed ZIP backups (meta+lp inside) to save disk space.
    seen_stems: set[str] = set()
    for p in sorted(dir_path.glob("*.zip")):
        try:
            stem = str(p.stem)
            if not stem:
                continue
            with zipfile.ZipFile(p, mode="r") as z:
                meta_name = stem + ".json"
                if meta_name not in z.namelist():
                    # best-effort: pick the first json
                    cands = [n for n in z.namelist() if n.lower().endswith(".json")]
                    if not cands:
                        continue
                    meta_name = cands[0]
                meta = json.loads(z.read(meta_name).decode("utf-8", errors="replace"))
            if not isinstance(meta, dict):
                continue
            if not include_db_full and str(meta.get("kind") or "") == "db_full":
                continue
            backup_id = str(meta.get("id") or stem)
            out.append({
                **meta,
                "id": backup_id,
                "file": stem,
                "zip_file": p.name,
                "zip_bytes": int(p.stat().st_size) if p.exists() else 0,
                "bytes": int(meta.get("bytes") or 0),
            })
            seen_stems.add(stem)
        except Exception:
            continue

    # Legacy: meta json next to raw lp
    for p in sorted(dir_path.glob("*.json")):
        try:
            if str(p.stem) in seen_stems:
                continue
            meta = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(meta, dict):
                continue
            if not include_db_full and str(meta.get("kind") or "") == "db_full":
                continue
            backup_id = str(meta.get("id") or p.stem)
            lp = dir_path / (p.stem + ".lp")
            out.append({
                **meta,
                "id": backup_id,
                "file": p.stem,
                "zip_file": None,
                "zip_bytes": 0,
                "bytes": int(lp.stat().st_size) if lp.exists() else int(meta.get("bytes") or 0),
            })
        except Exception:
            continue
    # newest first
    out.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return out


def _read_backup_meta(dir_path: Path, backup_id: str) -> dict[str, Any] | None:
    """Read backup meta JSON from the backup directory (safe-id only)."""
    bid = str(backup_id or "").strip()
    if not bid:
        return None
    if _backup_safe(bid) != bid:
        return None

    # Prefer packed zip.
    zpath = _backup_zip_path(dir_path, bid)
    if zpath.exists():
        try:
            stem = str(zpath.stem)
            with zipfile.ZipFile(zpath, mode="r") as z:
                name = stem + ".json"
                if name not in z.namelist():
                    cands = [n for n in z.namelist() if n.lower().endswith(".json")]
                    if not cands:
                        return None
                    name = cands[0]
                meta = json.loads(z.read(name).decode("utf-8", errors="replace"))
        except Exception:
            return None
    else:
        meta_path, _lp_path = _backup_files(dir_path, bid)
        if not meta_path.exists():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return None
    if not isinstance(meta, dict):
        return None
    return meta


@contextmanager
def _open_backup_lp_text(dir_path: Path, backup_id: str, *, is_fullbackup: bool = False):
    """Open the line protocol payload as text (supports packed .zip and legacy .lp).

    Yields a text file object (iterable by line).
    """

    bid = str(backup_id or "").strip()
    if not bid or _backup_safe(bid) != bid:
        raise FileNotFoundError("invalid backup id")

    zpath = _backup_zip_path(dir_path, bid)
    if zpath.exists():
        stem = str(zpath.stem)
        z = zipfile.ZipFile(zpath, mode="r")
        try:
            lp_name = stem + ".lp"
            if lp_name not in z.namelist():
                cands = [n for n in z.namelist() if n.lower().endswith(".lp")]
                if not cands:
                    raise FileNotFoundError("lp payload missing in zip")
                lp_name = cands[0]
            raw = z.open(lp_name, mode="r")
            try:
                txt = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                try:
                    yield txt
                finally:
                    try:
                        txt.close()
                    except Exception:
                        pass
            finally:
                try:
                    raw.close()
                except Exception:
                    pass
        finally:
            try:
                z.close()
            except Exception:
                pass
        return

    # Legacy files
    if is_fullbackup:
        _meta_path, lp_path = _fullbackup_files(dir_path, bid)
    else:
        _meta_path, lp_path = _backup_files(dir_path, bid)
    if not lp_path.exists():
        raise FileNotFoundError("lp payload missing")
    with lp_path.open("r", encoding="utf-8", errors="replace") as f:
        yield f


def _fmt_bytes(n: int | None) -> str:
    try:
        if n is None:
            return ""
        b = int(n)
        if b < 0:
            return ""
        if b < 1024:
            return f"{b} B"
        if b < 1024 * 1024:
            return f"{b / 1024.0:.1f} kB"
        if b < 1024 * 1024 * 1024:
            return f"{b / 1024.0 / 1024.0:.1f} MB"
        return f"{b / 1024.0 / 1024.0 / 1024.0:.2f} GB"
    except Exception:
        return ""


def _backup_job_public(job: dict[str, Any]) -> dict[str, Any]:
    written_b = int(job.get("written_bytes") or 0)
    return {
        "id": job.get("id"),
        "state": job.get("state"),
        "message": job.get("message"),
        "started_at": job.get("started_at"),
        "elapsed": _job_elapsed_hms(job),
        "written_bytes": written_b,
        "written_human": _fmt_bytes(written_b),
        "point_count": int(job.get("point_count") or 0),
        "backup_id": job.get("backup_id"),
        "backup_kind": job.get("backup_kind"),
        "query": job.get("query") or "",
        "cancelled": bool(job.get("cancelled")),
        "error": job.get("error"),
        "ready": job.get("state") in ("done", "error", "cancelled"),
    }


def _backup_job_thread(
    job_id: str,
    cfg: dict[str, Any],
    backup_kind: str,
    backup_id: str,
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    start_dt: datetime | None,
    stop_dt: datetime | None,
) -> None:
    with BACKUP_LOCK:
        job = BACKUP_JOBS.get(job_id)
    if not job:
        return

    def set_state(state: str, msg: str) -> None:
        with BACKUP_LOCK:
            if job_id in BACKUP_JOBS:
                BACKUP_JOBS[job_id]["state"] = state
                BACKUP_JOBS[job_id]["message"] = msg
                if state in ("done", "error", "cancelled"):
                    _job_set_finished(BACKUP_JOBS[job_id])

    def set_error(msg: str) -> None:
        with BACKUP_LOCK:
            if job_id in BACKUP_JOBS:
                BACKUP_JOBS[job_id]["error"] = msg

    def set_progress(**kw: Any) -> None:
        with BACKUP_LOCK:
            j = BACKUP_JOBS.get(job_id)
            if not j:
                return
            for k, v in kw.items():
                j[k] = v

    def is_cancelled() -> bool:
        with BACKUP_LOCK:
            j = BACKUP_JOBS.get(job_id) or {}
            if bool(j.get("cancelled")):
                return True

            try:
                max_s = int(cfg.get("jobs_max_runtime_seconds", 0) or 0)
            except Exception:
                max_s = 0
            if max_s <= 0:
                return False
            try:
                started_mono = float(j.get("started_mono") or 0.0)
            except Exception:
                started_mono = 0.0
            if started_mono > 0 and (time.monotonic() - started_mono) >= float(max_s):
                BACKUP_JOBS[job_id]["cancelled"] = True
                try:
                    LOG.warning("job_auto_cancel type=backup job_id=%s reason=max_runtime_seconds exceeded (%s)", job_id, max_s)
                except Exception:
                    pass
                return True
            return False

    bdir = backup_dir(cfg)
    bdir.mkdir(parents=True, exist_ok=True)
    meta_path, lp_path = _backup_files(bdir, backup_id)

    extra = flux_tag_filter(entity_id, friendly_name)
    range_clause = '|> range(start: time(v: "1970-01-01T00:00:00Z"))'
    start_iso = None
    stop_iso = None
    if backup_kind == "range" and start_dt and stop_dt:
        start_iso = _dt_to_rfc3339_utc(start_dt)
        stop_iso = _dt_to_rfc3339_utc(stop_dt)
        range_clause = f'|> range(start: time(v: "{start_iso}"), stop: time(v: "{stop_iso}"))'

    q = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> sort(columns: ["_time"])
'''

    log_query(f"backup.job {backup_kind} (flux)", q)
    set_state("running", "Export laeuft...")
    set_progress(query=q.strip(), written_bytes=0, point_count=0)

    count = 0
    oldest: datetime | None = None
    newest: datetime | None = None
    written_b = 0
    last_tick = time.monotonic()

    try:
        with v2_client(cfg) as c:
            qapi = c.query_api()
            with lp_path.open("w", encoding="utf-8") as f:
                for rec in qapi.query_stream(q, org=cfg["org"]):
                    if is_cancelled():
                        set_state("cancelled", "Abgebrochen")
                        raise RuntimeError("cancelled")
                    try:
                        t = rec.get_time()
                        v = rec.get_value()
                        m = rec.values.get("_measurement") or measurement
                        fld = rec.values.get("_field") or field
                        if v is None:
                            continue
                        p = Point(str(m))
                        for k, tv in (rec.values or {}).items():
                            if k in ("result", "table"):
                                continue
                            if str(k).startswith("_"):
                                continue
                            if tv is None:
                                continue
                            p = p.tag(str(k), str(tv))
                        p = p.field(str(fld), v)
                        if isinstance(t, datetime):
                            p = p.time(t, WritePrecision.NS)
                        lp = p.to_line_protocol()
                        if lp:
                            f.write(lp)
                            f.write("\n")
                            written_b += len(lp) + 1
                            count += 1
                            if isinstance(t, datetime):
                                if oldest is None or t < oldest:
                                    oldest = t
                                if newest is None or t > newest:
                                    newest = t
                    except Exception:
                        continue

                    now = time.monotonic()
                    if (now - last_tick) >= 0.25:
                        set_progress(written_bytes=written_b, point_count=count)
                        last_tick = now

        bytes_size = written_b
        if bytes_size <= 0:
            try:
                bytes_size = int(lp_path.stat().st_size)
            except Exception:
                bytes_size = written_b

        meta = {
            "id": backup_id,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "kind": backup_kind,
            "display_name": friendly_name or entity_id or f"{measurement}_{field}",
            "measurement": measurement,
            "field": field,
            "entity_id": entity_id,
            "friendly_name": friendly_name,
            "point_count": count,
            "bytes": bytes_size,
            "oldest_time": _dt_to_rfc3339_utc(oldest) if oldest else None,
            "newest_time": _dt_to_rfc3339_utc(newest) if newest else None,
            "start": start_iso or (_dt_to_rfc3339_utc(oldest) if oldest else None),
            "stop": stop_iso or (_dt_to_rfc3339_utc(newest) if newest else None),
        }
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
        try:
            _backup_pack_zip(bdir, backup_id, meta_path, lp_path)
        except Exception:
            pass
        set_progress(written_bytes=bytes_size, point_count=count)
        set_state("done", f"Backup created: {backup_id}")
        return
    except Exception as e:
        # On cancel, delete partial files (requested).
        msg = str(e)
        if "cancelled" in msg:
            try:
                if meta_path.exists():
                    meta_path.unlink()
            except Exception:
                pass
            try:
                if lp_path.exists():
                    lp_path.unlink()
            except Exception:
                pass
            try:
                zpath = _backup_zip_path(bdir, backup_id)
                if zpath.exists():
                    zpath.unlink()
            except Exception:
                pass
            return

        set_state("error", "Fehler")
        set_error(_short_influx_error(e))
        try:
            if meta_path.exists():
                meta_path.unlink()
        except Exception:
            pass
        try:
            if lp_path.exists():
                lp_path.unlink()
        except Exception:
            pass
        try:
            zpath = _backup_zip_path(bdir, backup_id)
            if zpath.exists():
                zpath.unlink()
        except Exception:
            pass
        return


def _fullbackup_job_public(job: dict[str, Any]) -> dict[str, Any]:
    written_b = int(job.get("written_bytes") or 0)
    return {
        "id": job.get("id"),
        "state": job.get("state"),
        "message": job.get("message"),
        "started_at": job.get("started_at"),
        "elapsed": _job_elapsed_hms(job),
        "format": str(job.get("format") or "lp"),
        "written_bytes": written_b,
        "written_human": _fmt_bytes(written_b),
        "point_count": int(job.get("point_count") or 0),
        "backup_id": job.get("backup_id"),
        "query": job.get("query") or "",
        "cancelled": bool(job.get("cancelled")),
        "error": job.get("error"),
        "ready": job.get("state") in ("done", "error", "cancelled"),
    }


def _fullbackup_job_thread(job_id: str, cfg: dict[str, Any], backup_id: str) -> None:
    with FULLBACKUP_LOCK:
        job = FULLBACKUP_JOBS.get(job_id)
    if not job:
        return

    def set_state(state: str, msg: str) -> None:
        with FULLBACKUP_LOCK:
            if job_id in FULLBACKUP_JOBS:
                FULLBACKUP_JOBS[job_id]["state"] = state
                FULLBACKUP_JOBS[job_id]["message"] = msg
                if state in ("done", "error", "cancelled"):
                    _job_set_finished(FULLBACKUP_JOBS[job_id])

    def set_error(msg: str) -> None:
        with FULLBACKUP_LOCK:
            if job_id in FULLBACKUP_JOBS:
                FULLBACKUP_JOBS[job_id]["error"] = msg

    def set_progress(**kw: Any) -> None:
        with FULLBACKUP_LOCK:
            j = FULLBACKUP_JOBS.get(job_id)
            if not j:
                return
            for k, v in kw.items():
                j[k] = v

    def is_cancelled() -> bool:
        with FULLBACKUP_LOCK:
            j = FULLBACKUP_JOBS.get(job_id) or {}
            if bool(j.get("cancelled")):
                return True

            try:
                max_s = int(cfg.get("jobs_max_runtime_seconds", 0) or 0)
            except Exception:
                max_s = 0
            if max_s <= 0:
                return False
            try:
                started_mono = float(j.get("started_mono") or 0.0)
            except Exception:
                started_mono = 0.0
            if started_mono > 0 and (time.monotonic() - started_mono) >= float(max_s):
                FULLBACKUP_JOBS[job_id]["cancelled"] = True
                try:
                    LOG.warning(
                        "job_auto_cancel type=fullbackup job_id=%s reason=max_runtime_seconds exceeded (%s)",
                        job_id,
                        max_s,
                    )
                except Exception:
                    pass
                return True
            return False

    bdir = backup_dir(cfg)
    bdir.mkdir(parents=True, exist_ok=True)
    meta_path, lp_path = _fullbackup_files(bdir, backup_id)

    set_state("running", "FullBackup laeuft...")

    influx_v = int(cfg.get("influx_version", 2) or 2)
    if influx_v == 3:
        set_state("error", "Nicht unterstuetzt")
        set_error("FullBackup wird aktuell nicht fuer InfluxDB v3 unterstuetzt.")
        return

    fmt = str(job.get("format") or "lp").strip() or "lp"
    if influx_v == 2 and fmt == "native_v2":
        if not _influx_cli_available():
            plat = _ha_platform()
            set_state("error", "Nicht unterstuetzt")
            set_error(
                "Native v2 FullBackup ist auf dieser Plattform nicht verfuegbar (Influx CLI fehlt). "
                f"HA Plattform: {plat}."
            )
            try:
                LOG.warning("native_cli_missing type=fullbackup platform=%s job_id=%s", plat, job_id)
            except Exception:
                pass
            return
        if not (cfg.get("org") and cfg.get("bucket")):
            set_state("error", "Konfiguration fehlt")
            set_error("Native v2 Backup erfordert org/bucket. Bitte in Einstellungen speichern.")
            return

        admin_token = str(cfg.get("admin_token") or "").strip()
        if not admin_token:
            set_state("error", "Konfiguration fehlt")
            set_error("Native v2 Backup erfordert admin_token. Bitte in Einstellungen speichern.")
            return

        # Run `influx backup` into a directory, then zip the directory for storage/download.
        payload_dir = bdir / (str(_backup_safe(backup_id)) + ".native")
        try:
            if payload_dir.exists():
                shutil.rmtree(payload_dir, ignore_errors=True)
        except Exception:
            pass
        payload_dir.mkdir(parents=True, exist_ok=True)

        cmd = ["influx", "backup", "--bucket", str(cfg.get("bucket")), str(payload_dir)]
        cmd_redacted = (
            f"influx backup --host {json.dumps(_influx_url(cfg))} --org {json.dumps(str(cfg.get('org') or ''))} "
            f"--bucket {json.dumps(str(cfg.get('bucket') or ''))} {json.dumps(str(payload_dir))}"
        )
        set_progress(query=cmd_redacted, written_bytes=0, point_count=0)

        tail: list[str] = []
        p: subprocess.Popen[str] | None = None
        try:
            env = _influx_cli_env(cfg, token=admin_token)
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            out = p.stdout
            last_tick_sz = 0.0
            while True:
                if is_cancelled():
                    try:
                        p.terminate()
                    except Exception:
                        pass
                    set_state("cancelled", "Abgebrochen")
                    raise RuntimeError("cancelled")

                # Read stdout without blocking cancellation.
                if out is not None:
                    try:
                        r, _w, _x = select.select([out], [], [], 0.25)
                    except Exception:
                        r = []
                    if r:
                        try:
                            ln = out.readline()
                        except Exception:
                            ln = ""
                        s = (ln or "").rstrip("\n")
                        if s:
                            tail.append(s)
                            if len(tail) > 30:
                                tail = tail[-30:]
                            set_state("running", s[:240])

                now = time.monotonic()
                if (now - last_tick_sz) >= 1.0:
                    # best-effort size progress of the payload directory
                    try:
                        cur_b = 0
                        for base, _dirs, files in os.walk(str(payload_dir)):
                            for fn in files:
                                try:
                                    cur_b += int(os.path.getsize(os.path.join(base, fn)) or 0)
                                except Exception:
                                    continue
                        set_progress(written_bytes=int(cur_b), point_count=0)
                    except Exception:
                        pass
                    last_tick_sz = now

                if p.poll() is not None:
                    break

            rc = p.wait() if p is not None else 1
            if rc != 0:
                msg = "Native Backup fehlgeschlagen"
                if tail:
                    msg = msg + ": " + tail[-1]
                raise RuntimeError(msg)

            # Determine raw size (best-effort)
            raw_bytes = 0
            try:
                for base, _dirs, files in os.walk(str(payload_dir)):
                    for fn in files:
                        try:
                            raw_bytes += int(os.path.getsize(os.path.join(base, fn)) or 0)
                        except Exception:
                            continue
            except Exception:
                raw_bytes = 0

            meta = {
                "id": backup_id,
                "display_name": f"FullBackup (v2 native) {backup_id}",
                "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "kind": "db_full",
                "format": "native_v2",
                "influx_version": 2,
                "org": cfg.get("org"),
                "bucket": cfg.get("bucket"),
                "point_count": 0,
                "bytes": int(raw_bytes),
            }
            meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
            zpath = _backup_pack_zip_tree(
                bdir,
                backup_id,
                meta_path=meta_path,
                payload_dir=payload_dir,
                payload_arc_prefix="native",
            )
            try:
                set_progress(written_bytes=int(zpath.stat().st_size), point_count=0)
            except Exception:
                set_progress(written_bytes=0, point_count=0)
            set_state("done", f"FullBackup created: {backup_id}")
            return
        except Exception as e:
            msg = str(e)
            if "cancelled" in msg:
                try:
                    if meta_path.exists():
                        meta_path.unlink()
                except Exception:
                    pass
                try:
                    if payload_dir.exists():
                        shutil.rmtree(payload_dir, ignore_errors=True)
                except Exception:
                    pass
                try:
                    zpath = _backup_zip_path(bdir, backup_id)
                    if zpath.exists():
                        zpath.unlink()
                except Exception:
                    pass
                return

            set_state("error", "Fehler")
            set_error(_short_influx_error(e if isinstance(e, Exception) else Exception(str(e))))
            try:
                if meta_path.exists():
                    meta_path.unlink()
            except Exception:
                pass
            try:
                if payload_dir.exists():
                    shutil.rmtree(payload_dir, ignore_errors=True)
            except Exception:
                pass
            try:
                zpath = _backup_zip_path(bdir, backup_id)
                if zpath.exists():
                    zpath.unlink()
            except Exception:
                pass
            return

    count = 0
    written_b = 0
    last_tick = time.monotonic()
    oldest: datetime | None = None
    newest: datetime | None = None

    try:
        if influx_v == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                set_state("error", "Konfiguration fehlt")
                set_error("InfluxDB v2 erfordert token/org/bucket. Bitte in Einstellungen speichern.")
                return

            q = f'''\
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "1970-01-01T00:00:00Z"))
  |> sort(columns: ["_time"])
'''
            set_progress(query=q.strip(), written_bytes=0, point_count=0)

            with v2_client(cfg) as c:
                qapi = c.query_api()
                with lp_path.open("w", encoding="utf-8") as f:
                    for rec in qapi.query_stream(q, org=cfg["org"]):
                        if is_cancelled():
                            set_state("cancelled", "Abgebrochen")
                            raise RuntimeError("cancelled")
                        try:
                            t = rec.get_time()
                            v = rec.get_value()
                            m = rec.values.get("_measurement")
                            fld = rec.values.get("_field")
                            if v is None or not m or not fld:
                                continue

                            p = Point(str(m))
                            for k, tv in (rec.values or {}).items():
                                if k in ("result", "table"):
                                    continue
                                if str(k).startswith("_"):
                                    continue
                                if tv is None:
                                    continue
                                p = p.tag(str(k), str(tv))

                            p = p.field(str(fld), v)
                            if isinstance(t, datetime):
                                p = p.time(t, WritePrecision.NS)
                            lp = p.to_line_protocol()
                            if lp:
                                f.write(lp)
                                f.write("\n")
                                written_b += len(lp) + 1
                                count += 1
                                if isinstance(t, datetime):
                                    if oldest is None or t < oldest:
                                        oldest = t
                                    if newest is None or t > newest:
                                        newest = t
                        except Exception:
                            continue

                        now = time.monotonic()
                        if (now - last_tick) >= 0.25:
                            set_progress(written_bytes=written_b, point_count=count)
                            last_tick = now

            meta = {
                "id": backup_id,
                "display_name": f"FullBackup (v2) {backup_id}",
                "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "kind": "db_full",
                "format": "lp",
                "influx_version": 2,
                "org": cfg.get("org"),
                "bucket": cfg.get("bucket"),
                "point_count": count,
                "bytes": 0,
                "oldest_time": _dt_to_rfc3339_utc(oldest) if oldest else None,
                "newest_time": _dt_to_rfc3339_utc(newest) if newest else None,
                "start": _dt_to_rfc3339_utc(oldest) if oldest else None,
                "stop": _dt_to_rfc3339_utc(newest) if newest else None,
            }
        elif influx_v == 1:
            if not cfg.get("database"):
                set_state("error", "Konfiguration fehlt")
                set_error("InfluxDB v1 erfordert database. Bitte in Einstellungen speichern.")
                return

            q = "SHOW MEASUREMENTS"
            set_progress(query=q, written_bytes=0, point_count=0)
            c = v1_client(cfg)
            try:
                try:
                    c.switch_database(cfg.get("database"))
                except Exception:
                    pass

                def _v1_items(res_obj: Any, key: str) -> list[str]:
                    items: list[str] = []
                    try:
                        for _, pts in (res_obj or {}).items():
                            for p in pts:
                                v = p.get(key)
                                if v:
                                    items.append(str(v))
                    except Exception:
                        return []
                    return items

                mres = c.query("SHOW MEASUREMENTS")
                measurements = sorted(set(_v1_items(mres, "name")))

                with lp_path.open("w", encoding="utf-8") as f:
                    for m in measurements:
                        if is_cancelled():
                            set_state("cancelled", "Abgebrochen")
                            raise RuntimeError("cancelled")

                        # Determine tag keys / field types for correct line protocol formatting.
                        tag_keys = sorted(set(_v1_items(c.query(f'SHOW TAG KEYS FROM "{m}"'), "tagKey")))
                        ftypes: dict[str, str] = {}
                        try:
                            fres = c.query(f'SHOW FIELD KEYS FROM "{m}"')
                            for _, pts in (fres or {}).items():
                                for p in pts:
                                    fk = p.get("fieldKey")
                                    ft = p.get("fieldType")
                                    if fk and ft:
                                        ftypes[str(fk)] = str(ft)
                        except Exception:
                            ftypes = {}

                        # Stream all points for this measurement (may be large).
                        try:
                            rs = c.query(f'SELECT * FROM "{m}"', epoch="ns", chunked=True, chunk_size=5000)
                        except TypeError:
                            rs = c.query(f'SELECT * FROM "{m}"', epoch="ns")

                        gp = getattr(rs, "get_points", None)
                        if not gp:
                            continue
                        for pt in gp():
                            if is_cancelled():
                                set_state("cancelled", "Abgebrochen")
                                raise RuntimeError("cancelled")
                            try:
                                ts = pt.get("time")
                                if ts is None:
                                    continue
                                if isinstance(ts, (int, float)):
                                    t_ns = int(ts)
                                    t_dt = datetime.fromtimestamp(t_ns / 1_000_000_000.0, tz=timezone.utc)
                                else:
                                    t_dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
                                    t_ns = int(t_dt.timestamp() * 1_000_000_000)

                                tags: dict[str, str] = {}
                                for k in tag_keys:
                                    tv = pt.get(k)
                                    if tv is None:
                                        continue
                                    s = str(tv)
                                    if not s:
                                        continue
                                    tags[k] = s

                                fields: dict[str, str] = {}
                                for k in sorted(pt.keys()):
                                    if k == "time":
                                        continue
                                    if k in tag_keys:
                                        continue
                                    v = pt.get(k)
                                    if v is None:
                                        continue
                                    fv = _lp_format_field_value(v, ftypes.get(k))
                                    if fv is None:
                                        continue
                                    fields[k] = fv
                                if not fields:
                                    continue

                                # Build line protocol: measurement[,tags] fields timestamp
                                meas = _lp_escape_key(str(m))
                                tag_str = ""
                                if tags:
                                    parts = [f"{_lp_escape_key(tk)}={_lp_escape_tag_value(tv)}" for tk, tv in sorted(tags.items())]
                                    tag_str = "," + ",".join(parts)
                                field_str = ",".join([f"{_lp_escape_key(fk)}={fields[fk]}" for fk in sorted(fields.keys())])
                                line = f"{meas}{tag_str} {field_str} {t_ns}"
                                f.write(line)
                                f.write("\n")
                                written_b += len(line) + 1
                                count += 1
                                if oldest is None or t_dt < oldest:
                                    oldest = t_dt
                                if newest is None or t_dt > newest:
                                    newest = t_dt
                            except Exception:
                                continue

                            now = time.monotonic()
                            if (now - last_tick) >= 0.25:
                                set_progress(written_bytes=written_b, point_count=count)
                                last_tick = now
            finally:
                try:
                    c.close()
                except Exception:
                    pass

            meta = {
                "id": backup_id,
                "display_name": f"FullBackup (v1) {backup_id}",
                "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "kind": "db_full",
                "format": "lp",
                "influx_version": 1,
                "database": cfg.get("database"),
                "point_count": count,
                "bytes": 0,
                "oldest_time": _dt_to_rfc3339_utc(oldest) if oldest else None,
                "newest_time": _dt_to_rfc3339_utc(newest) if newest else None,
                "start": _dt_to_rfc3339_utc(oldest) if oldest else None,
                "stop": _dt_to_rfc3339_utc(newest) if newest else None,
            }
        else:
            set_state("error", "Nicht unterstuetzt")
            set_error(f"FullBackup wird fuer influx_version={influx_v} nicht unterstuetzt.")
            return

        bytes_size = written_b
        if bytes_size <= 0:
            try:
                bytes_size = int(lp_path.stat().st_size)
            except Exception:
                bytes_size = written_b

        meta["bytes"] = bytes_size
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
        try:
            _backup_pack_zip(bdir, backup_id, meta_path, lp_path)
        except Exception:
            pass
        set_progress(written_bytes=bytes_size, point_count=count)
        set_state("done", f"FullBackup created: {backup_id}")
        return
    except Exception as e:
        msg = str(e)
        if "cancelled" in msg:
            try:
                if meta_path.exists():
                    meta_path.unlink()
            except Exception:
                pass
            try:
                if lp_path.exists():
                    lp_path.unlink()
            except Exception:
                pass
            try:
                zpath = _backup_zip_path(bdir, backup_id)
                if zpath.exists():
                    zpath.unlink()
            except Exception:
                pass
            return

        set_state("error", "Fehler")
        set_error(_short_influx_error(e))
        try:
            if meta_path.exists():
                meta_path.unlink()
        except Exception:
            pass
        try:
            if lp_path.exists():
                lp_path.unlink()
        except Exception:
            pass
        try:
            zpath = _backup_zip_path(bdir, backup_id)
            if zpath.exists():
                zpath.unlink()
        except Exception:
            pass
        return


def _fullrestore_job_public(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": job.get("id"),
        "state": job.get("state"),
        "message": job.get("message"),
        "started_at": job.get("started_at"),
        "elapsed": _job_elapsed_hms(job),
        "format": str(job.get("format") or "lp"),
        "target_bucket": job.get("target_bucket"),
        "overwrite": bool(job.get("overwrite")),
        "applied": int(job.get("applied") or 0),
        "read_lines": int(job.get("read_lines") or 0),
        "backup_id": job.get("backup_id"),
        "cancelled": bool(job.get("cancelled")),
        "error": job.get("error"),
        "ready": job.get("state") in ("done", "error", "cancelled"),
    }


def _fullrestore_job_thread(job_id: str, cfg: dict[str, Any], backup_id: str) -> None:
    with FULLRESTORE_LOCK:
        job = FULLRESTORE_JOBS.get(job_id)
    if not job:
        return

    def set_state(state: str, msg: str) -> None:
        with FULLRESTORE_LOCK:
            if job_id in FULLRESTORE_JOBS:
                FULLRESTORE_JOBS[job_id]["state"] = state
                FULLRESTORE_JOBS[job_id]["message"] = msg
                if state in ("done", "error", "cancelled"):
                    _job_set_finished(FULLRESTORE_JOBS[job_id])

    def set_error(msg: str) -> None:
        with FULLRESTORE_LOCK:
            if job_id in FULLRESTORE_JOBS:
                FULLRESTORE_JOBS[job_id]["error"] = msg

    def set_progress(**kw: Any) -> None:
        with FULLRESTORE_LOCK:
            j = FULLRESTORE_JOBS.get(job_id)
            if not j:
                return
            for k, v in kw.items():
                j[k] = v

    def is_cancelled() -> bool:
        with FULLRESTORE_LOCK:
            j = FULLRESTORE_JOBS.get(job_id) or {}
            if bool(j.get("cancelled")):
                return True

            try:
                max_s = int(cfg.get("jobs_max_runtime_seconds", 0) or 0)
            except Exception:
                max_s = 0
            if max_s <= 0:
                return False
            try:
                started_mono = float(j.get("started_mono") or 0.0)
            except Exception:
                started_mono = 0.0
            if started_mono > 0 and (time.monotonic() - started_mono) >= float(max_s):
                FULLRESTORE_JOBS[job_id]["cancelled"] = True
                try:
                    LOG.warning(
                        "job_auto_cancel type=fullrestore job_id=%s reason=max_runtime_seconds exceeded (%s)",
                        job_id,
                        max_s,
                    )
                except Exception:
                    pass
                return True
            return False

    influx_v = int(cfg.get("influx_version", 2) or 2)
    if influx_v == 3:
        set_state("error", "Nicht unterstuetzt")
        set_error("FullRestore wird aktuell nicht fuer InfluxDB v3 unterstuetzt.")
        return
    if influx_v == 2:
        if not str(cfg.get("org") or "").strip():
            set_state("error", "Konfiguration fehlt")
            set_error("InfluxDB v2 erfordert org. Bitte in Einstellungen speichern.")
            return
    elif influx_v == 1:
        if not cfg.get("database"):
            set_state("error", "Konfiguration fehlt")
            set_error("InfluxDB v1 erfordert database. Bitte in Einstellungen speichern.")
            return
    else:
        set_state("error", "Nicht unterstuetzt")
        set_error(f"FullRestore wird fuer influx_version={influx_v} nicht unterstuetzt.")
        return

    bdir = backup_dir(cfg)
    meta = _read_backup_meta(bdir, backup_id) or {}
    if str(meta.get("kind") or "") != "db_full":
        set_state("error", "Backup ungueltig")
        set_error("Kein FullBackup (kind!=db_full).")
        return

    fmt = str(meta.get("format") or job.get("format") or "lp").strip() or "lp"
    if fmt != "native_v2":
        try:
            # Ensure payload exists (zip or legacy)
            with _open_backup_lp_text(bdir, backup_id, is_fullbackup=True):
                pass
        except Exception:
            set_state("error", "Backup nicht gefunden")
            set_error("FullBackup Datei nicht gefunden.")
            return
    if fmt == "native_v2":
        if not _influx_cli_available():
            plat = _ha_platform()
            set_state("error", "Nicht unterstuetzt")
            set_error(
                "Native FullRestore ist auf dieser Plattform nicht verfuegbar (Influx CLI fehlt). "
                f"HA Plattform: {plat}."
            )
            try:
                LOG.warning("native_cli_missing type=fullrestore platform=%s job_id=%s", plat, job_id)
            except Exception:
                pass
            return
        if influx_v != 2:
            set_state("error", "Nicht unterstuetzt")
            set_error("Native FullRestore wird nur fuer InfluxDB v2 unterstuetzt.")
            return

        admin_token = str(cfg.get("admin_token") or "").strip()
        if not admin_token:
            set_state("error", "Konfiguration fehlt")
            set_error("Native FullRestore erfordert admin_token. Bitte in Einstellungen speichern.")
            return

        src_bucket = str(meta.get("bucket") or "").strip()
        if not src_bucket:
            set_state("error", "Backup ungueltig")
            set_error("Native FullBackup meta.bucket fehlt.")
            return

        tgt_bucket = str(job.get("target_bucket") or "").strip() or src_bucket
        overwrite = bool(job.get("overwrite"))

        # Native backups require the packed zip file.
        zpath = _backup_zip_path(bdir, backup_id)
        if not zpath.exists():
            set_state("error", "Backup nicht gefunden")
            set_error("Native FullBackup ZIP Datei nicht gefunden.")
            return

        set_state("running", "Native Restore laeuft...")
        out_lines = 0

        def _bucket_exists(name: str) -> bool:
            try:
                with v2_admin_client(cfg, timeout_seconds_override=min(20, int(cfg.get("timeout_seconds") or 10))) as c:
                    b = c.buckets_api().find_buckets(org=str(cfg.get("org") or ""))
                    buckets = getattr(b, "buckets", None) or []
                    for buck in buckets:
                        try:
                            if str(getattr(buck, "name", "") or "") == name:
                                return True
                        except Exception:
                            continue
            except Exception:
                return False
            return False

        def _delete_bucket(name: str) -> None:
            with v2_admin_client(cfg, timeout_seconds_override=min(60, int(cfg.get("timeout_seconds") or 10))) as c:
                bapi = c.buckets_api()
                b = bapi.find_buckets(org=str(cfg.get("org") or ""))
                buckets = getattr(b, "buckets", None) or []
                for buck in buckets:
                    try:
                        if str(getattr(buck, "name", "") or "") == name:
                            bapi.delete_bucket(buck)
                            return
                    except Exception:
                        continue

        # Enforce the CLI rule: cannot restore into an existing bucket.
        try:
            if _bucket_exists(tgt_bucket):
                if not overwrite:
                    set_state("error", "Bucket existiert")
                    set_error(
                        "influx restore kann nicht in existierende Buckets schreiben. "
                        "Nutze ein neues Ziel (new-bucket) oder aktiviere 'Ueberschreiben' (loescht Zielbucket vorher)."
                    )
                    return
                _delete_bucket(tgt_bucket)
                # Give the server a short moment to finalize the delete.
                t0 = time.monotonic()
                while time.monotonic() - t0 < 10.0:
                    if not _bucket_exists(tgt_bucket):
                        break
                    time.sleep(0.5)
        except Exception as e:
            set_state("error", "Fehler")
            set_error(_short_influx_error(e))
            return

        # Extract zip to temp dir and run `influx restore`.
        cmd: list[str] = ["influx", "restore", "--bucket", src_bucket]
        if tgt_bucket != src_bucket:
            cmd.extend(["--new-bucket", tgt_bucket])

        cmd_redacted = (
            f"influx restore --host {json.dumps(_influx_url(cfg))} --org {json.dumps(str(cfg.get('org') or ''))} "
            f"--bucket {json.dumps(src_bucket)}"
            + (f" --new-bucket {json.dumps(tgt_bucket)}" if tgt_bucket != src_bucket else "")
            + " <backup_dir>"
        )
        set_progress(read_lines=0, applied=0, target_bucket=tgt_bucket, overwrite=overwrite)
        try:
            set_progress(message=None, query=cmd_redacted)
        except Exception:
            pass

        tail: list[str] = []
        p: subprocess.Popen[str] | None = None
        try:
            with tempfile.TemporaryDirectory(prefix="influxbro_native_restore_") as tmpdir:
                tmp = Path(tmpdir)
                with zipfile.ZipFile(zpath, mode="r") as z:
                    # safe extraction (zip is user-controlled via upload/download)
                    for name in z.namelist():
                        n = str(name or "")
                        if not n or n.startswith("/") or ".." in n.replace("\\", "/").split("/"):
                            raise RuntimeError("invalid zip entry")
                    z.extractall(tmp)

                payload = tmp / "native"
                if not payload.exists():
                    payload = tmp

                cmd2 = cmd + [str(payload)]
                env = _influx_cli_env(cfg, token=admin_token)
                p = subprocess.Popen(
                    cmd2,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env,
                )
                out = p.stdout
                last_tick = time.monotonic()
                while True:
                    if is_cancelled():
                        try:
                            p.terminate()
                        except Exception:
                            pass
                        set_state("cancelled", "Abgebrochen")
                        raise RuntimeError("cancelled")

                    if out is not None:
                        try:
                            r, _w, _x = select.select([out], [], [], 0.25)
                        except Exception:
                            r = []
                        if r:
                            try:
                                ln = out.readline()
                            except Exception:
                                ln = ""
                            s = (ln or "").rstrip("\n")
                            if s:
                                out_lines += 1
                                tail.append(s)
                                if len(tail) > 30:
                                    tail = tail[-30:]
                                set_state("running", s[:240])

                    now = time.monotonic()
                    if (now - last_tick) >= 0.5:
                        set_progress(read_lines=out_lines, applied=0)
                        last_tick = now

                    if p.poll() is not None:
                        break

                rc = p.wait() if p is not None else 1
                if rc != 0:
                    msg = "Native Restore fehlgeschlagen"
                    if tail:
                        msg = msg + ": " + tail[-1]
                    raise RuntimeError(msg)

        except Exception as e:
            msg = str(e)
            if "cancelled" in msg:
                return
            set_state("error", "Fehler")
            set_error(_short_influx_error(e if isinstance(e, Exception) else Exception(str(e))))
            return

        set_progress(read_lines=out_lines, applied=0)
        set_state("done", "Native Restore done")
        return

    set_state("running", "Restore laeuft...")
    read_lines = 0
    applied = 0
    last_tick = time.monotonic()

    try:
        if influx_v == 2:
            with v2_client(cfg) as c:
                wapi = c.write_api(write_options=SYNCHRONOUS)
                batch: list[str] = []
                with _open_backup_lp_text(bdir, backup_id, is_fullbackup=True) as f:
                    for line in f:
                        if is_cancelled():
                            set_state("cancelled", "Abgebrochen")
                            raise RuntimeError("cancelled")
                        s = line.strip("\n")
                        if not s.strip():
                            continue
                        read_lines += 1
                        batch.append(s)
                        if len(batch) >= 2000:
                            wapi.write(
                                bucket=cfg["bucket"],
                                org=cfg["org"],
                                record=batch,
                                write_precision=WritePrecision.NS,
                            )
                            applied += len(batch)
                            batch = []

                        now = time.monotonic()
                        if (now - last_tick) >= 0.25:
                            set_progress(read_lines=read_lines, applied=applied)
                            last_tick = now

                    if batch:
                        wapi.write(
                            bucket=cfg["bucket"],
                            org=cfg["org"],
                            record=batch,
                            write_precision=WritePrecision.NS,
                        )
                        applied += len(batch)
        elif influx_v == 1:
            c = v1_client(cfg)
            try:
                try:
                    c.switch_database(cfg.get("database"))
                except Exception:
                    pass

                batch: list[str] = []
                with _open_backup_lp_text(bdir, backup_id, is_fullbackup=True) as f:
                    for line in f:
                        if is_cancelled():
                            set_state("cancelled", "Abgebrochen")
                            raise RuntimeError("cancelled")
                        s = line.strip("\n")
                        if not s.strip():
                            continue
                        read_lines += 1
                        batch.append(s)
                        if len(batch) >= 2000:
                            c.write_points(
                                batch,
                                database=cfg.get("database"),
                                protocol="line",
                                time_precision="n",
                            )
                            applied += len(batch)
                            batch = []

                        now = time.monotonic()
                        if (now - last_tick) >= 0.25:
                            set_progress(read_lines=read_lines, applied=applied)
                            last_tick = now

                    if batch:
                        c.write_points(
                            batch,
                            database=cfg.get("database"),
                            protocol="line",
                            time_precision="n",
                        )
                        applied += len(batch)
            finally:
                try:
                    c.close()
                except Exception:
                    pass

        set_progress(read_lines=read_lines, applied=applied)
        set_state("done", f"Restored points: {applied}")
        return
    except Exception as e:
        msg = str(e)
        if "cancelled" in msg:
            return
        set_state("error", "Fehler")
        set_error(_short_influx_error(e))
        return


def _lp_escape_key(v: str) -> str:
    # For measurement, tag keys, and field keys.
    return (v or "").replace("\\", "\\\\").replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def _lp_escape_tag_value(v: str) -> str:
    return (v or "").replace("\\", "\\\\").replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def _lp_escape_field_string(v: str) -> str:
    # String field values must be double-quoted; escape backslashes and quotes.
    s = str(v or "")
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def _lp_format_field_value(v: Any, field_type: str | None) -> str | None:
    """Format a Python value into line protocol field value.

    field_type is InfluxDB v1 SHOW FIELD KEYS type string (e.g. integer, float, boolean, string).
    """
    if v is None:
        return None
    ft = str(field_type or "").strip().lower()

    # Prefer the declared field type when available.
    try:
        if ft == "integer":
            return f"{int(v)}i"
        if ft == "float":
            return str(float(v))
        if ft == "boolean":
            return "true" if bool(v) else "false"
        if ft == "string":
            return _lp_escape_field_string(str(v))
    except Exception:
        pass

    # Fallback: infer from Python type.
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int) and not isinstance(v, bool):
        return f"{v}i"
    if isinstance(v, float):
        if not math.isfinite(v):
            return None
        return str(v)
    if isinstance(v, (bytes, bytearray)):
        return _lp_escape_field_string(v.decode("utf-8", errors="replace"))
    return _lp_escape_field_string(str(v))


def _dt_to_ns(dt: datetime) -> int:
    return int(dt.astimezone(timezone.utc).timestamp() * 1_000_000_000)


@app.get("/api/backups")
def api_backups():
    cfg = load_cfg()
    bdir = backup_dir(cfg)

    measurement = (request.args.get("measurement") or "").strip()
    field = (request.args.get("field") or "").strip()
    entity_id = (request.args.get("entity_id") or "").strip() or None
    friendly_name = (request.args.get("friendly_name") or "").strip() or None

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    backups = _list_backups(bdir)
    filtered: list[dict[str, Any]] = []
    for b in backups:
        if str(b.get("measurement") or "") != measurement:
            continue
        if str(b.get("field") or "") != field:
            continue
        if entity_id and str(b.get("entity_id") or "") != entity_id:
            continue
        if friendly_name and str(b.get("friendly_name") or "") != friendly_name:
            continue
        filtered.append(b)

    latest = filtered[0] if filtered else None
    return jsonify({"ok": True, "backups": filtered, "latest": latest})


@app.get("/api/backups_all")
def api_backups_all():
    cfg = load_cfg()
    bdir = backup_dir(cfg)
    backups = _list_backups(bdir)
    return jsonify({"ok": True, "backups": backups})


@app.get("/api/fullbackups_all")
def api_fullbackups_all():
    cfg = load_cfg()
    bdir = backup_dir(cfg)
    backups = [b for b in _list_backups(bdir, include_db_full=True) if str(b.get("kind") or "") == "db_full"]
    return jsonify({"ok": True, "backups": backups})


@app.post("/api/fullbackup_job/start")
def api_fullbackup_job_start():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    ok_free, msg = _backup_require_free_space(cfg)
    if not ok_free:
        return jsonify({"ok": False, "error": msg}), 507

    influx_v = int(cfg.get("influx_version", 2) or 2)
    if influx_v == 3:
        return jsonify({"ok": False, "error": "fullbackup currently does not support InfluxDB v3"}), 400
    if influx_v == 2:
        fmt = str(body.get("format") or body.get("mode") or "").strip() or "lp"
        if fmt == "native_v2":
            if not _influx_cli_available():
                plat = _ha_platform()
                try:
                    LOG.warning("native_cli_missing type=fullbackup platform=%s", plat)
                except Exception:
                    pass
                return jsonify({
                    "ok": False,
                    "error": (
                        "Native v2 FullBackup ist auf dieser Plattform nicht verfuegbar (Influx CLI fehlt). "
                        f"HA Plattform: {plat}."
                    ),
                }), 400
            if not (cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "Native v2 FullBackup requires org and bucket. Bitte in Einstellungen speichern.",
                }), 400
            if not str(cfg.get("admin_token") or "").strip():
                return jsonify({
                    "ok": False,
                    "error": "Native v2 FullBackup requires admin_token (Einstellungen).",
                }), 400

            # Preflight: ensure the admin token has permissions for metadata backup.
            # Influx CLI needs to read authorizations -> requires an all-access token.
            try:
                with v2_admin_client(cfg, timeout_seconds_override=min(8, int(cfg.get("timeout_seconds") or 10))) as c:
                    try:
                        # best-effort: will fail with 401 if token is not all-access
                        # best-effort: will fail with 401 if token is not all-access
                        # Older/newer client libs may have different signatures; avoid passing params.
                        c.authorizations_api().find_authorizations()  # type: ignore[attr-defined]
                    except Exception as e:
                        raise e
            except Exception as e:
                try:
                    LOG.warning("fullbackup_preflight_failed err=%s", _short_influx_error(e))
                except Exception:
                    pass
                return jsonify({
                    "ok": False,
                    "error": _short_influx_error(e),
                }), 400
        else:
            fmt = "lp"
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400
    elif influx_v == 1:
        fmt = "lp"
        if not cfg.get("database"):
            return jsonify({
                "ok": False,
                "error": "InfluxDB v1 requires database. Bitte in Einstellungen konfigurieren.",
            }), 400
    else:
        return jsonify({"ok": False, "error": f"unsupported influx_version: {influx_v}"}), 400

    job_id = uuid.uuid4().hex
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if influx_v == 2 and fmt == "native_v2":
        backup_id = f"fullbackup__db_full__native_v2__{ts}"
    else:
        backup_id = f"fullbackup__db_full__v{influx_v}__{ts}"

    bdir = backup_dir(cfg)
    bdir.mkdir(parents=True, exist_ok=True)
    meta_path, lp_path = _fullbackup_files(bdir, backup_id)
    if _backup_zip_path(bdir, backup_id).exists() or meta_path.exists() or lp_path.exists():
        return jsonify({"ok": False, "error": "backup id collision"}), 409

    ip = _req_ip()
    ua = _req_ua()
    job = {
        "id": job_id,
        "state": "queued",
        "message": "Start...",
        "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "started_mono": time.monotonic(),
        "trigger_page": "backup",
        "trigger_ip": ip,
        "trigger_ua": ua,
        "backup_id": backup_id,
        "influx_version": influx_v,
        "format": fmt,
        "written_bytes": 0,
        "point_count": 0,
        "cancelled": False,
        "error": None,
    }

    with FULLBACKUP_LOCK:
        FULLBACKUP_JOBS[job_id] = job
        cutoff = time.monotonic() - 24 * 3600
        old = [k for k, v in FULLBACKUP_JOBS.items() if float(v.get("started_mono") or 0) < cutoff]
        for k in old:
            FULLBACKUP_JOBS.pop(k, None)

    try:
        LOG.info(
            "job_start type=fullbackup job_id=%s ip=%s ua=%s backup_id=%s",
            job_id,
            ip,
            ua,
            backup_id,
        )
    except Exception:
        pass

    t = threading.Thread(target=_fullbackup_job_thread, args=(job_id, cfg, backup_id), daemon=True)
    t.start()
    return jsonify({"ok": True, "job_id": job_id, "backup_id": backup_id})


@app.get("/api/fullbackup_job/status")
def api_fullbackup_job_status():
    job_id = (request.args.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with FULLBACKUP_LOCK:
        job = FULLBACKUP_JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    return jsonify({"ok": True, "status": _fullbackup_job_public(job)})


@app.post("/api/fullbackup_job/cancel")
def api_fullbackup_job_cancel():
    body = request.get_json(force=True) or {}
    job_id = (body.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with FULLBACKUP_LOCK:
        job = FULLBACKUP_JOBS.get(job_id)
        if not job:
            return jsonify({"ok": False, "error": "job not found"}), 404
        job["cancelled"] = True
    try:
        LOG.info("job_cancel type=fullbackup job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
    except Exception:
        pass
    return jsonify({"ok": True})


@app.get("/api/fullbackup_download")
def api_fullbackup_download():
    cfg = load_cfg()
    bdir = backup_dir(cfg)
    backup_id = str(request.args.get("id") or "").strip()
    if not backup_id:
        return jsonify({"ok": False, "error": "id required"}), 400
    if _backup_safe(backup_id) != backup_id:
        return jsonify({"ok": False, "error": "invalid id"}), 400

    meta = _read_backup_meta(bdir, backup_id) or {}
    if str(meta.get("kind") or "") != "db_full":
        return jsonify({"ok": False, "error": "not a fullbackup (kind!=db_full)"}), 400

    # Prefer packed zip on disk
    zpath = _backup_zip_path(bdir, backup_id)
    if zpath.exists() and zpath.is_file():
        return send_file(zpath, as_attachment=True, download_name=zpath.name, mimetype="application/zip")

    # Legacy: zip meta+lp on the fly
    meta_path, lp_path = _fullbackup_files(bdir, backup_id)
    if not meta_path.exists() or not lp_path.exists():
        return jsonify({"ok": False, "error": "backup not found"}), 404

    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
            z.write(meta_path, arcname=meta_path.name)
            z.write(lp_path, arcname=lp_path.name)
        buf.seek(0)
        fn = f"{backup_id}.zip"
        return send_file(buf, as_attachment=True, download_name=fn, mimetype="application/zip")
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500


@app.post("/api/fullbackup_delete")
def api_fullbackup_delete():
    body = request.get_json(force=True) or {}
    backup_id = (body.get("id") or "").strip()
    if not backup_id:
        return jsonify({"ok": False, "error": "id required"}), 400
    if _backup_safe(backup_id) != backup_id:
        return jsonify({"ok": False, "error": "invalid id"}), 400
    cfg = load_cfg()
    bdir = backup_dir(cfg)
    bdir.mkdir(parents=True, exist_ok=True)

    meta = _read_backup_meta(bdir, backup_id) or {}
    if str(meta.get("kind") or "") != "db_full":
        return jsonify({"ok": False, "error": "not a fullbackup (kind!=db_full)"}), 400
    zpath = _backup_zip_path(bdir, backup_id)
    meta_path, lp_path = _fullbackup_files(bdir, backup_id)
    removed = 0
    for p in (zpath, meta_path, lp_path):
        try:
            if p.exists():
                p.unlink()
                removed += 1
        except Exception:
            pass
    if removed == 0:
        return jsonify({"ok": False, "error": "backup not found"}), 404
    return jsonify({"ok": True, "message": f"Deleted: {backup_id}"})


@app.post("/api/fullrestore_job/start")
def api_fullrestore_job_start():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", False)
    ok_confirm = confirm is True or str(confirm).strip().lower() in ("1", "true", "yes", "on")
    if not ok_confirm:
        return jsonify({"ok": False, "error": "Confirmation required"}), 400

    backup_id = str(body.get("id") or "").strip()
    if not backup_id:
        return jsonify({"ok": False, "error": "id required"}), 400

    influx_v = int(cfg.get("influx_version", 2) or 2)
    if influx_v == 3:
        return jsonify({"ok": False, "error": "fullrestore currently does not support InfluxDB v3"}), 400
    if influx_v == 2:
        if not str(cfg.get("org") or "").strip():
            return jsonify({
                "ok": False,
                "error": "InfluxDB v2 requires org. Bitte in /config YAML einlesen und speichern.",
            }), 400
    elif influx_v == 1:
        if not cfg.get("database"):
            return jsonify({
                "ok": False,
                "error": "InfluxDB v1 requires database. Bitte in Einstellungen konfigurieren.",
            }), 400
    else:
        return jsonify({"ok": False, "error": f"unsupported influx_version: {influx_v}"}), 400

    bdir = backup_dir(cfg)
    meta = _read_backup_meta(bdir, backup_id)
    if not meta:
        return jsonify({"ok": False, "error": "backup not found"}), 404
    if str(meta.get("kind") or "") != "db_full":
        return jsonify({"ok": False, "error": "not a fullbackup (kind!=db_full)"}), 400
    try:
        meta_v = int(meta.get("influx_version") or 0)
    except Exception:
        meta_v = 0
    if meta_v and meta_v != influx_v:
        return jsonify({"ok": False, "error": f"backup influx_version mismatch: backup={meta_v} cfg={influx_v}"}), 400
    fmt = str(meta.get("format") or "lp").strip() or "lp"
    if influx_v == 2 and fmt == "native_v2":
        if not _influx_cli_available():
            plat = _ha_platform()
            try:
                LOG.warning("native_cli_missing type=fullrestore platform=%s backup_id=%s", plat, backup_id)
            except Exception:
                pass
            return jsonify({
                "ok": False,
                "error": (
                    "Native FullRestore ist auf dieser Plattform nicht verfuegbar (Influx CLI fehlt). "
                    f"HA Plattform: {plat}."
                ),
            }), 400
        # Native restore uses the Influx CLI and requires an admin token.
        if not str(cfg.get("admin_token") or "").strip():
            return jsonify({"ok": False, "error": "Native restore requires admin_token (Einstellungen)"}), 400
        if meta.get("org") and str(meta.get("org")) != str(cfg.get("org") or ""):
            return jsonify({"ok": False, "error": "backup org mismatch (configure same org for restore)"}), 400
    elif influx_v == 2:
        if not (cfg.get("token") and cfg.get("bucket")):
            return jsonify({
                "ok": False,
                "error": "InfluxDB v2 (Line Protocol) requires token and bucket. Bitte in /config YAML einlesen und speichern.",
            }), 400
        if meta.get("bucket") and str(meta.get("bucket")) != str(cfg.get("bucket") or ""):
            return jsonify({"ok": False, "error": "backup bucket mismatch (configure same bucket for restore)"}), 400
        if meta.get("org") and str(meta.get("org")) != str(cfg.get("org") or ""):
            return jsonify({"ok": False, "error": "backup org mismatch (configure same org for restore)"}), 400
    if influx_v == 1:
        if meta.get("database") and str(meta.get("database")) != str(cfg.get("database") or ""):
            return jsonify({"ok": False, "error": "backup database mismatch (configure same database for restore)"}), 400

    target_bucket = str(body.get("target_bucket") or "").strip() or None
    overwrite = body.get("overwrite", False)
    overwrite_on = overwrite is True or str(overwrite).strip().lower() in ("1", "true", "yes", "on")

    job_id = uuid.uuid4().hex
    ip = _req_ip()
    ua = _req_ua()
    job = {
        "id": job_id,
        "state": "queued",
        "message": "Start...",
        "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "started_mono": time.monotonic(),
        "trigger_page": "restore",
        "trigger_ip": ip,
        "trigger_ua": ua,
        "backup_id": backup_id,
        "influx_version": influx_v,
        "format": fmt,
        "target_bucket": target_bucket,
        "overwrite": bool(overwrite_on),
        "read_lines": 0,
        "applied": 0,
        "cancelled": False,
        "error": None,
    }
    with FULLRESTORE_LOCK:
        FULLRESTORE_JOBS[job_id] = job
        cutoff = time.monotonic() - 24 * 3600
        old = [k for k, v in FULLRESTORE_JOBS.items() if float(v.get("started_mono") or 0) < cutoff]
        for k in old:
            FULLRESTORE_JOBS.pop(k, None)

    try:
        LOG.info("job_start type=fullrestore job_id=%s ip=%s ua=%s backup_id=%s", job_id, ip, ua, backup_id)
    except Exception:
        pass

    t = threading.Thread(target=_fullrestore_job_thread, args=(job_id, cfg, backup_id), daemon=True)
    t.start()
    return jsonify({"ok": True, "job_id": job_id})


@app.get("/api/fullrestore_job/status")
def api_fullrestore_job_status():
    job_id = (request.args.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with FULLRESTORE_LOCK:
        job = FULLRESTORE_JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    return jsonify({"ok": True, "status": _fullrestore_job_public(job)})


@app.post("/api/fullrestore_job/cancel")
def api_fullrestore_job_cancel():
    body = request.get_json(force=True) or {}
    job_id = (body.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with FULLRESTORE_LOCK:
        job = FULLRESTORE_JOBS.get(job_id)
        if not job:
            return jsonify({"ok": False, "error": "job not found"}), 404
        job["cancelled"] = True
    try:
        LOG.info("job_cancel type=fullrestore job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
    except Exception:
        pass
    return jsonify({"ok": True})


@app.post("/api/backup_create")
def api_backup_create():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    bdir = backup_dir(cfg)
    ok_free, msg = _backup_require_free_space(cfg)
    if not ok_free:
        return jsonify({"ok": False, "error": msg}), 507
    body = request.get_json(force=True) or {}
    measurement = (body.get("measurement") or "").strip()
    field = (body.get("field") or "").strip()
    entity_id = (body.get("entity_id") or "").strip() or None
    friendly_name = (body.get("friendly_name") or "").strip() or None

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400
    if not entity_id and not friendly_name:
        return jsonify({"ok": False, "error": "entity_id or friendly_name required"}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "backup currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    bdir.mkdir(parents=True, exist_ok=True)

    # Derive a stable display name for file ids
    display = friendly_name or entity_id or f"{measurement}_{field}"
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_kind = "full"
    backup_id = _backup_safe(display) + "__" + backup_kind + "__" + ts
    meta_path, lp_path = _backup_files(bdir, backup_id)
    if _backup_zip_path(bdir, backup_id).exists() or meta_path.exists() or lp_path.exists():
        return jsonify({"ok": False, "error": "backup id collision"}), 409

    # Export all points for this single signal
    extra = flux_tag_filter(entity_id, friendly_name)
    range_clause = '|> range(start: time(v: "1970-01-01T00:00:00Z"))'
    q = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> sort(columns: ["_time"])
'''

    log_query("api.backup_create (flux)", q)
    count = 0
    oldest: datetime | None = None
    newest: datetime | None = None

    try:
        with v2_client(cfg) as c:
            qapi = c.query_api()

            with lp_path.open("w", encoding="utf-8") as f:
                for rec in qapi.query_stream(q, org=cfg["org"]):
                    # rec is a FluxRecord
                    try:
                        t = rec.get_time()
                        v = rec.get_value()
                        m = rec.values.get("_measurement") or measurement
                        fld = rec.values.get("_field") or field

                        # Only export points with a value
                        if v is None:
                            continue

                        p = Point(str(m))
                        for k, tv in (rec.values or {}).items():
                            if k in ("result", "table"):
                                continue
                            if str(k).startswith("_"):
                                continue
                            if tv is None:
                                continue
                            p = p.tag(str(k), str(tv))

                        p = p.field(str(fld), v)
                        if isinstance(t, datetime):
                            p = p.time(t, WritePrecision.NS)
                        lp = p.to_line_protocol()
                        if lp:
                            f.write(lp)
                            f.write("\n")
                            count += 1
                            if isinstance(t, datetime):
                                if oldest is None or t < oldest:
                                    oldest = t
                                if newest is None or t > newest:
                                    newest = t
                    except Exception:
                        continue

        bytes_size = int(lp_path.stat().st_size) if lp_path.exists() else 0
        meta = {
            "id": backup_id,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "kind": backup_kind,
            "display_name": display,
            "measurement": measurement,
            "field": field,
            "entity_id": entity_id,
            "friendly_name": friendly_name,
            "point_count": count,
            "bytes": bytes_size,
            "oldest_time": _dt_to_rfc3339_utc(oldest) if oldest else None,
            "newest_time": _dt_to_rfc3339_utc(newest) if newest else None,
            "start": _dt_to_rfc3339_utc(oldest) if oldest else None,
            "stop": _dt_to_rfc3339_utc(newest) if newest else None,
        }
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
        try:
            _backup_pack_zip(bdir, backup_id, meta_path, lp_path)
        except Exception:
            # If packing fails, keep legacy files.
            pass
        return jsonify({"ok": True, "message": f"Backup created: {backup_id}", "backup": meta, "query": q.strip()})
    except Exception as e:
        # Cleanup partial files
        try:
            if meta_path.exists():
                meta_path.unlink()
        except Exception:
            pass
        try:
            if lp_path.exists():
                lp_path.unlink()
        except Exception:
            pass
        try:
            zpath = _backup_zip_path(bdir, backup_id)
            if zpath.exists():
                zpath.unlink()
        except Exception:
            pass
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.get("/api/backup_location")
def api_backup_location():
    cfg = load_cfg()
    bdir = backup_dir(cfg)
    du = _backup_disk_usage_bytes(cfg)
    addon_used = _addon_data_usage_bytes()
    return jsonify({
        "ok": True,
        "container_path": str(bdir),
        "slug": "influxbro",
        "disk_usage": du,
        "addon_used_bytes": addon_used,
        "min_free_mb": cfg.get("backup_min_free_mb", 0),
    })


@app.get("/api/backup_download")
def api_backup_download():
    cfg = load_cfg()
    bdir = backup_dir(cfg)
    backup_id = str(request.args.get("id") or "").strip()
    if not backup_id:
        return jsonify({"ok": False, "error": "id required"}), 400
    if _backup_safe(backup_id) != backup_id:
        return jsonify({"ok": False, "error": "invalid id"}), 400

    meta = _read_backup_meta(bdir, backup_id) or {}
    if str(meta.get("kind") or "") == "db_full":
        return jsonify({"ok": False, "error": "this is a fullbackup; use /api/fullbackup_download"}), 400

    # Prefer packed zip on disk
    zpath = _backup_zip_path(bdir, backup_id)
    if zpath.exists() and zpath.is_file():
        return send_file(zpath, as_attachment=True, download_name=zpath.name, mimetype="application/zip")

    meta_path, lp_path = _backup_files(bdir, backup_id)
    if not meta_path.exists() or not lp_path.exists():
        return jsonify({"ok": False, "error": "backup not found"}), 404

    # Legacy: zip both files for a single download.
    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
            z.write(meta_path, arcname=meta_path.name)
            z.write(lp_path, arcname=lp_path.name)
        buf.seek(0)
        fn = f"{backup_id}.zip"
        return send_file(buf, as_attachment=True, download_name=fn, mimetype="application/zip")
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500


@app.post("/api/backup_job/start")
def api_backup_job_start():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}

    ok_free, msg = _backup_require_free_space(cfg)
    if not ok_free:
        return jsonify({"ok": False, "error": msg}), 507

    kind = str(body.get("kind") or "full").strip().lower()
    if kind not in ("full", "range"):
        return jsonify({"ok": False, "error": "kind must be full or range"}), 400

    measurement = (body.get("measurement") or "").strip()
    field = (body.get("field") or "").strip()
    entity_id = (body.get("entity_id") or "").strip() or None
    friendly_name = (body.get("friendly_name") or "").strip() or None
    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400
    if not entity_id and not friendly_name:
        return jsonify({"ok": False, "error": "entity_id or friendly_name required"}), 400

    start_dt: datetime | None = None
    stop_dt: datetime | None = None
    if kind == "range":
        try:
            start_dt, stop_dt = _get_start_stop_from_payload(body)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "backup currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    job_id = uuid.uuid4().hex
    display = friendly_name or entity_id or f"{measurement}_{field}"
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_id = _backup_safe(display) + "__" + kind + "__" + ts

    bdir = backup_dir(cfg)
    bdir.mkdir(parents=True, exist_ok=True)
    meta_path, lp_path = _backup_files(bdir, backup_id)
    if _backup_zip_path(bdir, backup_id).exists() or meta_path.exists() or lp_path.exists():
        return jsonify({"ok": False, "error": "backup id collision"}), 409

    ip = _req_ip()
    ua = _req_ua()
    job = {
        "id": job_id,
        "state": "queued",
        "message": "Start...",
        "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "started_mono": time.monotonic(),
        "trigger_page": "backup",
        "trigger_ip": ip,
        "trigger_ua": ua,
        "backup_kind": kind,
        "backup_id": backup_id,
        "measurement": measurement,
        "field": field,
        "entity_id": entity_id,
        "friendly_name": friendly_name,
        "start": _dt_to_rfc3339_utc(start_dt) if (start_dt and stop_dt) else None,
        "stop": _dt_to_rfc3339_utc(stop_dt) if (start_dt and stop_dt) else None,
        "written_bytes": 0,
        "point_count": 0,
        "cancelled": False,
        "error": None,
    }

    with BACKUP_LOCK:
        BACKUP_JOBS[job_id] = job
        cutoff = time.monotonic() - 24 * 3600
        old = [k for k, v in BACKUP_JOBS.items() if float(v.get("started_mono") or 0) < cutoff]
        for k in old:
            BACKUP_JOBS.pop(k, None)

    try:
        LOG.info(
            "job_start type=backup job_id=%s ip=%s ua=%s backup_id=%s kind=%s measurement=%s field=%s entity_id=%s friendly_name=%s",
            job_id,
            ip,
            ua,
            backup_id,
            kind,
            measurement,
            field,
            entity_id or "",
            friendly_name or "",
        )
    except Exception:
        pass

    t = threading.Thread(
        target=_backup_job_thread,
        args=(job_id, cfg, kind, backup_id, measurement, field, entity_id, friendly_name, start_dt, stop_dt),
        daemon=True,
    )
    t.start()
    return jsonify({"ok": True, "job_id": job_id, "backup_id": backup_id})


@app.get("/api/backup_job/status")
def api_backup_job_status():
    job_id = (request.args.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with BACKUP_LOCK:
        job = BACKUP_JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    return jsonify({"ok": True, "status": _backup_job_public(job)})


@app.post("/api/backup_job/cancel")
def api_backup_job_cancel():
    body = request.get_json(force=True) or {}
    job_id = (body.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with BACKUP_LOCK:
        job = BACKUP_JOBS.get(job_id)
        if not job:
            return jsonify({"ok": False, "error": "job not found"}), 404
        job["cancelled"] = True
    try:
        LOG.info("job_cancel type=backup job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
    except Exception:
        pass
    return jsonify({"ok": True})


@app.post("/api/backup_create_range")
def api_backup_create_range():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    bdir = backup_dir(cfg)
    ok_free, msg = _backup_require_free_space(cfg)
    if not ok_free:
        return jsonify({"ok": False, "error": msg}), 507
    body = request.get_json(force=True) or {}
    measurement = (body.get("measurement") or "").strip()
    field = (body.get("field") or "").strip()
    entity_id = (body.get("entity_id") or "").strip() or None
    friendly_name = (body.get("friendly_name") or "").strip() or None

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400
    if not entity_id and not friendly_name:
        return jsonify({"ok": False, "error": "entity_id or friendly_name required"}), 400

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "backup currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    bdir.mkdir(parents=True, exist_ok=True)

    display = friendly_name or entity_id or f"{measurement}_{field}"
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_kind = "range"
    backup_id = _backup_safe(display) + "__" + backup_kind + "__" + ts
    meta_path, lp_path = _backup_files(bdir, backup_id)
    if _backup_zip_path(bdir, backup_id).exists() or meta_path.exists() or lp_path.exists():
        return jsonify({"ok": False, "error": "backup id collision"}), 409

    extra = flux_tag_filter(entity_id, friendly_name)
    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    range_clause = f'|> range(start: time(v: "{start}"), stop: time(v: "{stop}"))'
    q = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> sort(columns: ["_time"])
'''

    log_query("api.backup_create_range (flux)", q)
    count = 0
    oldest: datetime | None = None
    newest: datetime | None = None

    try:
        with v2_client(cfg) as c:
            qapi = c.query_api()
            with lp_path.open("w", encoding="utf-8") as f:
                for rec in qapi.query_stream(q, org=cfg["org"]):
                    try:
                        t = rec.get_time()
                        v = rec.get_value()
                        m = rec.values.get("_measurement") or measurement
                        fld = rec.values.get("_field") or field
                        if v is None:
                            continue
                        p = Point(str(m))
                        for k, tv in (rec.values or {}).items():
                            if k in ("result", "table"):
                                continue
                            if str(k).startswith("_"):
                                continue
                            if tv is None:
                                continue
                            p = p.tag(str(k), str(tv))
                        p = p.field(str(fld), v)
                        if isinstance(t, datetime):
                            p = p.time(t, WritePrecision.NS)
                        lp = p.to_line_protocol()
                        if lp:
                            f.write(lp)
                            f.write("\n")
                            count += 1
                            if isinstance(t, datetime):
                                if oldest is None or t < oldest:
                                    oldest = t
                                if newest is None or t > newest:
                                    newest = t
                    except Exception:
                        continue

        bytes_size = int(lp_path.stat().st_size) if lp_path.exists() else 0
        meta = {
            "id": backup_id,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "kind": backup_kind,
            "display_name": display,
            "measurement": measurement,
            "field": field,
            "entity_id": entity_id,
            "friendly_name": friendly_name,
            "start": start,
            "stop": stop,
            "point_count": count,
            "bytes": bytes_size,
            "oldest_time": _dt_to_rfc3339_utc(oldest) if oldest else None,
            "newest_time": _dt_to_rfc3339_utc(newest) if newest else None,
        }
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
        try:
            _backup_pack_zip(bdir, backup_id, meta_path, lp_path)
        except Exception:
            pass
        return jsonify({"ok": True, "message": f"Backup created: {backup_id}", "backup": meta, "query": q.strip()})
    except Exception as e:
        try:
            if meta_path.exists():
                meta_path.unlink()
        except Exception:
            pass
        try:
            if lp_path.exists():
                lp_path.unlink()
        except Exception:
            pass
        try:
            zpath = _backup_zip_path(bdir, backup_id)
            if zpath.exists():
                zpath.unlink()
        except Exception:
            pass
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/backup_delete")
def api_backup_delete():
    body = request.get_json(force=True) or {}
    backup_id = (body.get("id") or "").strip()
    if not backup_id:
        return jsonify({"ok": False, "error": "id required"}), 400
    if _backup_safe(backup_id) != backup_id:
        return jsonify({"ok": False, "error": "invalid id"}), 400
    cfg = load_cfg()
    bdir = backup_dir(cfg)
    bdir.mkdir(parents=True, exist_ok=True)

    meta = _read_backup_meta(bdir, backup_id) or {}
    if str(meta.get("kind") or "") == "db_full":
        return jsonify({"ok": False, "error": "this is a fullbackup; use /api/fullbackup_delete"}), 400

    zpath = _backup_zip_path(bdir, backup_id)
    meta_path, lp_path = _backup_files(bdir, backup_id)
    removed = 0
    for p in (zpath, meta_path, lp_path):
        try:
            if p.exists():
                p.unlink()
                removed += 1
        except Exception:
            pass
    if removed == 0:
        return jsonify({"ok": False, "error": "backup not found"}), 404
    return jsonify({"ok": True, "message": f"Deleted: {backup_id}"})


@app.post("/api/backup_restore")
def api_backup_restore():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", False)
    ok_confirm = confirm is True or str(confirm).strip().lower() in ("1", "true", "yes", "on")
    if not ok_confirm:
        return jsonify({"ok": False, "error": "Confirmation required"}), 400

    backup_id = (body.get("id") or "").strip()
    if not backup_id:
        return jsonify({"ok": False, "error": "id required"}), 400
    if _backup_safe(backup_id) != backup_id:
        return jsonify({"ok": False, "error": "invalid id"}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "restore currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    bdir = backup_dir(cfg)
    meta = _read_backup_meta(bdir, backup_id) or {}
    if str(meta.get("kind") or "") == "db_full":
        return jsonify({"ok": False, "error": "this is a fullbackup; use /api/fullrestore_job/start"}), 400

    try:
        # Ensure the payload exists (zip or legacy)
        with _open_backup_lp_text(bdir, backup_id, is_fullbackup=False):
            pass
    except Exception:
        return jsonify({"ok": False, "error": "backup not found"}), 404

    try:
        with v2_client(cfg) as c:
            wapi = c.write_api(write_options=SYNCHRONOUS)
            batch: list[str] = []
            applied = 0
            with _open_backup_lp_text(bdir, backup_id, is_fullbackup=False) as f:
                for line in f:
                    line = line.strip("\n")
                    if not line.strip():
                        continue
                    batch.append(line)
                    if len(batch) >= 2000:
                        wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=batch, write_precision=WritePrecision.NS)
                        applied += len(batch)
                        batch = []
                if batch:
                    wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=batch, write_precision=WritePrecision.NS)
                    applied += len(batch)

        return jsonify({"ok": True, "message": f"Restored points: {applied}", "applied": applied})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/backup_copy")
def api_backup_copy():
    """Copy points from a backup to a target signal.

    This rewrites measurement/field and optionally overrides entity_id/friendly_name tags.
    Existing points in the target series are overwritten (upsert) for matching timestamp+tags.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", False)
    ok_confirm = confirm is True or str(confirm).strip().lower() in ("1", "true", "yes", "on")
    if not ok_confirm:
        return jsonify({"ok": False, "error": "Confirmation required"}), 400

    backup_id = (body.get("id") or "").strip()
    if not backup_id:
        return jsonify({"ok": False, "error": "id required"}), 400

    target_measurement = (body.get("target_measurement") or "").strip()
    target_field = (body.get("target_field") or "").strip()
    if not target_measurement or not target_field:
        return jsonify({"ok": False, "error": "target_measurement and target_field required"}), 400

    target_entity_id = (body.get("target_entity_id") or "").strip() or None
    target_friendly_name = (body.get("target_friendly_name") or "").strip() or None

    start_dt: datetime | None = None
    stop_dt: datetime | None = None
    start_ns: int | None = None
    stop_ns: int | None = None
    if body.get("start") and body.get("stop"):
        try:
            start_dt, stop_dt = _get_start_stop_from_payload(body)
            if not start_dt or not stop_dt:
                raise ValueError("start and stop required")
            start_ns = _dt_to_ns(start_dt)
            stop_ns = _dt_to_ns(stop_dt)
        except Exception as e:
            return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "copy currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    bdir = backup_dir(cfg)
    try:
        # Ensure the payload exists (zip or legacy)
        with _open_backup_lp_text(bdir, backup_id, is_fullbackup=False):
            pass
    except Exception:
        return jsonify({"ok": False, "error": "backup not found"}), 404

    tgt_meas = _lp_escape_key(target_measurement)
    tgt_field = _lp_escape_key(target_field)

    try:
        preview_limit = int(cfg.get("restore_preview_lines", 5))
    except Exception:
        preview_limit = 5
    if preview_limit < 0:
        preview_limit = 0
    if preview_limit > 200:
        preview_limit = 200
    preview_lines: list[str] = []
    override_tags: dict[str, str] = {}
    if target_entity_id:
        override_tags["entity_id"] = _lp_escape_tag_value(target_entity_id)
    if target_friendly_name:
        override_tags["friendly_name"] = _lp_escape_tag_value(target_friendly_name)

    def _is_escaped(s: str, i: int) -> bool:
        # true if s[i] is escaped by an odd number of backslashes before it
        n = 0
        j = i - 1
        while j >= 0 and s[j] == "\\":
            n += 1
            j -= 1
        return (n % 2) == 1

    def _find_unescaped(s: str, ch: str) -> int:
        for i, c in enumerate(s):
            if c != ch:
                continue
            if not _is_escaped(s, i):
                return i
        return -1

    def _split_unescaped(s: str, ch: str) -> list[str]:
        out: list[str] = []
        cur: list[str] = []
        for i, c in enumerate(s):
            if c == ch and not _is_escaped(s, i):
                out.append("".join(cur))
                cur = []
            else:
                cur.append(c)
        out.append("".join(cur))
        return out

    def _split_tag_kv(tok: str) -> tuple[str, str] | None:
        i = _find_unescaped(tok, "=")
        if i <= 0:
            return None
        return tok[:i], tok[i + 1 :]

    def _rewrite_line(line: str) -> str | None:
        # Split: <measurement,tags> <fieldset> <timestamp>
        # NOTE: tag values can contain escaped spaces ("\\ "), so we must not use find(" ")
        # blindly.
        s = line.strip("\r\n")
        if not s.strip():
            return None

        # Timestamp is always the last token (unescaped).
        j = s.rfind(" ")
        if j <= 0:
            return None
        ts_raw = s[j + 1 :].strip()
        if not ts_raw:
            return None
        # Guard against weird tails
        if not ts_raw.isdigit():
            return None

        rest = s[:j]

        # Split mt vs fieldset on the first unescaped space.
        i = _find_unescaped(rest, " ")
        if i <= 0:
            return None
        mt = rest[:i]
        fieldset = rest[i + 1 :].strip()
        if not fieldset:
            return None

        # Optional time filter
        if start_ns is not None and stop_ns is not None:
            try:
                ts = int(ts_raw)
            except Exception:
                return None
            if ts < start_ns or ts > stop_ns:
                return None

        # Parse measurement + tags (comma is escaped in line protocol).
        parts = _split_unescaped(mt, ",")
        if not parts:
            return None
        tags_in = parts[1:]
        tag_map: dict[str, str] = {}
        tag_order: list[str] = []
        for tok in tags_in:
            kv = _split_tag_kv(tok)
            if not kv:
                continue
            k, v = kv
            tag_order.append(k)
            tag_map[k] = v
        for k, v in override_tags.items():
            tag_map[k] = v

        tags_out: list[str] = []
        for k in tag_order:
            if k in tag_map:
                tags_out.append(f"{k}={tag_map[k]}")
        for k in sorted(tag_map.keys()):
            if k not in tag_order:
                tags_out.append(f"{k}={tag_map[k]}")

        # Replace field key (first field key only, keep remaining fields as-is)
        fields = _split_unescaped(fieldset, ",")
        if not fields:
            return None
        f0 = fields[0]
        eq = f0.find("=")
        if eq <= 0:
            return None
        field_val = f0[eq + 1 :]
        fields[0] = f"{tgt_field}={field_val}"
        new_fieldset = ",".join(fields)

        if tags_out:
            new_mt = tgt_meas + "," + ",".join(tags_out)
        else:
            new_mt = tgt_meas
        return f"{new_mt} {new_fieldset} {ts_raw}"

    try:
        with v2_client(cfg) as c:
            wapi = c.write_api(write_options=SYNCHRONOUS)
            batch: list[str] = []
            applied = 0
            skipped = 0
            with _open_backup_lp_text(bdir, backup_id, is_fullbackup=False) as f:
                for raw in f:
                    out = _rewrite_line(raw)
                    if not out:
                        skipped += 1
                        continue
                    if preview_limit > 0 and len(preview_lines) < preview_limit:
                        preview_lines.append(out)
                    batch.append(out)
                    if len(batch) >= 2000:
                        wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=batch, write_precision=WritePrecision.NS)
                        applied += len(batch)
                        batch = []
                if batch:
                    wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=batch, write_precision=WritePrecision.NS)
                    applied += len(batch)

        return jsonify({
            "ok": True,
            "message": f"Copied points: {applied}",
            "applied": applied,
            "skipped": skipped,
            "preview_limit": preview_limit,
            "preview_lines": preview_lines,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


def _restore_copy_job_public(job: dict[str, Any]) -> dict[str, Any]:
    total_b = job.get("total_bytes")
    read_b = int(job.get("read_bytes") or 0)
    pct = None
    if isinstance(total_b, int) and total_b > 0:
        pct = min(100.0, (read_b / float(total_b)) * 100.0)
    return {
        "id": job.get("id"),
        "state": job.get("state"),
        "message": job.get("message"),
        "started_at": job.get("started_at"),
        "elapsed": _job_elapsed_hms(job),
        "applied": int(job.get("applied") or 0),
        "skipped": int(job.get("skipped") or 0),
        "read_bytes": read_b,
        "total_bytes": total_b,
        "percent": pct,
        "current_time_ms": job.get("current_time_ms"),
        "last_written_time_ms": job.get("last_written_time_ms"),
        "cancelled": bool(job.get("cancelled")),
        "error": job.get("error"),
        "ready": job.get("state") in ("done", "error", "cancelled"),
    }


def _restore_copy_job_thread(
    job_id: str,
    cfg: dict[str, Any],
    backup_id: str,
    target_measurement: str,
    target_field: str,
    target_entity_id: str | None,
    target_friendly_name: str | None,
    start_ns: int | None,
    stop_ns: int | None,
) -> None:
    with RESTORE_COPY_LOCK:
        job = RESTORE_COPY_JOBS.get(job_id)
    if not job:
        return

    def set_state(state: str, msg: str) -> None:
        with RESTORE_COPY_LOCK:
            if job_id in RESTORE_COPY_JOBS:
                RESTORE_COPY_JOBS[job_id]["state"] = state
                RESTORE_COPY_JOBS[job_id]["message"] = msg
                if state in ("done", "error", "cancelled"):
                    _job_set_finished(RESTORE_COPY_JOBS[job_id])

    def set_error(msg: str) -> None:
        with RESTORE_COPY_LOCK:
            if job_id in RESTORE_COPY_JOBS:
                RESTORE_COPY_JOBS[job_id]["error"] = msg

    def set_progress(**kw: Any) -> None:
        with RESTORE_COPY_LOCK:
            j = RESTORE_COPY_JOBS.get(job_id)
            if not j:
                return
            for k, v in kw.items():
                j[k] = v

    set_state("running", "Starte...")

    bdir = backup_dir(cfg)
    meta_path, lp_path = _backup_files(bdir, backup_id)
    if not lp_path.exists():
        set_state("error", "Fehler")
        set_error("backup not found")
        return

    try:
        total_bytes = int(lp_path.stat().st_size)
    except Exception:
        total_bytes = None
    set_progress(total_bytes=total_bytes)

    tgt_meas = _lp_escape_key(target_measurement)
    tgt_field = _lp_escape_key(target_field)

    try:
        preview_limit = int(cfg.get("restore_preview_lines", 5))
    except Exception:
        preview_limit = 5
    if preview_limit < 0:
        preview_limit = 0
    if preview_limit > 200:
        preview_limit = 200

    preview_lines: list[str] = []
    override_tags: dict[str, str] = {}
    if target_entity_id:
        override_tags["entity_id"] = _lp_escape_tag_value(target_entity_id)
    if target_friendly_name:
        override_tags["friendly_name"] = _lp_escape_tag_value(target_friendly_name)

    def _is_escaped(s: str, i: int) -> bool:
        n = 0
        j = i - 1
        while j >= 0 and s[j] == "\\":
            n += 1
            j -= 1
        return (n % 2) == 1

    def _find_unescaped(s: str, ch: str) -> int:
        for i, c in enumerate(s):
            if c != ch:
                continue
            if not _is_escaped(s, i):
                return i
        return -1

    def _split_unescaped(s: str, ch: str) -> list[str]:
        out: list[str] = []
        cur: list[str] = []
        for i, c in enumerate(s):
            if c == ch and not _is_escaped(s, i):
                out.append("".join(cur))
                cur = []
            else:
                cur.append(c)
        out.append("".join(cur))
        return out

    def _split_tag_kv(tok: str) -> tuple[str, str] | None:
        i = _find_unescaped(tok, "=")
        if i <= 0:
            return None
        return tok[:i], tok[i + 1 :]

    def _raw_ts_ns(line: str) -> int | None:
        s = (line or "").strip("\r\n")
        j = s.rfind(" ")
        if j <= 0:
            return None
        ts_raw = s[j + 1 :].strip()
        if not ts_raw or not ts_raw.isdigit():
            return None
        try:
            return int(ts_raw)
        except Exception:
            return None

    def _rewrite_line(line: str) -> str | None:
        s = line.strip("\r\n")
        if not s.strip():
            return None

        j = s.rfind(" ")
        if j <= 0:
            return None
        ts_raw = s[j + 1 :].strip()
        if not ts_raw or not ts_raw.isdigit():
            return None

        rest = s[:j]
        i = _find_unescaped(rest, " ")
        if i <= 0:
            return None
        mt = rest[:i]
        fieldset = rest[i + 1 :].strip()
        if not fieldset:
            return None

        if start_ns is not None and stop_ns is not None:
            try:
                ts = int(ts_raw)
            except Exception:
                return None
            if ts < start_ns or ts > stop_ns:
                return None

        parts = _split_unescaped(mt, ",")
        if not parts:
            return None
        tags_in = parts[1:]
        tag_map: dict[str, str] = {}
        tag_order: list[str] = []
        for tok in tags_in:
            kv = _split_tag_kv(tok)
            if not kv:
                continue
            k, v = kv
            tag_order.append(k)
            tag_map[k] = v
        for k, v in override_tags.items():
            tag_map[k] = v

        tags_out: list[str] = []
        for k in tag_order:
            if k in tag_map:
                tags_out.append(f"{k}={tag_map[k]}")
        for k in sorted(tag_map.keys()):
            if k not in tag_order:
                tags_out.append(f"{k}={tag_map[k]}")

        fields = _split_unescaped(fieldset, ",")
        if not fields:
            return None
        f0 = fields[0]
        eq = f0.find("=")
        if eq <= 0:
            return None
        field_val = f0[eq + 1 :]
        fields[0] = f"{tgt_field}={field_val}"
        new_fieldset = ",".join(fields)

        if tags_out:
            new_mt = tgt_meas + "," + ",".join(tags_out)
        else:
            new_mt = tgt_meas
        return f"{new_mt} {new_fieldset} {ts_raw}"

    applied = 0
    dirty_series: set[tuple[str, str, str | None, str | None]] = set()
    skipped = 0
    read_bytes = 0
    batch: list[str] = []
    last_written_time_ms: int | None = None
    current_time_ms: int | None = None
    last_tick = time.monotonic()

    try:
        with v2_client(cfg) as c:
            wapi = c.write_api(write_options=SYNCHRONOUS)
            set_state("running", "Lese Backup...")
            with lp_path.open("rb") as f:
                for raw_b in f:
                    with RESTORE_COPY_LOCK:
                        j = RESTORE_COPY_JOBS.get(job_id) or {}
                        if bool(j.get("cancelled")):
                            set_state("cancelled", "Abgebrochen")
                            return

                    read_bytes += len(raw_b)
                    raw = raw_b.decode("utf-8", errors="replace")

                    ts_ns = _raw_ts_ns(raw)
                    if ts_ns is not None:
                        current_time_ms = int(ts_ns // 1_000_000)

                    out = _rewrite_line(raw)
                    if not out:
                        skipped += 1
                    else:
                        if preview_limit > 0 and len(preview_lines) < preview_limit:
                            preview_lines.append(out)
                        batch.append(out)

                    now = time.monotonic()
                    if (now - last_tick) >= 0.25:
                        set_progress(
                            read_bytes=read_bytes,
                            applied=applied,
                            skipped=skipped,
                            current_time_ms=current_time_ms,
                            last_written_time_ms=last_written_time_ms,
                        )
                        last_tick = now

                    if len(batch) >= 2000:
                        set_state("running", "Schreibe in InfluxDB...")
                        wapi.write(
                            bucket=cfg["bucket"],
                            org=cfg["org"],
                            record=batch,
                            write_precision=WritePrecision.NS,
                        )
                        applied += len(batch)
                        # last point timestamp in the batch
                        ts_last = _raw_ts_ns(batch[-1])
                        if ts_last is not None:
                            last_written_time_ms = int(ts_last // 1_000_000)
                        batch = []
                        set_progress(
                            read_bytes=read_bytes,
                            applied=applied,
                            skipped=skipped,
                            current_time_ms=current_time_ms,
                            last_written_time_ms=last_written_time_ms,
                        )

                if batch:
                    set_state("running", "Schreibe in InfluxDB...")
                    wapi.write(
                        bucket=cfg["bucket"],
                        org=cfg["org"],
                        record=batch,
                        write_precision=WritePrecision.NS,
                    )
                    applied += len(batch)
                    ts_last = _raw_ts_ns(batch[-1])
                    if ts_last is not None:
                        last_written_time_ms = int(ts_last // 1_000_000)
                    batch = []
                    set_progress(
                        read_bytes=read_bytes,
                        applied=applied,
                        skipped=skipped,
                        current_time_ms=current_time_ms,
                        last_written_time_ms=last_written_time_ms,
                    )

        with RESTORE_COPY_LOCK:
            if job_id in RESTORE_COPY_JOBS:
                RESTORE_COPY_JOBS[job_id]["result"] = {
                    "applied": applied,
                    "skipped": skipped,
                    "preview_limit": preview_limit,
                    "preview_lines": preview_lines,
                }
        try:
            if applied > 0:
                _dash_cache_mark_dirty_series(target_measurement, target_field, target_entity_id, target_friendly_name, "restore_copy")
                _stats_cache_mark_dirty_series(target_measurement, target_field, target_entity_id, target_friendly_name, "restore_copy")
        except Exception:
            pass
        set_state("done", f"Copied points: {applied}")
    except Exception as e:
        set_error(_short_influx_error(e))
        set_state("error", "Fehler")


@app.post("/api/restore_job/start")
def api_restore_job_start():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", False)
    ok_confirm = confirm is True or str(confirm).strip().lower() in ("1", "true", "yes", "on")
    if not ok_confirm:
        return jsonify({"ok": False, "error": "Confirmation required"}), 400

    backup_id = (body.get("id") or "").strip()
    if not backup_id:
        return jsonify({"ok": False, "error": "id required"}), 400
    if _backup_safe(backup_id) != backup_id:
        return jsonify({"ok": False, "error": "invalid id"}), 400

    bdir = backup_dir(cfg)
    meta = _read_backup_meta(bdir, backup_id) or {}
    if str(meta.get("kind") or "") == "db_full":
        return jsonify({"ok": False, "error": "selected backup is a fullbackup; use FullRestore"}), 400

    target_measurement = (body.get("target_measurement") or "").strip()
    target_field = (body.get("target_field") or "").strip()
    if not target_measurement or not target_field:
        return jsonify({"ok": False, "error": "target_measurement and target_field required"}), 400

    target_entity_id = (body.get("target_entity_id") or "").strip() or None
    target_friendly_name = (body.get("target_friendly_name") or "").strip() or None

    start_ns: int | None = None
    stop_ns: int | None = None
    if body.get("start") and body.get("stop"):
        try:
            start_dt, stop_dt = _get_start_stop_from_payload(body)
            if not start_dt or not stop_dt:
                raise ValueError("start and stop required")
            start_ns = _dt_to_ns(start_dt)
            stop_ns = _dt_to_ns(stop_dt)
        except Exception as e:
            return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "copy currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    job_id = uuid.uuid4().hex
    ip = _req_ip()
    ua = _req_ua()
    job = {
        "id": job_id,
        "state": "queued",
        "message": "Start...",
        "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "started_mono": time.monotonic(),
        "trigger_page": "restore",
        "trigger_ip": ip,
        "trigger_ua": ua,
        "applied": 0,
        "skipped": 0,
        "read_bytes": 0,
        "total_bytes": None,
        "current_time_ms": None,
        "last_written_time_ms": None,
        "cancelled": False,
        "error": None,
        "result": None,
    }

    try:
        start_s = _dt_to_rfc3339_utc(start_dt) if (body.get("start") and body.get("stop") and start_dt) else ""
        stop_s = _dt_to_rfc3339_utc(stop_dt) if (body.get("start") and body.get("stop") and stop_dt) else ""
    except Exception:
        start_s = ""
        stop_s = ""
    try:
        LOG.info(
            "job_start type=restore_copy job_id=%s ip=%s ua=%s backup_id=%s target=%s/%s entity_id=%s friendly_name=%s start=%s stop=%s",
            job_id,
            ip,
            ua,
            backup_id,
            target_measurement,
            target_field,
            target_entity_id or "",
            target_friendly_name or "",
            start_s,
            stop_s,
        )
    except Exception:
        pass

    # Cleanup old jobs
    with RESTORE_COPY_LOCK:
        RESTORE_COPY_JOBS[job_id] = job
        cutoff = time.monotonic() - 3600
        old = [k for k, v in RESTORE_COPY_JOBS.items() if float(v.get("started_mono") or 0) < cutoff]
        for k in old:
            if k != job_id:
                RESTORE_COPY_JOBS.pop(k, None)

    t = threading.Thread(
        target=_restore_copy_job_thread,
        args=(
            job_id,
            cfg,
            backup_id,
            target_measurement,
            target_field,
            target_entity_id,
            target_friendly_name,
            start_ns,
            stop_ns,
        ),
        daemon=True,
    )
    t.start()
    return jsonify({"ok": True, "job_id": job_id})


@app.get("/api/restore_job/status")
def api_restore_job_status():
    job_id = (request.args.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with RESTORE_COPY_LOCK:
        job = RESTORE_COPY_JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    return jsonify({"ok": True, "status": _restore_copy_job_public(job)})


@app.get("/api/restore_job/result")
def api_restore_job_result():
    job_id = (request.args.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with RESTORE_COPY_LOCK:
        job = RESTORE_COPY_JOBS.get(job_id)
        res = job.get("result") if job else None
        state = job.get("state") if job else None
        err = job.get("error") if job else None
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    if state != "done":
        return jsonify({"ok": True, "ready": False, "state": state, "error": err})
    return jsonify({"ok": True, "ready": True, **(res or {})})


@app.post("/api/restore_job/cancel")
def api_restore_job_cancel():
    body = request.get_json(force=True) or {}
    job_id = (body.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with RESTORE_COPY_LOCK:
        job = RESTORE_COPY_JOBS.get(job_id)
        if not job:
            return jsonify({"ok": False, "error": "job not found"}), 404
        job["cancelled"] = True
    try:
        LOG.info("job_cancel type=restore_copy job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
    except Exception:
        pass
    return jsonify({"ok": True})


def _combine_job_public(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": job.get("id"),
        "state": job.get("state"),
        "message": job.get("message"),
        "started_at": job.get("started_at"),
        "elapsed": _job_elapsed_hms(job),
        "read": int(job.get("read") or 0),
        "written": int(job.get("written") or 0),
        "skipped": int(job.get("skipped") or 0),
        "backup_id": job.get("backup_id"),
        "backup_before": bool(job.get("backup_before", True)),
        "delete_target_first": bool(job.get("delete_target_first", False)),
        "current_time_ms": job.get("current_time_ms"),
        "last_written_time_ms": job.get("last_written_time_ms"),
        "cancelled": bool(job.get("cancelled")),
        "error": job.get("error"),
        "ready": job.get("state") in ("done", "error", "cancelled"),
    }


def _combine_job_thread(
    job_id: str,
    cfg: dict[str, Any],
    source: dict[str, Any],
    target: dict[str, Any],
    start_dt: datetime,
    stop_dt: datetime,
) -> None:
    with COMBINE_LOCK:
        job = COMBINE_JOBS.get(job_id)
    if not job:
        return

    def set_state(state: str, msg: str) -> None:
        with COMBINE_LOCK:
            if job_id in COMBINE_JOBS:
                COMBINE_JOBS[job_id]["state"] = state
                COMBINE_JOBS[job_id]["message"] = msg
                if state in ("done", "error", "cancelled"):
                    _job_set_finished(COMBINE_JOBS[job_id])

    def set_error(msg: str) -> None:
        with COMBINE_LOCK:
            if job_id in COMBINE_JOBS:
                COMBINE_JOBS[job_id]["error"] = msg

    def set_progress(**kw: Any) -> None:
        with COMBINE_LOCK:
            j = COMBINE_JOBS.get(job_id)
            if not j:
                return
            for k, v in kw.items():
                j[k] = v

    def is_cancelled() -> bool:
        with COMBINE_LOCK:
            j = COMBINE_JOBS.get(job_id) or {}
            return bool(j.get("cancelled"))

    set_state("running", "Starte...")

    src_m = str(source.get("measurement") or "").strip()
    src_f = str(source.get("field") or "").strip()
    src_eid = str(source.get("entity_id") or "").strip() or None
    src_fn = str(source.get("friendly_name") or "").strip() or None

    tgt_m = str(target.get("measurement") or "").strip()
    tgt_f = str(target.get("field") or "").strip()
    tgt_eid = str(target.get("entity_id") or "").strip() or None
    tgt_fn = str(target.get("friendly_name") or "").strip() or None

    backup_before = bool(job.get("backup_before", True))
    delete_target_first = bool(job.get("delete_target_first", False))

    if not (src_m and src_f and tgt_m and tgt_f):
        set_error("missing measurement/field")
        set_state("error", "Fehler")
        return

    # For safety/rollback, require at least one identifying tag on both sides.
    if not (src_eid or src_fn):
        set_error("source requires entity_id or friendly_name")
        set_state("error", "Fehler")
        return
    if not (tgt_eid or tgt_fn):
        set_error("target requires entity_id or friendly_name")
        set_state("error", "Fehler")
        return

    try:
        max_points = int(cfg.get("ui_query_manual_max_points", 200000) or 200000)
    except Exception:
        max_points = 200000
    if max_points < 1000:
        max_points = 1000
    if max_points > 2000000:
        max_points = 2000000

    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    extra = flux_tag_filter(src_eid, src_fn)

    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(src_m)} and r._field == {_flux_str(src_f)}{extra})
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: {max_points})
'''

    log_query("combine.copy (flux)", q)

    read = 0
    written = 0
    skipped = 0
    last_written_time_ms = None
    set_state("running", "Lese Punkte...")

    # Optional: create a rollback-safe backup of the target series in the same time window.
    backup_id = None
    try:
        if backup_before:
            set_state("running", "Backup Zielbereich...")
            disp = f"combine_target__{tgt_fn or tgt_eid or tgt_m}"
            backup_id = _backup_create_range(
                cfg,
                measurement=tgt_m,
                field=tgt_f,
                entity_id=tgt_eid,
                friendly_name=tgt_fn,
                start_dt=start_dt,
                stop_dt=stop_dt,
                display_name=disp,
            )
            set_progress(backup_id=backup_id)
    except Exception as e:
        set_error(f"backup_before failed: {_short_influx_error(e)}")
        set_state("error", "Fehler")
        return

    # Optional: delete target range first (destructive).
    try:
        if delete_target_first:
            set_state("running", "Loesche Zielbereich...")
            predicate = f"_measurement={_flux_str(tgt_m)} AND _field={_flux_str(tgt_f)}"
            if tgt_eid:
                predicate += f" AND entity_id={_flux_str(tgt_eid)}"
            if tgt_fn:
                predicate += f" AND friendly_name={_flux_str(tgt_fn)}"
            with v2_client(cfg) as c:
                c.delete_api().delete(start=start_dt, stop=stop_dt, predicate=predicate, bucket=cfg["bucket"], org=cfg["org"])
    except Exception as e:
        set_error(f"delete_target_first failed: {_short_influx_error(e)}")
        set_state("error", "Fehler")
        return

    try:
        with v2_client(cfg) as c:
            qapi = c.query_api()
            wapi = c.write_api(write_options=SYNCHRONOUS)

            batch: list[Point] = []
            for rec in qapi.query_stream(q, org=cfg["org"]):
                if is_cancelled():
                    set_state("cancelled", "Abgebrochen")
                    return
                read += 1
                try:
                    ts = rec.get_time()
                    val = rec.get_value()
                    if not isinstance(ts, datetime):
                        skipped += 1
                        continue
                    if isinstance(val, bool) or not isinstance(val, (int, float)):
                        skipped += 1
                        continue

                    p = Point(tgt_m)

                    # Preserve tags from source row (best-effort), then override entity_id/friendly_name.
                    try:
                        for k, tv in (rec.values or {}).items():
                            if k in ("result", "table"):
                                continue
                            if str(k).startswith("_"):
                                continue
                            if tv is None:
                                continue
                            # keep as tag
                            p = p.tag(str(k), str(tv))
                    except Exception:
                        pass

                    if tgt_eid:
                        p = p.tag("entity_id", tgt_eid)
                    if tgt_fn:
                        p = p.tag("friendly_name", tgt_fn)

                    p = p.field(tgt_f, val).time(ts, WritePrecision.NS)
                    batch.append(p)
                    if len(batch) >= 2000:
                        wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=batch)
                        written += len(batch)
                        last_written_time_ms = int(ts.timestamp() * 1000)
                        batch = []
                except Exception:
                    skipped += 1
                    continue

                if read % 1000 == 0:
                    cur_ms = None
                    try:
                        if isinstance(ts, datetime):
                            cur_ms = int(ts.timestamp() * 1000)
                    except Exception:
                        cur_ms = None
                    set_progress(read=read, written=written, skipped=skipped, current_time_ms=cur_ms, last_written_time_ms=last_written_time_ms)
                    set_state("running", f"Kopiere... {read}")

            if batch:
                try:
                    wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=batch)
                    written += len(batch)
                except Exception:
                    pass

        set_progress(read=read, written=written, skipped=skipped, last_written_time_ms=last_written_time_ms)

        try:
            _history_append({
                "kind": "combine",
                "action": "combine_copy",
                "source": {"measurement": src_m, "field": src_f, "entity_id": src_eid, "friendly_name": src_fn},
                "target": {"measurement": tgt_m, "field": tgt_f, "entity_id": tgt_eid, "friendly_name": tgt_fn},
                "series": {
                    "measurement": tgt_m,
                    "field": tgt_f,
                    "entity_id": tgt_eid,
                    "friendly_name": tgt_fn,
                    "tags": {"entity_id": tgt_eid, "friendly_name": tgt_fn},
                },
                "start": start,
                "stop": stop,
                "backup_id": backup_id,
                "backup_before": bool(backup_before),
                "delete_target_first": bool(delete_target_first),
                "read": read,
                "written": written,
                "skipped": skipped,
                "ip": _req_ip(),
                "ua": _req_ua(),
            })
        except Exception:
            pass

        try:
            _dash_cache_mark_dirty_series(tgt_m, tgt_f, tgt_eid, tgt_fn, "combine")
            _stats_cache_mark_dirty_series(tgt_m, tgt_f, tgt_eid, tgt_fn, "combine")
        except Exception:
            pass

        set_state("done", f"Fertig. geschrieben: {written}")
    except Exception as e:
        set_error(_short_influx_error(e))
        set_state("error", "Fehler")


@app.post("/api/combine_job/start")
def api_combine_job_start():
    try:
        cfg = _overlay_from_yaml_if_enabled(load_cfg())
        body = request.get_json(force=True) or {}

        confirm = body.get("confirm", False)
        ok_confirm = confirm is True or str(confirm).strip().lower() in ("1", "true", "yes", "on")
        if not ok_confirm:
            return jsonify({"ok": False, "error": "Confirmation required"}), 400

        if int(cfg.get("influx_version", 2)) != 2:
            return jsonify({"ok": False, "error": "combine currently supports InfluxDB v2 only"}), 400
        if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
            return jsonify({
                "ok": False,
                "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
            }), 400

        src = body.get("source")
        tgt = body.get("target")
        if not isinstance(src, dict) or not isinstance(tgt, dict):
            return jsonify({"ok": False, "error": "source and target required"}), 400

        direction = str(body.get("direction") or "src_to_tgt").strip().lower()
        if direction not in ("src_to_tgt", "tgt_to_src"):
            return jsonify({"ok": False, "error": "direction must be src_to_tgt or tgt_to_src"}), 400
        if direction == "tgt_to_src":
            src, tgt = tgt, src

        # Validate payload early so the user sees a clear API error (instead of a background job failure).
        try:
            _combine_series_payload(src)
            _combine_series_payload(tgt)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 400

        backup_before = body.get("backup_before", True)
        backup_before_on = backup_before is True or str(backup_before).strip().lower() in ("1", "true", "yes", "on")

        delete_first = body.get("delete_target_first", False)
        delete_first_on = delete_first is True or str(delete_first).strip().lower() in ("1", "true", "yes", "on")
        if delete_first_on:
            if not ALLOW_DELETE:
                return jsonify({"ok": False, "error": "Delete is disabled (ALLOW_DELETE=false)"}), 400

        try:
            start_dt, stop_dt = _get_start_stop_from_payload(body)
        except Exception as e:
            return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
        if not start_dt or not stop_dt:
            return jsonify({"ok": False, "error": "start and stop required"}), 400

        job_id = uuid.uuid4().hex
        ip = _req_ip()
        ua = _req_ua()
        job = {
            "id": job_id,
            "state": "queued",
            "message": "Start...",
            "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "started_mono": time.monotonic(),
            "trigger_page": "combine",
            "trigger_ip": ip,
            "trigger_ua": ua,
            "read": 0,
            "written": 0,
            "skipped": 0,
            "current_time_ms": None,
            "last_written_time_ms": None,
            "cancelled": False,
            "error": None,
            "backup_before": bool(backup_before_on),
            "delete_target_first": bool(delete_first_on),
        }

        try:
            LOG.info("job_start type=combine job_id=%s ip=%s ua=%s", job_id, ip, ua)
        except Exception:
            pass

        with COMBINE_LOCK:
            COMBINE_JOBS[job_id] = job
            cutoff = time.monotonic() - 6 * 3600
            old = [k for k, v in COMBINE_JOBS.items() if float(v.get("started_mono") or 0) < cutoff]
            for k in old:
                if k != job_id:
                    COMBINE_JOBS.pop(k, None)

        t = threading.Thread(target=_combine_job_thread, args=(job_id, cfg, src, tgt, start_dt, stop_dt), daemon=True)
        t.start()
        return jsonify({"ok": True, "job_id": job_id})
    except Exception as e:
        try:
            LOG.exception("api_combine_job_start failed")
        except Exception:
            pass
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


def _combine_series_payload(x: dict[str, Any]) -> tuple[str, str, str | None, str | None]:
    m = str(x.get("measurement") or "").strip()
    f = str(x.get("field") or "value").strip() or "value"
    eid = str(x.get("entity_id") or "").strip() or None
    fn = str(x.get("friendly_name") or "").strip() or None
    if not m or not f:
        raise ValueError("measurement and field required")
    if not eid and not fn:
        raise ValueError("entity_id or friendly_name required")
    return m, f, eid, fn


def _combine_window_seconds(start_dt: datetime, stop_dt: datetime, bins: int) -> int:
    try:
        s = float((stop_dt - start_dt).total_seconds())
    except Exception:
        s = 0.0
    if s <= 0:
        return 1
    b = int(bins)
    if b < 50:
        b = 50
    if b > 600:
        b = 600
    every = int(max(1.0, s / float(b)))
    if every > 86400:
        every = 86400
    return every


@app.post("/api/combine_timeline")
def api_combine_timeline():
    """Return bucketed counts for a series in a time window (for timeline UI)."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "combine timeline supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({"ok": False, "error": "InfluxDB v2 requires token, org, bucket"}), 400

    body = request.get_json(force=True) or {}
    series = body.get("series")
    if not isinstance(series, dict):
        return jsonify({"ok": False, "error": "series required"}), 400
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    if not start_dt or not stop_dt:
        return jsonify({"ok": False, "error": "start and stop required"}), 400

    try:
        bins = int(body.get("bins") or 220)
    except Exception:
        bins = 220
    bins = min(600, max(50, bins))

    try:
        m, f, eid, fn = _combine_series_payload(series)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    every_s = _combine_window_seconds(start_dt, stop_dt, bins)
    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    extra = flux_tag_filter(eid, fn)
    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(m)} and r._field == {_flux_str(f)}{extra})
  |> aggregateWindow(every: {every_s}s, fn: count, createEmpty: false)
  |> keep(columns: ["_time", "_value"])
  |> sort(columns: ["_time"], desc: false)
'''

    pts: list[dict[str, Any]] = []
    try:
        with v2_client(cfg, timeout_seconds_override=min(30, int(cfg.get("timeout_seconds") or 10))) as c:
            qapi = c.query_api()
            for rec in qapi.query_stream(q, org=cfg["org"]):
                try:
                    t = rec.get_time()
                    v = rec.get_value()
                    if not isinstance(t, datetime):
                        continue
                    if v is None:
                        continue
                    pts.append({"t_ms": int(t.timestamp() * 1000), "v": int(v)})
                except Exception:
                    continue
        return jsonify({"ok": True, "every_seconds": every_s, "points": pts})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/combine_preview")
def api_combine_preview():
    """Return downsampled numeric values for a series in a time window (for mini-graph UI)."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "combine preview supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({"ok": False, "error": "InfluxDB v2 requires token, org, bucket"}), 400

    body = request.get_json(force=True) or {}
    series = body.get("series")
    if not isinstance(series, dict):
        return jsonify({"ok": False, "error": "series required"}), 400
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    if not start_dt or not stop_dt:
        return jsonify({"ok": False, "error": "start and stop required"}), 400

    try:
        points = int(body.get("points") or 260)
    except Exception:
        points = 260
    points = min(800, max(60, points))

    try:
        m, f, eid, fn = _combine_series_payload(series)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    every_s = _combine_window_seconds(start_dt, stop_dt, points)
    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    extra = flux_tag_filter(eid, fn)
    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(m)} and r._field == {_flux_str(f)}{extra})
  |> aggregateWindow(every: {every_s}s, fn: mean, createEmpty: false)
  |> keep(columns: ["_time", "_value"])
  |> sort(columns: ["_time"], desc: false)
'''

    pts: list[dict[str, Any]] = []
    try:
        with v2_client(cfg, timeout_seconds_override=min(30, int(cfg.get("timeout_seconds") or 10))) as c:
            qapi = c.query_api()
            for rec in qapi.query_stream(q, org=cfg["org"]):
                try:
                    t = rec.get_time()
                    v = rec.get_value()
                    if not isinstance(t, datetime):
                        continue
                    if v is None or isinstance(v, bool) or not isinstance(v, (int, float)):
                        continue
                    pts.append({"t_ms": int(t.timestamp() * 1000), "v": float(v)})
                except Exception:
                    continue
        return jsonify({"ok": True, "every_seconds": every_s, "points": pts})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.get("/api/combine_job/status")
def api_combine_job_status():
    job_id = (request.args.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with COMBINE_LOCK:
        job = COMBINE_JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    return jsonify({"ok": True, "status": _combine_job_public(job)})


@app.get("/api/jobs")
def api_jobs():
    """List background jobs across subsystems."""

    try:
        limit = int(request.args.get("limit", "80"))
    except Exception:
        limit = 80
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500

    out: list[dict[str, Any]] = []
    cfg = load_cfg()
    dash_mode = _cache_mode_str(cfg, "dash_cache")
    stats_mode = _cache_mode_str(cfg, "stats_cache")
    stats_full_mode = _cache_mode_str(cfg, "stats_full")

    with GLOBAL_STATS_LOCK:
        g_items = list(GLOBAL_STATS_JOBS.items())
    for _, j in g_items:
        pub = _job_public(j)
        pub["type"] = "global_stats"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        pub["timer_id"] = j.get("timer_id")
        if j.get("cache_id"):
            pub["cache_kind"] = "stats"
            pub["mode"] = stats_mode
        elif str(j.get("timer_id") or "").strip() == "stats_full":
            pub["mode"] = stats_full_mode
        _jobs_history_upsert(pub)
        out.append(pub)

    with RESTORE_COPY_LOCK:
        r_items = list(RESTORE_COPY_JOBS.items())
    for _, j in r_items:
        pub = _restore_copy_job_public(j)
        pub["type"] = "restore_copy"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        _jobs_history_upsert(pub)
        out.append(pub)

    with COMBINE_LOCK:
        x_items = list(COMBINE_JOBS.items())
    for _, j in x_items:
        pub = _combine_job_public(j)
        pub["type"] = "combine"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        _jobs_history_upsert(pub)
        out.append(pub)

    with BACKUP_LOCK:
        b_items = list(BACKUP_JOBS.items())
    for _, j in b_items:
        pub = _backup_job_public(j)
        pub["type"] = "backup"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        _jobs_history_upsert(pub)
        out.append(pub)

    with FULLBACKUP_LOCK:
        fb_items = list(FULLBACKUP_JOBS.items())
    for _, j in fb_items:
        pub = _fullbackup_job_public(j)
        pub["type"] = "fullbackup"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        _jobs_history_upsert(pub)
        out.append(pub)

    with FULLRESTORE_LOCK:
        fr_items = list(FULLRESTORE_JOBS.items())
    for _, j in fr_items:
        pub = _fullrestore_job_public(j)
        pub["type"] = "fullrestore"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        _jobs_history_upsert(pub)
        out.append(pub)

    with DASH_CACHE_JOBS_LOCK:
        c_items = list(DASH_CACHE_JOBS.items())
    for _, j in c_items:
        pub = _dash_cache_job_public(j)
        pub["type"] = "dash_cache"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        pub["cache_id"] = j.get("cache_id")
        pub["action"] = j.get("action")
        pub["cache_kind"] = "dash"
        pub["mode"] = dash_mode
        _jobs_history_upsert(pub)
        out.append(pub)

    with ANALYSIS_CACHE_PATCH_LOCK:
        acp_items = list(ANALYSIS_CACHE_PATCH_JOBS.items())
    for _, j in acp_items:
        pub = _analysis_cache_patch_job_public(j)
        pub["type"] = "analysis_cache_patch"
        _jobs_history_upsert(pub)
        out.append(pub)

    with ANALYSIS_NIGHTLY_LOCK:
        an_items = list(ANALYSIS_NIGHTLY_JOBS.items())
    for _, j in an_items:
        pub = _analysis_nightly_job_public(j)
        pub["type"] = "analysis_nightly"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        pub["timer_id"] = j.get("timer_id")
        _jobs_history_upsert(pub)
        out.append(pub)

    with EXPORT_LOCK:
        e_items = list(EXPORT_JOBS.items())
    for _, j in e_items:
        pub = _export_job_public(j)
        pub["type"] = "export"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        _jobs_history_upsert(pub)
        out.append(pub)

    active_ids = {str(x.get("id") or "").strip() for x in out if str(x.get("id") or "").strip()}
    for row in _jobs_history_load():
        rid = str(row.get("id") or "").strip()
        if not rid or rid in active_ids:
            continue
        out.append(row)

    def _sort_key(x: dict[str, Any]) -> float:
        try:
            # Prefer started_mono if available via elapsed? Not exposed, so sort by started_at.
            return datetime.fromisoformat(str(x.get("started_at") or "").replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0.0

    out.sort(key=_sort_key, reverse=True)
    if len(out) > limit:
        out = out[:limit]
    return jsonify({"ok": True, "jobs": out})


@app.post("/api/jobs/cancel")
def api_jobs_cancel():
    body = request.get_json(force=True) or {}
    job_id = (body.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400

    with GLOBAL_STATS_LOCK:
        if job_id in GLOBAL_STATS_JOBS:
            GLOBAL_STATS_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=global_stats job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    with RESTORE_COPY_LOCK:
        if job_id in RESTORE_COPY_JOBS:
            RESTORE_COPY_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=restore_copy job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    with COMBINE_LOCK:
        if job_id in COMBINE_JOBS:
            COMBINE_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=combine job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    with BACKUP_LOCK:
        if job_id in BACKUP_JOBS:
            BACKUP_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=backup job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    with FULLBACKUP_LOCK:
        if job_id in FULLBACKUP_JOBS:
            FULLBACKUP_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=fullbackup job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    with FULLRESTORE_LOCK:
        if job_id in FULLRESTORE_JOBS:
            FULLRESTORE_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=fullrestore job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    with DASH_CACHE_JOBS_LOCK:
        if job_id in DASH_CACHE_JOBS:
            DASH_CACHE_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=dash_cache job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    with ANALYSIS_CACHE_PATCH_LOCK:
        if job_id in ANALYSIS_CACHE_PATCH_JOBS:
            ANALYSIS_CACHE_PATCH_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=analysis_cache_patch job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    with ANALYSIS_NIGHTLY_LOCK:
        if job_id in ANALYSIS_NIGHTLY_JOBS:
            ANALYSIS_NIGHTLY_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=analysis_nightly job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    with EXPORT_LOCK:
        if job_id in EXPORT_JOBS:
            EXPORT_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=export job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    return jsonify({"ok": False, "error": "job not found"}), 404


@app.get("/api/cache/list")
def api_cache_list():
    cfg = load_cfg()
    enabled = bool(cfg.get("dash_cache_enabled", True))
    items = _dash_cache_list_meta() if enabled else []

    def _sort_key(m: dict[str, Any]) -> tuple[float, float]:
        return (_dash_cache_ts(m, "last_used_at") or _dash_cache_ts(m, "updated_at"), _dash_cache_ts(m, "updated_at"))

    items.sort(key=_sort_key, reverse=True)
    now_ts = datetime.now(timezone.utc).timestamp()
    out = []
    for m in items:
        try:
            mm = dict(m)
            upd = _dash_cache_ts(mm, "updated_at")
            mm["age_seconds"] = int(max(0, now_ts - upd)) if upd else None
            mm["stale"] = _dash_cache_is_stale(cfg, mm)
            out.append(mm)
        except Exception:
            continue
    return jsonify({
        "ok": True,
        "enabled": enabled,
        "caches": out,
        "settings": {
            "refresh_mode": cfg.get("dash_cache_refresh_mode"),
            "refresh_hours": cfg.get("dash_cache_refresh_hours"),
            "refresh_daily_at": cfg.get("dash_cache_refresh_daily_at"),
            "max_items": cfg.get("dash_cache_max_items"),
            "max_mb": cfg.get("dash_cache_max_mb"),
            "auto_update": cfg.get("dash_cache_auto_update"),
        },
    })


def _timer_parse_hms(s: str, default: tuple[int, int, int]) -> tuple[int, int, int]:
    try:
        raw = str(s or "").strip()
        if not re.match(r"^\d{2}:\d{2}:\d{2}$", raw):
            return default
        parts = raw.split(":")
        hh, mm, ss = int(parts[0]), int(parts[1]), int(parts[2])
        if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59):
            return default
        return (hh, mm, ss)
    except Exception:
        return default


def _timer_parse_weekday(v: Any, default: int = 0) -> int:
    """Parse weekday to Python's 0=Mon..6=Sun."""

    try:
        if isinstance(v, int):
            d = v
        else:
            s = str(v or "").strip().lower()
            if s.isdigit():
                d = int(s)
            else:
                m = {
                    "mon": 0,
                    "monday": 0,
                    "di": 1,
                    "tue": 1,
                    "tuesday": 1,
                    "mi": 2,
                    "wed": 2,
                    "wednesday": 2,
                    "do": 3,
                    "thu": 3,
                    "thursday": 3,
                    "fr": 4,
                    "fri": 4,
                    "friday": 4,
                    "sa": 5,
                    "sat": 5,
                    "saturday": 5,
                    "so": 6,
                    "sun": 6,
                    "sunday": 6,
                }
                d = m.get(s[:3], default)
        if d < 0:
            d = 0
        if d > 6:
            d = 6
        return int(d)
    except Exception:
        return int(default)


def _timer_last_boundary_local(
    now_local: datetime,
    *,
    mode: str,
    hh: int,
    mm: int,
    ss: int,
    weekday: int,
) -> datetime | None:
    """Return the most recent scheduled run time (local tz) that is <= now."""

    try:
        run = now_local.replace(hour=hh, minute=mm, second=ss, microsecond=0)
        if mode == "daily":
            if now_local < run:
                run = run - timedelta(days=1)
            return run

        if mode == "weekly":
            wd = int(weekday)
            delta = (now_local.weekday() - wd) % 7
            run = run - timedelta(days=delta)
            if now_local < run:
                run = run - timedelta(days=7)
            return run

        return None
    except Exception:
        return None


def _cache_mode_str(cfg: dict[str, Any], base: str) -> str:
    """Human-readable cache refresh mode string."""

    def _mode_defaults() -> tuple[str, int, str, int]:
        if base == "dash_cache":
            return ("hours", 6, "00:00:00", 0)
        if base == "stats_cache":
            return ("daily", 24, "03:00:00", 0)
        if base == "stats_full":
            return ("manual", 24, "03:00:00", 0)
        if base == "analysis_nightly":
            return ("daily", 24, "03:30:00", 0)
        return ("daily", 24, "03:00:00", 0)

    try:
        mode = str(cfg.get(f"{base}_refresh_mode") or "").strip().lower()
    except Exception:
        mode = ""
    def_mode, def_h, def_at, def_wd = _mode_defaults()
    if mode not in ("hours", "daily", "weekly", "manual"):
        mode = def_mode

    daily_at = str(cfg.get(f"{base}_refresh_daily_at") or def_at).strip() or def_at
    try:
        hours = int(cfg.get(f"{base}_refresh_hours") or def_h)
    except Exception:
        hours = def_h

    wd = _timer_parse_weekday(cfg.get(f"{base}_refresh_weekday"), default=def_wd)
    hh, mm, ss = _timer_parse_hms(daily_at, (3, 0, 0))
    daily_at = f"{hh:02d}:{mm:02d}:{ss:02d}"

    if mode == "hours":
        return f"hours | hours: {hours}"
    if mode == "daily":
        return f"daily | at: {daily_at}"
    if mode == "weekly":
        return f"weekly | weekday: {wd} | at: {daily_at}"
    return "manual"


def _cache_next_update_iso_from(cfg: dict[str, Any], base: str, updated_at_iso: str | None) -> str | None:
    """Best-effort next update time based on settings + last updated time."""

    try:
        if not updated_at_iso:
            return None
        updated_dt = _parse_iso_datetime(str(updated_at_iso))
        if not updated_dt:
            return None

        mode = str(cfg.get(f"{base}_refresh_mode") or "").strip().lower()
        if mode not in ("hours", "daily", "weekly", "manual"):
            mode = "hours" if base == "dash_cache" else "daily"

        if mode == "manual":
            return None

        if mode == "hours":
            try:
                h = int(cfg.get(f"{base}_refresh_hours") or (6 if base == "dash_cache" else 24))
            except Exception:
                h = 6 if base == "dash_cache" else 24
            if h <= 0:
                return None
            nxt = updated_dt + timedelta(hours=h)
            return nxt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

        at = str(cfg.get(f"{base}_refresh_daily_at") or ("00:00:00" if base == "dash_cache" else "03:00:00")).strip() or "00:00:00"
        hh, mm, ss = _timer_parse_hms(at, (0, 0, 0))

        upd_local = updated_dt.astimezone()

        if mode == "daily":
            run = upd_local.replace(hour=hh, minute=mm, second=ss, microsecond=0)
            if run <= upd_local:
                run = run + timedelta(days=1)
            return run.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

        # weekly
        wd = _timer_parse_weekday(cfg.get(f"{base}_refresh_weekday"), default=0)
        run = upd_local.replace(hour=hh, minute=mm, second=ss, microsecond=0)
        delta = (wd - run.weekday()) % 7
        run = run + timedelta(days=delta)
        if run <= upd_local:
            run = run + timedelta(days=7)
        return run.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    except Exception:
        return None


@app.get("/api/cache/all")
def api_cache_all():
    cfg = load_cfg()
    now_ts = datetime.now(timezone.utc).timestamp()

    out: list[dict[str, Any]] = []

    # Dashboard cache
    dash_enabled = bool(cfg.get("dash_cache_enabled", True))
    dash_items = _dash_cache_list_meta() if dash_enabled else []
    dash_mode = _cache_mode_str(cfg, "dash_cache")
    dash_auto = bool(cfg.get("dash_cache_auto_update", True))
    for m in dash_items:
        try:
            mm = dict(m)
            upd = _dash_cache_ts(mm, "updated_at")
            mm["age_seconds"] = int(max(0, now_ts - upd)) if upd else None
            mm["stale"] = _dash_cache_is_stale(cfg, mm)
            mm["bereich"] = "Dashboard"
            mm["ausloeser"] = str(mm.get("trigger_page") or "dashboard")
            mm["modus"] = dash_mode
            mm["next_update_at"] = _cache_next_update_iso_from(cfg, "dash_cache", str(mm.get("updated_at") or "")) if dash_auto else None
            mm["cache_kind"] = "dash"
            out.append(mm)
        except Exception:
            continue

    # Statistik cache
    stats_enabled = bool(cfg.get("stats_cache_enabled", True))
    stats_items = _stats_cache_list_meta() if stats_enabled else []
    stats_mode = _cache_mode_str(cfg, "stats_cache")
    stats_auto = bool(cfg.get("stats_cache_auto_update", True))
    for m in stats_items:
        try:
            mm = dict(m)
            upd = _stats_cache_ts(mm, "updated_at")
            mm["age_seconds"] = int(max(0, now_ts - upd)) if upd else None
            mm["stale"] = _stats_cache_is_stale(cfg, mm)
            mm["bereich"] = "Statistik"
            mm["ausloeser"] = str(mm.get("trigger_page") or "stats")
            mm["modus"] = stats_mode
            mm["next_update_at"] = _cache_next_update_iso_from(cfg, "stats_cache", str(mm.get("updated_at") or "")) if stats_auto else None
            mm["cache_kind"] = "stats"
            out.append(mm)
        except Exception:
            continue

    def _sort_key(x: dict[str, Any]) -> tuple[float, float]:
        try:
            a = 0.0
            try:
                a = float(_parse_iso_datetime(str(x.get("last_used_at") or "") or "").timestamp())
            except Exception:
                a = 0.0
            b = 0.0
            try:
                b = float(_parse_iso_datetime(str(x.get("updated_at") or "") or "").timestamp())
            except Exception:
                b = 0.0
            return (a, b)
        except Exception:
            return (0.0, 0.0)

    out.sort(key=_sort_key, reverse=True)
    return jsonify({
        "ok": True,
        "caches": out,
        "settings": {
            "dash": {
                "enabled": dash_enabled,
                "auto_update": dash_auto,
                "mode": dash_mode,
                "refresh_mode": cfg.get("dash_cache_refresh_mode"),
                "refresh_hours": cfg.get("dash_cache_refresh_hours"),
                "refresh_daily_at": cfg.get("dash_cache_refresh_daily_at"),
            },
            "stats": {
                "enabled": stats_enabled,
                "auto_update": stats_auto,
                "mode": stats_mode,
                "refresh_mode": cfg.get("stats_cache_refresh_mode"),
                "refresh_hours": cfg.get("stats_cache_refresh_hours"),
                "refresh_daily_at": cfg.get("stats_cache_refresh_daily_at"),
            },
        },
    })


@app.post("/api/cache/peek")
def api_cache_peek():
    """Return cached dashboard query result if present (cache-only; no DB query)."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    range_key = str(body.get("range") or "24h")
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    unit = str(body.get("unit") or "").strip()
    detail_mode = str(body.get("detail_mode") or "dynamic").strip().lower()
    if detail_mode not in ("dynamic", "manual"):
        detail_mode = "dynamic"
    try:
        manual_density_pct = int(body.get("manual_density_pct") or 100)
    except Exception:
        manual_density_pct = 100
    manual_density_pct = min(100, max(1, manual_density_pct))

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception:
        start_dt, stop_dt = None, None

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    if not bool(cfg.get("dash_cache_enabled", True)):
        return jsonify({"ok": False, "error": "cache disabled"}), 404

    key = _dash_cache_key(
        cfg,
        body,
        measurement,
        field,
        range_key,
        entity_id,
        friendly_name,
        unit,
        detail_mode,
        manual_density_pct,
        start_dt,
        stop_dt,
    )
    cache_id = _dash_cache_id(key)
    meta = _dash_cache_load_meta(cache_id)
    payload = _dash_cache_load_payload(cache_id)
    if not meta or not payload or not bool(payload.get("ok")):
        return jsonify({"ok": False, "error": "cache miss"}), 404

    _dash_cache_touch_used(cache_id)
    out = dict(payload)
    out["cached"] = True
    out["cache"] = {
        "id": cache_id,
        "updated_at": meta.get("updated_at"),
        "dirty": bool(meta.get("dirty")),
        "mismatch": bool(meta.get("mismatch")),
    }
    return jsonify(out)


@app.post("/api/cache/plan")
def api_cache_plan():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    range_key = str(body.get("range") or "24h")
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    unit = str(body.get("unit") or "").strip()
    detail_mode = str(body.get("detail_mode") or "dynamic").strip().lower()
    if detail_mode not in ("dynamic", "manual"):
        detail_mode = "dynamic"
    try:
        manual_density_pct = int(body.get("manual_density_pct") or 100)
    except Exception:
        manual_density_pct = 100
    manual_density_pct = min(100, max(1, manual_density_pct))
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception:
        start_dt, stop_dt = None, None

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400
    if not bool(cfg.get("dash_cache_enabled", True)):
        return jsonify({"ok": True, "plan": {"has_cache": False, "segments": [], "gaps": [], "changes": [], "reason": "cache_disabled", "reason_label": "Dashboard-Cache ist deaktiviert."}})

    plan = _dash_cache_plan(
        cfg,
        body,
        measurement,
        field,
        range_key,
        entity_id,
        friendly_name,
        unit,
        detail_mode,
        manual_density_pct,
        start_dt,
        stop_dt,
    )

    out_segments = []
    for seg in plan.get("segments") or []:
        meta = seg.get("meta") if isinstance(seg.get("meta"), dict) else {}
        out_segments.append({
            "cache_id": str(seg.get("cache_id") or ""),
            "created_at": meta.get("created_at"),
            "updated_at": meta.get("updated_at"),
            "use_start": _dt_to_rfc3339_utc(seg.get("use_start")),
            "use_stop": _dt_to_rfc3339_utc(seg.get("use_stop")),
            "covered_start": _dt_to_rfc3339_utc(seg.get("covered_start")),
            "covered_stop": _dt_to_rfc3339_utc(seg.get("covered_stop")),
            "row_count": meta.get("row_count"),
            "outlier_count": meta.get("outlier_count"),
        })

    out_gaps = [
        {"start": _dt_to_rfc3339_utc(a), "stop": _dt_to_rfc3339_utc(b)}
        for a, b in (plan.get("gaps") or [])
    ]
    return jsonify({
        "ok": True,
        "plan": {
            "has_cache": bool(plan.get("has_cache")),
            "exact": bool(plan.get("exact")),
            "request": plan.get("request") or {},
            "segments": out_segments,
            "gaps": out_gaps,
            "changes": plan.get("changes") or [],
            "cached_outlier_count": int(plan.get("cached_outlier_count") or 0),
            "full_reference_ms": plan.get("full_reference_ms"),
            "estimated_total_ms": plan.get("estimated_total_ms"),
            "estimated_savings_ms": plan.get("estimated_savings_ms"),
            "reason": None if bool(plan.get("has_cache")) else "no_matching_cache",
            "reason_label": None if bool(plan.get("has_cache")) else "Kein passender Dashboard-Cache fuer Auswahl, Zeitraum und Detailmodus vorhanden.",
        },
    })


@app.post("/api/analysis_cache/plan")
def api_analysis_cache_plan():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    t0 = time.monotonic()
    plan = _analysis_cache_plan(cfg, measurement, field, entity_id, friendly_name, start_dt, stop_dt)
    out_segments = []
    for seg in plan.get("segments") or []:
        meta = seg.get("meta") if isinstance(seg.get("meta"), dict) else {}
        filtered_rows = seg.get("filtered_rows") if isinstance(seg.get("filtered_rows"), list) else []
        out_segments.append({
            "cache_id": str(seg.get("cache_id") or ""),
            "updated_at": meta.get("updated_at"),
            "use_start": _dt_to_rfc3339_utc(seg.get("use_start")),
            "use_stop": _dt_to_rfc3339_utc(seg.get("use_stop")),
            "covered_start": meta.get("covered_start"),
            "covered_stop": meta.get("covered_stop"),
            "outlier_count": meta.get("outlier_count"),
            "bytes": meta.get("bytes"),
            "patch_status": str(meta.get("patch_status") or "ok"),
            "checkpoint_count": int(meta.get("checkpoint_count") or 0),
            "type_counts": _analysis_type_counts(filtered_rows),
            "outlier_times": _analysis_outlier_times(filtered_rows),
            "outlier_details": _analysis_outlier_details(filtered_rows),
        })
    out_gaps = [{"start": _dt_to_rfc3339_utc(a), "stop": _dt_to_rfc3339_utc(b)} for a, b in (plan.get("gaps") or [])]
    out_dirty = [{"start": _dt_to_rfc3339_utc(a), "stop": _dt_to_rfc3339_utc(b)} for a, b in (plan.get("dirty_ranges") or [])]
    out_repaired = [
        {
            "cache_id": str(seg.get("cache_id") or ""),
            "start": str(seg.get("start") or ""),
            "stop": str(seg.get("stop") or ""),
            "repair_reason": str(seg.get("repair_reason") or ""),
        }
        for seg in (plan.get("repaired_segments") or [])
        if isinstance(seg, dict)
    ]
    out_blocked = [
        {
            "cache_id": str(seg.get("cache_id") or ""),
            "start": str(seg.get("start") or ""),
            "stop": str(seg.get("stop") or ""),
            "patch_status": str(seg.get("patch_status") or "ok"),
            "dirty_reason": str(seg.get("dirty_reason") or "history_change"),
            "change_count": int(seg.get("change_count") or 0),
            "repair_reason": seg.get("repair_reason"),
            "repair_error": seg.get("repair_error"),
        }
        for seg in (plan.get("blocked_segments") or [])
        if isinstance(seg, dict)
    ]
    summary_counts = _analysis_type_counts([r for seg in (plan.get("segments") or []) for r in (seg.get("filtered_rows") or []) if isinstance(r, dict)])

    try:
        segs_n = len(out_segments)
        gaps_n = len(out_gaps)
        dirty_n = len(out_dirty)
        _worklog_append_op(
            purpose="analysis",
            op="cache_plan",
            status="ok",
            detail=f"Analyse-Cache-Plan: segs={segs_n} gaps={gaps_n} dirty={dirty_n}",
            measurement=str(measurement),
            field=str(field),
            entity_id=str(entity_id or ""),
            friendly_name=str(friendly_name or ""),
            window_start=_dt_to_rfc3339_utc(start_dt),
            window_stop=_dt_to_rfc3339_utc(stop_dt),
            source="cache" if bool(plan.get("has_cache")) else "db",
            reason_code="cache_plan",
            reason_label="Plan bestimmt, was aus Cache wiederverwendet und was neu gelesen werden muss.",
            duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
            counts={"segments": segs_n, "gaps": gaps_n, "dirty_ranges": dirty_n, "cached_outliers": int(plan.get("cached_outlier_count") or 0)},
            cache={"series_key": str(plan.get("series_key") or "")},
            extra={
                "segments": out_segments[:3],
                "gaps": out_gaps[:3],
                "dirty_ranges": out_dirty[:3],
                "blocked_segments": out_blocked[:3],
            },
        )
    except Exception:
        pass
    return jsonify({
        "ok": True,
        "plan": {
            "request": plan.get("request") or {},
            "has_cache": bool(plan.get("has_cache")),
            "segments": out_segments,
            "gaps": out_gaps,
            "dirty_ranges": out_dirty,
            "changes": plan.get("changes") or [],
            "repaired_segments": out_repaired,
            "blocked_segments": out_blocked,
            "cached_outlier_count": int(plan.get("cached_outlier_count") or 0),
            "cached_outlier_type_counts": summary_counts,
            "series_key": str(plan.get("series_key") or ""),
        },
    })


_ANALYSIS_CACHE_ID_RE = re.compile(r"^[0-9a-f]{40}$")


@app.get("/api/analysis_cache/block_info")
def api_analysis_cache_block_info():
    """Return file and meta details for a single analysis cache block."""

    cache_id = str(request.args.get("cache_id") or "").strip().lower()
    if not cache_id or not _ANALYSIS_CACHE_ID_RE.match(cache_id):
        return jsonify({"ok": False, "error": "invalid cache_id"}), 400

    meta_path = _analysis_cache_meta_path(cache_id)
    data_path = _analysis_cache_data_path(cache_id)

    def _stat(p: Path) -> tuple[bool, int | None]:
        try:
            if not p.exists() or not p.is_file():
                return False, None
            return True, int(p.stat().st_size)
        except Exception:
            return False, None

    meta_exists, meta_bytes = _stat(meta_path)
    data_exists, data_bytes = _stat(data_path)

    meta = _analysis_cache_load_meta(cache_id) or {}

    return jsonify({
        "ok": True,
        "info": {
            "cache_id": cache_id,
            "meta_file": meta_path.name,
            "data_file": data_path.name,
            "meta_path": f"/data/analysis_cache/{meta_path.name}",
            "data_path": f"/data/analysis_cache/{data_path.name}",
            "meta_exists": bool(meta_exists),
            "data_exists": bool(data_exists),
            "meta_bytes": meta_bytes,
            "data_bytes": data_bytes,
            "meta": meta,
        },
    })


@app.post("/api/analysis_cache/segment")
def api_analysis_cache_segment():
    body = request.get_json(force=True) or {}
    cache_id = str(body.get("cache_id") or "").strip()
    if not cache_id:
        return jsonify({"ok": False, "error": "cache_id required"}), 400
    meta = _analysis_cache_load_meta(cache_id)
    payload = _analysis_cache_load_payload(cache_id)
    if not meta or not payload or not bool(payload.get("ok")):
        return jsonify({"ok": False, "error": "cache miss"}), 404
    try:
        meta["last_used_at"] = _utc_now_iso_ms()
        _analysis_cache_write_meta(meta)
    except Exception:
        pass
    return jsonify({"ok": True, "cache": meta, "payload": payload})


@app.post("/api/analysis_cache/store_segment")
def api_analysis_cache_store_segment():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    start_iso = str(body.get("start") or "").strip()
    stop_iso = str(body.get("stop") or "").strip()
    rows = body.get("rows") if isinstance(body.get("rows"), list) else []
    scanned = int(body.get("scanned") or 0)
    checkpoints = body.get("checkpoints") if isinstance(body.get("checkpoints"), list) else []
    final_state = body.get("final_state") if isinstance(body.get("final_state"), dict) else {}
    windows_meta = body.get("windows_meta") if isinstance(body.get("windows_meta"), dict) else None
    if not measurement or not field or not start_iso or not stop_iso:
        return jsonify({"ok": False, "error": "measurement, field, start, stop required"}), 400

    t0 = time.monotonic()
    LOG.info(
        "api.analysis_cache.store_segment called measurement=%s field=%s entity_id=%s friendly_name=%s start=%s stop=%s rows=%d scanned=%d",
        measurement,
        field,
        entity_id,
        friendly_name,
        start_iso,
        stop_iso,
        len(rows),
        scanned,
    )
    meta = _analysis_cache_store_segment(
        cfg,
        measurement,
        field,
        entity_id,
        friendly_name,
        start_iso,
        stop_iso,
        rows,
        scanned,
        checkpoints=checkpoints,
        final_state=final_state,
        windows_meta=windows_meta,
    )
    if not meta:
        return jsonify({"ok": False, "error": "store failed"}), 500
    LOG.info(
        "api.analysis_cache.store_segment ok cache_id=%s series_key=%s outlier_count=%s bytes=%s",
        str(meta.get("id") or ""),
        str(meta.get("series_key") or ""),
        str(meta.get("outlier_count") or 0),
        str(meta.get("bytes") or 0),
    )
    try:
        _worklog_append_op(
            purpose="analysis",
            op="cache_store",
            status="ok",
            detail=f"Analyse-Cache Segment gespeichert: rows={len(rows)} scanned={scanned}",
            measurement=str(measurement),
            field=str(field),
            entity_id=str(entity_id or ""),
            friendly_name=str(friendly_name or ""),
            window_start=str(start_iso),
            window_stop=str(stop_iso),
            source="cache",
            reason_code="cache_store",
            reason_label="Neu gelesene Analyse-Ergebnisse wurden als Cache-Segment persistent gespeichert.",
            duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
            counts={"rows": len(rows), "scanned": scanned, "checkpoints": len(checkpoints)},
            cache={"cache_id": str(meta.get("id") or ""), "series_key": str(meta.get("series_key") or ""), "bytes": meta.get("bytes")},
        )
    except Exception:
        pass
    return jsonify({"ok": True, "cache": meta})


@app.post("/api/analysis_cache/patch_windows")
def api_analysis_cache_patch_windows():
    """Patch (persist) per-outlier raw windows into analysis_cache payload rows.

    Used for incremental backfill (e.g. cache-preload with missing windows) and for
    chunk-boundary completion where after-context becomes known later.

    Important: does NOT update meta.updated_at (to avoid triggering history-change / dirty logic).
    """

    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    series_key = str(body.get("series_key") or "").strip() or None
    cache_ids = body.get("cache_ids") if isinstance(body.get("cache_ids"), list) else []
    updates_in = body.get("updates") if isinstance(body.get("updates"), list) else []
    windows_meta = body.get("windows_meta") if isinstance(body.get("windows_meta"), dict) else None

    if not series_key:
        if not measurement or not field:
            return jsonify({"ok": False, "error": "measurement, field required (or series_key)"}), 400
        series_key = _analysis_cache_series_key(measurement, field, entity_id, friendly_name)

    updates: dict[str, dict[str, Any]] = {}
    for u in updates_in:
        if not isinstance(u, dict):
            continue
        t = str(u.get("time") or "").strip()
        w = u.get("window") if isinstance(u.get("window"), dict) else None
        if not t or not w:
            continue
        updates[t] = dict(w)

    if not updates:
        return jsonify({"ok": True, "patched": 0, "segments": 0})
    if len(updates) > 5000:
        return jsonify({"ok": False, "error": "too many updates (max 5000)"}), 413

    # Infer windows_meta from the first update if not provided.
    if not isinstance(windows_meta, dict) or not windows_meta:
        try:
            first_w = next(iter(updates.values()))
            windows_meta = {
                "n_before": first_w.get("n_before"),
                "n_after": first_w.get("n_after"),
                "algo_v": first_w.get("algo_v"),
                "computed_at": _utc_now_iso_ms(),
            }
        except Exception:
            windows_meta = None

    # Select candidate segments.
    candidates: list[str] = []
    if cache_ids:
        for cid in cache_ids:
            c = str(cid or "").strip()
            if c:
                candidates.append(c)
    else:
        for meta in _analysis_cache_list_meta():
            try:
                if str(meta.get("series_key") or "") != str(series_key or ""):
                    continue
                cid = str(meta.get("id") or "").strip()
                if cid:
                    candidates.append(cid)
            except Exception:
                continue

    patched = 0
    touched_segments = 0
    for cache_id in list(dict.fromkeys(candidates)):
        meta = _analysis_cache_load_meta(cache_id)
        if not meta or str(meta.get("series_key") or "") != str(series_key or ""):
            continue
        payload = _analysis_cache_load_payload(cache_id)
        if not payload or not bool(payload.get("ok")):
            continue
        rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
        if not rows:
            continue

        by_time: dict[str, dict[str, Any]] = {}
        for r in rows:
            if isinstance(r, dict) and str(r.get("time") or "").strip():
                by_time[str(r.get("time") or "").strip()] = r

        changed = False
        for t, w in updates.items():
            r = by_time.get(t)
            if not r:
                continue
            r["window"] = dict(w)
            changed = True
            patched += 1

        if not changed:
            continue

        # Update payload meta so the UI can detect stale/mismatched window configs.
        if isinstance(payload.get("meta"), dict) and isinstance(windows_meta, dict) and windows_meta:
            try:
                payload["meta"]["windows_n_before"] = int(windows_meta.get("n_before") or 0) or None
            except Exception:
                payload["meta"]["windows_n_before"] = None
            try:
                payload["meta"]["windows_n_after"] = int(windows_meta.get("n_after") or 0) or None
            except Exception:
                payload["meta"]["windows_n_after"] = None
            try:
                payload["meta"]["windows_algo_v"] = int(windows_meta.get("algo_v") or 0) or None
            except Exception:
                payload["meta"]["windows_algo_v"] = None
            payload["meta"]["windows_computed_at"] = str(windows_meta.get("computed_at") or "").strip() or None

        _analysis_cache_write_payload(cache_id, payload)
        touched_segments += 1

    return jsonify({"ok": True, "patched": patched, "segments": touched_segments, "series_key": series_key})


@app.get("/api/analysis_cache/list")
def api_analysis_cache_list():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    rows = _analysis_cache_group_list(cfg)
    LOG.info("api.analysis_cache.list result groups=%d", len(rows))
    return jsonify({"ok": True, "series": rows})


@app.post("/api/analysis_cache/delete")
def api_analysis_cache_delete():
    body = request.get_json(force=True) or {}
    cache_id = str(body.get("cache_id") or "").strip()
    series_key = str(body.get("series_key") or "").strip()
    delete_all = bool(body.get("all"))
    if delete_all:
        for meta in _analysis_cache_list_meta():
            _analysis_cache_delete_id(str(meta.get("id") or ""))
        return jsonify({"ok": True, "deleted": "all"})
    if cache_id:
        _analysis_cache_delete_id(cache_id)
        return jsonify({"ok": True, "deleted": cache_id})
    if series_key:
        count = 0
        for meta in _analysis_cache_list_meta():
            if str(meta.get("series_key") or "") != series_key:
                continue
            _analysis_cache_delete_id(str(meta.get("id") or ""))
            count += 1
        return jsonify({"ok": True, "deleted": count})
    return jsonify({"ok": False, "error": "cache_id or series_key required"}), 400


@app.post("/api/analysis_cache/rebuild")
def api_analysis_cache_rebuild():
    body = request.get_json(force=True) or {}
    series_key = str(body.get("series_key") or "").strip()
    if not series_key:
        return jsonify({"ok": False, "error": "series_key required"}), 400
    t0 = time.monotonic()
    metas = [m for m in _analysis_cache_list_meta() if str(m.get("series_key") or "") == series_key]
    if not metas:
        return jsonify({"ok": False, "error": "series not found"}), 404
    metas.sort(key=lambda m: str(m.get("covered_start") or ""))
    rebuilt = 0
    for meta in metas:
        key = meta.get("key") if isinstance(meta.get("key"), dict) else {}
        measurement = str(key.get("measurement") or meta.get("measurement") or "")
        field = str(key.get("field") or meta.get("field") or "")
        entity_id = str(key.get("entity_id") or meta.get("entity_id") or "") or None
        friendly_name = str(key.get("friendly_name") or meta.get("friendly_name") or "") or None
        start_iso = str(key.get("start") or meta.get("covered_start") or "")
        stop_iso = str(key.get("stop") or meta.get("covered_stop") or "")
        try:
            rows, scanned = _analysis_cache_fetch_segment(cfg, measurement, field, entity_id, friendly_name, start_iso, stop_iso)
        except _ApiError as e:
            return jsonify({"ok": False, "error": str(e)}), int(getattr(e, "status_code", 500) or 500)
        cfg = _overlay_from_yaml_if_enabled(load_cfg())
        _analysis_cache_store_segment(
            cfg,
            measurement,
            field,
            entity_id,
            friendly_name,
            start_iso,
            stop_iso,
            rows,
            scanned,
        )
        rebuilt += 1
    try:
        _worklog_append_op(
            purpose="analysis",
            op="cache_rebuild",
            status="ok",
            detail=f"Analyse-Cache rebuild: rebuilt={rebuilt}",
            source="cache",
            reason_code="rebuild",
            reason_label="Cache-Segmente wurden neu berechnet und erneut gespeichert.",
            duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
            counts={"rebuilt": rebuilt},
            cache={"series_key": series_key},
        )
    except Exception:
        pass
    return jsonify({"ok": True, "rebuilt": rebuilt})


@app.post("/api/analysis_cache/combine")
def api_analysis_cache_combine():
    try:
        cfg = _overlay_from_yaml_if_enabled(load_cfg())
        body = request.get_json(force=True) or {}
        series_key = str(body.get("series_key") or "").strip()
        if not series_key:
            return jsonify({"ok": False, "error": "series_key required"}), 400
        t0 = time.monotonic()
        metas = [m for m in _analysis_cache_list_meta() if str(m.get("series_key") or "") == series_key]
        if not metas:
            return jsonify({"ok": False, "error": "series not found"}), 404
        groups_all = [g for g in _analysis_cache_contiguous_groups(metas) if len(g) > 1]
        groups: list[list[dict[str, Any]]] = []
        skipped_dirty_segments: list[dict[str, Any]] = []
        repaired_before_combine: list[dict[str, Any]] = []
        for group in groups_all:
            dirty_group = False
            resolved_group: list[dict[str, Any]] = []
            for meta in group:
                start_dt, stop_dt = _analysis_cache_meta_span(meta)
                if not start_dt or not stop_dt:
                    dirty_group = True
                    skipped_dirty_segments.append({
                        "cache_id": str(meta.get("id") or ""),
                        "start": str(meta.get("covered_start") or ""),
                        "stop": str(meta.get("covered_stop") or ""),
                        "patch_status": str(meta.get("patch_status") or "ok"),
                        "dirty_reason": str(meta.get("dirty_reason") or "invalid_span"),
                    })
                    continue
                resolved = _analysis_cache_resolve_segment_reuse(cfg, meta, start_dt, stop_dt)
                if bool(resolved.get("reused_after_repair")):
                    repaired_before_combine.append({
                        "cache_id": str(meta.get("id") or ""),
                        "repair_reason": str(resolved.get("repair_reason") or "patched"),
                    })
                if not bool(resolved.get("usable")):
                    changes = resolved.get("changes") if isinstance(resolved.get("changes"), list) else []
                    patch_status = str(resolved.get("patch_status") or "ok")
                    dirty_group = True
                    skipped_dirty_segments.append({
                        "cache_id": str(meta.get("id") or ""),
                        "start": str(meta.get("covered_start") or ""),
                        "stop": str(meta.get("covered_stop") or ""),
                        "patch_status": patch_status,
                        "dirty_reason": str(resolved.get("dirty_reason") or "history_change"),
                        "change_count": len(changes),
                        "repair_reason": resolved.get("repair_reason"),
                        "repair_error": resolved.get("repair_error"),
                    })
                    continue
                resolved_group.append(resolved.get("meta") if isinstance(resolved.get("meta"), dict) else meta)
            if not dirty_group:
                groups.append(resolved_group or group)
        if not groups:
            try:
                _worklog_append_op(
                    purpose="analysis",
                    op="cache_combine",
                    status="ok",
                    detail="Analyse-Cache combine: keine sauberen Gruppen zum Kombinieren",
                    source="cache",
                    reason_code="combine",
                    duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
                    counts={"groups_combined": 0, "skipped_dirty": len(skipped_dirty_segments)},
                    cache={"series_key": series_key},
                    extra={"skipped_dirty_segments": skipped_dirty_segments[:3]},
                )
            except Exception:
                pass
            return jsonify({
                "ok": True,
                "created": [],
                "deleted_ids": [],
                "groups_combined": 0,
                "repaired_before_combine": repaired_before_combine,
                "skipped_dirty_segments": skipped_dirty_segments,
                "note": "no clean contiguous segments to combine",
            })
        created: list[dict[str, Any]] = []
        deleted_ids: list[str] = []
        for group in groups:
            merged = _analysis_cache_merge_group(cfg, group)
            if not merged:
                continue
            created.append({
                "cache_id": str(merged.get("id") or ""),
                "start": str(merged.get("covered_start") or ""),
                "stop": str(merged.get("covered_stop") or ""),
                "updated_at": str(merged.get("updated_at") or ""),
                "outlier_count": int(merged.get("outlier_count") or 0),
            })
            deleted_ids.extend([str(m.get("id") or "") for m in group])
        if not created:
            return jsonify({"ok": False, "error": "combine failed"}), 500

        try:
            _worklog_append_op(
                purpose="analysis",
                op="cache_combine",
                status="ok",
                detail=f"Analyse-Cache combine: groups_combined={len(created)} deleted={len(deleted_ids)}",
                source="cache",
                reason_code="combine",
                reason_label="Zusammenhaengende saubere Segmente wurden zu groesseren Segmenten kombiniert.",
                duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
                counts={"groups_combined": len(created), "deleted": len(deleted_ids)},
                cache={"series_key": series_key, "created": created[:3]},
                extra={"repaired_before_combine": repaired_before_combine[:3], "skipped_dirty_segments": skipped_dirty_segments[:3]},
            )
        except Exception:
            pass
        return jsonify({
            "ok": True,
            "created": created,
            "deleted_ids": deleted_ids,
            "groups_combined": len(created),
            "repaired_before_combine": repaired_before_combine,
            "skipped_dirty_segments": skipped_dirty_segments,
        })
    except _ApiError as e:
        LOG.error("api.analysis_cache.combine api_error series_key=%s error=%s", request.get_json(silent=True) and str((request.get_json(silent=True) or {}).get("series_key") or "") or "", e)
        try:
            _worklog_append_op(
                purpose="analysis",
                op="cache_combine",
                status="err",
                detail=f"Analyse-Cache combine Fehler: {str(e) or e.__class__.__name__}",
                source="cache",
                reason_code="combine",
            )
        except Exception:
            pass
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), int(getattr(e, "status_code", 500) or 500)
    except Exception as e:
        LOG.error("api.analysis_cache.combine unexpected error: %s", e, exc_info=True)
        try:
            _worklog_append_op(
                purpose="analysis",
                op="cache_combine",
                status="err",
                detail=f"Analyse-Cache combine Fehler: {_short_influx_error(e)}",
                source="cache",
                reason_code="combine",
            )
        except Exception:
            pass
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/cache/delete")
def api_cache_delete():
    body = request.get_json(force=True) or {}
    cache_id = str(body.get("cache_id") or "").strip()
    delete_all = bool(body.get("all"))

    try:
        if delete_all:
            if DASH_CACHE_DIR.exists():
                for p in DASH_CACHE_DIR.glob("*"):
                    try:
                        if p.is_file():
                            p.unlink(missing_ok=True)
                    except Exception:
                        continue
            return jsonify({"ok": True, "deleted": "all"})

        if not cache_id:
            return jsonify({"ok": False, "error": "cache_id required"}), 400
        _dash_cache_meta_path(cache_id).unlink(missing_ok=True)
        _dash_cache_data_path(cache_id).unlink(missing_ok=True)
        return jsonify({"ok": True, "deleted": cache_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500


@app.post("/api/cache/check")
def api_cache_check():
    body = request.get_json(force=True) or {}
    cache_id = str(body.get("cache_id") or "").strip()
    if not cache_id:
        return jsonify({"ok": False, "error": "cache_id required"}), 400
    if not _dash_cache_load_meta(cache_id):
        return jsonify({"ok": False, "error": "cache not found"}), 404
    job_id = _dash_cache_start_job("check", cache_id, trigger_page="jobs")
    return jsonify({"ok": True, "job_id": job_id})


@app.post("/api/cache/update")
def api_cache_update():
    body = request.get_json(force=True) or {}
    cache_id = str(body.get("cache_id") or "").strip()
    if not cache_id:
        return jsonify({"ok": False, "error": "cache_id required"}), 400
    if not _dash_cache_load_meta(cache_id):
        return jsonify({"ok": False, "error": "cache not found"}), 404
    job_id = _dash_cache_start_job("update", cache_id, trigger_page="jobs")
    return jsonify({"ok": True, "job_id": job_id})


def _stats_cache_start_update_job(cache_id: str, trigger_page: str, timer_id: str | None = None) -> str:
    meta = _stats_cache_load_meta(cache_id)
    if not meta:
        raise _ApiError("cache not found", 404)
    key = meta.get("key") or {}
    if not isinstance(key, dict) or str(key.get("kind") or "") != "global_stats":
        raise _ApiError("invalid cache key", 400)

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if not bool(cfg.get("stats_cache_enabled", True)):
        raise _ApiError("cache disabled", 400)

    rk = str(key.get("range") or "custom").strip().lower() or "custom"
    if rk == "custom":
        s = str(key.get("start") or "").strip()
        e = str(key.get("stop") or "").strip()
        if not (s and e):
            raise _ApiError("custom cache requires start/stop", 400)
        start_dt = _parse_iso_datetime(s)
        stop_dt = _parse_iso_datetime(e)
        if not start_dt or not stop_dt:
            raise _ApiError("invalid start/stop", 400)
    else:
        start_dt, stop_dt = _stats_cache_range_to_datetimes(rk)

    field_filter = str(key.get("field_filter") or "").strip() or None
    measurement_filter = str(key.get("measurement") or "").strip() or None
    entity_id_filter = str(key.get("entity_id") or "").strip() or None
    friendly_name_filter = str(key.get("friendly_name") or "").strip() or None
    cols_raw = key.get("columns")
    columns = [str(x) for x in cols_raw] if isinstance(cols_raw, list) else None
    try:
        page_limit = int(key.get("page_limit") or 200)
    except Exception:
        page_limit = 200
    page_limit = min(200, max(10, page_limit))

    # mark dirty (best-effort) until job writes a fresh payload
    try:
        meta["dirty"] = True
        meta["dirty_reason"] = "update_requested"
        meta["dirty_at"] = _utc_now_iso_ms()
        _stats_cache_write_meta(meta)
    except Exception:
        pass

    return _global_stats_start_job(
        cfg,
        start_dt,
        stop_dt,
        field_filter,
        measurement_filter,
        entity_id_filter,
        friendly_name_filter,
        None,
        columns,
        page_limit,
        trigger_page=trigger_page,
        timer_id=timer_id,
        cache_id=cache_id,
        cache_key=key,
    )


@app.get("/api/stats_cache/list")
def api_stats_cache_list():
    cfg = load_cfg()
    enabled = bool(cfg.get("stats_cache_enabled", True))
    items = _stats_cache_list_meta() if enabled else []

    def _sort_key(m: dict[str, Any]) -> tuple[float, float]:
        return (_stats_cache_ts(m, "last_used_at") or _stats_cache_ts(m, "updated_at"), _stats_cache_ts(m, "updated_at"))

    items.sort(key=_sort_key, reverse=True)
    now_ts = datetime.now(timezone.utc).timestamp()
    out = []
    for m in items:
        try:
            mm = dict(m)
            upd = _stats_cache_ts(mm, "updated_at")
            mm["age_seconds"] = int(max(0, now_ts - upd)) if upd else None
            mm["stale"] = _stats_cache_is_stale(cfg, mm)
            out.append(mm)
        except Exception:
            continue
    return jsonify({
        "ok": True,
        "enabled": enabled,
        "caches": out,
        "settings": {
            "refresh_mode": cfg.get("stats_cache_refresh_mode"),
            "refresh_hours": cfg.get("stats_cache_refresh_hours"),
            "refresh_daily_at": cfg.get("stats_cache_refresh_daily_at"),
            "max_items": cfg.get("stats_cache_max_items"),
            "max_mb": cfg.get("stats_cache_max_mb"),
            "auto_update": cfg.get("stats_cache_auto_update"),
        },
    })


@app.get("/api/stats_cache/get")
def api_stats_cache_get():
    cache_id = str(request.args.get("cache_id") or "").strip()
    if not cache_id:
        return jsonify({"ok": False, "error": "cache_id required"}), 400
    meta = _stats_cache_load_meta(cache_id)
    payload = _stats_cache_load_payload(cache_id)
    if not meta or not payload:
        return jsonify({"ok": False, "error": "cache miss"}), 404

    try:
        limit = int(request.args.get("limit", "5000"))
    except Exception:
        limit = 5000
    limit = min(20000, max(1, limit))
    try:
        offset = int(request.args.get("offset", "0"))
    except Exception:
        offset = 0
    offset = max(0, offset)

    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        rows = []

    key = payload.get("key") if isinstance(payload, dict) else None
    if not isinstance(key, dict):
        key = meta.get("key") if isinstance(meta, dict) else None
    if not isinstance(key, dict):
        key = {}
    cols = key.get("columns") if isinstance(key.get("columns"), list) else []

    _stats_cache_touch_used(cache_id)
    return jsonify({
        "ok": True,
        "ready": True,
        "rows": rows[offset : offset + limit],
        "total": len(rows),
        "columns": cols,
        "key": key,
        "cache": {
            "id": cache_id,
            "updated_at": meta.get("updated_at"),
            "dirty": bool(meta.get("dirty")),
            "mismatch": bool(meta.get("mismatch")),
            "covered_start": payload.get("covered_start") if isinstance(payload, dict) else None,
            "covered_stop": payload.get("covered_stop") if isinstance(payload, dict) else None,
        },
    })


@app.post("/api/stats_cache/delete")
def api_stats_cache_delete():
    body = request.get_json(force=True) or {}
    cache_id = str(body.get("cache_id") or "").strip()
    delete_all = bool(body.get("all"))

    try:
        if delete_all:
            if STATS_CACHE_DIR.exists():
                for p in STATS_CACHE_DIR.glob("*"):
                    try:
                        if p.is_file():
                            p.unlink(missing_ok=True)
                    except Exception:
                        continue
            return jsonify({"ok": True, "deleted": "all"})

        if not cache_id:
            return jsonify({"ok": False, "error": "cache_id required"}), 400
        _stats_cache_meta_path(cache_id).unlink(missing_ok=True)
        _stats_cache_data_path(cache_id).unlink(missing_ok=True)
        return jsonify({"ok": True, "deleted": cache_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500


@app.post("/api/stats_cache/update")
def api_stats_cache_update():
    body = request.get_json(force=True) or {}
    cache_id = str(body.get("cache_id") or "").strip()
    if not cache_id:
        return jsonify({"ok": False, "error": "cache_id required"}), 400
    try:
        job_id = _stats_cache_start_update_job(cache_id, trigger_page="jobs")
        return jsonify({"ok": True, "job_id": job_id})
    except _ApiError as e:
        return jsonify({"ok": False, "error": e.message}), e.status
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


def _stats_cache_next_run_iso(cfg: dict[str, Any]) -> str | None:
    try:
        mode = str(cfg.get("stats_cache_refresh_mode") or "daily").strip().lower()
        if mode not in ("hours", "daily", "weekly", "manual"):
            mode = "daily"
        if mode == "manual":
            return None
        now_local = datetime.now().astimezone()
        if mode == "hours":
            try:
                h = int(cfg.get("stats_cache_refresh_hours", 24) or 24)
            except Exception:
                h = 24
            if h <= 0:
                return None
            nxt = now_local + timedelta(hours=h)
            return nxt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

        at = str(cfg.get("stats_cache_refresh_daily_at") or "03:00:00").strip() or "03:00:00"
        hh, mm, ss = _timer_parse_hms(at, (3, 0, 0))
        wd = _timer_parse_weekday(cfg.get("stats_cache_refresh_weekday"), default=0)

        run = now_local.replace(hour=hh, minute=mm, second=ss, microsecond=0)
        if mode == "daily":
            if run <= now_local:
                run = run + timedelta(days=1)
        else:
            # weekly
            delta = (wd - run.weekday()) % 7
            run = run + timedelta(days=delta)
            if run <= now_local:
                run = run + timedelta(days=7)

        return run.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    except Exception:
        return None


def _cache_schedule_next_run_iso(cfg: dict[str, Any], base: str) -> str | None:
    """Compute next run for a cache scheduler (best-effort, local time)."""

    try:
        mode = str(cfg.get(f"{base}_refresh_mode") or "daily").strip().lower()
        if mode not in ("hours", "daily", "weekly", "manual"):
            mode = "daily"
        if mode == "manual":
            return None

        now_local = datetime.now().astimezone()
        if mode == "hours":
            try:
                h = int(cfg.get(f"{base}_refresh_hours", 24) or 24)
            except Exception:
                h = 24
            if h <= 0:
                return None
            nxt = now_local + timedelta(hours=h)
            return nxt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

        at = str(cfg.get(f"{base}_refresh_daily_at") or "03:00:00").strip() or "03:00:00"
        hh, mm, ss = _timer_parse_hms(at, (3, 0, 0))
        wd = _timer_parse_weekday(cfg.get(f"{base}_refresh_weekday"), default=0)

        run = now_local.replace(hour=hh, minute=mm, second=ss, microsecond=0)
        if mode == "daily":
            if run <= now_local:
                run = run + timedelta(days=1)
        else:
            delta = (wd - run.weekday()) % 7
            run = run + timedelta(days=delta)
            if run <= now_local:
                run = run + timedelta(days=7)

        return run.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    except Exception:
        return None


def _analysis_nightly_job_public(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": job.get("id"),
        "state": job.get("state"),
        "message": job.get("message"),
        "started_at": job.get("started_at"),
        "updated_at": job.get("updated_at"),
        "finished_at": job.get("finished_at"),
        "elapsed": _job_elapsed_hms(job),
        "current": job.get("current") or "",
        "series_key": job.get("series_key") or "",
        "measurement": job.get("measurement") or "",
        "field": job.get("field") or "",
        "entity_id": job.get("entity_id") or "",
        "friendly_name": job.get("friendly_name") or "",
        "trigger_page": job.get("trigger_page") or "",
        "timer_id": job.get("timer_id") or "",
        "cancelled": bool(job.get("cancelled")),
        "error": job.get("error"),
        "ready": job.get("state") in ("done", "error", "cancelled"),
    }


def _analysis_nightly_inflight(series_key: str) -> bool:
    sk = str(series_key or "").strip()
    if not sk:
        return False
    with ANALYSIS_NIGHTLY_LOCK:
        for j in ANALYSIS_NIGHTLY_JOBS.values():
            try:
                if str(j.get("series_key") or "") != sk:
                    continue
                st = str(j.get("state") or "")
                if st and st not in ("done", "error", "cancelled"):
                    return True
            except Exception:
                continue
    return False


def _analysis_nightly_any_inflight() -> bool:
    try:
        with ANALYSIS_NIGHTLY_LOCK:
            for j in ANALYSIS_NIGHTLY_JOBS.values():
                try:
                    st = str(j.get("state") or "")
                    if st and st not in ("done", "error", "cancelled"):
                        return True
                except Exception:
                    continue
    except Exception:
        return False
    return False


def _analysis_nightly_series_last_runs() -> dict[str, str]:
    try:
        st = _timers_state_get("analysis_nightly")
        m = st.get("series_last_run") if isinstance(st, dict) else None
        if not isinstance(m, dict):
            return {}
        out: dict[str, str] = {}
        for k, v in m.items():
            ks = str(k or "").strip()
            vs = str(v or "").strip()
            if ks and vs:
                out[ks] = vs
        return out
    except Exception:
        return {}


def _analysis_nightly_set_series_last_run(series_key: str, at_iso: str) -> None:
    try:
        sk = str(series_key or "").strip()
        if not sk:
            return
        st = _timers_state_load()
        cur = st.get("analysis_nightly")
        cur = cur if isinstance(cur, dict) else {}
        m = cur.get("series_last_run")
        m = m if isinstance(m, dict) else {}
        m[sk] = str(at_iso or "").strip() or _utc_now_iso_ms()
        # best-effort cap
        if len(m) > 5000:
            # keep some arbitrary tail by timestamp
            try:
                items = [(k, v) for k, v in m.items() if str(k).strip() and str(v).strip()]
                items.sort(key=lambda kv: str(kv[1]))
                m = dict(items[-4500:])
            except Exception:
                pass
        cur["series_last_run"] = m
        st["analysis_nightly"] = cur
        _timers_state_save(st)
    except Exception:
        return


def _analysis_nightly_due_boundary(cfg: dict[str, Any]) -> datetime | None:
    try:
        mode = str(cfg.get("analysis_nightly_refresh_mode") or "daily").strip().lower()
        if mode not in ("hours", "daily", "weekly", "manual"):
            mode = "daily"
        if mode == "manual":
            return None
        if mode == "hours":
            return None
        at = str(cfg.get("analysis_nightly_refresh_daily_at") or "03:30:00").strip() or "03:30:00"
        hh, mm, ss = _timer_parse_hms(at, (3, 30, 0))
        wd = _timer_parse_weekday(cfg.get("analysis_nightly_refresh_weekday"), default=0)
        now_local = datetime.now().astimezone()
        return _timer_last_boundary_local(now_local, mode=mode, hh=hh, mm=mm, ss=ss, weekday=wd)
    except Exception:
        return None


def _analysis_nightly_pick_series(cfg: dict[str, Any]) -> dict[str, Any] | None:
    try:
        if not bool(cfg.get("analysis_nightly_enabled", True)) or not bool(cfg.get("analysis_nightly_auto_update", True)):
            return None

        # Keep concurrency low: process one series at a time.
        if _analysis_nightly_any_inflight():
            return None

        mode = str(cfg.get("analysis_nightly_refresh_mode") or "daily").strip().lower()
        if mode not in ("hours", "daily", "weekly", "manual"):
            mode = "daily"
        if mode == "manual":
            return None

        rows = _analysis_cache_group_list(cfg)
        if not rows:
            return None

        last_runs = _analysis_nightly_series_last_runs()
        boundary = _analysis_nightly_due_boundary(cfg)
        now_utc = datetime.now(timezone.utc)
        due: list[tuple[float, dict[str, Any]]] = []

        for row in rows:
            try:
                sk = str(row.get("series_key") or "").strip()
                if not sk:
                    continue
                if _analysis_nightly_inflight(sk):
                    continue

                last_iso = last_runs.get(sk) or ""
                last_dt = None
                try:
                    last_dt = _parse_iso_datetime(str(last_iso)) if last_iso else None
                except Exception:
                    last_dt = None

                is_due = False
                if mode == "hours":
                    try:
                        h = int(cfg.get("analysis_nightly_refresh_hours") or 24)
                    except Exception:
                        h = 24
                    h = max(1, min(8760, h))
                    if not last_dt:
                        is_due = True
                    else:
                        is_due = (now_utc.timestamp() - last_dt.timestamp()) >= float(h * 3600)
                else:
                    if boundary is None:
                        continue
                    if not last_dt:
                        is_due = True
                    else:
                        last_local = last_dt.astimezone(datetime.now().astimezone().tzinfo)
                        is_due = last_local < boundary

                if not is_due:
                    continue

                score = last_dt.timestamp() if last_dt else 0.0
                due.append((score, row))
            except Exception:
                continue

        if not due:
            return None
        due.sort(key=lambda it: it[0])
        return due[0][1]
    except Exception:
        return None


def _analysis_nightly_refresh_series(cfg: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    """Run an analysis-cache refresh for one series (best-effort)."""

    sk = str(row.get("series_key") or "").strip()
    measurement = str(row.get("measurement") or "").strip()
    field = str(row.get("field") or "").strip()
    entity_id = str(row.get("entity_id") or "").strip() or None
    friendly_name = str(row.get("friendly_name") or "").strip() or None
    if not (sk and measurement and field):
        raise _ApiError("invalid series", 400)

    try:
        h = int(cfg.get("analysis_nightly_window_hours") or 24)
    except Exception:
        h = 24
    h = max(1, min(24 * 365, h))
    stop_dt = datetime.now(timezone.utc)
    start_dt = stop_dt - timedelta(hours=h)
    start_iso = _dt_to_rfc3339_utc(start_dt)
    stop_iso = _dt_to_rfc3339_utc(stop_dt)

    plan = _analysis_cache_plan(cfg, measurement, field, entity_id, friendly_name, start_dt, stop_dt)
    gaps = plan.get("gaps") if isinstance(plan.get("gaps"), list) else []
    dirty = plan.get("dirty_ranges") if isinstance(plan.get("dirty_ranges"), list) else []
    todo = []
    for it in (gaps + dirty):
        try:
            a, b = it
            if not a or not b:
                continue
            if b <= a:
                continue
            todo.append((a, b))
        except Exception:
            continue

    stored = 0
    scanned_total = 0
    outliers_total = 0
    for a, b in todo:
        seg_start = _dt_to_rfc3339_utc(a)
        seg_stop = _dt_to_rfc3339_utc(b)
        rows2, scanned = _analysis_cache_fetch_segment(cfg, measurement, field, entity_id, friendly_name, seg_start, seg_stop)
        _analysis_cache_store_segment(cfg, measurement, field, entity_id, friendly_name, seg_start, seg_stop, rows2, scanned)
        stored += 1
        scanned_total += int(scanned or 0)
        outliers_total += len(rows2)

    # Combine contiguous clean segments (best-effort)
    try:
        with app.test_request_context("/api/analysis_cache/combine", method="POST", json={"series_key": sk}):
            resp = api_analysis_cache_combine()
        if isinstance(resp, tuple):
            resp0 = resp[0]
        else:
            resp0 = resp
        data = resp0.get_json(silent=True) if hasattr(resp0, "get_json") else None
        combined = int((data or {}).get("groups_combined") or 0)
    except Exception:
        combined = 0

    return {
        "series_key": sk,
        "start": start_iso,
        "stop": stop_iso,
        "segments_stored": stored,
        "scanned": scanned_total,
        "outliers": outliers_total,
        "groups_combined": combined,
        "gaps": len(gaps),
        "dirty": len(dirty),
    }


def _analysis_nightly_job_thread(job_id: str) -> None:
    def set_state(state: str, msg: str, current: str | None = None) -> None:
        timer_id = None
        extra = None
        with ANALYSIS_NIGHTLY_LOCK:
            if job_id not in ANALYSIS_NIGHTLY_JOBS:
                return
            ANALYSIS_NIGHTLY_JOBS[job_id]["state"] = state
            ANALYSIS_NIGHTLY_JOBS[job_id]["message"] = msg
            ANALYSIS_NIGHTLY_JOBS[job_id]["updated_at"] = _utc_now_iso_ms()
            if current is not None:
                ANALYSIS_NIGHTLY_JOBS[job_id]["current"] = current
            if state in ("done", "error", "cancelled"):
                _job_set_finished(ANALYSIS_NIGHTLY_JOBS[job_id])
                timer_id = ANALYSIS_NIGHTLY_JOBS[job_id].get("timer_id")
                try:
                    started_mono = float(ANALYSIS_NIGHTLY_JOBS[job_id].get("started_mono") or 0.0)
                except Exception:
                    started_mono = 0.0
                dur_ms = int(max(0.0, (time.monotonic() - started_mono) * 1000.0)) if started_mono > 0 else None
                err = str(ANALYSIS_NIGHTLY_JOBS[job_id].get("error") or "").strip() or None
                if state == "error" and not err:
                    err = str(msg or "").strip() or None
                extra = {"duration_ms": dur_ms, "error": err}
        if timer_id and state in ("done", "error", "cancelled"):
            _timer_mark_finished(str(timer_id), state, extra=extra)

    try:
        with ANALYSIS_NIGHTLY_LOCK:
            job = ANALYSIS_NIGHTLY_JOBS.get(job_id) or {}
            if bool(job.get("cancelled")):
                set_state("cancelled", "Abgebrochen")
                return
            series_row = job.get("series") if isinstance(job.get("series"), dict) else {}
            series_key = str(job.get("series_key") or "").strip()

        cfg = _overlay_from_yaml_if_enabled(load_cfg())
        set_state("running", "Nightly Analyse-Refresh laeuft...", current=series_key)
        t0 = time.monotonic()
        res = _analysis_nightly_refresh_series(cfg, series_row)
        dur_ms = int(max(0.0, (time.monotonic() - t0) * 1000.0))
        _analysis_nightly_set_series_last_run(str(res.get("series_key") or series_key), _utc_now_iso_ms())

        try:
            _worklog_append_op(
                purpose="analysis",
                op="nightly_refresh",
                status="ok",
                detail=f"Nightly Analyse-Refresh: stored={int(res.get('segments_stored') or 0)} combined={int(res.get('groups_combined') or 0)}",
                measurement=str(series_row.get("measurement") or ""),
                field=str(series_row.get("field") or ""),
                entity_id=str(series_row.get("entity_id") or ""),
                friendly_name=str(series_row.get("friendly_name") or ""),
                window_start=str(res.get("start") or ""),
                window_stop=str(res.get("stop") or ""),
                duration_ms=dur_ms,
                source="scheduler",
                reason_code="analysis_nightly",
                counts={
                    "segments_stored": int(res.get("segments_stored") or 0),
                    "scanned": int(res.get("scanned") or 0),
                    "outliers": int(res.get("outliers") or 0),
                },
                cache={"series_key": str(res.get("series_key") or series_key)},
            )
        except Exception:
            pass

        try:
            _timer_event_append("analysis_nightly", "run", {
                "state": "done",
                "series_key": str(res.get("series_key") or series_key),
                "duration_ms": dur_ms,
                "segments_stored": int(res.get("segments_stored") or 0),
                "scanned": int(res.get("scanned") or 0),
                "outliers": int(res.get("outliers") or 0),
                "job_id": job_id,
            })
        except Exception:
            pass

        set_state("done", f"OK: stored={int(res.get('segments_stored') or 0)} scanned={int(res.get('scanned') or 0)} outliers={int(res.get('outliers') or 0)}")
    except Exception as e:
        err = str(e) or e.__class__.__name__
        with ANALYSIS_NIGHTLY_LOCK:
            if job_id in ANALYSIS_NIGHTLY_JOBS:
                ANALYSIS_NIGHTLY_JOBS[job_id]["error"] = err
        try:
            _timer_event_append("analysis_nightly", "run", {"state": "error", "error": err, "job_id": job_id})
        except Exception:
            pass
        try:
            _worklog_append_op(
                purpose="analysis",
                op="nightly_refresh",
                status="err",
                detail=f"Nightly Analyse-Refresh Fehler: {err}",
                source="scheduler",
                reason_code="analysis_nightly",
            )
        except Exception:
            pass
        set_state("error", err)


def _analysis_nightly_start_job(series_row: dict[str, Any], trigger_page: str, timer_id: str | None = None) -> str:
    sk = str(series_row.get("series_key") or "").strip()
    if not sk:
        raise _ApiError("series_key missing", 400)
    if _analysis_nightly_inflight(sk):
        raise _ApiError("series already inflight", 409)
    job_id = uuid.uuid4().hex
    now = _utc_now_iso_ms()
    job = {
        "id": job_id,
        "type": "analysis_nightly",
        "timer_id": str(timer_id or "analysis_nightly").strip() or "analysis_nightly",
        "trigger_page": str(trigger_page or "").strip(),
        "trigger_ip": _req_ip(),
        "trigger_ua": _req_ua(),
        "series_key": sk,
        "measurement": series_row.get("measurement"),
        "field": series_row.get("field"),
        "entity_id": series_row.get("entity_id"),
        "friendly_name": series_row.get("friendly_name"),
        "series": dict(series_row),
        "state": "pending",
        "message": "Job wird gestartet...",
        "current": sk,
        "started_at": now,
        "updated_at": now,
        "started_mono": time.monotonic(),
        "cancelled": False,
        "error": None,
    }
    with ANALYSIS_NIGHTLY_LOCK:
        ANALYSIS_NIGHTLY_JOBS[job_id] = job
        # best-effort cleanup
        cutoff = time.monotonic() - float(6 * 3600)
        old = [k for k, v in ANALYSIS_NIGHTLY_JOBS.items() if float(v.get("started_mono") or 0) < cutoff]
        for k in old:
            ANALYSIS_NIGHTLY_JOBS.pop(k, None)
    th = threading.Thread(target=_analysis_nightly_job_thread, args=(job_id,), daemon=True)
    th.start()
    try:
        _timer_mark_started(str(timer_id or "analysis_nightly"), job_id=job_id)
    except Exception:
        pass
    return job_id


@app.get("/api/timers")
def api_timers():
    cfg = load_cfg()
    st_dash = _timers_state_get("dash_cache")
    st_stats = _timers_state_get("stats_cache")
    st_full = _timers_state_get("stats_full")
    st_an = _timers_state_get("analysis_nightly")
    timers = [
        {
            "id": "dash_cache",
            "enabled": bool(cfg.get("dash_cache_enabled", True)),
            "auto_update": bool(cfg.get("dash_cache_auto_update", True)),
            "refresh_mode": str(cfg.get("dash_cache_refresh_mode") or "hours").strip().lower(),
            "refresh_hours": int(cfg.get("dash_cache_refresh_hours") or 6),
            "refresh_daily_at": str(cfg.get("dash_cache_refresh_daily_at") or "00:00:00"),
            "refresh_weekday": int(cfg.get("dash_cache_refresh_weekday") or 0),
            "mode": _cache_mode_str(cfg, "dash_cache"),
            "next_run_at": _cache_schedule_next_run_iso(cfg, "dash_cache"),
            "last_started_at": st_dash.get("last_started_at"),
            "last_run_at": st_dash.get("last_run_at"),
            "last_state": st_dash.get("last_state"),
            "last_duration_ms": st_dash.get("last_duration_ms"),
            "last_error": st_dash.get("last_error"),
            "comment": "Aktualisiert faellige Dashboard Cache Eintraege im Hintergrund (dirty/mismatch/stale).",
        },
        {
            "id": "stats_cache",
            "enabled": bool(cfg.get("stats_cache_enabled", True)),
            "auto_update": bool(cfg.get("stats_cache_auto_update", True)),
            "refresh_mode": str(cfg.get("stats_cache_refresh_mode") or "daily").strip().lower(),
            "refresh_hours": int(cfg.get("stats_cache_refresh_hours") or 24),
            "refresh_daily_at": str(cfg.get("stats_cache_refresh_daily_at") or "03:00:00"),
            "refresh_weekday": int(cfg.get("stats_cache_refresh_weekday") or 0),
            "mode": _cache_mode_str(cfg, "stats_cache"),
            "next_run_at": _cache_schedule_next_run_iso(cfg, "stats_cache"),
            "last_started_at": st_stats.get("last_started_at"),
            "last_run_at": st_stats.get("last_run_at"),
            "last_state": st_stats.get("last_state"),
            "last_duration_ms": st_stats.get("last_duration_ms"),
            "last_error": st_stats.get("last_error"),
            "comment": "Aktualisiert faellige Statistik Cache Eintraege im Hintergrund (dirty/mismatch/stale).",
        },
        {
            "id": "stats_full",
            "enabled": True,
            "refresh_mode": str(cfg.get("stats_full_refresh_mode") or "manual").strip().lower(),
            "refresh_hours": int(cfg.get("stats_full_refresh_hours") or 24),
            "refresh_daily_at": str(cfg.get("stats_full_refresh_daily_at") or "03:00:00"),
            "refresh_weekday": int(cfg.get("stats_full_refresh_weekday") or 0),
            "auto_update": str(cfg.get("stats_full_refresh_mode") or "manual").strip().lower() != "manual",
            "mode": _cache_mode_str(cfg, "stats_full"),
            "next_run_at": _cache_schedule_next_run_iso(cfg, "stats_full"),
            "last_started_at": st_full.get("last_started_at"),
            "last_run_at": st_full.get("last_run_at"),
            "last_state": st_full.get("last_state"),
            "last_duration_ms": st_full.get("last_duration_ms"),
            "last_error": st_full.get("last_error"),
            "comment": "Manueller Job: laedt Statistik komplett (inkl. Details wie count/min/max/mean) fuer alle Serien.",
        },
        {
            "id": "analysis_nightly",
            "enabled": bool(cfg.get("analysis_nightly_enabled", True)),
            "auto_update": bool(cfg.get("analysis_nightly_auto_update", True)),
            "refresh_mode": str(cfg.get("analysis_nightly_refresh_mode") or "daily").strip().lower(),
            "refresh_hours": int(cfg.get("analysis_nightly_refresh_hours") or 24),
            "refresh_daily_at": str(cfg.get("analysis_nightly_refresh_daily_at") or "03:30:00"),
            "refresh_weekday": int(cfg.get("analysis_nightly_refresh_weekday") or 0),
            "mode": _cache_mode_str(cfg, "analysis_nightly"),
            "next_run_at": _cache_schedule_next_run_iso(cfg, "analysis_nightly"),
            "last_started_at": st_an.get("last_started_at"),
            "last_run_at": st_an.get("last_run_at"),
            "last_state": st_an.get("last_state"),
            "last_duration_ms": st_an.get("last_duration_ms"),
            "last_error": st_an.get("last_error"),
            "comment": "Nightly-Job: aktualisiert Analysecache fuer alle bereits analysierten Serien (1x pro Nacht).",
        },
    ]
    return jsonify({"ok": True, "timers": timers})


@app.get("/api/timers/history")
def api_timers_history():
    tid = str(request.args.get("id") or "").strip()
    if tid not in ("dash_cache", "stats_cache", "stats_full", "analysis_nightly"):
        return jsonify({"ok": False, "error": "invalid timer id"}), 400

    try:
        limit = int(request.args.get("limit") or 50)
    except Exception:
        limit = 50
    limit = min(200, max(1, limit))

    st = _timers_state_get(tid)
    xs = st.get("events") if isinstance(st, dict) else None
    xs = xs if isinstance(xs, list) else []
    xs2 = [it for it in xs if isinstance(it, dict)]
    xs2 = xs2[-limit:]
    return jsonify({"ok": True, "id": tid, "events": xs2, "state": st})


@app.post("/api/timers/schedule")
def api_timers_schedule():
    body = request.get_json(force=True) or {}
    tid = str(body.get("id") or "").strip()
    if tid not in ("dash_cache", "stats_cache", "stats_full", "analysis_nightly"):
        return jsonify({"ok": False, "error": "invalid timer id"}), 400

    mode = str(body.get("refresh_mode") or "").strip().lower()
    if mode not in ("hours", "daily", "weekly", "manual"):
        return jsonify({"ok": False, "error": "refresh_mode must be hours|daily|weekly|manual"}), 400

    cfg = load_cfg()
    cfg[f"{tid}_refresh_mode"] = mode

    if mode == "manual":
        try:
            save_cfg(cfg)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500
        try:
            _timer_event_append(tid, "schedule", {"mode": mode})
        except Exception:
            pass
        return api_timers()

    if mode == "hours":
        try:
            h = int(body.get("refresh_hours") or cfg.get(f"{tid}_refresh_hours") or (6 if tid == "dash_cache" else 24))
        except Exception:
            h = 6 if tid == "dash_cache" else 24
        if h < 1:
            h = 1
        if h > 8760:
            h = 8760
        cfg[f"{tid}_refresh_hours"] = h

    else:
        # daily/weekly time
        s = str(body.get("refresh_daily_at") or cfg.get(f"{tid}_refresh_daily_at") or ("00:00:00" if tid == "dash_cache" else ("03:30:00" if tid == "analysis_nightly" else "03:00:00"))).strip()
        if not re.match(r"^\d{2}:\d{2}:\d{2}$", s):
            return jsonify({"ok": False, "error": "refresh_daily_at must be HH:MM:SS"}), 400
        try:
            hh, mm, ss = [int(x) for x in s.split(":")]
        except Exception:
            return jsonify({"ok": False, "error": "invalid refresh_daily_at"}), 400
        if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59):
            return jsonify({"ok": False, "error": "refresh_daily_at out of range"}), 400
        cfg[f"{tid}_refresh_daily_at"] = s

        if mode == "weekly":
            wd = body.get("refresh_weekday")
            w = _timer_parse_weekday(wd, default=int(cfg.get(f"{tid}_refresh_weekday") or 0))
            cfg[f"{tid}_refresh_weekday"] = int(w)

    try:
        save_cfg(cfg)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500

    try:
        _timer_event_append(tid, "schedule", {
            "mode": mode,
            "refresh_hours": cfg.get(f"{tid}_refresh_hours"),
            "refresh_daily_at": cfg.get(f"{tid}_refresh_daily_at"),
            "refresh_weekday": cfg.get(f"{tid}_refresh_weekday"),
        })
    except Exception:
        pass
    return api_timers()


@app.post("/api/timers/auto_update")
def api_timers_auto_update():
    """Enable/disable automatic scheduled runs for one or more timers."""

    body = request.get_json(force=True) or {}
    ids_raw = body.get("ids")
    if isinstance(ids_raw, str):
        ids = [ids_raw]
    elif isinstance(ids_raw, list):
        ids = [str(x) for x in ids_raw]
    else:
        ids = []

    enabled_raw = body.get("enabled", True)
    enabled = enabled_raw is True or str(enabled_raw).strip().lower() in ("1", "true", "yes", "on")

    valid = {"dash_cache", "stats_cache", "stats_full", "analysis_nightly"}
    ids2 = [str(x or "").strip() for x in ids]
    ids2 = [x for x in ids2 if x in valid]
    if not ids2:
        return jsonify({"ok": False, "error": "ids required"}), 400

    cfg = load_cfg()
    for tid in ids2:
        if tid in ("dash_cache", "stats_cache", "analysis_nightly"):
            cfg[f"{tid}_auto_update"] = bool(enabled)
        elif tid == "stats_full":
            cur_mode = str(cfg.get("stats_full_refresh_mode") or "manual").strip().lower() or "manual"
            if not enabled:
                # store previous mode (best-effort) so enable can restore it
                if cur_mode != "manual":
                    try:
                        st = _timers_state_load()
                        cur = st.get("stats_full")
                        cur = cur if isinstance(cur, dict) else {}
                        cur["prev_refresh_mode"] = cur_mode
                        st["stats_full"] = cur
                        _timers_state_save(st)
                    except Exception:
                        pass
                cfg["stats_full_refresh_mode"] = "manual"
            else:
                # restore previous non-manual mode if available
                prev = None
                try:
                    st = _timers_state_load()
                    cur = st.get("stats_full")
                    cur = cur if isinstance(cur, dict) else {}
                    prev = str(cur.get("prev_refresh_mode") or "").strip().lower() or None
                    if prev in ("hours", "daily", "weekly"):
                        cfg["stats_full_refresh_mode"] = prev
                    elif cur_mode == "manual":
                        cfg["stats_full_refresh_mode"] = "daily"
                    # clear after successful restore attempt
                    if "prev_refresh_mode" in cur:
                        cur.pop("prev_refresh_mode", None)
                        st["stats_full"] = cur
                        _timers_state_save(st)
                except Exception:
                    if cur_mode == "manual":
                        cfg["stats_full_refresh_mode"] = "daily"

        try:
            _timer_event_append(tid, "auto_update", {"enabled": bool(enabled), "ip": _req_ip()})
        except Exception:
            pass

    try:
        save_cfg(cfg)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500

    return api_timers()


@app.post("/api/timers/start")
def api_timers_start():
    body = request.get_json(force=True) or {}
    tid = str(body.get("id") or "").strip()
    if tid not in ("dash_cache", "stats_cache", "stats_full", "analysis_nightly"):
        return jsonify({"ok": False, "error": "invalid timer id"}), 400

    cfg = _overlay_from_yaml_if_enabled(load_cfg())

    if tid == "dash_cache":
        if not bool(cfg.get("dash_cache_enabled", True)):
            return jsonify({"ok": False, "error": "dash cache disabled"}), 400

        pick = None
        pick_prio = 999
        for m in _dash_cache_list_meta():
            try:
                cid = str(m.get("id") or "").strip()
                if not cid:
                    continue
                if bool(m.get("dirty")):
                    prio = 0
                elif bool(m.get("mismatch")):
                    prio = 1
                elif _dash_cache_is_stale(cfg, m):
                    prio = 5
                else:
                    continue
                if prio < pick_prio:
                    pick = cid
                    pick_prio = prio
            except Exception:
                continue

        if not pick:
            return jsonify({"ok": True, "started": False})
        try:
            job_id = _dash_cache_start_job("update", pick, trigger_page="timers", timer_id=tid)
            try:
                _timer_event_append(tid, "manual_start", {"job_id": job_id, "cache_id": pick})
            except Exception:
                pass
            _timer_mark_started(tid, job_id=job_id)
            return jsonify({"ok": True, "started": True, "job_id": job_id, "cache_id": pick})
        except Exception as e:
            return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

    if tid == "stats_cache":
        try:
            pick = None
            pick_prio = 999
            for m in _stats_cache_list_meta():
                try:
                    cid = str(m.get("id") or "").strip()
                    if not cid:
                        continue
                    if bool(m.get("dirty")):
                        prio = 0
                    elif bool(m.get("mismatch")):
                        prio = 1
                    elif _stats_cache_is_stale(cfg, m):
                        prio = 5
                    else:
                        continue
                    if prio < pick_prio:
                        pick = cid
                        pick_prio = prio
                except Exception:
                    continue

            if not pick:
                return jsonify({"ok": True, "started": False})

            job_id = _stats_cache_start_update_job(pick, trigger_page="timers", timer_id=tid)
            try:
                _timer_event_append(tid, "manual_start", {"job_id": job_id, "cache_id": pick})
            except Exception:
                pass
            _timer_mark_started(tid, job_id=job_id)
            return jsonify({"ok": True, "started": True, "job_id": job_id, "cache_id": pick})
        except _ApiError as e:
            return jsonify({"ok": False, "error": e.message}), e.status
        except Exception as e:
            return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

    if tid == "analysis_nightly":
        try:
            rows = _analysis_cache_group_list(cfg)
            if not rows:
                return jsonify({"ok": True, "started": False})
            # Prefer a due series (ignore enabled/auto_update for manual start)
            cfg2 = dict(cfg)
            cfg2["analysis_nightly_enabled"] = True
            cfg2["analysis_nightly_auto_update"] = True
            pick = _analysis_nightly_pick_series(cfg2) or rows[0]
            job_id = _analysis_nightly_start_job(pick, trigger_page="timers", timer_id=tid)
            try:
                _timer_event_append(tid, "manual_start", {"job_id": job_id, "series_key": str(pick.get("series_key") or "")})
            except Exception:
                pass
            return jsonify({"ok": True, "started": True, "job_id": job_id, "series_key": str(pick.get("series_key") or "")})
        except _ApiError as e:
            return jsonify({"ok": False, "error": e.message}), e.status
        except Exception as e:
            return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

    # stats_full
    try:
        stop_dt = datetime.now(timezone.utc)
        try:
            max_days = int(cfg.get("stats_full_max_days") or 3650)
        except Exception:
            max_days = 3650
        max_days = min(36500, max(1, max_days))
        start_dt = stop_dt - timedelta(days=max_days)
        cols = ["last_value", "oldest_time", "newest_time", "count", "min", "max", "mean"]
        job_id = _global_stats_start_job(
            cfg=cfg,
            start_dt=start_dt,
            stop_dt=stop_dt,
            field_filter=None,
            measurement_filter=None,
            entity_id_filter=None,
            friendly_name_filter=None,
            series_list=None,
            columns=cols,
            page_limit=200,
            trigger_page="timers",
            timer_id=tid,
            cache_id=None,
            cache_key=None,
        )
        try:
            _timer_event_append(tid, "manual_start", {"job_id": job_id, "max_days": max_days})
        except Exception:
            pass
        _timer_mark_started(tid, job_id=job_id)
        return jsonify({"ok": True, "started": True, "job_id": job_id})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/timers/cancel")
def api_timers_cancel():
    body = request.get_json(force=True) or {}
    tid = str(body.get("id") or "").strip()
    if tid not in ("dash_cache", "stats_cache", "stats_full", "analysis_nightly"):
        return jsonify({"ok": False, "error": "invalid timer id"}), 400

    cancelled = 0
    try:
        _timer_event_append(tid, "cancel_request", {"ip": _req_ip(), "ua": _req_ua()})
    except Exception:
        pass
    if tid == "dash_cache":
        with DASH_CACHE_JOBS_LOCK:
            for jid, j in list(DASH_CACHE_JOBS.items()):
                try:
                    st = str(j.get("state") or "")
                    if st and st not in ("done", "error", "cancelled"):
                        DASH_CACHE_JOBS[jid]["cancelled"] = True
                        cancelled += 1
                except Exception:
                    continue
        return jsonify({"ok": True, "cancelled": cancelled})

    if tid == "analysis_nightly":
        # best-effort cancel: mark inflight analysis_nightly jobs cancelled
        with ANALYSIS_NIGHTLY_LOCK:
            for jid, j in list(ANALYSIS_NIGHTLY_JOBS.items()):
                try:
                    st = str(j.get("state") or "")
                    if st and st not in ("done", "error", "cancelled"):
                        ANALYSIS_NIGHTLY_JOBS[jid]["cancelled"] = True
                        cancelled += 1
                except Exception:
                    continue
        return jsonify({"ok": True, "cancelled": cancelled})

    # stats_cache and stats_full both run as global_stats jobs
    with GLOBAL_STATS_LOCK:
        for jid, j in list(GLOBAL_STATS_JOBS.items()):
            try:
                st = str(j.get("state") or "")
                if not st or st in ("done", "error", "cancelled"):
                    continue
                if tid == "stats_cache" and not str(j.get("cache_id") or "").strip():
                    continue
                if tid == "stats_full" and str(j.get("timer_id") or "").strip() != "stats_full":
                    continue
                GLOBAL_STATS_JOBS[jid]["cancelled"] = True
                cancelled += 1
            except Exception:
                continue
    return jsonify({"ok": True, "cancelled": cancelled})


@app.get("/api/stats_cache/schedule")
def api_stats_cache_schedule():
    cfg = load_cfg()
    enabled = bool(cfg.get("stats_cache_enabled", True))
    auto = bool(cfg.get("stats_cache_auto_update", True))
    items = _stats_cache_list_meta() if enabled else []
    due = 0
    try:
        for m in items:
            if bool(m.get("dirty")) or bool(m.get("mismatch")) or _stats_cache_is_stale(cfg, m):
                due += 1
    except Exception:
        due = 0
    return jsonify({
        "ok": True,
        "enabled": enabled,
        "auto_update": auto,
        "caches": len(items),
        "due": due,
        "next_run_at": _stats_cache_next_run_iso(cfg),
        "settings": {
            "refresh_mode": cfg.get("stats_cache_refresh_mode"),
            "refresh_hours": cfg.get("stats_cache_refresh_hours"),
            "refresh_daily_at": cfg.get("stats_cache_refresh_daily_at"),
        },
    })


@app.post("/api/stats_cache/run_now")
def api_stats_cache_run_now():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if not bool(cfg.get("stats_cache_enabled", True)):
        return jsonify({"ok": False, "error": "cache disabled"}), 400

    pick = None
    pick_prio = 999
    for m in _stats_cache_list_meta():
        try:
            cid = str(m.get("id") or "").strip()
            if not cid:
                continue
            if bool(m.get("dirty")):
                prio = 0
            elif bool(m.get("mismatch")):
                prio = 1
            elif _stats_cache_is_stale(cfg, m):
                prio = 5
            else:
                continue
            if prio < pick_prio:
                pick = cid
                pick_prio = prio
        except Exception:
            continue

    if not pick:
        return jsonify({"ok": True, "started": False})

    try:
        job_id = _stats_cache_start_update_job(pick, trigger_page="jobs")
        return jsonify({"ok": True, "started": True, "job_id": job_id, "cache_id": pick})
    except _ApiError as e:
        return jsonify({"ok": False, "error": e.message}), e.status
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

@app.post("/api/config")
def api_set_config():
    body = request.get_json(force=True) or {}
    old_cfg = load_cfg()
    cfg = dict(old_cfg)
    allowed = set(DEFAULT_CFG.keys())
    changed_keys = []
    for k, v in body.items():
        if k not in allowed:
            continue
        if k in ("token", "admin_token", "password") and v == "********":
            continue
        old_val = old_cfg.get(k)
        if old_val != v:
            changed_keys.append(k)
        cfg[k] = v

    LOG.info("api.config_save called from=%s changed=%s", request.remote_addr, changed_keys)

    try:
        cfg["influx_version"] = int(cfg.get("influx_version", 2))
    except Exception:
        cfg["influx_version"] = 2
    try:
        cfg["port"] = int(cfg.get("port", 8086))
    except Exception:
        cfg["port"] = 8086
    cfg["verify_ssl"] = bool(cfg.get("verify_ssl", True))
    try:
        cfg["timeout_seconds"] = int(cfg.get("timeout_seconds", 10))
    except Exception:
        cfg["timeout_seconds"] = 10

    try:
        cfg["ui_table_visible_rows"] = int(cfg.get("ui_table_visible_rows", 20))
    except Exception:
        cfg["ui_table_visible_rows"] = 20
    if cfg["ui_table_visible_rows"] <= 0:
        cfg["ui_table_visible_rows"] = 20

    try:
        cfg["ui_decimals"] = int(cfg.get("ui_decimals", 3))
    except Exception:
        cfg["ui_decimals"] = 3
    if cfg["ui_decimals"] < 0:
        cfg["ui_decimals"] = 0
    if cfg["ui_decimals"] > 10:
        cfg["ui_decimals"] = 10

    def _clamp_int(key: str, default: int, lo: int, hi: int) -> None:
        try:
            cfg[key] = int(cfg.get(key, default))
        except Exception:
            cfg[key] = default
        if cfg[key] < lo:
            cfg[key] = lo
        if cfg[key] > hi:
            cfg[key] = hi

    def _clamp_float(key: str, default: float, lo: float, hi: float) -> None:
        try:
            cfg[key] = float(cfg.get(key, default))
        except Exception:
            cfg[key] = default
        if cfg[key] < lo:
            cfg[key] = lo
        if cfg[key] > hi:
            cfg[key] = hi

    _clamp_int("ui_font_size_px", 14, 10, 22)
    _clamp_int("ui_font_small_px", 11, 9, 18)
    _clamp_int("ui_popup_pre_font_px", 10, 8, 24)
    _clamp_int("ui_popup_history_font_px", 10, 8, 24)
    _clamp_int("ui_pagecard_title_px", 30, 18, 48)
    _clamp_int("ui_page_search_highlight_width_px", 5, 1, 12)
    _clamp_int("ui_page_search_highlight_duration_ms", 8000, 200, 10000)
    _clamp_int("ui_status_font_px", 12, 9, 18)
    _clamp_int("ui_status_bar_height_px", 38, 28, 90)
    _clamp_int("ui_table_row_height_px", 13, 9, 60)
    _clamp_int("ui_backup_table_row_height_px", 13, 9, 60)
    _clamp_int("ui_backup_visible_rows", 24, 5, 200)
    _clamp_int("ui_restore_visible_rows", 24, 5, 200)
    _clamp_int("ui_outlier_visible_rows", 10, 5, 200)
    _clamp_int("ui_raw_outlier_display_limit_per_type", 100, 1, 1000)
    _clamp_int("ui_query_manual_max_points", 200000, 1000, 2000000)
    _clamp_int("ui_graph_jump_padding_intervals", 1, 0, 50)
    _clamp_int("ui_edit_neighbors_n", 5, 1, 50)
    _clamp_int("ui_edit_details_visible_rows", 12, 4, 80)
    _clamp_int("ui_edit_graph_buffer_minutes", 30, 0, 24 * 60)
    _clamp_int("ui_edit_graph_max_points", 50000, 1000, 200000)
    _clamp_int("ui_graph_ctx_before_minutes", 60, 0, 24 * 60)
    _clamp_int("ui_graph_ctx_after_minutes", 60, 0, 24 * 60)
    _clamp_int("ui_query_max_points", 5000, 500, 200000)
    _clamp_int("ui_raw_max_points", 20000, 1000, 200000)
    _clamp_int("ui_raw_center_max_points", 2000, 1, 200000)
    _clamp_int("ui_raw_center_range_default", 100, 0, 200000)
    _clamp_int("ui_raw_center_min_points", 10, 1, 100000)
    _clamp_int("ui_raw_outlier_context_rows", 10, 1, 500)
    _clamp_int("ui_raw_target_chunk_ms", 5000, 1000, max(1000, int(cfg.get("timeout_seconds", 60) or 60) * 1000))
    _clamp_int("ui_analysis_max_age_years", 5, 1, 50)
    _clamp_float("ui_checkbox_scale", 0.85, 0.5, 1.6)
    _clamp_int("ui_filter_label_width_px", 170, 80, 360)
    _clamp_int("ui_filter_control_width_px", 320, 180, 900)
    _clamp_int("ui_filter_search_width_px", 160, 80, 420)

    # Selection fields (master template)
    _clamp_int("ui_sel_field_font_px", 13, 9, 22)
    _clamp_int("ui_sel_label_font_px", 12, 9, 22)
    _clamp_int("ui_sel_desc_font_px", 11, 9, 22)
    _clamp_int("ui_sel_width_px", 260, 120, 900)

    _clamp_int("jobs_max_runtime_seconds", 0, 0, 7 * 24 * 60 * 60)

    def _clamp_color(key: str, default: str) -> None:
        try:
            s = str(cfg.get(key, default) or "").strip()
        except Exception:
            s = default
        if not re.match(r"^#[0-9a-fA-F]{6}$", s):
            s = default
        cfg[key] = s

    def _clamp_color_opt(key: str, allow_words: tuple[str, ...] = ()) -> None:
        """Clamp a color-ish string to a safe subset.

        Allowed values:
        - "" (meaning: use default)
        - any word from allow_words (e.g. "transparent", "inherit")
        - "#RRGGBB"
        """
        try:
            s = str(cfg.get(key, "") or "").strip()
        except Exception:
            s = ""
        if not s:
            cfg[key] = ""
            return
        if s in allow_words:
            cfg[key] = s
            return
        if re.match(r"^#[0-9a-fA-F]{6}$", s):
            cfg[key] = s
            return
        cfg[key] = ""

    _clamp_color("ui_job_color_running", "#eef3ff")
    _clamp_color("ui_job_color_done", "#eefaf1")
    _clamp_color("ui_job_color_error", "#fff0f0")
    _clamp_color("ui_job_color_cancelled", "#f6f6f6")
    _clamp_color("ui_picker_outline_light_bg", "#FF00AA")
    _clamp_color("ui_picker_outline_dark_bg", "#00E5FF")
    _clamp_color("ui_analysis_cache_hidden_color", "#b0b0b0")
    _clamp_color("ui_analysis_cache_missing_color", "#b00020")

    _clamp_color_opt("ui_section_title_bg", allow_words=("transparent",))
    _clamp_color_opt("ui_section_title_fg", allow_words=("inherit",))
    _clamp_color("ui_section_level2_bg", "#8BA293")
    _clamp_color("ui_section_level2_fg", "#FFFFFF")
    _clamp_color("ui_section_level3_bg", "#B8B17F")
    _clamp_color("ui_section_level3_fg", "#FFFFFF")
    _clamp_color("ui_page_search_highlight_color", "#FF9900")
    _clamp_color("ui_status_bar_bg", "#FFFFFF")
    _clamp_color("ui_status_bar_fg", "#111111")
    _clamp_int("ui_section_title_font_px", 13, 10, 22)
    _clamp_int("ui_section_level2_font_px", 12, 10, 22)
    _clamp_int("ui_section_level3_font_px", 11, 9, 20)

    _clamp_int("perf_corr_causal_gap_ms", 8, 0, 200)
    _clamp_int("perf_corr_timer_gap_ms", 1000, 0, 200000)
    _clamp_int("perf_corr_dep_zoom_pct", 0, 0, 300)

    try:
        cfg["import_measurement_transforms"] = str(cfg.get("import_measurement_transforms") or "").strip()
    except Exception:
        cfg["import_measurement_transforms"] = ""

    # Backups directory (must stay under /data)
    try:
        cfg["backup_dir"] = str(cfg.get("backup_dir") or "").strip()
    except Exception:
        cfg["backup_dir"] = str(DEFAULT_CFG.get("backup_dir") or "/data/backups")
    cfg["backup_dir"] = str(backup_dir(cfg))

    _clamp_int("backup_min_free_mb", 0, 0, 500000)
    _clamp_int("storage_budget_mb", 5, 0, 500000)

    # Validation: if backup free-space guard is enabled, it must be higher than the cache budget.
    try:
        bmin = int(cfg.get("backup_min_free_mb", 0) or 0)
    except Exception:
        bmin = 0
    try:
        budget = int(cfg.get("storage_budget_mb", 0) or 0)
    except Exception:
        budget = 0
    if bmin > 0 and budget > 0 and bmin <= budget:
        return jsonify({
            "ok": False,
            "error": "backup_min_free_mb muss groesser sein als min freier Cachespeicher (storage_budget_mb).",
        }), 400

    def _bool(key: str, default: bool = False) -> None:
        v = cfg.get(key, default)
        if isinstance(v, bool):
            cfg[key] = v
            return
        s = str(v).strip().lower()
        cfg[key] = s in ("1", "true", "yes", "on")

    _bool("ui_status_show_sysinfo", False)

    _bool("ui_picker_outline_auto", True)

    _bool("ui_tooltips_enabled", True)

    _bool("ui_sel_auto_width", True)

    # Note: writes_enabled removed; keep any existing key untouched.

    # Dashboard cache
    _bool("dash_cache_enabled", True)
    _bool("dash_cache_auto_update", True)
    _bool("dash_cache_update_on_use_if_stale", True)
    _clamp_int("dash_cache_refresh_hours", 6, 1, 8760)
    _clamp_int("dash_cache_max_items", 40, 0, 500)
    _clamp_int("dash_cache_max_mb", 50, 0, 2048)
    try:
        mode = str(cfg.get("dash_cache_refresh_mode") or "hours").strip().lower()
    except Exception:
        mode = "hours"
    if mode not in ("hours", "daily", "weekly", "manual"):
        mode = "hours"
    cfg["dash_cache_refresh_mode"] = mode
    try:
        s = str(cfg.get("dash_cache_refresh_daily_at") or "00:00:00").strip() or "00:00:00"
    except Exception:
        s = "00:00:00"
    if not re.match(r"^\d{2}:\d{2}:\d{2}$", s):
        s = "00:00:00"
    cfg["dash_cache_refresh_daily_at"] = s
    _clamp_int("dash_cache_refresh_weekday", 0, 0, 6)

    # Statistik cache
    _bool("stats_cache_enabled", True)
    _bool("stats_cache_auto_update", True)
    _clamp_int("stats_cache_refresh_hours", 24, 1, 8760)
    _clamp_int("stats_cache_max_items", 10, 0, 500)
    _clamp_int("stats_cache_max_mb", 50, 0, 2048)
    try:
        mode2 = str(cfg.get("stats_cache_refresh_mode") or "daily").strip().lower()
    except Exception:
        mode2 = "daily"
    if mode2 not in ("hours", "daily", "weekly", "manual"):
        mode2 = "daily"
    cfg["stats_cache_refresh_mode"] = mode2
    try:
        s2 = str(cfg.get("stats_cache_refresh_daily_at") or "03:00:00").strip() or "03:00:00"
    except Exception:
        s2 = "03:00:00"
    if not re.match(r"^\d{2}:\d{2}:\d{2}$", s2):
        s2 = "03:00:00"
    cfg["stats_cache_refresh_daily_at"] = s2
    _clamp_int("stats_cache_refresh_weekday", 0, 0, 6)

    # Timer job: stats_full
    _clamp_int("stats_full_refresh_hours", 24, 1, 8760)
    _clamp_int("stats_full_max_days", 3650, 1, 36500)
    try:
        mode3 = str(cfg.get("stats_full_refresh_mode") or "manual").strip().lower()
    except Exception:
        mode3 = "manual"
    if mode3 not in ("hours", "daily", "weekly", "manual"):
        mode3 = "manual"
    cfg["stats_full_refresh_mode"] = mode3
    try:
        s3 = str(cfg.get("stats_full_refresh_daily_at") or "03:00:00").strip() or "03:00:00"
    except Exception:
        s3 = "03:00:00"
    if not re.match(r"^\d{2}:\d{2}:\d{2}$", s3):
        s3 = "03:00:00"
    cfg["stats_full_refresh_daily_at"] = s3
    _clamp_int("stats_full_refresh_weekday", 0, 0, 6)

    # Logging
    _bool("log_to_file", True)
    _bool("log_http_requests", False)
    _bool("log_influx_queries", False)
    _bool("log_cache_usage", False)
    try:
        prof = str(cfg.get("log_profile") or "debug").strip().lower()
    except Exception:
        prof = "debug"
    if prof not in ("error", "debug", "trace"):
        prof = "debug"
    cfg["log_profile"] = prof

    # Backward compat: keep log_level in sync (used only if log_profile missing).
    if prof == "error":
        cfg["log_level"] = "ERROR"
    else:
        cfg["log_level"] = "DEBUG"

    _clamp_int("log_max_mb", 5, 1, 200)
    _clamp_int("log_backup_count", 5, 1, 50)
    _clamp_int("log_max_age_days", 14, 0, 365)
    _clamp_int("bugreport_log_history_hours", 1, 1, 168)

    # Tracing
    _bool("trace_enabled", True)
    _bool("trace_persist", True)
    _clamp_int("trace_max_entries", 1000, 100, 20000)
    _clamp_int("trace_max_days", 14, 1, 3650)

    # Worklog (Analyse/Statistik/Raw)
    _clamp_int("worklog_max_entries", 2000, 200, 50000)
    _clamp_int("worklog_max_days", 14, 1, 3650)

    def _clamp_num(key: str, default: float, lo: float, hi: float) -> None:
        try:
            cfg[key] = float(cfg.get(key, default))
        except Exception:
            cfg[key] = default
        if cfg[key] < lo:
            cfg[key] = lo
        if cfg[key] > hi:
            cfg[key] = hi

    _clamp_num("outlier_max_step_w", 30000, 1000, 200000)
    _clamp_num("outlier_max_step_kw", 30, 0.5, 200)
    _clamp_num("outlier_max_step_wh", 30000, 100, 10000000)
    _clamp_num("outlier_max_step_kwh", 30, 0.01, 100000)
    _clamp_num("outlier_gap_seconds_default", 300, 1, 86400)

    _clamp_int("outlier_context_before_points", 10, 1, 5000)
    _clamp_int("outlier_context_after_points", 10, 1, 5000)

    def _clamp_num_opt(key: str) -> None:
        v = cfg.get(key)
        if v is None:
            cfg[key] = ""
            return
        if isinstance(v, str) and v.strip() == "":
            cfg[key] = ""
            return
        try:
            cfg[key] = float(v)
        except Exception:
            cfg[key] = ""

    _clamp_num_opt("outlier_bounds_min_default")
    _clamp_num_opt("outlier_bounds_max_default")
    _clamp_int("outlier_recovery_valid_streak_default", 2, 1, 50)

    try:
        cfg["outlier_max_step_units"] = str(cfg.get("outlier_max_step_units") or "")
    except Exception:
        cfg["outlier_max_step_units"] = ""
    if len(cfg["outlier_max_step_units"]) > 8000:
        cfg["outlier_max_step_units"] = cfg["outlier_max_step_units"][:8000]

    save_cfg(cfg)
    LOG.info("api.config_save done from=%s changed=%s", request.remote_addr, changed_keys)
    try:
        configure_logging(cfg)
    except Exception:
        pass
    return jsonify({"ok": True, "message": "Saved. New settings are used immediately."})

@app.post("/api/test")
def api_test():
    """Test InfluxDB connectivity.

    Uses (in order):
      1) Optional JSON body fields (current UI form values)
      2) Persisted runtime config
      3) Fallback: read missing values from the configured influx_yaml_path (does not persist)

    This matches the UI expectation: after loading values from influx.yaml (or even without saving),
    the test should succeed as long as the YAML contains the required parameters.
    """
    base_cfg = load_cfg()

    body = {}
    try:
        body = request.get_json(silent=True) or {}
    except Exception:
        body = {}

    # Start with persisted config, then overlay request body (but keep secrets if body is redacted)
    cfg = dict(base_cfg)
    allowed = set(DEFAULT_CFG.keys())
    for k, v in (body or {}).items():
        if k not in allowed:
            continue
        if k in ("token", "password") and v == "********":
            continue
        cfg[k] = v

    # Log a minimal, redacted trace for incoming test attempts to help debug UI/Ingress issues.
    try:
        src_ip = request.remote_addr or 'unknown'
        hdr_via = request.headers.get('X-Forwarded-For') or request.headers.get('Via') or ''
        body_keys = sorted(list((body or {}).keys()))
        has_token = bool((body or {}).get('token')) and (body.get('token') != '********')
        has_org = bool((body or {}).get('org'))
        has_bucket = bool((body or {}).get('bucket'))
        LOG.info('api.test called from=%s via=%s body_keys=%s has_token=%s has_org=%s has_bucket=%s', src_ip, hdr_via, body_keys, has_token, has_org, has_bucket)
    except Exception:
        try: LOG.debug('api.test: failed logging incoming request');
        except Exception: pass

    # Normalize types
    try:
        cfg["influx_version"] = int(cfg.get("influx_version", 2))
    except Exception:
        cfg["influx_version"] = 2
    try:
        cfg["port"] = int(cfg.get("port", 8086))
    except Exception:
        cfg["port"] = 8086
    cfg["verify_ssl"] = bool(cfg.get("verify_ssl", True))
    try:
        cfg["timeout_seconds"] = int(cfg.get("timeout_seconds", 10))
    except Exception:
        cfg["timeout_seconds"] = 10

    # If required fields are missing, try to load them from influx.yaml (no persistence)
    def _overlay_from_yaml_if_possible(cfg_in: dict) -> dict:
        merged, src = _overlay_from_yaml(cfg_in)
        if src:
            global LAST_AUTODETECT_SOURCE
            LAST_AUTODETECT_SOURCE = src
        return merged

    try:
        if cfg["influx_version"] == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                cfg = _overlay_from_yaml_if_possible(cfg)

            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({"ok": False, "error": "v2 needs token, org, bucket (oder gültige influx.yaml im angegebenen Pfad)."}), 400

            with v2_client(cfg) as c:
                q = f'import "influxdata/influxdb/schema"\nschema.measurements(bucket: "{cfg["bucket"]}") |> limit(n:1)'
                c.query_api().query(q, org=cfg["org"])
                LOG.info("api.test done from=%s result=OK version=2", request.remote_addr)
                return jsonify({"ok": True, "message": "Connection OK (v2)."})
        else:
            if not cfg.get("database"):
                cfg = _overlay_from_yaml_if_possible(cfg)

            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "v1 needs database (oder gültige influx.yaml im angegebenen Pfad)."}), 400

            c = v1_client(cfg)
            c.ping()
            LOG.info("api.test done from=%s result=OK version=1", request.remote_addr)
            return jsonify({"ok": True, "message": "Connection OK (v1)."})
    except Exception as e:
        LOG.error("api.test error from=%s: %s", request.remote_addr, _short_influx_error(e), exc_info=True)
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/query_test")
def api_query_test():
    """Execute a free-form InfluxDB query with safety checks.

    Accepts JSON body:
      - query: the Flux (v2) or InfluxQL (v1) query string
      - influx_version: 1 or 2 (defaults to config)

    Returns:
      - ok, query, query_language, is_mutating, rows, start, stop, duration_ms
    """
    import re as _re
    from datetime import datetime, timezone

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(silent=True) or {}
    raw_query = str(body.get("query") or "").strip()

    if not raw_query:
        return jsonify({"ok": False, "error": "Query ist leer."}), 400

    influx_version = int(body.get("influx_version") or cfg.get("influx_version", 2))

    # Detect query language and mutating statements
    query_lower = raw_query.lower()
    query_language = "flux" if influx_version == 2 else "influxql"

    MUTATING_FLUX = ["to(", "drop(", "delete"]
    MUTATING_INFLUXQL = [
        _re.compile(r"\bdelete\b", _re.IGNORECASE),
        _re.compile(r"\bdrop\b", _re.IGNORECASE),
        _re.compile(r"\bselect\s+.+\binto\b", _re.IGNORECASE),
    ]

    is_mutating = False
    mutation_hint = ""

    if influx_version == 2:
        for pattern in MUTATING_FLUX:
            if pattern in query_lower:
                is_mutating = True
                mutation_hint = f"Mutierendes Flux-Statement erkannt ('{pattern}'). Ausfuehrung verweigert."
                break
    else:
        for pattern in MUTATING_INFLUXQL:
            if pattern.search(raw_query):
                is_mutating = True
                mutation_hint = "Mutierendes InfluxQL-Statement erkannt. Ausfuehrung verweigert."
                break

    if is_mutating:
        return jsonify({
            "ok": False,
            "error": mutation_hint,
            "query": raw_query,
            "query_language": query_language,
            "is_mutating": True,
        }), 403

    start_iso = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    rows = []

    try:
        if influx_version == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({"ok": False, "error": "v2: token, org, bucket fehlen."}), 400
            with v2_client(cfg) as c:
                log_query("query_test", raw_query)
                result = c.query_api().query(raw_query, org=cfg["org"])
                for table in result:
                    for record in table.records:
                        row = {}
                        for key, val in record.values.items():
                            row[key] = val
                        rows.append(row)
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "v1: database fehlt."}), 400
            c = v1_client(cfg)
            log_query("query_test", raw_query)
            result = c.query(raw_query)
            for _, points in result.items():
                for p in points:
                    rows.append(dict(p))

        dur_ms = int((time.perf_counter() - t0) * 1000)
        stop_iso = datetime.now(timezone.utc).isoformat()

        return jsonify({
            "ok": True,
            "query": raw_query,
            "query_language": query_language,
            "is_mutating": False,
            "rows": rows,
            "start": start_iso,
            "stop": stop_iso,
            "duration_ms": dur_ms,
        })
    except Exception as e:
        dur_ms = int((time.perf_counter() - t0) * 1000)
        stop_iso = datetime.now(timezone.utc).isoformat()
        return jsonify({
            "ok": False,
            "error": _short_influx_error(e),
            "query": raw_query,
            "query_language": query_language,
            "is_mutating": False,
            "start": start_iso,
            "stop": stop_iso,
            "duration_ms": dur_ms,
        }), 500


@app.get("/api/influx_ping")
def api_influx_ping():
    """Best-effort connection check using the saved configuration.

    Intended for the bottom status bar.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    fp = _stats_cache_cfg_fp(cfg)
    now_mono = time.monotonic()

    with INFLUX_PING_LOCK:
        last = dict(INFLUX_PING_CACHE or {})
        if last.get("fp") == fp and (now_mono - float(last.get("at_mono") or 0.0)) < 25.0:
            return jsonify(last.get("payload") or {"ok": True, "connected": None, "message": "cached"})

    out: dict[str, Any] = {
        "ok": True,
        "connected": None,
        "message": "unknown",
        "checked_at": _utc_now_iso_ms(),
        "influx_version": int(cfg.get("influx_version", 2) or 2),
    }

    try:
        if int(cfg.get("influx_version", 2) or 2) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                out["connected"] = False
                out["message"] = "v2: token/org/bucket missing"
            else:
                with v2_client(cfg, timeout_seconds_override=3) as c:
                    q = f'import "influxdata/influxdb/schema"\nschema.measurements(bucket: "{cfg["bucket"]}") |> limit(n:1)'
                    c.query_api().query(q, org=cfg["org"])
                out["connected"] = True
                out["message"] = "ok"
        else:
            if not cfg.get("database"):
                out["connected"] = False
                out["message"] = "v1: database missing"
            else:
                c = v1_client(cfg)
                c.ping()
                out["connected"] = True
                out["message"] = "ok"
    except Exception as e:
        out["connected"] = False
        out["message"] = _short_influx_error(e)

    with INFLUX_PING_LOCK:
        INFLUX_PING_CACHE.clear()
        INFLUX_PING_CACHE.update({"fp": fp, "at_mono": now_mono, "payload": out})
    return jsonify(out)
@app.get("/api/measurements")
def measurements():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    range_key = request.args.get("range")
    field = request.args.get("field", "")
    entity_id = request.args.get("entity_id", "") or None
    friendly_name = request.args.get("friendly_name", "") or None
    start_raw = request.args.get("start")
    stop_raw = request.args.get("stop")
    start_dt: datetime | None = None
    stop_dt: datetime | None = None
    if start_raw or stop_raw:
        try:
            start_dt, stop_dt = _get_start_stop_from_payload({"start": start_raw, "stop": stop_raw})
        except Exception as e:
            return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    selector_range = _selector_range_key(range_key, start_dt, stop_dt)
    try:
        selector_limit = min(200000, max(1, int(cfg.get("ui_query_max_points", 5000) or 5000)))
    except Exception:
        selector_limit = 5000
    try:
        if int(cfg.get("influx_version",2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400
            with v2_client(cfg) as c:
                if field or entity_id or friendly_name or start_dt or stop_dt:
                    range_clause = _flux_range_clause(selector_range, start_dt, stop_dt)
                    predicate_parts = ["exists r._measurement"]
                    if field:
                        predicate_parts.append(f"r._field == {_flux_str(field)}")
                    if entity_id:
                        predicate_parts.append(f"r.entity_id == {_flux_str(entity_id)}")
                    if friendly_name:
                        predicate_parts.append(f"r.friendly_name == {_flux_str(friendly_name)}")
                    predicate = " and ".join(predicate_parts)
                    q = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => {predicate})
  |> keep(columns: ["_measurement"])
  |> distinct(column: "_measurement")
  |> sort(columns: ["_measurement"])
  |> map(fn: (r) => ({{ _value: r._measurement }}))
  |> keep(columns: ["_value"])
  |> limit(n: {selector_limit})
'''
                else:
                    q = f'import "influxdata/influxdb/schema"\nschema.measurements(bucket: "{cfg["bucket"]}")'
                log_query("api.measurements (flux)", q)
                tables = c.query_api().query(q, org=cfg["org"])
                items = []
                for t in tables:
                    for r in t.records:
                        items.append(str(r.get_value()))
                result = sorted(set(items))
                _log_selector_debug("measurements", {
                    "filters": {"field": field or "", "entity_id": entity_id or "", "friendly_name": friendly_name or "", "range": selector_range},
                    "count": len(result),
                    "items": result,
                })
                return jsonify({"ok": True, "measurements": result})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            c = v1_client(cfg)
            q = "SHOW MEASUREMENTS"
            log_query("api.measurements (influxql)", q)
            res = c.query(q)
            items = []
            for _, points in res.items():
                for p in points:
                    items.append(p.get("name"))
            result = sorted(set(items))
            _log_selector_debug("measurements", {
                "filters": {"field": field or "", "entity_id": entity_id or "", "friendly_name": friendly_name or "", "range": selector_range},
                "count": len(result),
                "items": result,
            })
            return jsonify({"ok": True, "measurements": result})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

@app.get("/api/fields")
def fields():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    measurement = request.args.get("measurement", "")
    range_key = request.args.get("range")
    entity_id = request.args.get("entity_id", "") or None
    friendly_name = request.args.get("friendly_name", "") or None
    start_raw = request.args.get("start")
    stop_raw = request.args.get("stop")
    start_dt: datetime | None = None
    stop_dt: datetime | None = None
    if start_raw or stop_raw:
        try:
            start_dt, stop_dt = _get_start_stop_from_payload({"start": start_raw, "stop": stop_raw})
        except Exception as e:
            return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    selector_range = _selector_range_key(range_key, start_dt, stop_dt)
    try:
        selector_limit = min(200000, max(1, int(cfg.get("ui_query_max_points", 5000) or 5000)))
    except Exception:
        selector_limit = 5000
    if not measurement and not entity_id and not friendly_name:
        return jsonify({"ok": False, "error": "measurement or tag filter required"}), 400
    try:
        if int(cfg.get("influx_version",2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400
            with v2_client(cfg) as c:
                range_clause = _flux_range_clause(selector_range, start_dt, stop_dt)
                predicate_parts = ["exists r._field"]
                if measurement:
                    predicate_parts.append(f"r._measurement == {_flux_str(measurement)}")
                if entity_id:
                    predicate_parts.append(f"r.entity_id == {_flux_str(entity_id)}")
                if friendly_name:
                    predicate_parts.append(f"r.friendly_name == {_flux_str(friendly_name)}")
                predicate = " and ".join(predicate_parts)
                q = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => {predicate})
  |> keep(columns: ["_field"])
  |> distinct(column: "_field")
  |> sort(columns: ["_field"])
  |> map(fn: (r) => ({{ _value: r._field }}))
  |> keep(columns: ["_value"])
  |> limit(n: {selector_limit})
'''
                log_query("api.fields (flux)", q)
                tables = c.query_api().query(q, org=cfg["org"])
                fs = []
                for t in tables:
                    for r in t.records:
                        fs.append(str(r.get_value()))
                result = sorted(set(fs))
                _log_selector_debug("fields", {
                    "filters": {"measurement": measurement or "", "entity_id": entity_id or "", "friendly_name": friendly_name or "", "range": selector_range},
                    "count": len(result),
                    "items": result,
                })
                return jsonify({"ok": True, "fields": result})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            if not measurement:
                return jsonify({"ok": False, "error": "measurement required for InfluxDB v1"}), 400
            c = v1_client(cfg)
            q = f'SHOW FIELD KEYS FROM "{measurement}"'
            log_query("api.fields (influxql)", q)
            res = c.query(q)
            fs = []
            for _, points in res.items():
                for p in points:
                    fs.append(p.get("fieldKey"))
            result = sorted(set(fs))
            _log_selector_debug("fields", {
                "filters": {"measurement": measurement or "", "entity_id": entity_id or "", "friendly_name": friendly_name or "", "range": selector_range},
                "count": len(result),
                "items": result,
            })
            return jsonify({"ok": True, "fields": result})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

@app.get("/api/tag_values")
def tag_values():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    tag = request.args.get("tag", "")
    measurement = request.args.get("measurement", "")
    field = request.args.get("field", "")
    range_key = request.args.get("range")
    entity_id = request.args.get("entity_id", "") or None
    friendly_name = request.args.get("friendly_name", "") or None
    start_raw = request.args.get("start")
    stop_raw = request.args.get("stop")

    if not tag:
        return jsonify({"ok": False, "error": "tag required"}), 400

    # Keep this endpoint constrained; tag name is interpolated into Flux.
    allowed_tags = {"entity_id", "friendly_name"}
    if tag not in allowed_tags:
        return jsonify({"ok": False, "error": "unsupported tag"}), 400

    start_dt: datetime | None = None
    stop_dt: datetime | None = None
    if start_raw or stop_raw:
        try:
            start_dt, stop_dt = _get_start_stop_from_payload({"start": start_raw, "stop": stop_raw})
        except Exception as e:
            return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    selector_range = _selector_range_key(range_key, start_dt, stop_dt)
    try:
        selector_limit = min(200000, max(1, int(cfg.get("ui_query_max_points", 5000) or 5000)))
    except Exception:
        selector_limit = 5000

    try:
        if int(cfg.get("influx_version",2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400
            predicate_parts = []
            if measurement:
                predicate_parts.append(f"r._measurement == {_flux_str(measurement)}")
            if field:
                predicate_parts.append(f"r._field == {_flux_str(field)}")
            if entity_id:
                predicate_parts.append(f"r.entity_id == {_flux_str(entity_id)}")
            if friendly_name:
                predicate_parts.append(f"r.friendly_name == {_flux_str(friendly_name)}")
            predicate = " and ".join(predicate_parts) if predicate_parts else "true"

            with v2_client(cfg) as c:
                # schema.tagValues does not support stop; for custom ranges we use a direct query.
                if stop_dt and start_dt:
                    range_clause = _flux_range_clause(selector_range, start_dt, stop_dt)
                    q = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => {predicate})
  |> filter(fn: (r) => exists r.{tag})
  |> keep(columns: ["{tag}"])
  |> distinct(column: "{tag}")
  |> sort(columns: ["{tag}"])
  |> map(fn: (r) => ({{ _value: r.{tag} }}))
  |> keep(columns: ["_value"])
  |> limit(n: {selector_limit})
'''
                else:
                    start_arg = range_to_flux(selector_range)
                    q = f'''
import "influxdata/influxdb/schema"
schema.tagValues(
  bucket: "{cfg["bucket"]}",
  tag: "{tag}",
  predicate: (r) => {predicate},
  start: {start_arg}
)
'''
                log_query("api.tag_values (flux)", q)
                tables = c.query_api().query(q, org=cfg["org"])
                vals = []
                for t in tables:
                    for r in t.records:
                        vals.append(str(r.get_value()))
                result = sorted(set(vals))
                _log_selector_debug("tag_values", {
                    "tag": tag,
                    "filters": {"measurement": measurement or "", "field": field or "", "entity_id": entity_id or "", "friendly_name": friendly_name or "", "range": selector_range},
                    "count": len(result),
                    "items": result,
                })
                return jsonify({"ok": True, "values": result})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            c = v1_client(cfg)
            where = f"WHERE {_influxql_time_where(selector_range, start_dt, stop_dt)}"
            if entity_id:
                safe_entity_id = entity_id.replace("'", "\\'")
                where += f' AND "entity_id"=\'{safe_entity_id}\''
            if friendly_name:
                safe_name = friendly_name.replace("'", "\\'")
                where += f' AND "friendly_name"=\'{safe_name}\''
            q = f'SHOW TAG VALUES WITH KEY = "{tag}" {where}'
            log_query("api.tag_values (influxql)", q)
            res = c.query(q)
            vals = []
            for _, points in res.items():
                for p in points:
                    v = p.get("value")
                    if v is not None:
                        vals.append(str(v))
            result = sorted(set(vals))
            _log_selector_debug("tag_values", {
                "tag": tag,
                "filters": {"measurement": measurement or "", "field": field or "", "entity_id": entity_id or "", "friendly_name": friendly_name or "", "range": selector_range},
                "count": len(result),
                "items": result,
            })
            return jsonify({"ok": True, "values": result})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/tag_combo_ranges")
def api_tag_combo_ranges():
    """Return per-tag time ranges for a measurement/field.

    Used to show "multiple entity_id" for a friendly_name (and vice versa).
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}

    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    group_tag = str(body.get("group_tag") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    allowed_tags = {"entity_id", "friendly_name"}
    if group_tag not in allowed_tags:
        return jsonify({"ok": False, "error": "unsupported group_tag"}), 400

    # fixed filters must use supported tags
    if entity_id and friendly_name:
        # Both is allowed but typically only one is used.
        pass

    try:
        limit = int(body.get("limit", 50))
    except Exception:
        limit = 50
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "tag_combo_ranges currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    conds = [f"r._measurement == {_flux_str(measurement)}", f"r._field == {_flux_str(field)}"]
    if entity_id:
        conds.append(f"r.entity_id == {_flux_str(entity_id)}")
    if friendly_name:
        conds.append(f"r.friendly_name == {_flux_str(friendly_name)}")
    conds.append(f"exists r.{group_tag}")
    predicate = " and ".join(conds)

    bucket = str(cfg["bucket"])
    q = f'''
base = from(bucket: "{bucket}")
  |> range(start: time(v: "1970-01-01T00:00:00Z"))
  |> filter(fn: (r) => {predicate})
  |> keep(columns: ["{group_tag}", "_time"])
  |> group(columns: ["{group_tag}"])

base
  |> reduce(
    identity: {{oldest_time: time(v: "2100-01-01T00:00:00Z"), newest_time: time(v: "1970-01-01T00:00:00Z"), count: 0}},
    fn: (r, acc) => ({{
      oldest_time: if r._time < acc.oldest_time then r._time else acc.oldest_time,
      newest_time: if r._time > acc.newest_time then r._time else acc.newest_time,
      count: acc.count + 1,
    }}),
  )
  |> keep(columns: ["{group_tag}", "oldest_time", "newest_time", "count"])
  |> sort(columns: ["count"], desc: true)
  |> limit(n: {limit})
'''

    def _iso_any(v: Any) -> str | None:
        if isinstance(v, datetime):
            return _dt_to_rfc3339_utc(v)
        if isinstance(v, str) and v.strip():
            return v.strip()
        return None

    out_rows: list[dict[str, Any]] = []
    try:
        with v2_client(cfg) as c:
            tables = c.query_api().query(q, org=cfg["org"])
            for t in tables or []:
                for rec in getattr(t, "records", []) or []:
                    vals = getattr(rec, "values", {}) or {}
                    v = vals.get(group_tag)
                    if v is None:
                        continue
                    out_rows.append({
                        "value": str(v),
                        "count": int(vals.get("count") or 0),
                        "oldest_time": _iso_any(vals.get("oldest_time")),
                        "newest_time": _iso_any(vals.get("newest_time")),
                    })
        return jsonify({"ok": True, "rows": out_rows})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

class _ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def _query_payload(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    range_key: str,
    entity_id: str | None,
    friendly_name: str | None,
    unit: str,
    detail_mode: str,
    manual_density_pct: int,
    start_dt: datetime | None,
    stop_dt: datetime | None,
) -> dict[str, Any]:
    if not measurement or not field:
        raise _ApiError("measurement and field required", status=400)

    def _count_points_v2(qapi, range_clause: str, extra: str) -> int | None:
        try:
            qcnt = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_value"])
  |> count(column: "_value")
'''
            for rec in qapi.query_stream(qcnt, org=cfg["org"]):
                try:
                    v = rec.get_value()
                    if isinstance(v, bool):
                        continue
                    if isinstance(v, (int, float)):
                        return int(v)
                except Exception:
                    continue
        except Exception:
            return None
        return None

    try:
        if int(cfg.get("influx_version", 2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                raise _ApiError(
                    "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                    status=400,
                )

            extra = flux_tag_filter(entity_id, friendly_name)
            with v2_client(cfg) as c:
                qapi = c.query_api()

                range_clause = _flux_range_clause(range_key, start_dt, stop_dt)
                total_points = _count_points_v2(qapi, range_clause, extra)
                base = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"])
'''

                if detail_mode == "manual":
                    try:
                        max_points = int(cfg.get("ui_query_manual_max_points", 200000) or 200000)
                    except Exception:
                        max_points = 200000
                    max_points = min(2000000, max(1000, max_points))

                    q = base + f"  |> limit(n: {max_points})\n"
                    q = log_query("api.query manual (flux)", q)

                    rows: list[dict[str, Any]] = []
                    for rec in qapi.query_stream(q, org=cfg["org"]):
                        try:
                            ts = rec.get_time()
                            val = rec.get_value()
                            if not isinstance(ts, datetime):
                                continue
                            rows.append({"time": ts.astimezone(timezone.utc).isoformat(), "value": val})
                        except Exception:
                            continue

                    return {
                        "ok": True,
                        "rows": rows,
                        "query": q.strip(),
                        "meta": {
                            "mode": "manual",
                            "manual_density_pct": manual_density_pct,
                            "max_points": max_points,
                            "returned": len(rows),
                            "unit": unit,
                            "total_points": total_points,
                            "covered_start": _dt_to_rfc3339_utc(start_dt) if start_dt else (rows[0]["time"] if rows else None),
                            "covered_stop": _dt_to_rfc3339_utc(stop_dt) if stop_dt else (rows[-1]["time"] if rows else None),
                            "outlier_count": 0,
                        },
                    }

                # dynamic
                try:
                    target_points = int(cfg.get("ui_query_max_points", 5000) or 5000)
                except Exception:
                    target_points = 5000
                target_points = min(200000, max(500, target_points))

                span_ms = None
                try:
                    if start_dt and stop_dt:
                        span_ms = int((stop_dt - start_dt).total_seconds() * 1000.0)
                except Exception:
                    span_ms = None
                every_ms = 0
                if span_ms is not None and span_ms > 0:
                    every_ms = int(math.ceil(span_ms / float(target_points)))
                if every_ms < 1000:
                    every_ms = 0

                q = base
                mode = "raw"
                if every_ms:
                    mode = "downsample"
                    q = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> aggregateWindow(every: {every_ms}ms, fn: max, createEmpty: false)
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"])
'''
                q = log_query("api.query dynamic (flux)", q)

                coarse: list[tuple[datetime, float]] = []
                for rec in qapi.query_stream(q, org=cfg["org"]):
                    try:
                        ts = rec.get_time()
                        val = rec.get_value()
                        if not isinstance(ts, datetime):
                            continue
                        if isinstance(val, bool) or not isinstance(val, (int, float)):
                            continue
                        coarse.append((ts.astimezone(timezone.utc), float(val)))
                    except Exception:
                        continue
                coarse.sort(key=lambda x: x[0])

                try:
                    step_th = float(_outlier_max_step(cfg, measurement, unit))
                except Exception:
                    step_th = 0.0
                if step_th < 0:
                    step_th = 0.0

                try:
                    pad_n = int(cfg.get("ui_graph_jump_padding_intervals", 1) or 1)
                except Exception:
                    pad_n = 1
                pad_n = min(50, max(0, pad_n))
                pad_ms = int(every_ms * pad_n) if every_ms else 0

                jump_spans: list[dict[str, Any]] = []
                if step_th and len(coarse) >= 2:
                    for i in range(1, len(coarse)):
                        t0, v0 = coarse[i - 1]
                        t1, v1 = coarse[i]
                        d = abs(v1 - v0)
                        if d <= step_th:
                            continue
                        a = min(t0, t1)
                        b = max(t0, t1)
                        if pad_ms:
                            a = a - timedelta(milliseconds=pad_ms)
                            b = b + timedelta(milliseconds=pad_ms)
                        jump_spans.append({
                            "start": _dt_to_rfc3339_utc_ms(a),
                            "stop": _dt_to_rfc3339_utc_ms(b),
                            "delta": d,
                        })

                merged: list[tuple[datetime, datetime]] = []
                if jump_spans:
                    tmp = []
                    for sp in jump_spans:
                        try:
                            a = _parse_iso_datetime(str(sp.get("start") or ""))
                            b = _parse_iso_datetime(str(sp.get("stop") or ""))
                            if b <= a:
                                continue
                            tmp.append((a, b))
                        except Exception:
                            continue
                    tmp.sort(key=lambda x: x[0])
                    for a, b in tmp:
                        if not merged:
                            merged.append((a, b))
                            continue
                        la, lb = merged[-1]
                        if a <= lb:
                            merged[-1] = (la, max(lb, b))
                        else:
                            merged.append((a, b))

                refine_points: dict[str, float] = {}
                total_refine = 0
                per_span_limit = 5000
                total_cap = 50000
                if merged:
                    for a, b in merged:
                        if total_refine >= total_cap:
                            break
                        lim = min(per_span_limit, total_cap - total_refine)
                        s = _dt_to_rfc3339_utc(a)
                        e = _dt_to_rfc3339_utc(b)
                        q2 = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{s}"), stop: time(v: "{e}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"])
  |> limit(n: {lim})
'''
                        q2 = log_query("api.query refine (flux)", q2)
                        for rec in qapi.query_stream(q2, org=cfg["org"]):
                            try:
                                ts = rec.get_time()
                                val = rec.get_value()
                                if not isinstance(ts, datetime):
                                    continue
                                if isinstance(val, bool) or not isinstance(val, (int, float)):
                                    continue
                                refine_points[_dt_to_rfc3339_utc_ms(ts)] = float(val)
                                total_refine += 1
                                if total_refine >= total_cap:
                                    break
                            except Exception:
                                continue

                merged_map: dict[str, float] = {}
                for ts, v in coarse:
                    merged_map[_dt_to_rfc3339_utc_ms(ts)] = float(v)
                for k, v in refine_points.items():
                    merged_map[str(k)] = float(v)
                times = sorted(merged_map.keys())
                rows_all = [{"time": t, "value": merged_map[t]} for t in times]

                max_return = int(target_points + total_cap)
                if max_return < 1000:
                    max_return = 1000
                if len(rows_all) > max_return:
                    keep = set(refine_points.keys())
                    keep_rows = [r for r in rows_all if str(r.get("time")) in keep]
                    rest_rows = [r for r in rows_all if str(r.get("time")) not in keep]
                    remain = max_return - len(keep_rows)
                    if remain <= 0:
                        step = max(1, math.ceil(len(keep_rows) / max_return))
                        rows_all = keep_rows[::step]
                    else:
                        if len(rest_rows) > remain:
                            step = max(1, math.ceil(len(rest_rows) / remain))
                            rest_rows = rest_rows[::step]
                        rows_all = sorted(keep_rows + rest_rows, key=lambda r: str(r.get("time") or ""))

                    return {
                        "ok": True,
                        "rows": rows_all,
                        "query": q.strip(),
                        "meta": {
                        "mode": "dynamic",
                        "coarse_mode": mode,
                        "every_ms": every_ms,
                        "target_points": target_points,
                        "returned": len(rows_all),
                        "refined": len(refine_points),
                        "jump_threshold": step_th,
                            "jump_padding_intervals": pad_n,
                            "jump_spans": jump_spans,
                            "unit": unit,
                            "total_points": total_points,
                            "covered_start": _dt_to_rfc3339_utc(start_dt) if start_dt else (rows_all[0]["time"] if rows_all else None),
                            "covered_stop": _dt_to_rfc3339_utc(stop_dt) if stop_dt else (rows_all[-1]["time"] if rows_all else None),
                            "outlier_count": len(jump_spans),
                        },
                    }

        # v1
        if not cfg.get("database"):
            raise _ApiError("InfluxDB v1 requires database. Bitte konfigurieren.", status=400)
        c = v1_client(cfg)
        tag_where = influxql_tag_filter(entity_id, friendly_name)
        time_where = _influxql_time_where(range_key, start_dt, stop_dt)
        q = f'SELECT "{field}" FROM "{measurement}" WHERE {time_where}{tag_where} ORDER BY time ASC'
        log_query("api.query (influxql)", q)
        res = c.query(q)
        rows: list[dict[str, Any]] = []
        for _, points in res.items():
            for p in points:
                rows.append({"time": p.get("time"), "value": p.get(field)})

        total_points = None
        try:
            qcnt = f'SELECT COUNT("{field}") AS c FROM "{measurement}" WHERE {time_where}{tag_where}'
            res2 = c.query(qcnt)
            for _, pts in res2.items():
                for p in pts:
                    v = p.get("c")
                    if isinstance(v, (int, float)):
                        total_points = int(v)
                        break
                if total_points is not None:
                    break
        except Exception:
            total_points = None

        if detail_mode == "manual":
            try:
                max_points = int(cfg.get("ui_query_manual_max_points", 200000) or 200000)
            except Exception:
                max_points = 200000
            max_points = min(2000000, max(1000, max_points))
            if len(rows) > max_points:
                step = max(1, math.ceil(len(rows) / max_points))
                rows = rows[::step]
            return {
                "ok": True,
                "rows": rows,
                "query": q.strip(),
                "meta": {
                    "mode": "manual",
                    "manual_density_pct": manual_density_pct,
                    "max_points": max_points,
                    "returned": len(rows),
                    "unit": unit,
                    "total_points": total_points,
                },
            }

        max_points = int(cfg.get("ui_query_max_points", 5000) or 5000)
        max_points = min(200000, max(500, max_points))
        if len(rows) > max_points:
            step = max(1, math.ceil(len(rows) / max_points))
            rows = rows[::step]
        return {
            "ok": True,
            "rows": rows,
            "query": q.strip(),
            "meta": {
                "mode": "dynamic",
                "target_points": max_points,
                "returned": len(rows),
                "unit": unit,
                "total_points": total_points,
            },
        }
    except _ApiError:
        raise
    except Exception as e:
        raise e


@app.post("/api/query")
def query():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    range_key = str(body.get("range") or "24h")
    entity_id = (body.get("entity_id") or None)
    friendly_name = (body.get("friendly_name") or None)
    unit = str(body.get("unit") or "").strip()

    LOG.info("api.query called from=%s measurement=%s field=%s range=%s",
        request.remote_addr, measurement, field, range_key)

    detail_mode = str(body.get("detail_mode") or "dynamic").strip().lower()
    if detail_mode not in ("dynamic", "manual"):
        detail_mode = "dynamic"
    try:
        manual_density_pct = int(body.get("manual_density_pct") or 100)
    except Exception:
        manual_density_pct = 100
    manual_density_pct = min(100, max(1, manual_density_pct))
    cache_strategy = str(body.get("cache_strategy") or "default").strip().lower()
    if cache_strategy not in ("default", "reuse", "refresh"):
        cache_strategy = "default"

    t0 = time.monotonic()
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        LOG.error("api.query parse_error: %s", e)
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    req_start, req_stop = _dash_cache_requested_range(range_key, start_dt, stop_dt)
    requested_span_s = max(1.0, (req_stop - req_start).total_seconds())
    series_key = _dash_cache_series_key(
        measurement,
        field,
        str(entity_id) if entity_id else None,
        str(friendly_name) if friendly_name else None,
        detail_mode,
    )

    # Correlation id for cache usage logging
    run_id = uuid.uuid4().hex

    try:
        LOG.debug(
            "api.query measurement=%s field=%s range=%s entity_id=%s friendly_name=%s",
            measurement,
            field,
            range_key,
            bool(entity_id),
            bool(friendly_name),
        )
    except Exception:
        pass

    cache_id = None
    key = None
    try:
        if bool(cfg.get("dash_cache_enabled", True)):
            key = _dash_cache_key(
                cfg,
                body,
                measurement,
                field,
                range_key,
                str(entity_id) if entity_id else None,
                str(friendly_name) if friendly_name else None,
                unit,
                detail_mode,
                manual_density_pct,
                start_dt,
                stop_dt,
            )
            cache_id = _dash_cache_id(key)
            meta = _dash_cache_load_meta(cache_id)
            if cache_strategy != "refresh" and meta and not bool(meta.get("dirty")):
                t0 = time.perf_counter()
                cached = _dash_cache_load_payload(cache_id)
                dur_ms = int((time.perf_counter() - t0) * 1000)
                if cached and bool(cached.get("ok")):
                    try:
                        _cache_usage_append(cfg, {
                            "kind": "dash_cache_hit",
                            "page": "dashboard",
                            "run_id": run_id,
                            "cache_id": cache_id,
                            "step": "read_payload",
                            "dur_ms": dur_ms,
                            "rows": len(cached.get("rows") or []) if isinstance(cached.get("rows"), list) else None,
                            "bytes": meta.get("bytes"),
                            "series_key": series_key,
                            "requested_span_s": requested_span_s,
                            "note": f"range={range_key} detail={detail_mode}",
                        })
                    except Exception:
                        pass
                    _dash_cache_touch_used(cache_id)
                    try:
                        _dash_last_set_from_query(body, cache_id, key)
                    except Exception:
                        pass
                    out = dict(cached)
                    out["cached"] = True
                    out["cache"] = {"id": cache_id, "updated_at": meta.get("updated_at"), "strategy": "exact"}
                    out["cache_plan"] = {
                        "strategy": "exact",
                        "segments_used": 1,
                        "gaps_loaded": 0,
                        "steps": [{
                            "label": "Exakten Cache verwendet",
                            "status": "ok",
                            "sub": f"Cache-Datum: {str(meta.get('updated_at') or '-')}",
                        }],
                        "estimated_savings_ms": None,
                    }
                    # Persist a trace query entry even for cache hits so the Waterfall can show a hint.
                    try:
                        try:
                            q_cached = str(cached.get("query") or "")
                        except Exception:
                            q_cached = ""
                        q_sane = _strip_trace_prefix(q_cached)
                        if not q_sane.strip():
                            q_sane = f"// dash_cache_hit cache_id={cache_id} strategy=exact"
                        log_query("api.query (dash_cache_hit)", q_sane)
                    except Exception:
                        pass

                    # Enqueue background refresh if stale (best-effort)
                    try:
                        if bool(cfg.get("dash_cache_update_on_use_if_stale", True)) and _dash_cache_is_stale(cfg, meta):
                            _dash_cache_mark_dirty_id(cache_id, "stale")
                            try:
                                _cache_usage_append(cfg, {
                                    "kind": "dash_cache_mark_dirty",
                                    "page": "dashboard",
                                    "run_id": run_id,
                                    "cache_id": cache_id,
                                    "step": "stale",
                                    "note": "marked dirty (stale)",
                                })
                            except Exception:
                                pass
                    except Exception:
                        pass
                    return jsonify(out)
                else:
                    try:
                        _cache_usage_append(cfg, {
                            "kind": "dash_cache_miss",
                            "page": "dashboard",
                            "run_id": run_id,
                            "cache_id": cache_id,
                            "step": "read_payload",
                            "dur_ms": dur_ms,
                            "series_key": series_key,
                            "requested_span_s": requested_span_s,
                            "note": "payload missing/invalid",
                        })
                    except Exception:
                        pass
            else:
                try:
                    _cache_usage_append(cfg, {
                        "kind": "dash_cache_miss",
                        "page": "dashboard",
                        "run_id": run_id,
                        "cache_id": cache_id,
                        "step": "meta",
                        "series_key": series_key,
                        "requested_span_s": requested_span_s,
                        "note": ("dirty" if (meta and bool(meta.get("dirty"))) else "no_meta"),
                    })
                except Exception:
                    pass
    except Exception:
        # Cache is best-effort. Ignore and fall back to DB query.
        cache_id = None
        key = None

    if cache_strategy == "reuse" and bool(cfg.get("dash_cache_enabled", True)) and key and cache_id:
        try:
            plan = _dash_cache_plan(
                cfg,
                body,
                measurement,
                field,
                range_key,
                str(entity_id) if entity_id else None,
                str(friendly_name) if friendly_name else None,
                unit,
                detail_mode,
                manual_density_pct,
                start_dt,
                stop_dt,
            )
            if plan.get("has_cache") and not plan.get("exact") and (plan.get("segments") or []):
                row_groups: list[list[dict[str, Any]]] = []
                cache_steps: list[dict[str, Any]] = []
                source_cache_ids: list[str] = []
                gap_query_ms = 0
                used_jump_spans: list[dict[str, Any]] = []
                total_points_acc: int | None = 0
                for seg in plan.get("segments") or []:
                    seg_t0 = time.perf_counter()
                    rows_seg = list(seg.get("filtered_rows") or [])
                    seg_ms = int((time.perf_counter() - seg_t0) * 1000)
                    row_groups.append(rows_seg)
                    source_cache_ids.append(str(seg.get("cache_id") or ""))
                    meta_seg = seg.get("meta") if isinstance(seg.get("meta"), dict) else {}
                    payload_seg = seg.get("payload") if isinstance(seg.get("payload"), dict) else {}
                    meta_info = payload_seg.get("meta") if isinstance(payload_seg.get("meta"), dict) else {}
                    js = meta_info.get("jump_spans") if isinstance(meta_info.get("jump_spans"), list) else []
                    used_jump_spans.extend(js)
                    try:
                        tp = meta_info.get("total_points")
                        total_points_acc = (int(total_points_acc or 0) + int(tp)) if isinstance(tp, (int, float)) else total_points_acc
                    except Exception:
                        total_points_acc = None
                    _dash_cache_touch_used(str(seg.get("cache_id") or ""))
                    try:
                        _cache_usage_append(cfg, {
                            "kind": "dash_cache_partial_hit",
                            "page": "dashboard",
                            "run_id": run_id,
                            "cache_id": str(seg.get("cache_id") or ""),
                            "step": "segment",
                            "dur_ms": seg_ms,
                            "rows": len(rows_seg),
                            "series_key": series_key,
                            "requested_span_s": requested_span_s,
                            "note": f"{_dt_to_rfc3339_utc(seg.get('use_start'))}..{_dt_to_rfc3339_utc(seg.get('use_stop'))}",
                        })
                    except Exception:
                        pass
                    cache_steps.append({
                        "label": "Cache-Segment verwendet",
                        "status": "ok",
                        "sub": f"{_dt_to_rfc3339_utc(seg.get('use_start'))} bis {_dt_to_rfc3339_utc(seg.get('use_stop'))} | Cache: {str(meta_seg.get('updated_at') or '-')}",
                    })

                for ga, gb in plan.get("gaps") or []:
                    gap_t0 = time.perf_counter()
                    part = _query_payload(
                        cfg,
                        measurement,
                        field,
                        range_key,
                        str(entity_id) if entity_id else None,
                        str(friendly_name) if friendly_name else None,
                        unit,
                        detail_mode,
                        manual_density_pct,
                        ga,
                        gb,
                    )
                    part_ms = int((time.perf_counter() - gap_t0) * 1000)
                    gap_query_ms += part_ms
                    row_groups.append(list(part.get("rows") or []))
                    part_meta = part.get("meta") if isinstance(part.get("meta"), dict) else {}
                    js = part_meta.get("jump_spans") if isinstance(part_meta.get("jump_spans"), list) else []
                    used_jump_spans.extend(js)
                    cache_steps.append({
                        "label": "Fehlenden Rest geladen",
                        "status": "ok",
                        "sub": f"{_dt_to_rfc3339_utc(ga)} bis {_dt_to_rfc3339_utc(gb)} | {part_ms}ms",
                    })
                    try:
                        _cache_usage_append(cfg, {
                            "kind": "dash_cache_partial_gap_query",
                            "page": "dashboard",
                            "run_id": run_id,
                            "cache_id": cache_id,
                            "step": "gap_query",
                            "dur_ms": part_ms,
                            "rows": len(part.get("rows") or []) if isinstance(part.get("rows"), list) else None,
                            "series_key": series_key,
                            "requested_span_s": requested_span_s,
                            "note": f"{_dt_to_rfc3339_utc(ga)}..{_dt_to_rfc3339_utc(gb)}",
                        })
                    except Exception:
                        pass

                merge_t0 = time.perf_counter()
                merged_rows = _dash_cache_merge_rows(row_groups)
                merge_ms = int((time.perf_counter() - merge_t0) * 1000)
                cache_steps.append({
                    "label": "Cache-Daten zusammengefuehrt",
                    "status": "ok",
                    "sub": f"Segmente: {len(plan.get('segments') or [])} | Luecken: {len(plan.get('gaps') or [])}",
                })
                jump_unique: dict[str, dict[str, Any]] = {}
                for sp in used_jump_spans:
                    if not isinstance(sp, dict):
                        continue
                    k = f"{str(sp.get('start') or '')}|{str(sp.get('stop') or '')}|{str(sp.get('delta') or '')}"
                    jump_unique[k] = sp
                merged_jump_spans = list(jump_unique.values())
                payload = {
                    "ok": True,
                    "rows": merged_rows,
                    "query": "cache-partial-merge",
                    "meta": {
                        "mode": "manual" if detail_mode == "manual" else "dynamic",
                        "returned": len(merged_rows),
                        "unit": unit,
                        "total_points": total_points_acc,
                        "jump_spans": merged_jump_spans,
                        "outlier_count": len(merged_jump_spans),
                        "covered_start": _dt_to_rfc3339_utc(req_start),
                        "covered_stop": _dt_to_rfc3339_utc(req_stop),
                        "cache_strategy": "partial_merge",
                        "query_ms_original": gap_query_ms,
                        "source_cache_ids": [x for x in source_cache_ids if x],
                    },
                }
                t_s0 = time.perf_counter()
                stored_meta = _dash_cache_store(cache_id, key, payload, trigger_page="dashboard")
                s_ms = int((time.perf_counter() - t_s0) * 1000)
                try:
                    _cache_usage_append(cfg, {
                        "kind": "dash_cache_partial_merge",
                        "page": "dashboard",
                        "run_id": run_id,
                        "cache_id": cache_id,
                        "step": "merge",
                        "dur_ms": merge_ms + s_ms,
                        "rows": len(merged_rows),
                        "series_key": series_key,
                        "requested_span_s": requested_span_s,
                        "note": f"segments={len(source_cache_ids)} gaps={len(plan.get('gaps') or [])}",
                    })
                except Exception:
                    pass
                try:
                    if cache_id:
                        _dash_last_set_from_query(body, cache_id, key)
                except Exception:
                    pass
                payload["cached"] = True
                payload["cache"] = {
                    "id": cache_id,
                    "updated_at": stored_meta.get("updated_at") if isinstance(stored_meta, dict) else _utc_now_iso_ms(),
                    "strategy": "partial_merge",
                }
                savings_ms = plan.get("estimated_savings_ms")
                if savings_ms is not None:
                    cache_steps.append({
                        "label": "Geschaetzte Zeitersparnis",
                        "status": "ok",
                        "sub": f"ca. {int(savings_ms)}ms gegenueber Vollabfrage",
                    })
                payload["cache_plan"] = {
                    "strategy": "partial_merge",
                    "segments_used": len(source_cache_ids),
                    "gaps_loaded": len(plan.get("gaps") or []),
                    "steps": cache_steps,
                    "estimated_savings_ms": savings_ms,
                    "changes": plan.get("changes") or [],
                }
                return jsonify(payload)
        except Exception:
            pass

    try:
        t_db0 = time.perf_counter()
        payload = _query_payload(
            cfg,
            measurement,
            field,
            range_key,
            str(entity_id) if entity_id else None,
            str(friendly_name) if friendly_name else None,
            unit,
            detail_mode,
            manual_density_pct,
            start_dt,
            stop_dt,
        )
        db_ms = int((time.perf_counter() - t_db0) * 1000)
        try:
            _cache_usage_append(cfg, {
                "kind": "dash_db_query",
                "page": "dashboard",
                "run_id": run_id,
                "cache_id": cache_id,
                "step": "_query_payload",
                "dur_ms": db_ms,
                "rows": len(payload.get("rows") or []) if isinstance(payload.get("rows"), list) else None,
                "series_key": series_key,
                "requested_span_s": requested_span_s,
                "note": f"range={range_key} detail={detail_mode}",
            })
        except Exception:
            pass
        try:
            if isinstance(payload.get("meta"), dict):
                payload["meta"]["query_ms_original"] = db_ms
                payload["meta"].setdefault("cache_strategy", "fresh_query")
        except Exception:
            pass
        if cache_id and key and bool(cfg.get("dash_cache_enabled", True)):
            t_s0 = time.perf_counter()
            stored_meta = _dash_cache_store(cache_id, key, payload, trigger_page="dashboard")
            s_ms = int((time.perf_counter() - t_s0) * 1000)
            try:
                _cache_usage_append(cfg, {
                    "kind": "dash_cache_store",
                    "page": "dashboard",
                    "run_id": run_id,
                    "cache_id": cache_id,
                    "step": "store",
                    "dur_ms": s_ms,
                    "rows": stored_meta.get("row_count") if isinstance(stored_meta, dict) else None,
                    "bytes": stored_meta.get("bytes") if isinstance(stored_meta, dict) else None,
                    "series_key": series_key,
                    "requested_span_s": requested_span_s,
                    "note": f"range={range_key}",
                })
            except Exception:
                pass
            payload = dict(payload)
            payload["cached"] = False
            payload["cache"] = {"id": cache_id, "updated_at": _utc_now_iso_ms(), "strategy": "fresh_query"}
            payload["cache_plan"] = {
                "strategy": "fresh_query",
                "segments_used": 0,
                "gaps_loaded": 1,
                "steps": [{"label": "Datenbankabfrage ausgefuehrt", "status": "ok", "sub": f"{db_ms}ms"}],
                "estimated_savings_ms": None,
            }

        try:
            if cache_id:
                _dash_last_set_from_query(body, cache_id, key)
        except Exception:
            pass
        dur_ms = int((time.monotonic() - t0) * 1000)
        row_count = len(payload.get("rows") or [])
        LOG.info("api.query done from=%s rows=%d dur=%dms", request.remote_addr, row_count, dur_ms)
        return jsonify(payload)
    except _ApiError as e:
        dur_ms = int((time.monotonic() - t0) * 1000)
        LOG.error("api.query api_error: %s dur=%dms", e.message, dur_ms)
        return jsonify({"ok": False, "error": e.message}), int(e.status)
    except Exception as e:
        dur_ms = int((time.monotonic() - t0) * 1000)
        LOG.error("api.query error: %s dur=%dms", e, dur_ms, exc_info=True)
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.get("/api/monitoring/config")
def api_monitoring_config_get():
    return jsonify({"ok": True, "config": _monitor_load_config()})


@app.post("/api/monitoring/config")
def api_monitoring_config_set():
    body = request.get_json(force=True) or {}
    try:
        cfg = _monitor_save_config(body if isinstance(body, dict) else {})
        return jsonify({"ok": True, "config": cfg})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 400


@app.post("/api/monitoring/evaluate")
def api_monitoring_evaluate():
    body = request.get_json(force=True) or {}
    try:
        result = _monitor_evaluate(body if isinstance(body, dict) else {})
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 400


@app.get("/api/monitoring/events")
def api_monitoring_events():
    q = str(request.args.get("q") or "").strip().lower()
    only = str(request.args.get("kind") or "").strip().lower()
    rows = _monitor_events_read(int(request.args.get("limit", "500")))
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if only and str(row.get("kind") or "").strip().lower() != only:
            continue
        txt = json.dumps(row, ensure_ascii=True).lower()
        if q and q not in txt:
            continue
        out.append(row)
    return jsonify({"ok": True, "rows": out, "total": len(out)})


@app.get("/api/monitoring/pending")
def api_monitoring_pending():
    q = str(request.args.get("q") or "").strip().lower()
    rows = [r for r in _monitor_load_pending() if isinstance(r, dict)]
    out = []
    for row in rows:
        if str(row.get("status") or "open") != "open":
            continue
        txt = json.dumps(row, ensure_ascii=True).lower()
        if q and q not in txt:
            continue
        out.append(row)
    return jsonify({"ok": True, "rows": out, "total": len(out)})


def _monitor_pending_apply_common(pending_id: str, action: str, manual_value: Any = None) -> dict[str, Any]:
    rows = _monitor_load_pending()
    hit = None
    for row in rows:
        if isinstance(row, dict) and str(row.get("id") or "") == pending_id:
            hit = row
            break
    if not hit:
        raise ValueError("pending item not found")
    if str(hit.get("status") or "open") != "open":
        raise ValueError("pending item already closed")

    key = str(hit.get("key") or "").strip()
    state_all = _monitor_load_state()
    state = state_all.get(key) if isinstance(state_all.get(key), dict) else {}

    if action == "manual":
        try:
            manual_num = float(manual_value)
        except Exception:
            raise ValueError("manual value invalid")
        if not math.isfinite(manual_num):
            raise ValueError("manual value invalid")
        state["last_corrected_value"] = manual_num
        hit["applied_value"] = manual_num
    elif action == "apply":
        state["last_corrected_value"] = hit.get("suggested_value")
        hit["applied_value"] = hit.get("suggested_value")
    elif action == "reject":
        hit["applied_value"] = None
    else:
        raise ValueError("invalid action")

    hit["status"] = "rejected" if action == "reject" else "applied"
    hit["closed_at"] = _utc_now_iso_ms()
    hit["closed_action"] = action
    state_all[key] = state
    _monitor_recount_pending(state_all, key)
    _monitor_save_state(state_all)
    _monitor_save_pending(rows)
    _monitor_event_append({
        "kind": "pending_" + action,
        "key": key,
        "label": hit.get("label") or key,
        "at": hit.get("closed_at"),
        "reason": hit.get("reason"),
        "reason_label": hit.get("reason_label"),
        "raw_value": hit.get("raw_value"),
        "corrected_value": hit.get("applied_value"),
        "correction_action": hit.get("suggested_action"),
        "correction_status": hit.get("status"),
    })
    return hit


@app.post("/api/monitoring/pending/apply")
def api_monitoring_pending_apply():
    body = request.get_json(force=True) or {}
    pending_id = str(body.get("id") or "").strip()
    manual = body.get("manual_value")
    action = "manual" if manual not in (None, "") else "apply"
    try:
        row = _monitor_pending_apply_common(pending_id, action, manual)
        return jsonify({"ok": True, "row": row})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 400


@app.post("/api/monitoring/pending/reject")
def api_monitoring_pending_reject():
    body = request.get_json(force=True) or {}
    pending_id = str(body.get("id") or "").strip()
    try:
        row = _monitor_pending_apply_common(pending_id, "reject")
        return jsonify({"ok": True, "row": row})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 400


@app.get("/api/monitoring/critical")
def api_monitoring_critical():
    snap = _monitor_template_snapshot()
    q = str(request.args.get("q") or "").strip().lower()
    rows = []
    for row in snap.get("critical", []):
        txt = json.dumps(row, ensure_ascii=True).lower()
        if q and q not in txt:
            continue
        rows.append(row)
    return jsonify({"ok": True, "rows": rows, "total": len(rows)})


@app.get("/api/monitoring/templates")
def api_monitoring_templates():
    snap = _monitor_template_snapshot()
    return jsonify({"ok": True, **snap})


@app.post("/api/raw_points")
def api_raw_points():
    """Fetch raw points directly from InfluxDB for a specific time window.

    Intended for the Dashboard "Raw Daten" table.
    """
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    mode_str = str(body.get("mode") or "").strip().lower() or "window"

    LOG.info("api.raw_points called from=%s measurement=%s field=%s mode=%s",
        request.remote_addr, measurement, field, mode_str)

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    t0 = time.monotonic()
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        LOG.error("api.raw_points parse_error: %s", e)
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    if not start_dt or not stop_dt:
        return jsonify({"ok": False, "error": "start and stop required"}), 400

    raw_max = int(cfg.get("ui_raw_max_points", 20000) or 20000)
    if raw_max < 1000:
        raw_max = 1000
    if raw_max > 200000:
        raw_max = 200000

    try:
        limit = int(body.get("limit", raw_max))
    except Exception:
        limit = raw_max
    if limit < 1:
        limit = 1
    if limit > raw_max:
        limit = raw_max

    try:
        offset = int(body.get("offset", 0))
    except Exception:
        offset = 0
    if offset < 0:
        offset = 0

    include_total = bool(body.get("include_total", True))

    mode = str(body.get("mode") or "").strip().lower() or "window"
    center_raw = str(body.get("anchor_time") or body.get("center_time") or "").strip() or None
    center_dt: datetime | None = None
    if center_raw:
        try:
            center_dt = _parse_iso_datetime(center_raw)
        except Exception:
            center_dt = None

    # Centered mode uses two-sided paging around a selected timestamp.
    if center_dt and start_dt and stop_dt:
        if center_dt < start_dt:
            center_dt = start_dt
        if center_dt > stop_dt:
            center_dt = stop_dt
        mode = "center"
    else:
        center_dt = None
        mode = "window"

    before_limit = None
    after_limit = None
    before_offset = 0
    after_offset = 0
    center_minutes = None
    center_window_multiplier = 1
    if mode == "center":
        try:
            center_minutes = int(body.get("center_minutes") or 0)
        except Exception:
            center_minutes = 0
        try:
            before_limit = int(body.get("before_limit") or 0)
        except Exception:
            before_limit = 0
        try:
            after_limit = int(body.get("after_limit") or 0)
        except Exception:
            after_limit = 0
        try:
            before_offset = int(body.get("before_offset") or 0)
        except Exception:
            before_offset = 0
        try:
            after_offset = int(body.get("after_offset") or 0)
        except Exception:
            after_offset = 0

        if before_offset < 0:
            before_offset = 0
        if after_offset < 0:
            after_offset = 0

        if center_minutes and center_minutes > 0:
            center_window_multiplier = max(1, int(math.ceil(float(center_minutes) / max(1.0, float(cfg.get("ui_raw_center_range_default", 100) or 100)))))
            before_limit = None
            after_limit = None
        else:
            total_want = limit
            if before_limit <= 0 and after_limit <= 0:
                before_limit = max(1, total_want // 2)
                after_limit = max(1, total_want - before_limit)
            if before_limit <= 0:
                before_limit = 1
            if after_limit <= 0:
                after_limit = 1
            if (before_limit + after_limit) > raw_max:
                half = max(1, raw_max // 2)
                before_limit = min(before_limit, half)
                after_limit = max(1, raw_max - before_limit)

    try:
        LOG.debug(
            "api.raw_points mode=%s measurement=%s field=%s entity_id=%s friendly_name=%s limit=%s offset=%s before_off=%s after_off=%s",
            mode,
            measurement,
            field,
            bool(entity_id),
            bool(friendly_name),
            limit,
            offset,
            before_offset,
            after_offset,
        )
    except Exception:
        pass

    try:
        if int(cfg.get("influx_version", 2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400

            start = _dt_to_rfc3339_utc(start_dt)
            stop = _dt_to_rfc3339_utc(stop_dt)
            extra = flux_tag_filter(entity_id, friendly_name)

            q = ""
            q2 = ""
            q_count = ""
            if mode == "center" and center_dt is not None and center_minutes and center_minutes > 0:
                q_start_dt = max(start_dt, center_dt - timedelta(minutes=center_minutes))
                q_stop_dt = min(stop_dt, center_dt + timedelta(minutes=center_minutes))
                q_start = _dt_to_rfc3339_utc(q_start_dt)
                q_stop = _dt_to_rfc3339_utc(q_stop_dt)
                q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{q_start}"), stop: time(v: "{q_stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
'''
                q2 = ""
            elif mode == "center" and center_dt is not None and before_limit is not None and after_limit is not None:
                center = _dt_to_rfc3339_utc(center_dt)
                q_older = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> filter(fn: (r) => r._time <= time(v: "{center}"))
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {before_limit}, offset: {before_offset})
'''
                q_newer = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> filter(fn: (r) => r._time > time(v: "{center}"))
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: {after_limit}, offset: {after_offset})
'''
                q = (q_older.strip() + "\n\n-- newer --\n\n" + q_newer.strip()).strip()
                q2 = q_newer.strip()
            else:
                q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: {limit}, offset: {offset})
'''

            q = log_query("api.raw_points (flux)", q)

            q_count = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_value"])
  |> group()
  |> count(column: "_value")
'''

            if include_total:
                q_count = log_query("api.raw_points (flux count)", q_count)

            rows: list[dict[str, Any]] = []
            total_count: int | None = None
            with v2_client(cfg) as c:
                qapi = c.query_api()
                before_returned = 0
                after_returned = 0
                if mode == "center" and center_dt is not None and center_minutes and center_minutes > 0:
                    q_start_dt = max(start_dt, center_dt - timedelta(minutes=center_minutes))
                    q_stop_dt = min(stop_dt, center_dt + timedelta(minutes=center_minutes))
                    q_start = _dt_to_rfc3339_utc(q_start_dt)
                    q_stop = _dt_to_rfc3339_utc(q_stop_dt)
                    q = log_query("api.raw_points (flux center_minutes)", q)
                    tables = qapi.query(q, org=cfg["org"])
                    for t in tables or []:
                        for r in getattr(t, "records", []) or []:
                            ts = r.get_time()
                            val = r.get_value()
                            if isinstance(ts, datetime):
                                rows.append({"time": _dt_to_rfc3339_utc_ms(ts), "value": val})
                    before_returned = len([r for r in rows if str(r.get("time") or "") <= _dt_to_rfc3339_utc_ms(center_dt)])
                    after_returned = max(0, len(rows) - before_returned)
                elif mode == "center" and center_dt is not None and before_limit is not None and after_limit is not None:
                    center = _dt_to_rfc3339_utc(center_dt)
                    extra2 = extra
                    q_older = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra2})
  |> filter(fn: (r) => r._time <= time(v: "{center}"))
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {before_limit}, offset: {before_offset})
'''
                    q_newer = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra2})
  |> filter(fn: (r) => r._time > time(v: "{center}"))
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: {after_limit}, offset: {after_offset})
'''
                    older: list[dict[str, Any]] = []
                    newer: list[dict[str, Any]] = []
                    q_older = log_query("api.raw_points (flux older)", q_older)
                    q_newer = log_query("api.raw_points (flux newer)", q_newer)
                    tables = qapi.query(q_older, org=cfg["org"])
                    for t in tables or []:
                        for r in getattr(t, "records", []) or []:
                            ts = r.get_time()
                            val = r.get_value()
                            if isinstance(ts, datetime):
                                older.append({"time": _dt_to_rfc3339_utc_ms(ts), "value": val})
                    tables = qapi.query(q_newer, org=cfg["org"])
                    for t in tables or []:
                        for r in getattr(t, "records", []) or []:
                            ts = r.get_time()
                            val = r.get_value()
                            if isinstance(ts, datetime):
                                newer.append({"time": _dt_to_rfc3339_utc_ms(ts), "value": val})
                    older.reverse()  # ascending
                    before_returned = len(older)
                    after_returned = len(newer)
                    rows = older + newer
                else:
                    tables = qapi.query(q, org=cfg["org"])
                    for t in tables or []:
                        for r in getattr(t, "records", []) or []:
                            ts = r.get_time()
                            val = r.get_value()
                            if isinstance(ts, datetime):
                                rows.append({"time": _dt_to_rfc3339_utc_ms(ts), "value": val})

                if include_total:
                    try:
                        tables = qapi.query(q_count, org=cfg["org"])
                        for t in tables or []:
                            for r in getattr(t, "records", []) or []:
                                v = r.get_value()
                                if v is not None:
                                    total_count = int(v)
                                    break
                            if total_count is not None:
                                break
                    except Exception:
                        total_count = None

            meta: dict[str, Any] = {
                "mode": mode,
                "start": start,
                "stop": stop,
                "limit": limit,
                "offset": offset,
                "returned": len(rows),
                "total_count": total_count,
                "query_language": "flux",
                "query": q.strip(),
                "query_count": q_count.strip() if include_total else None,
            }
            if mode == "center" and center_dt is not None and center_minutes and center_minutes > 0:
                meta.update({
                    "anchor_time": _dt_to_rfc3339_utc(center_dt),
                    "center_minutes": center_minutes,
                    "center_window_multiplier": center_window_multiplier,
                    "has_more_before": (center_dt - timedelta(minutes=center_minutes)) > start_dt,
                    "has_more_after": (center_dt + timedelta(minutes=center_minutes)) < stop_dt,
                })
            elif mode == "center" and center_dt is not None and before_limit is not None and after_limit is not None:
                meta.update({
                    "anchor_time": _dt_to_rfc3339_utc(center_dt),
                    "before_limit": before_limit,
                    "after_limit": after_limit,
                    "before_offset": before_offset,
                    "after_offset": after_offset,
                    "before_returned": before_returned,
                    "after_returned": after_returned,
                    "has_more_before": (before_returned == before_limit),
                    "has_more_after": (after_returned == after_limit),
                })
            try:
                _worklog_append_op(
                    purpose="raw",
                    op="raw_points",
                    status="ok",
                    detail=f"Raw-Punkte ({meta.get('mode')})",
                    measurement=str(measurement),
                    field=str(field),
                    entity_id=str(entity_id or ""),
                    friendly_name=str(friendly_name or ""),
                    window_start=str(meta.get("start") or ""),
                    window_stop=str(meta.get("stop") or ""),
                    source="db",
                    reason_code="raw_center" if str(meta.get("mode") or "") == "center" else "raw_window",
                    reason_label="Raw-Tabelle / Kontext um Ausreisser" if str(meta.get("mode") or "") == "center" else "Raw-Tabelle (Paging/Fenster)",
                    duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
                    counts={"rows": len(rows), "total_count": total_count},
                )
            except Exception:
                pass
            return jsonify({"ok": True, "rows": rows, "meta": meta})

        # v1
        if not cfg.get("database"):
            return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400

        c = v1_client(cfg)
        start = _dt_to_rfc3339_utc(start_dt)
        stop = _dt_to_rfc3339_utc(stop_dt)
        tag_where = influxql_tag_filter(entity_id, friendly_name)
        time_where = f"time >= '{start}' AND time <= '{stop}'"
        rows: list[dict[str, Any]] = []
        before_returned = 0
        after_returned = 0
        q = ""
        if mode == "center" and center_dt is not None and center_minutes and center_minutes > 0:
            q_start_dt = max(start_dt, center_dt - timedelta(minutes=center_minutes))
            q_stop_dt = min(stop_dt, center_dt + timedelta(minutes=center_minutes))
            q_start = _dt_to_rfc3339_utc(q_start_dt)
            q_stop = _dt_to_rfc3339_utc(q_stop_dt)
            q = f'SELECT "{field}" FROM "{measurement}" WHERE time >= \'{q_start}\' AND time <= \'{q_stop}\'{tag_where} ORDER BY time ASC'
            log_query("api.raw_points (influxql center_minutes)", q)
            res = c.query(q)
            for _, points in res.items():
                for p in points:
                    rows.append({"time": p.get("time"), "value": p.get(field)})
            before_returned = len([r for r in rows if str(r.get("time") or "") <= _dt_to_rfc3339_utc(center_dt)])
            after_returned = max(0, len(rows) - before_returned)
        elif mode == "center" and center_dt is not None and before_limit is not None and after_limit is not None:
            center = _dt_to_rfc3339_utc(center_dt)
            q_older = f'SELECT "{field}" FROM "{measurement}" WHERE {time_where}{tag_where} AND time <= \'{center}\' ORDER BY time DESC LIMIT {before_limit} OFFSET {before_offset}'
            q_newer = f'SELECT "{field}" FROM "{measurement}" WHERE {time_where}{tag_where} AND time > \'{center}\' ORDER BY time ASC LIMIT {after_limit} OFFSET {after_offset}'
            q = (q_older + "\n\n-- newer --\n\n" + q_newer).strip()
            log_query("api.raw_points (influxql older)", q_older)
            log_query("api.raw_points (influxql newer)", q_newer)
            res_o = c.query(q_older)
            older: list[dict[str, Any]] = []
            for _, points in res_o.items():
                for p in points:
                    older.append({"time": p.get("time"), "value": p.get(field)})
            res_n = c.query(q_newer)
            newer: list[dict[str, Any]] = []
            for _, points in res_n.items():
                for p in points:
                    newer.append({"time": p.get("time"), "value": p.get(field)})
            older.reverse()
            before_returned = len(older)
            after_returned = len(newer)
            rows = older + newer
        else:
            q = f'SELECT "{field}" FROM "{measurement}" WHERE {time_where}{tag_where} ORDER BY time ASC LIMIT {limit} OFFSET {offset}'
            log_query("api.raw_points (influxql)", q)
            res = c.query(q)
            for _, points in res.items():
                for p in points:
                    rows.append({"time": p.get("time"), "value": p.get(field)})

        total_count: int | None = None
        if include_total:
            try:
                q2 = f'SELECT COUNT("{field}") AS c FROM "{measurement}" WHERE {time_where}{tag_where}'
                log_query("api.raw_points (influxql count)", q2)
                res2 = c.query(q2)
                for _, points in res2.items():
                    for p in points:
                        v = p.get("c")
                        if v is not None:
                            total_count = int(v)
                            break
                    if total_count is not None:
                        break
            except Exception:
                total_count = None

        meta = {
            "mode": mode,
            "start": start,
            "stop": stop,
            "limit": limit,
            "offset": offset,
            "returned": len(rows),
            "total_count": total_count,
            "query_language": "influxql",
            "query": q,
            "query_count": q2 if include_total else None,
        }
        if mode == "center" and center_dt is not None and center_minutes and center_minutes > 0:
            meta.update({
                "anchor_time": _dt_to_rfc3339_utc(center_dt),
                "center_minutes": center_minutes,
                "center_window_multiplier": center_window_multiplier,
                "has_more_before": (center_dt - timedelta(minutes=center_minutes)) > start_dt,
                "has_more_after": (center_dt + timedelta(minutes=center_minutes)) < stop_dt,
            })
        elif mode == "center" and center_dt is not None and before_limit is not None and after_limit is not None:
            meta.update({
                "anchor_time": _dt_to_rfc3339_utc(center_dt),
                "before_limit": before_limit,
                "after_limit": after_limit,
                "before_offset": before_offset,
                "after_offset": after_offset,
                "before_returned": before_returned,
                "after_returned": after_returned,
                "has_more_before": (before_returned == before_limit),
                "has_more_after": (after_returned == after_limit),
            })
        try:
            _worklog_append_op(
                purpose="raw",
                op="raw_points",
                status="ok",
                detail=f"Raw-Punkte (v1 {mode})",
                measurement=str(measurement),
                field=str(field),
                entity_id=str(entity_id or ""),
                friendly_name=str(friendly_name or ""),
                window_start=str(start),
                window_stop=str(stop),
                source="db",
                reason_code="raw_center" if str(mode) == "center" else "raw_window",
                duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
                counts={"rows": len(rows)},
            )
        except Exception:
            pass
        return jsonify({"ok": True, "rows": rows, "meta": meta})

    except Exception as e:
        try:
            _worklog_append_op(
                purpose="raw",
                op="raw_points",
                status="err",
                detail=f"Raw-Punkte Fehler: {_short_influx_error(e)}",
                measurement=str(measurement),
                field=str(field),
                entity_id=str(entity_id or ""),
                friendly_name=str(friendly_name or ""),
                source="db",
                duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
            )
        except Exception:
            pass
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/raw_autotune")
def api_raw_autotune():
    """Server-side Auto-Tuning for UI `ui_raw_max_points`.

    Expects JSON body similar to /api/raw_points: measurement, field, start, stop, entity_id/friendly_name optional.
    Runs a small benchmark by issuing DB queries with varying limits and selects a `ui_raw_max_points` that keeps query time near a target.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}

    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    if not start_dt or not stop_dt:
        return jsonify({"ok": False, "error": "start and stop required"}), 400

    # tuning parameters (allow override)
    try:
        target_ms = int(body.get("target_ms", 1500))
    except Exception:
        target_ms = 1500
    try:
        step = int(body.get("step", 1000))
    except Exception:
        step = 1000
    try:
        min_pts = int(body.get("min_pts", 1000))
    except Exception:
        min_pts = 1000
    try:
        max_pts = int(body.get("max_pts", 200000))
    except Exception:
        max_pts = 200000

    # clamp sensible bounds
    min_pts = max(100, min_pts)
    max_pts = min(2000000, max_pts)
    step = max(1, abs(step))

    def _bench_v2(limit: int) -> float:
        # run a Flux query with limit and measure elapsed ms
        extra = flux_tag_filter(entity_id, friendly_name)
        start = _dt_to_rfc3339_utc(start_dt)
        stop = _dt_to_rfc3339_utc(stop_dt)
        q = f'''
from(bucket: "{cfg['bucket']}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: {limit})
'''
        t0 = time.perf_counter()
        with v2_client(cfg, timeout_seconds_override=max(5, int(cfg.get("timeout_seconds", 10)))) as c:
            try:
                # iterate through results to ensure query completes
                for _ in c.query_api().query_stream(q, org=cfg["org"]):
                    pass
            except Exception as e:
                raise
        return (time.perf_counter() - t0) * 1000.0

    def _bench_v1(limit: int) -> float:
        start = _dt_to_rfc3339_utc(start_dt)
        stop = _dt_to_rfc3339_utc(stop_dt)
        tag_where = influxql_tag_filter(entity_id, friendly_name)
        time_where = f"time >= '{start}' AND time <= '{stop}'"
        q = f'SELECT "{field}" FROM "{measurement}" WHERE {time_where}{tag_where} ORDER BY time ASC LIMIT {limit}'
        t0 = time.perf_counter()
        c = v1_client(cfg)
        try:
            res = c.query(q)
            # exhaust results
            for _, pts in res.items():
                for _ in pts:
                    pass
        finally:
            try:
                c.close()
            except Exception:
                pass
        return (time.perf_counter() - t0) * 1000.0

    try:
        # quick validation of connectivity
        if int(cfg.get("influx_version", 2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({"ok": False, "error": "InfluxDB v2 requires token/org/bucket"}), 400
            bench = _bench_v2
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database"}), 400
            bench = _bench_v1

        lo = max(min_pts, step * math.floor(min_pts / step))
        hi = max_pts - (max_pts % step)
        best = lo
        iter = 0
        last_ms = None
        while lo <= hi and iter < 12:
            mid = int(round((lo + hi) / (2.0 * step)) * step)
            mid = max(step, mid)
            try:
                ms = bench(mid)
            except Exception as e:
                # bench failed for this limit; reduce and continue
                hi = mid - step
                iter += 1
                continue
            last_ms = ms
            if ms <= target_ms:
                best = mid
                lo = mid + step
            else:
                hi = mid - step
            iter += 1

        # Persist the chosen value in runtime config
        cfg2 = load_cfg()
        cfg2["ui_raw_max_points"] = int(best)
        save_cfg(cfg2)
        return jsonify({"ok": True, "chosen": int(best), "measured_ms": float(last_ms or 0.0)})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/raw_overwrite")
def api_raw_overwrite():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    time_str = str(body.get("time") or "").strip()
    unit = str(body.get("unit") or "").strip()
    force_raw = body.get("force", False)
    force = force_raw is True or str(force_raw).strip().lower() in ("1", "true", "yes", "on")
    try:
        new_value = float(body.get("new_value"))
    except Exception:
        return jsonify({"ok": False, "error": "new_value must be a number"}), 400
    old_value = body.get("old_value")
    mode = str(body.get("mode") or "overwrite").strip()
    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400
    if not time_str:
        return jsonify({"ok": False, "error": "time required"}), 400
    try:
        ts = _parse_iso_datetime(time_str)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid time: {e}"}), 400
    try:
        if int(cfg.get("influx_version", 2)) == 2:
            extra = flux_tag_filter(entity_id, friendly_name)
            start = _dt_to_rfc3339_utc(ts - timedelta(seconds=1))
            stop = _dt_to_rfc3339_utc(ts + timedelta(seconds=1))
            q = f'''
from(bucket: "{cfg['bucket']}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: 5)
'''
            with v2_client(cfg) as c:
                tables = c.query_api().query(q, org=cfg["org"])
                existing = []
                for table in tables:
                    for rec in table.records:
                        existing.append(rec)
                if not existing:
                    return jsonify({"ok": False, "error": "Zeitpunkt nicht in DB gefunden"}), 404

                # Outlier rule guardrails (can be overridden via force=true)
                try:
                    best_rec = None
                    best_abs = None
                    for rec in existing:
                        rdt = rec.get_time()
                        if not isinstance(rdt, datetime):
                            continue
                        delta = abs((rdt.astimezone(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds())
                        if best_abs is None or delta < best_abs:
                            best_abs = delta
                            best_rec = rec
                    # Use the best record timestamp for neighbor context.
                    ts_eff = best_rec.get_time().astimezone(timezone.utc) if best_rec else ts.astimezone(timezone.utc)
                    chk = _check_outlier_edit_rules(cfg, measurement, field, entity_id, friendly_name, ts_eff, new_value, unit)
                    viol = chk.get("violations") or []
                    if viol and not force:
                        return (
                            jsonify({
                                "ok": False,
                                "error": "Outlier-Regel verletzt. Schreiben blockiert.",
                                "violations": viol,
                                "meta": chk.get("meta") or {},
                                "can_force": True,
                            }),
                            409,
                        )
                except Exception:
                    pass

                wapi = c.write_api(write_options=SYNCHRONOUS)
                point = Point(measurement).field(field, new_value).time(ts)
                if entity_id:
                    point = point.tag("entity_id", entity_id)
                if friendly_name:
                    point = point.tag("friendly_name", friendly_name)
                wapi.write(cfg["bucket"], cfg["org"], point)
                wapi.close()
        else:
            start = _dt_to_rfc3339_utc(ts - timedelta(seconds=1))
            stop = _dt_to_rfc3339_utc(ts + timedelta(seconds=1))
            tag_where = influxql_tag_filter(entity_id, friendly_name)
            q = f'SELECT "{field}" FROM "{measurement}" WHERE time >= \'{start}\' AND time <= \'{stop}\'{tag_where} ORDER BY time ASC LIMIT 5'
            c = v1_client(cfg)
            try:
                res = c.query(q)
                existing = []
                for _, pts in res.items():
                    existing.extend(pts)
                if not existing:
                    return jsonify({"ok": False, "error": "Zeitpunkt nicht in DB gefunden"}), 404

                # Outlier rule guardrails (can be overridden via force=true)
                try:
                    chk = _check_outlier_edit_rules(cfg, measurement, field, entity_id, friendly_name, ts, new_value, unit)
                    viol = chk.get("violations") or []
                    if viol and not force:
                        return (
                            jsonify({
                                "ok": False,
                                "error": "Outlier-Regel verletzt. Schreiben blockiert.",
                                "violations": viol,
                                "meta": chk.get("meta") or {},
                                "can_force": True,
                            }),
                            409,
                        )
                except Exception:
                    pass
                tags = {}
                if entity_id:
                    tags["entity_id"] = entity_id
                if friendly_name:
                    tags["friendly_name"] = friendly_name
                json_body = {"measurement": measurement, "tags": tags, "time": _dt_to_rfc3339_utc(ts), "fields": {field: new_value}}
                c.write_points([json_body])
            finally:
                try:
                    c.close()
                except Exception:
                    pass
        _history_append({
            "kind": "change",
            "series": {
                "measurement": measurement,
                "field": field,
                "entity_id": entity_id,
                "friendly_name": friendly_name,
                "tags": {"entity_id": entity_id, "friendly_name": friendly_name},
            },
            "time": time_str,
            "action": "overwrite",
            "old_value": old_value,
            "new_value": new_value,
            "reason": (f"{mode} [FORCED]" if force else (mode or "manual")),
            "ip": _req_ip(),
            "ua": _req_ua(),
        })
        _dash_cache_mark_dirty_series(measurement, field, entity_id, friendly_name, "raw_overwrite")
        _stats_cache_mark_dirty_series(measurement, field, entity_id, friendly_name, "raw_overwrite")
        patch_job_id = _analysis_cache_mark_dirty_series(cfg, measurement, field, entity_id, friendly_name, "raw_overwrite")
        return jsonify({"ok": True, "patch_job_id": patch_job_id})
    except Exception as e:
        LOG.error("api.raw_overwrite error: %s", e, exc_info=True)
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/window_points")
def api_window_points():
    """Return time/value points for a given window, optionally downsampled."""
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    start_str = body.get("start", "")
    stop_str = body.get("stop", "")

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    t0 = time.monotonic()
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        LOG.error("api.window_points parse_error: %s", e)
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    if not start_dt or not stop_dt:
        return jsonify({"ok": False, "error": "start and stop required"}), 400

    try:
        max_points = int(body.get("max_points") or cfg.get("ui_edit_graph_max_points") or 50000)
    except Exception:
        max_points = int(cfg.get("ui_edit_graph_max_points") or 50000)
    # Allow small requests (e.g. pixel-bound previews); callers can still request higher.
    if max_points < 50:
        max_points = 50
    if max_points > 200000:
        max_points = 200000

    # Downsample aggregation function (no averages for UI previews).
    agg_fn = str(body.get("agg_fn") or "max").strip().lower()
    if agg_fn not in ("max", "min"):
        agg_fn = "max"

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "window_points currently supports InfluxDB v2 only"}), 400

    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    extra = flux_tag_filter(entity_id, friendly_name)
    dur_ms = max(0.0, (stop_dt - start_dt).total_seconds() * 1000.0)
    every_ms = int(math.ceil(dur_ms / float(max_points))) if dur_ms > 0 else 1
    if every_ms < 1:
        every_ms = 1

    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)

    # If the window is dense, downsample via aggregateWindow.
    agg = ""
    mode = "raw"
    if every_ms > 1:
        agg = f'  |> aggregateWindow(every: {every_ms}ms, fn: {agg_fn}, createEmpty: false)\n'
        mode = f"downsample_{agg_fn}"

    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
{agg}  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: {max_points})
'''

    try:
        q = log_query("api.window_points (flux)", q)
        rows: list[dict[str, Any]] = []
        with v2_client(cfg) as c:
            tables = c.query_api().query(q, org=cfg["org"])
            for t in tables or []:
                for r in getattr(t, "records", []) or []:
                    ts = r.get_time()
                    val = r.get_value()
                    if isinstance(ts, datetime):
                        rows.append({"time": _dt_to_rfc3339_utc_ms(ts), "value": val})
        dur = int((time.monotonic() - t0) * 1000)
        LOG.info("api.window_points done from=%s measurement=%s mode=%s rows=%d dur=%dms",
            request.remote_addr, measurement, mode, len(rows), dur)
        return jsonify({
            "ok": True,
            "rows": rows,
            "meta": {
                "mode": mode,
                "every_ms": every_ms,
                "max_points": max_points,
                "agg_fn": agg_fn,
                "query_language": "flux",
                "query": q,
            },
        })
    except Exception as e:
        dur = int((time.monotonic() - t0) * 1000)
        LOG.error("api.window_points error: %s dur=%dms", e, dur, exc_info=True)
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/point_neighbors")
def api_point_neighbors():
    """Return n points before/after a given center time within a time window."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "neighbors currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    center_raw = str(body.get("center_time") or "").strip()

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400
    if not center_raw:
        return jsonify({"ok": False, "error": "center_time required"}), 400

    try:
        center_dt = _parse_iso_datetime(center_raw)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid center_time: {e}"}), 400

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    if not start_dt or not stop_dt:
        return jsonify({"ok": False, "error": "start and stop required"}), 400

    try:
        n = int(body.get("n", 5))
    except Exception:
        n = 5
    if n < 1:
        n = 1
    if n > 50:
        n = 50

    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    center = _dt_to_rfc3339_utc(center_dt)
    extra = flux_tag_filter(entity_id, friendly_name)

    q_older = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> filter(fn: (r) => r._time < time(v: "{center}"))
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {n})
'''

    q_newer = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> filter(fn: (r) => r._time > time(v: "{center}"))
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: {n})
'''

    older: list[dict[str, Any]] = []
    newer: list[dict[str, Any]] = []
    q_older = log_query("api.point_neighbors (flux older)", q_older)
    q_newer = log_query("api.point_neighbors (flux newer)", q_newer)
    try:
        with v2_client(cfg) as c:
            qapi = c.query_api()
            tables = qapi.query(q_older, org=cfg["org"])
            for t in tables or []:
                for r in getattr(t, "records", []) or []:
                    ts = r.get_time()
                    val = r.get_value()
                    if isinstance(ts, datetime):
                        older.append({"time": _dt_to_rfc3339_utc_ms(ts), "value": val})
            tables = qapi.query(q_newer, org=cfg["org"])
            for t in tables or []:
                for r in getattr(t, "records", []) or []:
                    ts = r.get_time()
                    val = r.get_value()
                    if isinstance(ts, datetime):
                        newer.append({"time": _dt_to_rfc3339_utc_ms(ts), "value": val})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

    older.reverse()  # ascending: oldest -> closest
    return jsonify({"ok": True, "older": older, "newer": newer, "n": n})


def _series_stats_total_cache_key(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
) -> dict[str, Any]:
    # Never persist secrets; cfg_fp is a stable fingerprint without tokens.
    return {
        "kind": "series_stats_total",
        "measurement": str(measurement or "").strip(),
        "field": str(field or "").strip(),
        "entity_id": str(entity_id or "").strip() or "",
        "friendly_name": str(friendly_name or "").strip() or "",
        "cfg_fp": _stats_cache_cfg_fp(cfg),
    }


def _stats_total_merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Merge two per-range stats dicts into a combined total."""

    def _num(v: object) -> float | None:
        try:
            if isinstance(v, bool):
                return None
            if isinstance(v, (int, float)):
                return float(v)
            return float(str(v))
        except Exception:
            return None

    def _dt(iso: object) -> datetime | None:
        try:
            return _parse_iso_datetime(str(iso or ""))
        except Exception:
            return None

    out = dict(a or {})
    ca = int(a.get("count") or 0) if isinstance(a, dict) else 0
    cb = int(b.get("count") or 0) if isinstance(b, dict) else 0
    out["count"] = int(max(0, ca + cb))

    # oldest/newest + first/last
    a_old = _dt((a or {}).get("oldest_time"))
    b_old = _dt((b or {}).get("oldest_time"))
    a_new = _dt((a or {}).get("newest_time"))
    b_new = _dt((b or {}).get("newest_time"))

    if b_old and (not a_old or b_old < a_old):
        out["oldest_time"] = (b or {}).get("oldest_time")
        out["first_value"] = (b or {}).get("first_value")
    if b_new and (not a_new or b_new > a_new):
        out["newest_time"] = (b or {}).get("newest_time")
        out["last_value"] = (b or {}).get("last_value")

    # numeric aggregation via sum
    sa = _num((a or {}).get("_sum"))
    sb = _num((b or {}).get("_sum"))
    if sa is not None and sb is not None and out["count"] > 0:
        s = sa + sb
        out["_sum"] = s
        out["mean"] = s / max(1, out["count"])
        a_min = _num((a or {}).get("min"))
        b_min = _num((b or {}).get("min"))
        a_max = _num((a or {}).get("max"))
        b_max = _num((b or {}).get("max"))
        if b_min is not None and (a_min is None or b_min < a_min):
            out["min"] = b_min
        if b_max is not None and (a_max is None or b_max > a_max):
            out["max"] = b_max
    else:
        # keep existing numeric fields if we can't safely aggregate
        out.pop("_sum", None)

    return out


def _stats_total_compute_v2(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    start_dt: datetime | None,
    stop_dt: datetime | None,
) -> dict[str, Any]:
    extra = flux_tag_filter(entity_id, friendly_name)
    if start_dt is None:
        range_clause = '|> range(start: time(v: "1970-01-01T00:00:00Z"))'
    else:
        s = _dt_to_rfc3339_utc_ms(start_dt)
        e = _dt_to_rfc3339_utc_ms(stop_dt or datetime.now(timezone.utc))
        range_clause = f'|> range(start: time(v: "{s}"), stop: time(v: "{e}"))'

    base_flux = f'''
data = from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time", "_value"])
  |> group()
'''

    def _q_one(suffix: str) -> str:
        return (base_flux + "\n" + suffix).strip() + "\n"

    def _first_record(tables):
        for t in tables or []:
            for rec in getattr(t, "records", []) or []:
                return rec
        return None

    out: dict[str, Any] = {
        "count": 0,
        "oldest_time": None,
        "newest_time": None,
        "first_value": None,
        "last_value": None,
        "min": None,
        "max": None,
        "mean": None,
        "_sum": None,
    }

    with v2_client(cfg) as c:
        qapi = c.query_api()

        # count
        q_count = _q_one("data |> count() |> limit(n:1)")
        log_query("api.stats (flux count)", q_count)
        tables = qapi.query(q_count, org=cfg["org"])
        rec = _first_record(tables)
        if rec is not None:
            try:
                out["count"] = int(rec.get_value() or 0)
            except Exception:
                out["count"] = 0

        if out["count"] > 0:
            # oldest/newest (+ first/last values)
            q_first = _q_one("data |> first()")
            q_last = _q_one("data |> last()")
            log_query("api.stats (flux first)", q_first)
            log_query("api.stats (flux last)", q_last)

            tables = qapi.query(q_first, org=cfg["org"])
            rec = _first_record(tables)
            if rec is not None:
                ts = rec.get_time()
                out["oldest_time"] = _dt_to_rfc3339_utc_ms(ts) if isinstance(ts, datetime) else ts
                out["first_value"] = rec.get_value()

            tables = qapi.query(q_last, org=cfg["org"])
            rec = _first_record(tables)
            if rec is not None:
                ts = rec.get_time()
                out["newest_time"] = _dt_to_rfc3339_utc_ms(ts) if isinstance(ts, datetime) else ts
                out["last_value"] = rec.get_value()

            # Numeric-only aggregates (sum/min/max). mean derived from sum/count.
            lv = out.get("last_value")
            is_num = isinstance(lv, (int, float)) and not isinstance(lv, bool)
            if is_num:
                try:
                    q_sum = _q_one("data |> sum() |> limit(n:1)")
                    log_query("api.stats (flux sum)", q_sum)
                    tables = qapi.query(q_sum, org=cfg["org"])
                    rec = _first_record(tables)
                    if rec is not None:
                        out["_sum"] = rec.get_value()
                except Exception:
                    pass

                for nm, tail in (
                    ("min", "data |> min() |> limit(n:1)"),
                    ("max", "data |> max() |> limit(n:1)"),
                ):
                    try:
                        qx = _q_one(tail)
                        log_query(f"api.stats (flux {nm})", qx)
                        tables = qapi.query(qx, org=cfg["org"])
                        rec = _first_record(tables)
                        if rec is not None:
                            out[nm] = rec.get_value()
                    except Exception:
                        continue

                try:
                    if out.get("_sum") is not None and out["count"] > 0:
                        out["mean"] = float(out.get("_sum") or 0.0) / max(1, int(out["count"] or 0))
                except Exception:
                    pass

    return out


def _stats_total_cached_v2(
    cfg: dict[str, Any],
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
) -> dict[str, Any]:
    key = _series_stats_total_cache_key(cfg, measurement, field, entity_id, friendly_name)
    cache_id = _series_stats_cache_id(key)
    meta = _series_stats_cache_load_meta(cache_id)
    payload = _series_stats_cache_load_payload(cache_id)

    def _clean(stats: dict[str, Any]) -> dict[str, Any]:
        out = dict(stats or {})
        out.pop("_sum", None)
        return out

    # Cache hit path
    if isinstance(meta, dict) and isinstance(payload, dict):
        try:
            if meta.get("dirty") or meta.get("mismatch"):
                raise ValueError("dirty")
            if str((meta.get("key") or {}).get("cfg_fp") or "") != str(key.get("cfg_fp") or ""):
                raise ValueError("cfg mismatch")
            stats0 = payload.get("stats")
            if not isinstance(stats0, dict):
                raise ValueError("bad payload")

            cov_stop = payload.get("covered_stop") or stats0.get("newest_time")
            cov_dt = _parse_iso_datetime(str(cov_stop or "")) if cov_stop else None
            if cov_dt is None:
                raise ValueError("no covered_stop")

            # Query delta since covered_stop (exclusive, +1ms).
            delta_start = cov_dt + timedelta(milliseconds=1)
            delta = _stats_total_compute_v2(cfg, measurement, field, entity_id, friendly_name, delta_start, None)
            if int(delta.get("count") or 0) <= 0:
                _series_stats_cache_touch_used(cache_id)
                return {"ok": True, "stats": _clean(stats0), "cached": True}

            merged = _stats_total_merge(stats0, delta)
            now_iso = _utc_now_iso_ms()
            payload2 = {
                "key": key,
                "stats": merged,
                "covered_start": merged.get("oldest_time") or payload.get("covered_start"),
                "covered_stop": merged.get("newest_time") or now_iso,
                "updated_at": now_iso,
            }
            bytes_n = _series_stats_cache_write_payload(cache_id, payload2)
            meta2 = dict(meta)
            meta2["dirty"] = False
            meta2["dirty_reason"] = ""
            meta2["dirty_at"] = ""
            meta2["updated_at"] = now_iso
            meta2["last_used_at"] = now_iso
            meta2["bytes"] = bytes_n
            _series_stats_cache_write_meta(meta2)
            return {"ok": True, "stats": _clean(merged), "cached": True}
        except Exception:
            pass

    # Full compute
    stats = _stats_total_compute_v2(cfg, measurement, field, entity_id, friendly_name, None, None)
    now_iso = _utc_now_iso_ms()
    payload2 = {
        "key": key,
        "stats": stats,
        "covered_start": stats.get("oldest_time"),
        "covered_stop": stats.get("newest_time") or now_iso,
        "updated_at": now_iso,
    }
    bytes_n = _series_stats_cache_write_payload(cache_id, payload2)
    meta2 = {
        "id": cache_id,
        "key": key,
        "dirty": False,
        "dirty_reason": "",
        "dirty_at": "",
        "updated_at": now_iso,
        "last_used_at": now_iso,
        "bytes": bytes_n,
    }
    _series_stats_cache_write_meta(meta2)
    return {"ok": True, "stats": _clean(stats), "cached": False}

@app.post("/api/stats")
def stats():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = body.get("measurement", "")
    field = body.get("field", "")
    range_key = body.get("range", "24h")
    entity_id = body.get("entity_id") or None
    friendly_name = body.get("friendly_name") or None

    stats_scope = (body.get("stats_scope") or "current").strip().lower()
    start_dt: datetime | None = None
    stop_dt: datetime | None = None
    if stats_scope in ("current", "range"):
        try:
            start_dt, stop_dt = _get_start_stop_from_payload(body)
        except Exception as e:
            return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    t0 = time.monotonic()

    try:
        LOG.debug(
            "api.stats measurement=%s field=%s scope=%s range=%s entity_id=%s friendly_name=%s",
            measurement,
            field,
            stats_scope,
            range_key,
            bool(entity_id),
            bool(friendly_name),
        )
    except Exception:
        pass

    try:
        if int(cfg.get("influx_version",2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400

            # Total stats can be expensive; use incremental per-series cache.
            if stats_scope in ("inf", "infinite", "all"):
                try:
                    res = _stats_total_cached_v2(cfg, measurement, field, entity_id, friendly_name)
                    try:
                        _worklog_append_op(
                            purpose="stats",
                            op="total",
                            status="ok",
                            detail=f"Total-Stats (scope={stats_scope}) {'cache' if res.get('cached') else 'db'}",
                            measurement=str(measurement),
                            field=str(field),
                            entity_id=str(entity_id or ""),
                            friendly_name=str(friendly_name or ""),
                            window_start=str((res.get('stats') or {}).get('oldest_time') or ""),
                            window_stop=str((res.get('stats') or {}).get('newest_time') or ""),
                            source="cache" if res.get("cached") else "db",
                            reason_code="stats_scope_inf",
                            reason_label="Gesamtstatistik (all-time) angefordert.",
                            duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
                        )
                    except Exception:
                        pass
                    return jsonify({"ok": True, "stats": res.get("stats") or {}, "stats_scope": stats_scope, "cached": bool(res.get("cached"))})
                except Exception as e:
                    try:
                        _worklog_append_op(
                            purpose="stats",
                            op="total",
                            status="err",
                            detail=f"Total-Stats fehlgeschlagen: {_short_influx_error(e)}",
                            measurement=str(measurement),
                            field=str(field),
                            entity_id=str(entity_id or ""),
                            friendly_name=str(friendly_name or ""),
                            source="db",
                            reason_code="stats_scope_inf",
                            duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
                        )
                    except Exception:
                        pass
                    return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

            extra = flux_tag_filter(entity_id, friendly_name)
            range_clause = _flux_range_clause_for_scope(stats_scope, range_key, start_dt, stop_dt)

            def _is_number(v: object) -> bool:
                return isinstance(v, (int, float)) and not isinstance(v, bool)

            # Avoid Flux `union` schema collisions (e.g. count int vs values float) by querying stats separately.
            base_flux = f'''
data = from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time", "_value"])
  |> group()
'''

            log_query("api.stats (flux base)", base_flux)

            def _q_one(suffix: str) -> str:
                return (base_flux + "\n" + suffix).strip() + "\n"

            def _first_record(tables):
                for t in tables or []:
                    for rec in getattr(t, "records", []) or []:
                        return rec
                return None

            out = {
                "count": 0,
                "oldest_time": None,
                "newest_time": None,
                "first_value": None,
                "last_value": None,
                "min": None,
                "max": None,
                "mean": None,
                "stddev": None,
                "p05": None,
                "p50": None,
                "p95": None,
            }

            with v2_client(cfg) as c:
                # count
                try:
                    q_count = _q_one("data |> count() |> limit(n:1)")
                    log_query("api.stats (flux count)", q_count)
                    tables = c.query_api().query(q_count, org=cfg["org"])
                    rec = _first_record(tables)
                    if rec is not None:
                        out["count"] = int(rec.get_value() or 0)
                except Exception:
                    pass

                # oldest/newest (+ first/last values)
                try:
                    q_old = _q_one('data |> first()')
                    log_query("api.stats (flux first)", q_old)
                    tables = c.query_api().query(q_old, org=cfg["org"])
                    rec = _first_record(tables)
                    if rec is not None:
                        ts = rec.get_time()
                        out["oldest_time"] = ts.astimezone(timezone.utc).isoformat() if isinstance(ts, datetime) else ts
                        out["first_value"] = rec.get_value()
                except Exception:
                    pass

                try:
                    q_new = _q_one('data |> last()')
                    log_query("api.stats (flux last)", q_new)
                    tables = c.query_api().query(q_new, org=cfg["org"])
                    rec = _first_record(tables)
                    if rec is not None:
                        ts = rec.get_time()
                        out["newest_time"] = ts.astimezone(timezone.utc).isoformat() if isinstance(ts, datetime) else ts
                        out["last_value"] = rec.get_value()
                except Exception:
                    pass

                # Numeric-only aggregates (best-effort)
                if _is_number(out.get("last_value")) and out["count"] > 0:
                    def _try_stat(name: str, flux_tail: str) -> None:
                        try:
                            qx = _q_one(flux_tail)
                            log_query(f"api.stats (flux {name})", qx)
                            tables = c.query_api().query(qx, org=cfg["org"])
                            rec = _first_record(tables)
                            if rec is not None:
                                out[name] = rec.get_value()
                        except Exception:
                            return

                    _try_stat("min", "data |> min() |> limit(n:1)")
                    _try_stat("max", "data |> max() |> limit(n:1)")
                    _try_stat("mean", "data |> mean() |> limit(n:1)")

            try:
                ws = _dt_to_rfc3339_utc(start_dt) if start_dt else ""
                we = _dt_to_rfc3339_utc(stop_dt) if stop_dt else ""
            except Exception:
                ws = ""
                we = ""
            try:
                _worklog_append_op(
                    purpose="stats",
                    op="range",
                    status="ok",
                    detail=f"Range-Stats (scope={stats_scope}, range={range_key})",
                    measurement=str(measurement),
                    field=str(field),
                    entity_id=str(entity_id or ""),
                    friendly_name=str(friendly_name or ""),
                    window_start=ws,
                    window_stop=we,
                    source="db",
                    reason_code="stats_scope_range",
                    reason_label="Statistik fuer aktuellen Zeitraum.",
                    duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
                )
            except Exception:
                pass
            return jsonify({"ok": True, "stats": out, "stats_scope": stats_scope})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            c = v1_client(cfg)
            tag_where = influxql_tag_filter(entity_id, friendly_name)
            time_where = _influxql_time_where_for_scope(stats_scope, range_key, start_dt, stop_dt)

            where_clause = f"WHERE {time_where}{tag_where}"
            out = {
                "count": 0,
                "oldest_time": None,
                "newest_time": None,
                "first_value": None,
                "last_value": None,
                "min": None,
                "max": None,
                "mean": None,
                "stddev": None,
                "p05": None,
                "p50": None,
                "p95": None,
            }

            # Count
            q_count = f'SELECT COUNT("{field}") as count FROM "{measurement}" {where_clause}'
            log_query("api.stats (influxql count)", q_count)
            res = c.query(q_count)
            for _, points in res.items():
                if points:
                    out["count"] = int(points[0].get("count") or 0)
                    break

            # Oldest/newest timestamps + values
            q_first = f'SELECT FIRST("{field}") FROM "{measurement}" {where_clause}'
            q_last = f'SELECT LAST("{field}") FROM "{measurement}" {where_clause}'
            log_query("api.stats (influxql first)", q_first)
            log_query("api.stats (influxql last)", q_last)
            ro = c.query(q_first)
            rn = c.query(q_last)
            for _, pts in ro.items():
                if pts:
                    out["oldest_time"] = pts[0].get("time")
                    out["first_value"] = pts[0].get("first") if "first" in pts[0] else pts[0].get(field)
                    break
            for _, pts in rn.items():
                if pts:
                    out["newest_time"] = pts[0].get("time")
                    out["last_value"] = pts[0].get("last") if "last" in pts[0] else pts[0].get(field)
                    break

            def _is_number(v: object) -> bool:
                return isinstance(v, (int, float)) and not isinstance(v, bool)

            # Numeric-only aggregates (best-effort)
            if _is_number(out.get("last_value")) and out["count"] > 0:
                try:
                    q_num = (
                        f'SELECT MIN("{field}") as min, MAX("{field}") as max, MEAN("{field}") as mean '
                        f'FROM "{measurement}" {where_clause}'
                    )
                    log_query("api.stats (influxql numeric)", q_num)
                    res2 = c.query(q_num)
                    for _, points in res2.items():
                        if not points:
                            continue
                        p = points[0]
                        out["min"] = p.get("min")
                        out["max"] = p.get("max")
                        out["mean"] = p.get("mean")
                        break
                except Exception:
                    pass

            try:
                _worklog_append_op(
                    purpose="stats",
                    op="range",
                    status="ok",
                    detail=f"Range-Stats (v1 scope={stats_scope}, range={range_key})",
                    measurement=str(measurement),
                    field=str(field),
                    entity_id=str(entity_id or ""),
                    friendly_name=str(friendly_name or ""),
                    source="db",
                    reason_code="stats_scope_range",
                    duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
                )
            except Exception:
                pass
            return jsonify({"ok": True, "stats": out, "stats_scope": stats_scope})
    except Exception as e:
        try:
            _worklog_append_op(
                purpose="stats",
                op="range" if stats_scope not in ("inf", "infinite", "all") else "total",
                status="err",
                detail=f"/api/stats Fehler: {_short_influx_error(e)}",
                measurement=str(measurement),
                field=str(field),
                entity_id=str(entity_id or ""),
                friendly_name=str(friendly_name or ""),
                source="db",
                duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
            )
        except Exception:
            pass
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.get("/api/global_stats")
def global_stats():
    """Compute global stats per signal.

    NOTE: Potentially expensive on large buckets; call on demand.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    try:
        limit = int(request.args.get("limit", "3000"))
    except Exception:
        limit = 3000
    if limit < 1:
        limit = 1
    if limit > 20000:
        limit = 20000

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "global_stats currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    keys = '["_measurement","_field","entity_id","friendly_name"]'

    # Optional time window to reduce load
    start_q = (request.args.get("start") or "").strip()
    stop_q = (request.args.get("stop") or "").strip()
    if start_q and stop_q:
        try:
            start_dt = _parse_iso_datetime(start_q)
            stop_dt = _parse_iso_datetime(stop_q)
            start = f'time(v: "{_dt_to_rfc3339_utc(start_dt)}")'
            stop = f'time(v: "{_dt_to_rfc3339_utc(stop_dt)}")'
        except Exception:
            start = 'time(v: "1970-01-01T00:00:00Z")'
            stop = None
    else:
        # Default to last 30 days
        start = "-30d"
        stop = None

    range_clause = f"|> range(start: {start}{', stop: ' + stop if stop else ''})"
    q = f'''
base = from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => exists r._measurement and exists r._field)
  |> group(columns: {keys})

c = base
  |> count(column: "_value")
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_value"])
  |> rename(columns: {{_value: "count"}})

mn = base
  |> min(column: "_value")
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_value"])
  |> rename(columns: {{_value: "min"}})

mx = base
  |> max(column: "_value")
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_value"])
  |> rename(columns: {{_value: "max"}})

me = base
  |> mean(column: "_value")
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_value"])
  |> rename(columns: {{_value: "mean"}})

old = base
  |> sort(columns: ["_time"], desc: false)
  |> first()
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_time"])
  |> rename(columns: {{_time: "oldest_time"}})

nw = base
  |> sort(columns: ["_time"], desc: true)
  |> first()
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_time","_value"])
  |> rename(columns: {{_time: "newest_time", _value: "last_value"}})

j1 = join(tables: {{a: c, b: mn}}, on: ["_measurement","_field","entity_id","friendly_name"], method: "inner")
j2 = join(tables: {{a: j1, b: mx}}, on: ["_measurement","_field","entity_id","friendly_name"], method: "inner")
j3 = join(tables: {{a: j2, b: me}}, on: ["_measurement","_field","entity_id","friendly_name"], method: "inner")
j4 = join(tables: {{a: j3, b: old}}, on: ["_measurement","_field","entity_id","friendly_name"], method: "inner")
j5 = join(tables: {{a: j4, b: nw}}, on: ["_measurement","_field","entity_id","friendly_name"], method: "inner")

j5 |> group() |> limit(n: {limit})
'''

    def _iso(v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            return _dt_to_rfc3339_utc(v)
        return str(v)

    try:
        with v2_client(cfg) as c:
            tables = c.query_api().query(q, org=cfg["org"])
            rows: list[dict[str, Any]] = []
            for t in tables or []:
                for rec in getattr(t, "records", []) or []:
                    vals = getattr(rec, "values", {}) or {}
                    rows.append({
                        "measurement": vals.get("_measurement"),
                        "field": vals.get("_field"),
                        "entity_id": vals.get("entity_id") or "",
                        "friendly_name": vals.get("friendly_name") or "",
                        "count": vals.get("count"),
                        "oldest_time": _iso(vals.get("oldest_time")),
                        "newest_time": _iso(vals.get("newest_time")),
                        "last_value": vals.get("last_value"),
                        "min": vals.get("min"),
                        "max": vals.get("max"),
                        "mean": vals.get("mean"),
                    })
            return jsonify({"ok": True, "rows": rows, "limit": limit})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


def _hms(seconds: float | int) -> str:
    try:
        s = int(max(0, float(seconds)))
    except Exception:
        s = 0
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _job_elapsed_hms(job: dict[str, Any]) -> str:
    """Compute elapsed time; stop when job is finished."""

    try:
        started = float(job.get("started_mono") or 0.0)
    except Exception:
        started = 0.0
    if started <= 0:
        started = time.monotonic()

    try:
        finished = float(job.get("finished_mono") or 0.0)
    except Exception:
        finished = 0.0

    st = str(job.get("state") or "")
    if st in ("done", "error", "cancelled") and finished > 0:
        return _hms(max(0.0, finished - started))
    return _hms(max(0.0, time.monotonic() - started))


def _job_set_finished(meta: dict[str, Any]) -> None:
    """Mark a job as finished once (best-effort)."""

    try:
        if meta.get("finished_at") and meta.get("finished_mono"):
            return
        meta["finished_at"] = meta.get("finished_at") or _utc_now_iso_ms()
        meta["finished_mono"] = meta.get("finished_mono") or time.monotonic()
    except Exception:
        return


def _jobs_history_load() -> list[dict[str, Any]]:
    try:
        if not JOBS_HISTORY_PATH.exists():
            return []
        raw = JOBS_HISTORY_PATH.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _jobs_history_save(rows: list[dict[str, Any]]) -> None:
    try:
        JOBS_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        JOBS_HISTORY_PATH.write_text(json.dumps(rows, ensure_ascii=True, indent=2), encoding="utf-8")
    except Exception:
        return


def _jobs_history_upsert(row: dict[str, Any]) -> None:
    try:
        rid = str(row.get("id") or "").strip()
        if not rid:
            return
        rows = _jobs_history_load()
        rows = [r for r in rows if str(r.get("id") or "").strip() != rid]
        rows.append(row)

        def _ts(x: dict[str, Any]) -> float:
            for key in ("updated_at", "finished_at", "started_at"):
                try:
                    val = str(x.get(key) or "").replace("Z", "+00:00")
                    if val:
                        return datetime.fromisoformat(val).timestamp()
                except Exception:
                    continue
            return 0.0

        rows.sort(key=_ts, reverse=True)
        _jobs_history_save(rows[:200])
    except Exception:
        return


def _job_get(job_id: str) -> dict[str, Any] | None:
    with GLOBAL_STATS_LOCK:
        return GLOBAL_STATS_JOBS.get(job_id)


def _job_public(job: dict[str, Any]) -> dict[str, Any]:
    total = job.get("total_points")
    scanned = int(job.get("scanned_points") or 0)

    pct = None
    total_series = job.get("total_series")
    groups = int(job.get("groups_count") or 0)
    if isinstance(total_series, int) and total_series > 0:
        pct = min(100.0, (groups / float(total_series)) * 100.0)
    elif isinstance(total, int) and total > 0:
        pct = min(100.0, (scanned / float(total)) * 100.0)
    return {
        "id": job.get("id"),
        "state": job.get("state"),
        "message": job.get("message"),
        "started_at": job.get("started_at"),
        "updated_at": job.get("updated_at"),
        "finished_at": job.get("finished_at"),
        "elapsed": _job_elapsed_hms(job),
        "total_points": total,
        "scanned_points": scanned,
        "percent": pct,
        "groups": groups,
        "total_series": total_series,
        "current": job.get("current") or "",
        "last_query_label": job.get("last_query_label") or "",
        "last_query": job.get("last_query") or "",
        "queries": job.get("queries") if isinstance(job.get("queries"), list) else [],
        "cancelled": bool(job.get("cancelled")),
        "error": job.get("error"),
        "ready": job.get("state") in ("done", "error", "cancelled"),
    }


def _global_stats_job_thread(
    job_id: str,
    cfg: dict[str, Any],
    start_dt: datetime,
    stop_dt: datetime,
    field_filter: str | None,
    measurement_filter: str | None,
    entity_id_filter: str | None,
    friendly_name_filter: str | None,
    series_list: list[dict[str, str]] | None,
    columns: list[str] | None,
    page_limit: int,
) -> None:
    with GLOBAL_STATS_LOCK:
        job = GLOBAL_STATS_JOBS.get(job_id)
    if not job:
        return

    cfg_local = dict(cfg)
    # Keep per-query timeouts bounded so cancellation is responsive.
    try:
        cfg_local["timeout_seconds"] = min(max(int(cfg_local.get("timeout_seconds", 10)), 10), 60)
    except Exception:
        cfg_local["timeout_seconds"] = 60

    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    ff = (field_filter or "").strip()
    mf = (measurement_filter or "").strip()
    eid_f = (entity_id_filter or "").strip()
    fn_f = (friendly_name_filter or "").strip()
    discover_after_iso = None
    try:
        with GLOBAL_STATS_LOCK:
            job_now = GLOBAL_STATS_JOBS.get(job_id) or {}
        discover_after_iso = str(job_now.get("cache_discover_after") or "").strip() or None
    except Exception:
        discover_after_iso = None

    want_cols = [str(c).strip() for c in (columns or []) if str(c).strip()]
    if not want_cols:
        # Default: keep initial load fast.
        want_cols = ["last_value", "oldest_time", "newest_time"]
    want_set = set(want_cols)

    # Details (reduce) are expensive; keep "oldest_time" lightweight.
    want_details = any(c in want_set for c in ("count", "min", "max", "mean"))
    want_oldest = ("oldest_time" in want_set)
    want_last = ("last_value" in want_set) or ("newest_time" in want_set)

    def _is_timeout_error(e: Exception) -> bool:
        s = str(e).lower()
        return ("timed out" in s) or ("timeout" in s) or ("read timed out" in s)

    # Chunking threshold for timeout recovery
    min_chunk_seconds = 5 * 60

    # Used only for progress messages. May be unknown for full scans.
    total_series: int | None = None
    if series_list is not None:
        try:
            total_series = len(series_list)
        except Exception:
            total_series = None
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["total_series"] = total_series

    def set_state(state: str, msg: str) -> None:
        timer_id = None
        extra = None
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["state"] = state
                GLOBAL_STATS_JOBS[job_id]["message"] = msg
                GLOBAL_STATS_JOBS[job_id]["updated_at"] = _utc_now_iso_ms()
                if state in ("done", "error", "cancelled"):
                    _job_set_finished(GLOBAL_STATS_JOBS[job_id])
                    timer_id = GLOBAL_STATS_JOBS[job_id].get("timer_id")
                    try:
                        started_mono = float(GLOBAL_STATS_JOBS[job_id].get("started_mono") or 0.0)
                    except Exception:
                        started_mono = 0.0
                    dur_ms = int(max(0.0, (time.monotonic() - started_mono) * 1000.0)) if started_mono > 0 else None
                    err = str(GLOBAL_STATS_JOBS[job_id].get("error") or "").strip() or None
                    if state == "error" and not err:
                        err = str(msg or "").strip() or None
                    extra = {"duration_ms": dur_ms, "error": err}
        if timer_id and state in ("done", "error", "cancelled"):
            _timer_mark_finished(str(timer_id), state, extra=extra)

    def should_cancel() -> bool:
        with GLOBAL_STATS_LOCK:
            j = GLOBAL_STATS_JOBS.get(job_id) or {}
            if bool(j.get("cancelled")):
                return True

            try:
                max_s = int(cfg.get("jobs_max_runtime_seconds", 0) or 0)
            except Exception:
                max_s = 0
            if max_s <= 0:
                return False

            try:
                started_mono = float(j.get("started_mono") or 0.0)
            except Exception:
                started_mono = 0.0
            if started_mono <= 0:
                return False

            if (time.monotonic() - started_mono) >= float(max_s):
                GLOBAL_STATS_JOBS[job_id]["cancelled"] = True
                try:
                    LOG.warning("job_auto_cancel type=global_stats job_id=%s reason=max_runtime_seconds exceeded (%s)", job_id, max_s)
                except Exception:
                    pass
                return True
            return False

    def set_query(label: str, q: str) -> None:
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["last_query_label"] = label
                GLOBAL_STATS_JOBS[job_id]["last_query"] = (q or "").strip()
                GLOBAL_STATS_JOBS[job_id]["updated_at"] = _utc_now_iso_ms()
                try:
                    xs = GLOBAL_STATS_JOBS[job_id].get("queries")
                    if not isinstance(xs, list):
                        xs = []
                    xs.append({
                        "at": _utc_now_iso_ms(),
                        "label": str(label or "").strip(),
                        "query": (q or "").strip(),
                    })
                    if len(xs) > 40:
                        xs = xs[-40:]
                    GLOBAL_STATS_JOBS[job_id]["queries"] = xs
                except Exception:
                    pass

    def _parse_ts(s: str | None) -> datetime | None:
        if not s:
            return None
        try:
            t = str(s).strip()
            if not t:
                return None
            if t.endswith("Z"):
                t = t[:-1] + "+00:00"
            return datetime.fromisoformat(t)
        except Exception:
            return None

    def _as_rfc3339(v: Any) -> str | None:
        if isinstance(v, datetime):
            return _dt_to_rfc3339_utc(v)
        if isinstance(v, str) and v.strip():
            return v.strip()
        return None

    def _chunk_ranges(a: datetime, b: datetime, max_days: int) -> list[tuple[datetime, datetime]]:
        out: list[tuple[datetime, datetime]] = []
        cur = a
        step = timedelta(days=max_days)
        while cur < b:
            nxt = cur + step
            if nxt > b:
                nxt = b
            out.append((cur, nxt))
            cur = nxt
        return out

    def _series_reduce_query(bucket: str, s_iso: str, e_iso: str, m: str, f: str, eid: str, fn: str) -> str:
        conds = [f"r._measurement == {_flux_str(m)}", f"r._field == {_flux_str(f)}"]
        if eid:
            conds.append(f"r.entity_id == {_flux_str(eid)}")
        if fn:
            conds.append(f"r.friendly_name == {_flux_str(fn)}")
        pred = " and ".join(conds)
        return f'''
data = from(bucket: "{bucket}")
  |> range(start: time(v: "{s_iso}"), stop: time(v: "{e_iso}"))
  |> filter(fn: (r) => {pred})
  // NOTE: removed typeOf() check for compatibility with older Influx/Flux versions where typeOf is not available.
  // Rely on downstream numeric conversion (float(v: r._value)) and error handling. If non-numeric values exist,
  // they will be ignored by the reduce logic or cause chunking which is handled by retries.
  |> map(fn: (r) => ({{ r with entity_id: if exists r.entity_id then string(v: r.entity_id) else "", friendly_name: if exists r.friendly_name then string(v: r.friendly_name) else "" }}))
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_time","_value"])
  |> group(columns: ["_measurement","_field","entity_id","friendly_name"])

data
  |> reduce(
    identity: {{seen: false, count: 0, sum: 0.0, min: 0.0, max: 0.0, oldest_time: time(v: "1970-01-01T00:00:00Z"), newest_time: time(v: "1970-01-01T00:00:00Z"), last_value: 0.0}},
    fn: (r, accumulator) => ({{
      seen: true,
      count: accumulator.count + 1,
      sum: accumulator.sum + float(v: r._value),
      min: if accumulator.seen == false then float(v: r._value) else if float(v: r._value) < accumulator.min then float(v: r._value) else accumulator.min,
      max: if accumulator.seen == false then float(v: r._value) else if float(v: r._value) > accumulator.max then float(v: r._value) else accumulator.max,
      oldest_time: if accumulator.seen == false then r._time else if r._time < accumulator.oldest_time then r._time else accumulator.oldest_time,
      newest_time: if accumulator.seen == false then r._time else if r._time > accumulator.newest_time then r._time else accumulator.newest_time,
      last_value: if accumulator.seen == false then float(v: r._value) else if r._time >= accumulator.newest_time then float(v: r._value) else accumulator.last_value,
    }})
  )
  |> map(fn: (r) => ({{
    _measurement: r._measurement,
    _field: r._field,
    entity_id: r.entity_id,
    friendly_name: r.friendly_name,
    count: r.count,
    sum: r.sum,
    min: r.min,
    max: r.max,
    oldest_time: r.oldest_time,
    newest_time: r.newest_time,
    last_value: r.last_value,
  }}))
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","count","sum","min","max","oldest_time","newest_time","last_value"])
'''

    def _series_stats(qapi: Any, bucket: str, m: str, f: str, eid: str, fn: str) -> dict[str, Any]:
        span_days = max(0.0, (stop_dt - start_dt).total_seconds() / 86400.0)
        chunks = _chunk_ranges(start_dt, stop_dt, 14) if span_days > 20 else [(start_dt, stop_dt)]

        def _is_timeout_error(e: Exception) -> bool:
            s = str(e).lower()
            return ("timed out" in s) or ("timeout" in s) or ("read timed out" in s)

        def _fetch_reduce_vals(a: datetime, b: datetime, depth: int = 0) -> dict[str, Any] | None:
            if should_cancel():
                raise RuntimeError("cancelled")
            s_iso = _dt_to_rfc3339_utc(a)
            e_iso = _dt_to_rfc3339_utc(b)
            q = _series_reduce_query(bucket, s_iso, e_iso, m, f, eid, fn)
            set_query(f"Details {m}/{f} chunk", q)
            try:
                tables = qapi.query(q, org=cfg_local["org"])
            except Exception as e:
                span_s = max(0.0, (b - a).total_seconds())
                if _is_timeout_error(e) and span_s > min_chunk_seconds:
                    mid = a + timedelta(seconds=(span_s / 2.0))
                    left = _fetch_reduce_vals(a, mid, depth + 1)
                    right = _fetch_reduce_vals(mid, b, depth + 1)
                    if not left:
                        return right
                    if not right:
                        return left
                    # Merge two reduce outputs into one
                    outm: dict[str, Any] = {}
                    try:
                        outm["count"] = int(left.get("count") or 0) + int(right.get("count") or 0)
                    except Exception:
                        outm["count"] = 0
                    try:
                        outm["sum"] = float(left.get("sum") or 0.0) + float(right.get("sum") or 0.0)
                    except Exception:
                        outm["sum"] = 0.0
                    try:
                        outm["min"] = min(float(left.get("min")), float(right.get("min")))
                    except Exception:
                        outm["min"] = left.get("min") if left.get("min") is not None else right.get("min")
                    try:
                        outm["max"] = max(float(left.get("max")), float(right.get("max")))
                    except Exception:
                        outm["max"] = left.get("max") if left.get("max") is not None else right.get("max")
                    outm["oldest_time"] = left.get("oldest_time") or right.get("oldest_time")
                    try:
                        lt = _parse_ts(str(left.get("oldest_time") or "") or None)
                        rt = _parse_ts(str(right.get("oldest_time") or "") or None)
                        if lt and rt:
                            outm["oldest_time"] = _dt_to_rfc3339_utc(min(lt, rt))
                    except Exception:
                        pass
                    outm["newest_time"] = right.get("newest_time") or left.get("newest_time")
                    try:
                        lt = _parse_ts(str(left.get("newest_time") or "") or None)
                        rt = _parse_ts(str(right.get("newest_time") or "") or None)
                        if lt and rt:
                            outm["newest_time"] = _dt_to_rfc3339_utc(max(lt, rt))
                    except Exception:
                        pass
                    # last_value should come from newest
                    outm["last_value"] = right.get("last_value") if right.get("last_value") is not None else left.get("last_value")
                    return outm
                # Give up; caller handles.
                raise

            vals: dict[str, Any] | None = None
            for t in tables or []:
                for rec in getattr(t, "records", []) or []:
                    vals = getattr(rec, "values", {}) or {}
                    break
                if vals is not None:
                    break
            return vals

        count = 0
        ssum = 0.0
        min_v: float | None = None
        max_v: float | None = None
        oldest_s: str | None = None
        newest_s: str | None = None
        newest_dt: datetime | None = None
        last_val: Any = None

        for i, (a, b) in enumerate(chunks):
            if should_cancel():
                raise RuntimeError("cancelled")
            set_query(f"Details {m}/{f} chunk {i+1}/{len(chunks)}", "")
            vals = _fetch_reduce_vals(a, b)
            if not vals:
                continue

            try:
                cnum = int(vals.get("count") or 0)
            except Exception:
                cnum = 0
            if cnum <= 0:
                continue

            count += cnum
            try:
                ssum += float(vals.get("sum") or 0.0)
            except Exception:
                pass

            try:
                vmin = float(vals.get("min"))
                min_v = vmin if min_v is None else min(min_v, vmin)
            except Exception:
                pass
            try:
                vmax = float(vals.get("max"))
                max_v = vmax if max_v is None else max(max_v, vmax)
            except Exception:
                pass

            ot_s = _as_rfc3339(vals.get("oldest_time"))
            nt_s = _as_rfc3339(vals.get("newest_time"))
            if ot_s:
                if oldest_s is None:
                    oldest_s = ot_s
                else:
                    odt = _parse_ts(oldest_s)
                    ndt = _parse_ts(ot_s)
                    if odt and ndt and ndt < odt:
                        oldest_s = ot_s
            if nt_s:
                ndt = _parse_ts(nt_s)
                if newest_dt is None or (ndt and newest_dt and ndt > newest_dt):
                    newest_dt = ndt
                    newest_s = nt_s
                    last_val = vals.get("last_value")

        mean = (ssum / float(count)) if count > 0 else None
        return {
            "count": count,
            "sum": ssum,
            "min": min_v,
            "max": max_v,
            "mean": mean,
            "oldest_time": oldest_s,
            "newest_time": newest_s,
            "last_value": last_val,
        }

    def _series_last(qapi: Any, bucket: str, m: str, f: str, eid: str, fn: str) -> dict[str, Any]:
        conds = [f"r._measurement == {_flux_str(m)}", f"r._field == {_flux_str(f)}"]
        if eid:
            conds.append(f"r.entity_id == {_flux_str(eid)}")
        if fn:
            conds.append(f"r.friendly_name == {_flux_str(fn)}")
        pred = " and ".join(conds)
        q = f'''
from(bucket: "{bucket}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => {pred})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 1)
'''
        set_query(f"Last {m}/{f}", q)
        tables = qapi.query(q, org=cfg_local["org"])
        newest = None
        last_v = None
        for t in tables or []:
            for rec in getattr(t, "records", []) or []:
                newest = rec.get_time()
                last_v = rec.get_value()
                break
            if newest is not None:
                break
        return {
            "newest_time": _as_rfc3339(newest),
            "last_value": last_v,
        }

    def _series_first(qapi: Any, bucket: str, m: str, f: str, eid: str, fn: str) -> dict[str, Any]:
        conds = [f"r._measurement == {_flux_str(m)}", f"r._field == {_flux_str(f)}"]
        if eid:
            conds.append(f"r.entity_id == {_flux_str(eid)}")
        if fn:
            conds.append(f"r.friendly_name == {_flux_str(fn)}")
        pred = " and ".join(conds)
        q = f'''
from(bucket: "{bucket}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => {pred})
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: 1)
'''
        set_query(f"First {m}/{f}", q)
        tables = qapi.query(q, org=cfg_local["org"])
        oldest = None
        for t in tables or []:
            for rec in getattr(t, "records", []) or []:
                oldest = rec.get_time()
                break
            if oldest is not None:
                break
        return {"oldest_time": _as_rfc3339(oldest)}

    try:
        # Skip expensive pre-counting. This keeps the job responsive and starts work immediately.
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["total_series"] = None
                GLOBAL_STATS_JOBS[job_id]["columns"] = list(want_cols)

        if should_cancel():
            set_state("cancelled", "Abgebrochen.")
            return

        set_state("query", "Berechne Statistiken in Happen...")

        rows: list[dict[str, Any]] = []
        scanned_points = 0

        # Expose a live view for incremental UI polling (best-effort).
        # The list reference is replaced with a final sorted list when the job finishes.
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["rows"] = rows

        def add_row(m: str, f: str, eid: str, fn: str, base_last: dict[str, Any] | None = None, det: dict[str, Any] | None = None) -> None:
            r: dict[str, Any] = {
                "measurement": m,
                "field": f,
                "entity_id": eid,
                "friendly_name": fn,
            }
            if base_last:
                if "oldest_time" in base_last:
                    r["oldest_time"] = base_last.get("oldest_time")
                if "newest_time" in base_last:
                    r["newest_time"] = base_last.get("newest_time")
                if "last_value" in base_last:
                    r["last_value"] = base_last.get("last_value")
            if det:
                for k in ("count", "min", "max", "mean", "oldest_time", "sum"):
                    if k in det:
                        if k == "sum":
                            r["__sum"] = det.get(k)
                        else:
                            r[k] = det.get(k)
                # det may also include newest/last
                if "newest_time" in det and "newest_time" not in r:
                    r["newest_time"] = det.get("newest_time")
                if "last_value" in det and "last_value" not in r:
                    r["last_value"] = det.get("last_value")
            rows.append(r)

        with v2_client(cfg_local) as c:
            qapi = c.query_api()

            def _series_last_span(a: datetime, b: datetime) -> list[dict[str, Any]]:
                s_iso = _dt_to_rfc3339_utc(a)
                e_iso = _dt_to_rfc3339_utc(b)
                ff_clause = f"|> filter(fn: (r) => r._field == {_flux_str(ff)})" if ff else ""
                mf_clause = f"|> filter(fn: (r) => r._measurement == {_flux_str(mf)})" if mf else ""
                tag_clause = ""
                if eid_f:
                    tag_clause += f"|> filter(fn: (r) => r.entity_id == {_flux_str(eid_f)})\n"
                if fn_f:
                    tag_clause += f"|> filter(fn: (r) => r.friendly_name == {_flux_str(fn_f)})\n"
                q_last = f'''
from(bucket: "{cfg_local["bucket"]}")
  |> range(start: time(v: "{s_iso}"), stop: time(v: "{e_iso}"))
  |> filter(fn: (r) => exists r._measurement and exists r._field)
  {mf_clause}
  {ff_clause}
  {tag_clause.strip()}
  |> map(fn: (r) => ({{ r with entity_id: if exists r.entity_id then string(v: r.entity_id) else "", friendly_name: if exists r.friendly_name then string(v: r.friendly_name) else "" }}))
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_time","_value"])
  |> group(columns: ["_measurement","_field","entity_id","friendly_name"])
  |> last()
'''
                set_query("Series span", q_last)
                out: list[dict[str, Any]] = []
                for rec in qapi.query_stream(q_last, org=cfg_local["org"]):
                    vals = getattr(rec, "values", {}) or {}
                    newest = rec.get_time() or vals.get("_time")
                    out.append({
                        "measurement": str(vals.get("_measurement") or ""),
                        "field": str(vals.get("_field") or ""),
                        "entity_id": str(vals.get("entity_id") or ""),
                        "friendly_name": str(vals.get("friendly_name") or ""),
                        "newest_time": _as_rfc3339(newest),
                        "last_value": rec.get_value(),
                    })
                return out

            def _series_last_span_split(a: datetime, b: datetime) -> list[dict[str, Any]]:
                if should_cancel():
                    raise RuntimeError("cancelled")
                min_chunk_seconds = 5 * 60
                span_s = max(0.0, (b - a).total_seconds())
                try:
                    return _series_last_span(a, b)
                except Exception as e:
                    if _is_timeout_error(e) and span_s > min_chunk_seconds:
                        mid = a + timedelta(seconds=(span_s / 2.0))
                        return _series_last_span_split(a, mid) + _series_last_span_split(mid, b)
                    raise

            # If series_list is provided: enrich only these series.
            if series_list is not None:
                try:
                    if discover_after_iso:
                        discover_after_dt = _parse_iso_datetime(discover_after_iso)
                        if discover_after_dt and discover_after_dt < stop_dt:
                            set_state("query", "Ergaenze Serienliste aus Cache-Fortsetzung...")
                            seed_map = {
                                (str(it.get("measurement") or ""), str(it.get("field") or ""), str(it.get("entity_id") or ""), str(it.get("friendly_name") or "")): dict(it)
                                for it in (series_list or []) if isinstance(it, dict)
                            }
                            for srow in _series_last_span_split(discover_after_dt, stop_dt):
                                key = (str(srow.get("measurement") or ""), str(srow.get("field") or ""), str(srow.get("entity_id") or ""), str(srow.get("friendly_name") or ""))
                                if key not in seed_map:
                                    seed_map[key] = dict(srow)
                            series_list = list(seed_map.values())
                            total_series = len(series_list)
                            with GLOBAL_STATS_LOCK:
                                if job_id in GLOBAL_STATS_JOBS:
                                    GLOBAL_STATS_JOBS[job_id]["total_series"] = total_series
                except Exception:
                    pass

                for idx, srow in enumerate(series_list):
                    if should_cancel():
                        set_state("cancelled", "Abgebrochen.")
                        return
                    m = str(srow.get("measurement") or "")
                    f = str(srow.get("field") or "")
                    eid = str(srow.get("entity_id") or "")
                    fn = str(srow.get("friendly_name") or "")
                    with GLOBAL_STATS_LOCK:
                        if job_id in GLOBAL_STATS_JOBS:
                            GLOBAL_STATS_JOBS[job_id]["current"] = fn or eid or (m + "/" + f)
                            GLOBAL_STATS_JOBS[job_id]["groups_count"] = idx

                    if want_details:
                        set_state("query", f"Details {idx+1}: {fn or eid or (m + '/' + f)}")
                        det = _series_stats(qapi, cfg_local["bucket"], m, f, eid, fn)
                        cnum = int(det.get("count") or 0)
                        if cnum <= 0:
                            continue
                        scanned_points += max(0, cnum)
                        add_row(m, f, eid, fn, None, det)
                    elif want_last or want_oldest:
                        set_state("query", f"Basis {idx+1}: {fn or eid or (m + '/' + f)}")
                        base = {}
                        if want_last:
                            base.update(_series_last(qapi, cfg_local["bucket"], m, f, eid, fn))
                        if want_oldest:
                            base.update(_series_first(qapi, cfg_local["bucket"], m, f, eid, fn))
                        if not any(base.get(k) is not None for k in ("oldest_time", "newest_time", "last_value")):
                            continue
                        add_row(m, f, eid, fn, base if base else None, None)
                    else:
                        add_row(m, f, eid, fn, None, None)

                    with GLOBAL_STATS_LOCK:
                        if job_id in GLOBAL_STATS_JOBS:
                            GLOBAL_STATS_JOBS[job_id]["scanned_points"] = scanned_points
                            GLOBAL_STATS_JOBS[job_id]["groups_count"] = idx + 1

            else:
                # Full scan: load series pages and optionally compute details.
                ff_clause = f"|> filter(fn: (r) => r._field == {_flux_str(ff)})" if ff else ""
                mf_clause = f"|> filter(fn: (r) => r._measurement == {_flux_str(mf)})" if mf else ""
                tag_clause = ""
                if eid_f:
                    tag_clause += f"|> filter(fn: (r) => r.entity_id == {_flux_str(eid_f)})\n"
                if fn_f:
                    tag_clause += f"|> filter(fn: (r) => r.friendly_name == {_flux_str(fn_f)})\n"

                def _series_first_span(a: datetime, b: datetime) -> list[dict[str, Any]]:
                    s_iso = _dt_to_rfc3339_utc(a)
                    e_iso = _dt_to_rfc3339_utc(b)
                    q_first = f'''
from(bucket: "{cfg_local["bucket"]}")
  |> range(start: time(v: "{s_iso}"), stop: time(v: "{e_iso}"))
  |> filter(fn: (r) => exists r._measurement and exists r._field)
  {mf_clause}
  {ff_clause}
  {tag_clause.strip()}
  |> map(fn: (r) => ({{ r with entity_id: if exists r.entity_id then string(v: r.entity_id) else "", friendly_name: if exists r.friendly_name then string(v: r.friendly_name) else "" }}))
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_time"])
  |> group(columns: ["_measurement","_field","entity_id","friendly_name"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: 1)
'''
                    set_query("Series span (first)", q_first)
                    out: list[dict[str, Any]] = []
                    for rec in qapi.query_stream(q_first, org=cfg_local["org"]):
                        vals = getattr(rec, "values", {}) or {}
                        oldest = rec.get_time() or vals.get("_time")
                        out.append({
                            "measurement": str(vals.get("_measurement") or ""),
                            "field": str(vals.get("_field") or ""),
                            "entity_id": str(vals.get("entity_id") or ""),
                            "friendly_name": str(vals.get("friendly_name") or ""),
                            "oldest_time": _as_rfc3339(oldest),
                        })
                    return out

                def _series_first_span_split(a: datetime, b: datetime) -> list[dict[str, Any]]:
                    if should_cancel():
                        raise RuntimeError("cancelled")
                    span_s = max(0.0, (b - a).total_seconds())
                    try:
                        return _series_first_span(a, b)
                    except Exception as e:
                        if _is_timeout_error(e) and span_s > min_chunk_seconds:
                            mid = a + timedelta(seconds=(span_s / 2.0))
                            left = _series_first_span_split(a, mid)
                            right = _series_first_span_split(mid, b)
                            return left + right
                        raise

                set_state("query", "Lade Serienliste...")

                series_map: dict[tuple[str, str, str, str], dict[str, Any]] = {}
                series_rows = _series_last_span_split(start_dt, stop_dt)
                for srow in series_rows:
                    if should_cancel():
                        set_state("cancelled", "Abgebrochen.")
                        return

                    m = str(srow.get("measurement") or "")
                    f = str(srow.get("field") or "")
                    eid = str(srow.get("entity_id") or "")
                    fn = str(srow.get("friendly_name") or "")

                    k = (m, f, eid, fn)
                    nt = str(srow.get("newest_time") or "")
                    cur = series_map.get(k)
                    if not cur:
                        series_map[k] = srow
                    else:
                        try:
                            at = _parse_ts(str(cur.get("newest_time") or "") or None)
                            bt = _parse_ts(nt or None)
                            if bt and (not at or bt > at):
                                series_map[k] = srow
                        except Exception:
                            series_map[k] = srow

                if want_oldest and not want_details:
                    set_state("query", "Lade Serienliste (oldest)...")
                    first_map: dict[tuple[str, str, str, str], str] = {}
                    first_rows = _series_first_span_split(start_dt, stop_dt)
                    for frow in first_rows:
                        if should_cancel():
                            set_state("cancelled", "Abgebrochen.")
                            return
                        m = str(frow.get("measurement") or "")
                        f = str(frow.get("field") or "")
                        eid = str(frow.get("entity_id") or "")
                        fn = str(frow.get("friendly_name") or "")
                        k = (m, f, eid, fn)
                        ot = str(frow.get("oldest_time") or "")
                        if not ot:
                            continue
                        cur_ot = first_map.get(k)
                        if not cur_ot:
                            first_map[k] = ot
                            continue
                        try:
                            at = _parse_ts(cur_ot or None)
                            bt = _parse_ts(ot or None)
                            if bt and (not at or bt < at):
                                first_map[k] = ot
                        except Exception:
                            first_map[k] = ot

                    for k, ot in first_map.items():
                        if k in series_map:
                            try:
                                series_map[k]["oldest_time"] = ot
                            except Exception:
                                pass

                series_list_full = list(series_map.values())
                with GLOBAL_STATS_LOCK:
                    if job_id in GLOBAL_STATS_JOBS:
                        GLOBAL_STATS_JOBS[job_id]["total_series"] = len(series_list_full)

                def _sort_key(it: dict[str, Any]) -> float:
                    try:
                        t = _parse_ts(str(it.get("newest_time") or "") or None)
                        return t.timestamp() if t else 0.0
                    except Exception:
                        return 0.0

                series_list_full.sort(key=_sort_key, reverse=True)

                for srow in series_list_full:
                    if should_cancel():
                        set_state("cancelled", "Abgebrochen.")
                        return

                    m = str(srow.get("measurement") or "")
                    f = str(srow.get("field") or "")
                    eid = str(srow.get("entity_id") or "")
                    fn = str(srow.get("friendly_name") or "")

                    display = fn or eid or (m + "/" + f)
                    with GLOBAL_STATS_LOCK:
                        if job_id in GLOBAL_STATS_JOBS:
                            GLOBAL_STATS_JOBS[job_id]["current"] = display

                    base_last = {
                        "oldest_time": srow.get("oldest_time"),
                        "newest_time": srow.get("newest_time"),
                        "last_value": srow.get("last_value"),
                    }
                    if want_details:
                        pos = len(rows) + 1
                        tot_s = str(total_series) if isinstance(total_series, int) else "?"
                        set_state("query", f"Details {pos}/{tot_s}: {display}")
                        det = _series_stats(qapi, cfg_local["bucket"], m, f, eid, fn)
                        cnum = int(det.get("count") or 0)
                        scanned_points += max(0, cnum)
                        add_row(m, f, eid, fn, base_last if want_last else None, det)
                    else:
                        add_row(m, f, eid, fn, base_last if want_last else None, None)

                    with GLOBAL_STATS_LOCK:
                        if job_id in GLOBAL_STATS_JOBS:
                            GLOBAL_STATS_JOBS[job_id]["scanned_points"] = scanned_points
                            GLOBAL_STATS_JOBS[job_id]["groups_count"] = len(rows)

        final_rows = sorted(rows, key=lambda r: int(r.get("count") or 0), reverse=True)
        try:
            with GLOBAL_STATS_LOCK:
                job_now = GLOBAL_STATS_JOBS.get(job_id) or {}
                merge_rows = job_now.get("cache_merge_rows") if isinstance(job_now.get("cache_merge_rows"), list) else []
            if merge_rows:
                final_rows = _stats_cache_merge_rows(merge_rows, final_rows)
        except Exception:
            pass
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["rows"] = final_rows
                GLOBAL_STATS_JOBS[job_id]["scanned_points"] = scanned_points
                GLOBAL_STATS_JOBS[job_id]["groups_count"] = len(final_rows)

        rows = final_rows

        # Persist stats cache (best-effort)
        try:
            cache_id = ""
            cache_key = None
            with GLOBAL_STATS_LOCK:
                j = GLOBAL_STATS_JOBS.get(job_id) or {}
                cache_id = str(j.get("cache_id") or "").strip()
                ck = j.get("cache_key")
                cache_key = ck if isinstance(ck, dict) else None

            if cache_id and cache_key:
                cfg_now = _overlay_from_yaml_if_enabled(load_cfg())
                if bool(cfg_now.get("stats_cache_enabled", True)) and int(cfg_now.get("stats_cache_max_items", 10) or 10) > 0:
                    payload = {
                        "generated_at": _utc_now_iso_ms(),
                        "key": cache_key,
                        "rows": rows,
                        "covered_start": str(j.get("cache_merge_start") or start),
                        "covered_stop": stop,
                    }
                    bytes_written = _stats_cache_write_payload(cache_id, payload)
                    meta = _stats_cache_load_meta(cache_id) or {"id": cache_id, "key": cache_key}
                    try:
                        meta.setdefault("trigger_page", (GLOBAL_STATS_JOBS.get(job_id) or {}).get("trigger_page") or "stats")
                    except Exception:
                        meta.setdefault("trigger_page", "stats")
                    meta["updated_at"] = payload["generated_at"]
                    meta["last_used_at"] = payload["generated_at"]
                    meta["row_count"] = len(rows)
                    meta["bytes"] = int(bytes_written or 0)
                    meta["dirty"] = False
                    meta["dirty_reason"] = None
                    meta["dirty_at"] = None
                    meta["mismatch"] = (str(cache_key.get("cfg_fp") or "") != _stats_cache_cfg_fp(cfg_now))
                    if "events" not in meta and isinstance((_stats_cache_load_meta(cache_id) or {}).get("events"), list):
                        meta["events"] = (_stats_cache_load_meta(cache_id) or {}).get("events")
                    _meta_add_event(meta, "store", f"rows={len(rows)}", at=str(payload["generated_at"] or ""))
                    _stats_cache_write_meta(meta)
                    _stats_cache_enforce_limits(cfg_now)
        except Exception:
            pass

        set_state("done", f"Fertig. Zeilen: {len(rows)}")
    except RuntimeError as e:
        if str(e) == "cancelled":
            set_state("cancelled", "Abgebrochen.")
            return
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["error"] = _short_influx_error(e)
        LOG.exception("global_stats_job failed (job_id=%s)", job_id)
        set_state("error", "Fehler")
    except Exception as e:
        last_label = ""
        last_query = ""
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["error"] = _short_influx_error(e)
                try:
                    last_label = str(GLOBAL_STATS_JOBS[job_id].get("last_query_label") or "")
                    last_query = str(GLOBAL_STATS_JOBS[job_id].get("last_query") or "")
                except Exception:
                    last_label = ""
                    last_query = ""
        if last_query:
            LOG.exception(
                "global_stats_job failed (job_id=%s, last_query_label=%s, last_query=%s)",
                job_id,
                last_label,
                last_query[:1000],
            )
        else:
            LOG.exception("global_stats_job failed (job_id=%s, last_query_label=%s)", job_id, last_label)
        set_state("error", "Fehler")


def _global_stats_start_job(
    cfg: dict[str, Any],
    start_dt: datetime,
    stop_dt: datetime,
    field_filter: str | None,
    measurement_filter: str | None,
    entity_id_filter: str | None,
    friendly_name_filter: str | None,
    series_list: list[dict[str, str]] | None,
    columns: list[str] | None,
    page_limit: int,
    trigger_page: str,
    timer_id: str | None = None,
    cache_id: str | None = None,
    cache_key: dict[str, Any] | None = None,
    cache_merge_rows: list[dict[str, Any]] | None = None,
    cache_merge_start: str | None = None,
    cache_discover_after: str | None = None,
) -> str:
    job_id = uuid.uuid4().hex
    ip = _req_ip()
    ua = _req_ua()
    job = {
        "id": job_id,
        "state": "queued",
        "message": "Start...",
        "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "started_mono": time.monotonic(),
        "trigger_page": trigger_page,
        "trigger_ip": ip,
        "trigger_ua": ua,
        "timer_id": str(timer_id or "").strip() or None,
        "total_points": None,
        "scanned_points": 0,
        "total_series": None,
        "groups_count": 0,
        "current": "",
        "last_query_label": "",
        "last_query": "",
        "queries": [],
        "rows": [],
        "cancelled": False,
        "error": None,
        "cache_id": cache_id,
        "cache_key": cache_key,
        "cache_merge_rows": list(cache_merge_rows or []),
        "cache_merge_start": str(cache_merge_start or "").strip() or None,
        "cache_discover_after": str(cache_discover_after or "").strip() or None,
        "field_filter": field_filter,
        "measurement": measurement_filter,
        "entity_id": entity_id_filter,
        "friendly_name": friendly_name_filter,
        "columns": columns or [],
    }

    try:
        LOG.info(
            "job_start type=global_stats job_id=%s timer_id=%s ip=%s ua=%s start=%s stop=%s field_filter=%s measurement=%s entity_id=%s friendly_name=%s cols=%s",
            job_id,
            str(timer_id or "") if timer_id else "",
            ip,
            ua,
            _dt_to_rfc3339_utc(start_dt),
            _dt_to_rfc3339_utc(stop_dt),
            (field_filter or "") if field_filter else "",
            measurement_filter or "",
            entity_id_filter or "",
            friendly_name_filter or "",
            ",".join(columns or []),
        )
    except Exception:
        pass

    with GLOBAL_STATS_LOCK:
        GLOBAL_STATS_JOBS[job_id] = job
        cutoff = time.monotonic() - 3600
        old = [k for k, v in GLOBAL_STATS_JOBS.items() if float(v.get("started_mono") or 0) < cutoff]
        for k in old:
            if k != job_id:
                GLOBAL_STATS_JOBS.pop(k, None)

    t = threading.Thread(
        target=_global_stats_job_thread,
        args=(
            job_id,
            cfg,
            start_dt,
            stop_dt,
            field_filter,
            measurement_filter,
            entity_id_filter,
            friendly_name_filter,
            series_list,
            columns,
            page_limit,
        ),
        daemon=True,
    )
    t.start()
    return job_id


def _global_stats_start_cached_job(
    cache_id: str,
    cache_key: dict[str, Any],
    rows: list[dict[str, Any]],
    columns: list[str] | None,
    trigger_page: str,
) -> str:
    job_id = uuid.uuid4().hex
    ip = _req_ip()
    ua = _req_ua()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    job = {
        "id": job_id,
        "state": "done",
        "message": f"Cache geladen. Zeilen: {len(rows)}",
        "started_at": now,
        "started_mono": time.monotonic(),
        "finished_at": now,
        "finished_mono": time.monotonic(),
        "trigger_page": trigger_page,
        "trigger_ip": ip,
        "trigger_ua": ua,
        "timer_id": None,
        "total_points": None,
        "scanned_points": 0,
        "total_series": len(rows),
        "groups_count": len(rows),
        "current": "cache",
        "last_query_label": "Cache",
        "last_query": "",
        "queries": [],
        "rows": list(rows or []),
        "cancelled": False,
        "error": None,
        "cache_id": cache_id,
        "cache_key": cache_key,
        "field_filter": cache_key.get("field_filter"),
        "measurement": cache_key.get("measurement"),
        "entity_id": cache_key.get("entity_id"),
        "friendly_name": cache_key.get("friendly_name"),
        "columns": list(columns or cache_key.get("columns") or []),
    }
    with GLOBAL_STATS_LOCK:
        GLOBAL_STATS_JOBS[job_id] = job
    try:
        LOG.info(
            "job_start type=global_stats cache_hit=1 job_id=%s cache_id=%s ip=%s ua=%s rows=%s",
            job_id,
            cache_id,
            ip,
            ua,
            len(rows),
        )
    except Exception:
        pass
    return job_id


@app.post("/api/global_stats_job/start")
def api_global_stats_job_start():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "global_stats currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    body = request.get_json(force=True) or {}
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    field_filter = body.get("field_filter")
    if field_filter is not None:
        field_filter = str(field_filter)
    ff = (field_filter or "").strip() or None

    measurement_filter = (body.get("measurement") or "").strip() or None
    entity_id_filter = (body.get("entity_id") or "").strip() or None
    friendly_name_filter = (body.get("friendly_name") or "").strip() or None

    cols = body.get("columns")
    columns: list[str] | None = None
    if isinstance(cols, list):
        columns = [str(x) for x in cols if x is not None]

    series_list: list[dict[str, str]] | None = None
    raw_series = body.get("series")
    if isinstance(raw_series, list):
        tmp: list[dict[str, str]] = []
        for it in raw_series:
            if not isinstance(it, dict):
                continue
            tmp.append({
                "measurement": str(it.get("measurement") or ""),
                "field": str(it.get("field") or ""),
                "entity_id": str(it.get("entity_id") or ""),
                "friendly_name": str(it.get("friendly_name") or ""),
            })
        series_list = tmp

    try:
        page_limit = int(body.get("page_limit", 200))
    except Exception:
        page_limit = 200
    if page_limit < 10:
        page_limit = 10
    if page_limit > 200:
        page_limit = 200

    cache_id = None
    cache_key = None
    stale_prefill = False
    stale_seed_series = None
    stale_discover_after = None
    try:
        if bool(cfg.get("stats_cache_enabled", True)) and int(cfg.get("stats_cache_max_items", 10) or 10) > 0:
            cache_key = _stats_cache_key(
                cfg,
                body,
                start_dt,
                stop_dt,
                ff,
                measurement_filter,
                entity_id_filter,
                friendly_name_filter,
                columns,
                page_limit,
            )
            cache_id = _stats_cache_id(cache_key)
            meta = _stats_cache_load_meta(cache_id) or {"id": cache_id, "key": cache_key}
            meta.setdefault("created_at", _utc_now_iso_ms())
            meta.setdefault("trigger_page", "stats")
            payload = _stats_cache_load_payload(cache_id) if cache_id else None
            cache_rows = payload.get("rows") if isinstance(payload, dict) and isinstance(payload.get("rows"), list) else None
            can_use_cache = bool(cache_rows) and not bool(meta.get("dirty")) and not bool(meta.get("mismatch")) and not _stats_cache_is_stale(cfg, meta)
            meta["last_used_at"] = _utc_now_iso_ms()
            if can_use_cache:
                _stats_cache_write_meta(meta)
                job_id = _global_stats_start_cached_job(
                    cache_id,
                    cache_key,
                    list(cache_rows or []),
                    columns,
                    trigger_page="stats",
                )
                return jsonify({"ok": True, "job_id": job_id, "cache_id": cache_id, "cache_hit": True})

            append_from = None
            append_rows = None
            try:
                rk = str(cache_key.get("range") or "").strip().lower()
                covered_start_s = str((payload or {}).get("covered_start") or "").strip()
                covered_stop_s = str((payload or {}).get("covered_stop") or "").strip()
                covered_start_dt = _parse_iso_datetime(covered_start_s) if covered_start_s else None
                covered_stop_dt = _parse_iso_datetime(covered_stop_s) if covered_stop_s else None
                cache_rows_ok = isinstance(cache_rows, list) and len(cache_rows) > 0
                if (
                    _stats_cache_append_supported(rk)
                    and cache_rows_ok
                    and not bool(meta.get("dirty"))
                    and not bool(meta.get("mismatch"))
                    and covered_start_dt
                    and covered_stop_dt
                    and abs((covered_start_dt - start_dt).total_seconds()) <= 1.0
                    and stop_dt > covered_stop_dt
                ):
                    append_from = covered_stop_dt
                    append_rows = list(cache_rows or [])
            except Exception:
                append_from = None
                append_rows = None

            if append_from and append_rows:
                meta["dirty"] = True
                meta["dirty_reason"] = "append_update"
                meta["dirty_at"] = _utc_now_iso_ms()
                _stats_cache_write_meta(meta)
                job_id = _global_stats_start_job(
                    cfg,
                    append_from,
                    stop_dt,
                    ff,
                    measurement_filter,
                    entity_id_filter,
                    friendly_name_filter,
                    series_list,
                    columns,
                    page_limit,
                    trigger_page="stats",
                    cache_id=cache_id,
                    cache_key=cache_key,
                    cache_merge_rows=append_rows,
                    cache_merge_start=covered_start_s,
                )
                return jsonify({"ok": True, "job_id": job_id, "cache_id": cache_id, "cache_append": True, "append_from": _dt_to_rfc3339_utc(append_from)})

            sliding_merge_rows = None
            sliding_series = None
            try:
                rk = str(cache_key.get("range") or "").strip().lower()
                covered_start_s = str((payload or {}).get("covered_start") or "").strip()
                covered_stop_s = str((payload or {}).get("covered_stop") or "").strip()
                covered_start_dt = _parse_iso_datetime(covered_start_s) if covered_start_s else None
                covered_stop_dt = _parse_iso_datetime(covered_stop_s) if covered_stop_s else None
                cache_rows_ok = isinstance(cache_rows, list) and len(cache_rows) > 0
                old_span = (covered_stop_dt - covered_start_dt).total_seconds() if covered_start_dt and covered_stop_dt else None
                new_span = (stop_dt - start_dt).total_seconds()
                if (
                    _stats_cache_sliding_supported(rk)
                    and cache_rows_ok
                    and not bool(meta.get("dirty"))
                    and not bool(meta.get("mismatch"))
                    and covered_start_dt and covered_stop_dt
                    and start_dt > covered_start_dt
                    and stop_dt > covered_stop_dt
                    and old_span is not None
                    and abs(old_span - new_span) <= 60.0
                ):
                    left_rows = _stats_cache_discover_series_span(cfg, covered_start_dt, start_dt, ff, measurement_filter, entity_id_filter, friendly_name_filter)
                    right_rows = _stats_cache_discover_series_span(cfg, covered_stop_dt, stop_dt, ff, measurement_filter, entity_id_filter, friendly_name_filter)
                    changed_keys = {
                        _stats_row_identity(r)
                        for r in list(left_rows or []) + list(right_rows or [])
                        if isinstance(r, dict)
                    }
                    if changed_keys:
                        sliding_merge_rows = [r for r in (cache_rows or []) if isinstance(r, dict) and _stats_row_identity(r) not in changed_keys]
                        series_map: dict[tuple[str, str, str, str], dict[str, Any]] = {}
                        for r in (cache_rows or []):
                            if not isinstance(r, dict):
                                continue
                            k = _stats_row_identity(r)
                            if k in changed_keys:
                                series_map[k] = {
                                    "measurement": k[0],
                                    "field": k[1],
                                    "entity_id": k[2],
                                    "friendly_name": k[3],
                                }
                        for r in list(left_rows or []) + list(right_rows or []):
                            if not isinstance(r, dict):
                                continue
                            k = _stats_row_identity(r)
                            if k in changed_keys:
                                series_map[k] = {
                                    "measurement": k[0],
                                    "field": k[1],
                                    "entity_id": k[2],
                                    "friendly_name": k[3],
                                }
                        sliding_series = list(series_map.values())
            except Exception:
                sliding_merge_rows = None
                sliding_series = None

            if sliding_merge_rows is not None and sliding_series is not None:
                meta["dirty"] = True
                meta["dirty_reason"] = "sliding_trim_append"
                meta["dirty_at"] = _utc_now_iso_ms()
                _stats_cache_write_meta(meta)
                job_id = _global_stats_start_job(
                    cfg,
                    start_dt,
                    stop_dt,
                    ff,
                    measurement_filter,
                    entity_id_filter,
                    friendly_name_filter,
                    sliding_series,
                    columns,
                    page_limit,
                    trigger_page="stats",
                    cache_id=cache_id,
                    cache_key=cache_key,
                    cache_merge_rows=sliding_merge_rows,
                    cache_merge_start=_dt_to_rfc3339_utc(start_dt),
                )
                return jsonify({"ok": True, "job_id": job_id, "cache_id": cache_id, "cache_slide": True, "cache_prefill": True})

            stale_prefill = bool(cache_rows) and not bool(meta.get("mismatch"))
            if stale_prefill:
                stale_seed_series = [
                    {
                        "measurement": str(r.get("measurement") or ""),
                        "field": str(r.get("field") or ""),
                        "entity_id": str(r.get("entity_id") or ""),
                        "friendly_name": str(r.get("friendly_name") or ""),
                    }
                    for r in (cache_rows or []) if isinstance(r, dict)
                ]
                try:
                    stale_discover_after = str((payload or {}).get("covered_stop") or "").strip() or None
                except Exception:
                    stale_discover_after = None
                meta["last_used_at"] = _utc_now_iso_ms()
                _stats_cache_write_meta(meta)
            meta["dirty"] = True
            meta["dirty_reason"] = "job_start"
            meta["dirty_at"] = _utc_now_iso_ms()
            _stats_cache_write_meta(meta)
    except Exception:
        cache_id = None
        cache_key = None

    job_id = _global_stats_start_job(
        cfg,
        start_dt,
        stop_dt,
        ff,
        measurement_filter,
        entity_id_filter,
        friendly_name_filter,
        stale_seed_series or series_list,
        columns,
        page_limit,
        trigger_page="stats",
        cache_id=cache_id,
        cache_key=cache_key,
        cache_discover_after=stale_discover_after,
    )
    return jsonify({"ok": True, "job_id": job_id, "cache_id": cache_id, "cache_prefill": bool(stale_prefill), "cache_hit": False})


@app.get("/api/global_stats_job/status")
def api_global_stats_job_status():
    job_id = (request.args.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    job = _job_get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    return jsonify({"ok": True, "status": _job_public(job)})


@app.get("/api/global_stats_job/result")
def api_global_stats_job_result():
    job_id = (request.args.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400

    partial = str(request.args.get("partial") or "").strip().lower() in ("1", "true", "yes")

    with GLOBAL_STATS_LOCK:
        job = GLOBAL_STATS_JOBS.get(job_id)
        if not job:
            LOG.warning("api.global_stats_job.result job_id=%s not found (expired or deleted)", job_id)
            return jsonify({"ok": False, "error": "job not found or expired", "expired": True}), 404
        state = str(job.get("state") or "")
        rows_all = list(job.get("rows") or [])
        cols = list(job.get("columns") or []) if isinstance(job.get("columns"), list) else []
        cache_id = str(job.get("cache_id") or "").strip() or None

    if state != "done" and not partial:
        return jsonify({"ok": True, "ready": False, "rows": [], "state": state, "columns": cols, "cache_id": cache_id})

    try:
        limit = int(request.args.get("limit", "5000"))
    except Exception:
        limit = 5000
    if limit < 1:
        limit = 1
    if limit > 20000:
        limit = 20000

    try:
        offset = int(request.args.get("offset", "0"))
    except Exception:
        offset = 0
    if offset < 0:
        offset = 0

    return jsonify({
        "ok": True,
        "ready": (state == "done"),
        "state": state,
        "rows": rows_all[offset : offset + limit],
        "total": len(rows_all),
        "columns": cols,
        "cache_id": cache_id,
    })


@app.post("/api/ui_event")
def api_ui_event():
    """Log UI events (button clicks etc.) for debugging."""

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}

    try:
        page = str(body.get("page") or "").strip()[:40]
        ui = str(body.get("ui") or "").strip()[:120]
        text = str(body.get("text") or "").strip()[:120]
        extra = body.get("extra")
        extra_s = ""
        if isinstance(extra, dict):
            # keep small and non-sensitive
            safe = {str(k)[:40]: str(v)[:120] for k, v in list(extra.items())[:10]}
            extra_s = json.dumps(safe, ensure_ascii=True)
        elif extra is not None:
            extra_s = str(extra)[:200]

        _ui_action_append({
            "page": page,
            "ui": ui,
            "text": text,
            "extra": extra,
            "ip": request.headers.get("X-Forwarded-For") or request.remote_addr or "",
            "ua": (request.headers.get("User-Agent") or "")[:80],
        })
        LOG.info("ui_event page=%s ui=%s text=%s extra=%s", page, ui, text, extra_s)

        try:
            _trace_add_ui_event(page, ui, text, extra)
        except Exception:
            pass
    except Exception:
        pass

    return jsonify({"ok": True})


@app.get("/api/trace/recent")
def api_trace_recent():
    if not TRACE_ENABLED:
        return jsonify({"ok": True, "enabled": False, "traces": []})
    try:
        limit = int(request.args.get("limit", "200"))
    except Exception:
        limit = 200
    limit = max(1, min(2000, limit))
    with TRACE_LOCK:
        tids = list(TRACE_MEM)[-limit:]
        xs = []
        for tid in tids:
            tr = TRACE_INDEX.get(tid)
            if isinstance(tr, dict):
                xs.append(_trace_summary(tr))
    return jsonify({"ok": True, "enabled": True, "traces": xs})


@app.get("/api/trace/<trace_id>")
def api_trace_get(trace_id: str):
    if not TRACE_ENABLED:
        return jsonify({"ok": False, "error": "tracing disabled"}), 400
    tid = str(trace_id or "").strip()
    if not tid:
        return jsonify({"ok": False, "error": "trace_id required"}), 400
    with TRACE_LOCK:
        tr = TRACE_INDEX.get(tid)
    if not tr:
        return jsonify({"ok": False, "error": "trace not found"}), 404
    try:
        if isinstance(tr, dict):
            _trace_normalize(tr, tid)
    except Exception:
        pass
    return jsonify({"ok": True, "trace": tr})


@app.post("/api/trace/client_span")
def api_trace_client_span():
    if not TRACE_ENABLED:
        return jsonify({"ok": True})
    body = request.get_json(force=True) or {}
    if not isinstance(body, dict):
        return jsonify({"ok": False, "error": "body must be object"}), 400
    tid = str(body.get("trace_id") or "").strip()
    if not tid:
        return jsonify({"ok": False, "error": "trace_id required"}), 400
    span = {
        "trace_id": tid,
        "span_id": str(body.get("span_id") or ""),
        "action": str(body.get("action") or ""),
        "page": str(body.get("page") or ""),
        "started_at": str(body.get("started_at") or ""),
        "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "kind": "http.client",
        "method": str(body.get("method") or ""),
        "url": _redact_secrets(str(body.get("url") or ""))[:400],
        "status_code": int(body.get("status_code") or 0),
        "dur_ms": int(body.get("dur_ms") or 0),
        "status": str(body.get("status") or ""),
    }
    _trace_add_client_span(span)
    return jsonify({"ok": True})


@app.post("/api/page_view")
def api_page_view():
    """Log page view events."""
    try:
        body = request.get_json(force=True) or {}
        page = str(body.get("page") or "").strip()[:80]
        LOG.info("page_view page=%s from=%s", page, request.remote_addr)
    except Exception:
        pass
    return jsonify({"ok": True})


@app.get("/api/ui_state")
def api_ui_state_get():
    prefix = str(request.args.get("prefix") or "").strip()
    st = _ui_state_load()
    if prefix:
        out = {k: v for k, v in st.items() if isinstance(k, str) and k.startswith(prefix)}
    else:
        out = dict(st)

    # Safety cap
    if len(out) > 5000:
        keys = sorted(out.keys())[:5000]
        out = {k: out[k] for k in keys}
    return jsonify({"ok": True, "items": out, "total": len(out)})


@app.post("/api/ui_state/set")
def api_ui_state_set():
    body = request.get_json(force=True) or {}

    items = body.get("items") if isinstance(body, dict) else None
    if items is None:
        # also allow single key/value
        k = body.get("key") if isinstance(body, dict) else None
        v = body.get("value") if isinstance(body, dict) else None
        items = {k: v} if k else {}

    if not isinstance(items, dict):
        return jsonify({"ok": False, "error": "items must be an object"}), 400

    st = _ui_state_load()
    changed = 0
    deleted = 0

    for k0, v0 in items.items():
        k = str(k0 or "").strip()
        if not _ui_state_key_ok(k):
            continue

        if v0 is None:
            if k in st:
                st.pop(k, None)
                deleted += 1
            continue

        # store as string (raw); caller can store JSON string if needed
        v = v0 if isinstance(v0, str) else json.dumps(v0, ensure_ascii=True)
        if not _ui_state_val_ok(v):
            continue
        if st.get(k) != v:
            st[k] = v
            changed += 1

    if changed or deleted:
        _ui_state_save(st)

    return jsonify({"ok": True, "changed": changed, "deleted": deleted, "total": len(st)})


@app.post("/api/ui_state/prune")
def api_ui_state_prune():
    body = request.get_json(force=True) or {}
    prefix = str(body.get("prefix") or "").strip()
    keep = body.get("keep")
    if not prefix:
        return jsonify({"ok": False, "error": "prefix required"}), 400
    if not _ui_state_key_ok(prefix):
        return jsonify({"ok": False, "error": "invalid prefix"}), 400
    if keep is None:
        keep = []
    if not isinstance(keep, list):
        return jsonify({"ok": False, "error": "keep must be a list"}), 400

    keep_set: set[str] = set()
    for k0 in keep:
        try:
            k = str(k0 or "").strip()
        except Exception:
            continue
        if not _ui_state_key_ok(k):
            continue
        if not k.startswith(prefix):
            continue
        keep_set.add(k)

    st = _ui_state_load()
    to_del = [k for k in st.keys() if isinstance(k, str) and k.startswith(prefix) and k not in keep_set]
    for k in to_del:
        st.pop(k, None)
    if to_del:
        _ui_state_save(st)
    return jsonify({"ok": True, "deleted": len(to_del), "prefix": prefix})


@app.get("/api/app_state")
def api_app_state_get():
    scope = str(request.args.get("scope") or "").strip()
    st = _app_state_load()
    if not scope:
        return jsonify({"ok": True, "state": st})
    val = st.get(scope) if isinstance(st, dict) else None
    return jsonify({"ok": True, "scope": scope, "state": val if isinstance(val, dict) else {}})


@app.post("/api/app_state/set")
def api_app_state_set():
    body = request.get_json(force=True) or {}
    scope = str(body.get("scope") or "").strip()
    state = body.get("state") if isinstance(body.get("state"), dict) else None
    if not scope:
        return jsonify({"ok": False, "error": "scope required"}), 400
    if state is None:
        return jsonify({"ok": False, "error": "state must be an object"}), 400
    st = _app_state_load()
    st[scope] = state
    _app_state_save(st)
    return jsonify({"ok": True, "scope": scope})


@app.get("/api/ui_profiles")
def api_ui_profiles_list():
    _profiles_ensure_defaults()
    active = _active_profile_get()
    return jsonify({"ok": True, "active": active, "profiles": _profile_list()})


@app.get("/api/ui_profiles/get")
def api_ui_profiles_get():
    _profiles_ensure_defaults()
    pid = str(request.args.get("id") or "").strip()
    if not _profile_id_ok(pid):
        return jsonify({"ok": False, "error": "invalid profile id"}), 400
    prof = _profile_load(pid)
    if not prof:
        return jsonify({"ok": False, "error": "profile not found"}), 404
    items = prof.get("items") if isinstance(prof.get("items"), dict) else {}
    # return only strings
    out_items: dict[str, str] = {}
    for k, v in items.items():
        if isinstance(k, str) and isinstance(v, str):
            out_items[k] = v
    return jsonify({"ok": True, "profile": {
        "id": str(prof.get("id") or pid),
        "label": str(prof.get("label") or pid),
        "updated_at": prof.get("updated_at"),
        "items": out_items,
        "count": len(out_items),
    }})


@app.post("/api/ui_profiles/create")
def api_ui_profiles_create():
    _profiles_ensure_defaults()
    body = request.get_json(force=True) or {}
    label = str(body.get("label") or "").strip()
    if not label:
        return jsonify({"ok": False, "error": "label required"}), 400
    pid = _profile_id_from_label(label)
    if not _profile_id_ok(pid):
        return jsonify({"ok": False, "error": "invalid profile id"}), 400
    path = _profile_path(pid)
    if path.exists():
        return jsonify({"ok": False, "error": "profile already exists"}), 400
    items = _ui_items_snapshot(prefix="influxbro")
    _profile_save(pid, label, items)
    return jsonify({"ok": True, "id": pid})


@app.post("/api/ui_profiles/rename")
def api_ui_profiles_rename():
    _profiles_ensure_defaults()
    body = request.get_json(force=True) or {}
    pid = str(body.get("id") or "").strip()
    label = str(body.get("label") or "").strip()
    if not _profile_id_ok(pid):
        return jsonify({"ok": False, "error": "invalid profile id"}), 400
    if not label:
        return jsonify({"ok": False, "error": "label required"}), 400
    prof = _profile_load(pid)
    if not prof:
        return jsonify({"ok": False, "error": "profile not found"}), 404
    items = prof.get("items") if isinstance(prof.get("items"), dict) else {}
    out_items: dict[str, str] = {}
    for k, v in items.items():
        if isinstance(k, str) and isinstance(v, str):
            out_items[k] = v
    _profile_save(pid, label, out_items)
    return jsonify({"ok": True})


@app.post("/api/ui_profiles/delete")
def api_ui_profiles_delete():
    _profiles_ensure_defaults()
    body = request.get_json(force=True) or {}
    pid = str(body.get("id") or "").strip()
    if not _profile_id_ok(pid):
        return jsonify({"ok": False, "error": "invalid profile id"}), 400
    path = _profile_path(pid)
    if not path.exists():
        return jsonify({"ok": False, "error": "profile not found"}), 404
    try:
        path.unlink(missing_ok=True)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500

    # adjust active if needed
    if _active_profile_get() == pid:
        xs = _profile_list()
        new_active = xs[0]["id"] if xs else None
        if new_active:
            _active_profile_set(str(new_active))
        else:
            try:
                UI_PROFILE_ACTIVE_PATH.unlink(missing_ok=True)
            except Exception:
                pass
    return jsonify({"ok": True})


@app.post("/api/ui_profiles/save")
def api_ui_profiles_save():
    _profiles_ensure_defaults()
    body = request.get_json(force=True) or {}
    pid = str(body.get("id") or "").strip()
    if not _profile_id_ok(pid):
        return jsonify({"ok": False, "error": "invalid profile id"}), 400
    prof = _profile_load(pid)
    if not prof:
        return jsonify({"ok": False, "error": "profile not found"}), 404
    label = str(prof.get("label") or pid)
    items = _ui_items_snapshot(prefix="influxbro")
    _profile_save(pid, label, items)
    return jsonify({"ok": True})


@app.post("/api/ui_profiles/apply")
def api_ui_profiles_apply():
    _profiles_ensure_defaults()
    body = request.get_json(force=True) or {}
    pid = str(body.get("id") or "").strip()
    if not _profile_id_ok(pid):
        return jsonify({"ok": False, "error": "invalid profile id"}), 400
    prof = _profile_load(pid)
    if not prof:
        return jsonify({"ok": False, "error": "profile not found"}), 404
    items = prof.get("items") if isinstance(prof.get("items"), dict) else {}

    # Replace all influxbro* keys in the global UI state with the profile content.
    st = _ui_state_load()
    for k in list(st.keys()):
        try:
            if isinstance(k, str) and k.startswith("influxbro"):
                st.pop(k, None)
        except Exception:
            continue
    for k, v in items.items():
        if isinstance(k, str) and isinstance(v, str) and _ui_state_key_ok(k) and _ui_state_val_ok(v):
            st[k] = v
    _ui_state_save(st)

    _active_profile_set(pid)
    return jsonify({"ok": True, "active": pid})


@app.get("/api/dashboard_last")
def api_dashboard_last():
    """Return last dashboard graph result from /data (cache-only; no DB query)."""

    _profiles_ensure_defaults()
    j = _dash_last_load() or {}
    cache_id = str(j.get("cache_id") or "").strip()
    if not cache_id:
        return jsonify({"ok": True, "found": False})

    meta = _dash_cache_load_meta(cache_id)
    payload = _dash_cache_load_payload(cache_id)
    if not meta or not payload or not bool(payload.get("ok")):
        return jsonify({"ok": True, "found": False, "cache_id": cache_id})

    try:
        _dash_cache_touch_used(cache_id)
    except Exception:
        pass

    sel = j.get("selection") if isinstance(j.get("selection"), dict) else {}
    return jsonify({
        "ok": True,
        "found": True,
        "cache_id": cache_id,
        "updated_at": meta.get("updated_at"),
        "selection": sel,
        "payload": payload,
        "cache": {
            "id": cache_id,
            "updated_at": meta.get("updated_at"),
            "dirty": bool(meta.get("dirty")),
            "mismatch": bool(meta.get("mismatch")),
        },
    })


@app.get("/api/cache_usage")
def api_cache_usage():
    try:
        limit = int(request.args.get("limit", "500"))
    except Exception:
        limit = 500
    rows = _cache_usage_tail(limit)
    return jsonify({"ok": True, "rows": rows, "total": len(rows)})


@app.post("/api/cache_usage/clear")
def api_cache_usage_clear():
    _cache_usage_clear()
    return jsonify({"ok": True, "message": "Cache usage log cleared."})


@app.get("/api/storage_usage")
def api_storage_usage():
    """Diagnostics: report disk usage for persisted artifacts (/data + backup dir)."""

    try:
        cfg = _overlay_from_yaml_if_enabled(load_cfg())
    except Exception:
        cfg = load_cfg()

    def _safe_stat(p: Path) -> dict[str, Any]:
        try:
            st = p.stat()
            return {"exists": True, "is_dir": p.is_dir(), "bytes": int(st.st_size), "mtime": st.st_mtime}
        except Exception:
            return {"exists": False, "is_dir": False, "bytes": 0, "mtime": None}

    def _dir_size(p: Path) -> tuple[int, int]:
        total = 0
        files = 0
        try:
            if not p.exists() or not p.is_dir():
                return 0, 0
        except Exception:
            return 0, 0
        try:
            for root, _dirs, fnames in os.walk(p):
                for fn in fnames:
                    try:
                        fp = Path(root) / fn
                        st = fp.stat()
                        total += int(st.st_size)
                        files += 1
                    except Exception:
                        continue
        except Exception:
            return total, files
        return total, files

    def _fmt_day(iso: str | None) -> str | None:
        try:
            if not iso:
                return None
            d = _trace_parse_iso(str(iso))
            if not d:
                return None
            return d.astimezone(timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            return None

    def _storage_hist_append(total_bytes: int, disk_total: int | None, disk_free: int | None) -> None:
        # Best-effort: one line per day.
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            return

        path = DATA_DIR / "storage_usage_history.jsonl"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        try:
            if path.exists():
                # Check last non-empty line day
                last_day = None
                try:
                    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
                    for ln in reversed(lines):
                        if not ln.strip():
                            continue
                        try:
                            j = json.loads(ln)
                            last_day = _fmt_day(str(j.get("at") or ""))
                        except Exception:
                            last_day = None
                        break
                except Exception:
                    last_day = None
                if last_day == today:
                    return
        except Exception:
            pass

        try:
            row = {
                "at": _utc_now_iso_ms(),
                "total_bytes": int(total_bytes),
                "disk_total": int(disk_total) if disk_total is not None else None,
                "disk_free": int(disk_free) if disk_free is not None else None,
            }
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=True) + "\n")
        except Exception:
            return

    def _storage_hist_tail(max_days: int = 400) -> list[dict[str, Any]]:
        path = DATA_DIR / "storage_usage_history.jsonl"
        out: list[dict[str, Any]] = []
        try:
            if not path.exists():
                return []
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return []

        # Keep last N distinct days.
        seen_days: set[str] = set()
        for ln in reversed(lines):
            if not ln.strip():
                continue
            try:
                j = json.loads(ln)
            except Exception:
                continue
            if not isinstance(j, dict):
                continue
            day = _fmt_day(str(j.get("at") or ""))
            if not day:
                continue
            if day in seen_days:
                continue
            seen_days.add(day)
            out.append(j)
            if len(out) >= max_days:
                break
        out.reverse()
        return out

    # Inventory of persisted artifacts
    items: list[dict[str, Any]] = []
    entries: list[tuple[str, Path]] = [
        ("log_file", LOG_FILE),
        ("runtime_cfg", RUNTIME_CFG_FILE),
        ("dash_last", DASH_LAST_PATH),
        ("ui_state", UI_STATE_PATH),
        ("app_state", APP_STATE_PATH),
        ("ui_profile_active", UI_PROFILE_ACTIVE_PATH),
        ("history", HISTORY_PATH),
        ("cache_usage", CACHE_USAGE_PATH),
        ("ui_actions", UI_ACTIONS_PATH),
        ("worklog", ANALYSIS_HISTORY_PATH),
        ("traces", TRACE_PATH),
        ("quality_cleanup_log", QUALITY_CLEANUP_LOG_PATH),
        ("monitor_cfg", MONITOR_CFG_PATH),
        ("monitor_state", MONITOR_STATE_PATH),
        ("monitor_pending", MONITOR_PENDING_PATH),
        ("monitor_events", MONITOR_EVENTS_PATH),
        ("jobs_history", JOBS_HISTORY_PATH),
        ("timers_state", TIMERS_STATE_PATH),
        ("analysis_start_cache", ANALYSIS_START_CACHE_PATH),
        ("exports_dir", EXPORT_DIR),
        ("imports_dir", IMPORT_DIR),
        ("ui_profiles_dir", UI_PROFILES_DIR),
        ("dash_cache_dir", DASH_CACHE_DIR),
        ("analysis_cache_dir", ANALYSIS_CACHE_DIR),
        ("stats_cache_dir", STATS_CACHE_DIR),
        ("series_stats_cache_dir", SERIES_STATS_CACHE_DIR),
        ("old_default_backups", OLD_DEFAULT_BACKUP_DIR),
        ("backup_dir", backup_dir(cfg)),
        ("config_influxbro_dir", (CONFIG_DIR / "influxbro")),
        ("storage_usage_history", (DATA_DIR / "storage_usage_history.jsonl")),
    ]

    for name, p in entries:
        st = _safe_stat(p)
        row = {
            "name": name,
            "path": str(p),
            "exists": bool(st.get("exists")),
            "kind": "dir" if bool(st.get("is_dir")) else "file",
            "bytes": 0,
            "files": None,
            "mtime": st.get("mtime"),
        }
        if row["exists"] and row["kind"] == "dir":
            b, n = _dir_size(p)
            row["bytes"] = b
            row["files"] = n
        elif row["exists"]:
            row["bytes"] = int(st.get("bytes") or 0)
        items.append(row)

    try:
        du = shutil.disk_usage(DATA_DIR)
        disk = {"path": str(DATA_DIR), "total": int(du.total), "used": int(du.used), "free": int(du.free)}
    except Exception:
        disk = {"path": str(DATA_DIR), "total": None, "used": None, "free": None}

    total_bytes = sum(int(it.get("bytes") or 0) for it in items)
    items.sort(key=lambda r: int(r.get("bytes") or 0), reverse=True)

    try:
        _storage_hist_append(total_bytes, disk.get("total"), disk.get("free"))
    except Exception:
        pass
    hist = _storage_hist_tail(400)

    try:
        budget_mb = int(cfg.get("storage_budget_mb", 0) or 0)
    except Exception:
        budget_mb = 0

    return jsonify({
        "ok": True,
        "disk": disk,
        "total_bytes": total_bytes,
        "items": items,
        "history": hist,
        "storage_budget_mb": budget_mb,
        "backup_min_free_mb": int(cfg.get("backup_min_free_mb", 0) or 0),
        "backup_dir": str(backup_dir(cfg)),
    })


@app.post("/api/cache_usage/ui_event")
def api_cache_usage_ui_event():
    """Record a UI-level cache usage event (e.g., button clicks) for the usage table."""

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}
    try:
        cfg = _overlay_from_yaml_if_enabled(load_cfg())
    except Exception:
        cfg = load_cfg()

    try:
        kind = str(body.get("kind") or "ui_event").strip()[:80]
        page = str(body.get("page") or "").strip()[:40]
        ui = str(body.get("ui") or "").strip()[:120]
        note = str(body.get("note") or body.get("text") or "").strip()[:400]
        run_id = str(body.get("run_id") or "").strip()[:80] or None
        _cache_usage_append(cfg, {
            "kind": kind,
            "page": page,
            "step": ui,
            "run_id": run_id,
            "note": note,
            "ip": _req_ip(),
        })
    except Exception:
        pass

    return jsonify({"ok": True})


@app.post("/api/analysis_history_event")
def api_analysis_history_event():
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}
    try:
        trace_id = str(body.get("trace_id") or "").strip()[:240]

        dur_ms: int | None = None
        try:
            if body.get("dur_ms") is not None:
                dur_ms = int(max(0, int(body.get("dur_ms") or 0)))
            else:
                extra0 = body.get("extra") if isinstance(body.get("extra"), dict) else None
                if extra0 and extra0.get("dur_ms") is not None:
                    dur_ms = int(max(0, int(extra0.get("dur_ms") or 0)))
        except Exception:
            dur_ms = None

        entry = {
            "kind": str(body.get("kind") or "analysis").strip()[:80],
            "step": str(body.get("step") or "").strip()[:120],
            "page": str(body.get("page") or "dashboard").strip()[:40],
            "measurement": str(body.get("measurement") or "").strip()[:200],
            "field": str(body.get("field") or "").strip()[:200],
            "entity_id": str(body.get("entity_id") or "").strip()[:200],
            "friendly_name": str(body.get("friendly_name") or "").strip()[:200],
            "detail": str(body.get("detail") or "").strip()[:4000],
            "status": str(body.get("status") or "").strip()[:40],
            "trace_id": trace_id,
            "dur_ms": dur_ms,
            "summary": body.get("summary") if isinstance(body.get("summary"), dict) else None,
            "extra": body.get("extra") if isinstance(body.get("extra"), dict) else None,
            "ip": _req_ip(),
            "ua": _req_ua(),
        }
        _analysis_history_append(entry)
        try:
            LOG.info(
                "analysis_event trace_id=%s dur_ms=%s kind=%s step=%s status=%s detail=%s extra=%s",
                str(entry.get("trace_id") or "-"),
                str(entry.get("dur_ms") if entry.get("dur_ms") is not None else 0),
                str(entry.get("kind") or ""),
                str(entry.get("step") or ""),
                str(entry.get("status") or ""),
                _redact_secrets(str(entry.get("detail") or "")[:400]),
                _redact_secrets(_json_short(entry.get("extra") if isinstance(entry.get("extra"), dict) else {}, 1200)),
            )
        except Exception:
            pass
    except Exception:
        pass
    return jsonify({"ok": True})


@app.get("/api/analysis_history")
def api_analysis_history():
    try:
        limit = int(request.args.get("limit", "500"))
    except Exception:
        limit = 500
    rows = _analysis_history_tail(limit)
    return jsonify({"ok": True, "rows": rows, "total": len(rows)})


@app.post("/api/worklog/event")
def api_worklog_event():
    """Alias for /api/analysis_history_event (UI worklog)."""

    return api_analysis_history_event()


@app.get("/api/worklog")
def api_worklog():
    """Alias for /api/analysis_history."""

    return api_analysis_history()


@app.post("/api/series_stats")
def api_series_stats():
    """Return basic stats for a measurement/field series."""
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None

    LOG.info("api.series_stats measurement=%s field=%s entity_id=%s",
        measurement, field, entity_id)

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    try:
        with v2_client(cfg) as c:
            qapi = c.query_api()
            # Get count, min, max, first, last
            q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: -10y)
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> filter(fn: (r) => r._field == "{field}")'''
            if entity_id:
                q += f'\n  |> filter(fn: (r) => r.entity_id == "{entity_id}")'
            if friendly_name:
                q += f'\n  |> filter(fn: (r) => r.friendly_name == "{friendly_name}")'
            q += '''
  |> group()
  |> sort(columns: ["_time"])
'''
            # Run multiple aggregations
            count_q = q + '  |> count()\n'
            min_q = q + '  |> min()\n'
            max_q = q + '  |> max()\n'
            first_q = q + '  |> first()\n'
            last_q = q + '  |> last()\n'

            stats: dict[str, Any] = {}
            try:
                for rec in qapi.query(count_q, org=cfg["org"]):
                    stats["count"] = rec.get_value()
            except Exception:
                pass
            try:
                for rec in qapi.query(min_q, org=cfg["org"]):
                    stats["min"] = rec.get_value()
            except Exception:
                pass
            try:
                for rec in qapi.query(max_q, org=cfg["org"]):
                    stats["max"] = rec.get_value()
            except Exception:
                pass
            try:
                for rec in qapi.query(first_q, org=cfg["org"]):
                    stats["oldest_time"] = rec.get_time()
                    stats["current_value"] = rec.get_value()
            except Exception:
                pass
            try:
                for rec in qapi.query(last_q, org=cfg["org"]):
                    stats["newest_time"] = rec.get_time()
                    stats["current_value"] = rec.get_value()
            except Exception:
                pass

            return jsonify({"ok": True, "stats": stats})
    except Exception as e:
        LOG.error("api.series_stats error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


def _client_event_log(kind_hint: str) -> Response:
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}

    try:
        page = str(body.get("page") or "").strip()[:80]
        message = str(body.get("message") or "").strip()[:500]
        href = str(body.get("href") or "").strip()[:500]
        ua = str(body.get("ua") or "").strip()[:200]
        stack = str(body.get("stack") or "").strip()[:4000]
        extra = body.get("extra")
        try:
            extra_s = json.dumps(extra, ensure_ascii=True)[:2000] if extra is not None else ""
        except Exception:
            extra_s = str(extra)[:2000] if extra is not None else ""

        kind = ""
        if isinstance(extra, dict):
            try:
                kind = str(extra.get("kind") or "").strip().lower()
            except Exception:
                kind = ""

        log_fn = LOG.error if kind_hint == "error" else LOG.info
        if kind in ("analysis_debug", "selector_debug", "ui_debug"):
            log_fn = LOG.info

        log_fn(
            "client_%s page=%s msg=%s href=%s ua=%s stack=%s extra=%s",
            kind_hint,
            page,
            message,
            href,
            ua,
            stack,
            extra_s,
        )
    except Exception:
        # Never fail the request.
        pass

    return jsonify({"ok": True})


@app.post("/api/client_error")
def api_client_error():
    """Receive client-side browser errors and write them to the server log."""

    return _client_event_log("error")


@app.post("/api/client_log")
def api_client_log():
    """Receive client-side info/debug events and write them to the server log."""

    return _client_event_log("log")


@app.post("/api/global_stats_job/cancel")
def api_global_stats_job_cancel():
    body = request.get_json(force=True) or {}
    job_id = (body.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with GLOBAL_STATS_LOCK:
        job = GLOBAL_STATS_JOBS.get(job_id)
        if not job:
            return jsonify({"ok": False, "error": "job not found"}), 404
        job["cancelled"] = True
    try:
        LOG.info("job_cancel type=global_stats job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
    except Exception:
        pass
    return jsonify({"ok": True})


@app.post("/api/global_series_page")
def api_global_series_page():
    """Load a page of series matching a time window.

    Returns one row per series with newest_time + last_value.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "global_series currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    body = request.get_json(force=True) or {}
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    try:
        offset = int(body.get("offset", 0))
    except Exception:
        offset = 0
    if offset < 0:
        offset = 0

    try:
        limit = int(body.get("limit", 10))
    except Exception:
        limit = 10
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200

    field_filter = body.get("field_filter")
    ff = (str(field_filter) if field_filter is not None else "").strip()

    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    ff_clause = f"|> filter(fn: (r) => r._field == {_flux_str(ff)})" if ff else ""
    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => exists r._measurement and exists r._field)
  {ff_clause}
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_time","_value"])
  |> group(columns: ["_measurement","_field","entity_id","friendly_name"])
  |> last()
  |> group()
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit}, offset: {offset})
'''

    rows: list[dict[str, Any]] = []
    try:
        with v2_client(cfg) as c:
            tables = c.query_api().query(q, org=cfg["org"])
            for t in tables or []:
                for rec in getattr(t, "records", []) or []:
                    vals = getattr(rec, "values", {}) or {}
                    m = str(vals.get("_measurement") or "")
                    f = str(vals.get("_field") or "")
                    eid = str(vals.get("entity_id") or "")
                    fn = str(vals.get("friendly_name") or "")
                    newest = rec.get_time() or vals.get("_time")
                    newest_s = None
                    if isinstance(newest, datetime):
                        newest_s = _dt_to_rfc3339_utc(newest)
                    elif isinstance(newest, str) and newest.strip():
                        newest_s = newest.strip()
                    rows.append({
                        "measurement": m,
                        "field": f,
                        "entity_id": eid,
                        "friendly_name": fn,
                        "newest_time": newest_s,
                        "last_value": rec.get_value(),
                        "oldest_time": None,
                        "count": None,
                        "min": None,
                        "max": None,
                        "mean": None,
                    })
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

    return jsonify({"ok": True, "rows": rows, "offset": offset, "limit": limit})


@app.post("/api/global_series_total")
def api_global_series_total():
    """Return total number of series for a time window (best effort)."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "global_series currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    body = request.get_json(force=True) or {}
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    field_filter = body.get("field_filter")
    ff = (str(field_filter) if field_filter is not None else "").strip()

    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    ff_clause = f"|> filter(fn: (r) => r._field == {_flux_str(ff)})" if ff else ""
    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => exists r._measurement and exists r._field)
  {ff_clause}
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_time","_value"])
  |> group(columns: ["_measurement","_field","entity_id","friendly_name"])
  |> last()
  |> group()
  |> count(column: "_value")
'''

    total: int | None = None
    try:
        with v2_client(cfg) as c:
            tables = c.query_api().query(q, org=cfg["org"])
            for t in tables or []:
                for rec in getattr(t, "records", []) or []:
                    v = rec.get_value()
                    if isinstance(v, (int, float)):
                        total = int(v)
                        break
                if total is not None:
                    break
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

    return jsonify({"ok": True, "total_series": total})


@app.post("/api/global_series_details")
def api_global_series_details():
    """Load detailed stats for a set of series keys."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "global_series currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    body = request.get_json(force=True) or {}
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    series = body.get("series") or []
    if not isinstance(series, list) or not series:
        return jsonify({"ok": False, "error": "series list required"}), 400
    if len(series) > 50:
        return jsonify({"ok": False, "error": "series list too large (max 50)"}), 400

    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)

    parts: list[str] = []
    keys: list[tuple[str, str, str, str]] = []
    for it in series:
        if not isinstance(it, dict):
            continue
        m = str(it.get("measurement") or "").strip()
        f = str(it.get("field") or "").strip()
        eid = str(it.get("entity_id") or "").strip()
        fn = str(it.get("friendly_name") or "").strip()
        if not m or not f:
            continue
        conds = [f"r._measurement == {_flux_str(m)}", f"r._field == {_flux_str(f)}"]
        if eid:
            conds.append(f"r.entity_id == {_flux_str(eid)}")
        if fn:
            conds.append(f"r.friendly_name == {_flux_str(fn)}")
        parts.append("(" + " and ".join(conds) + ")")
        keys.append((m, f, eid, fn))

    if not parts:
        return jsonify({"ok": False, "error": "no valid series keys"}), 400

    predicate = " or ".join(parts)
    q = f'''
data = from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => {predicate})
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","_time","_value"])
  |> group(columns: ["_measurement","_field","entity_id","friendly_name"])

data
  |> reduce(
    identity: {{seen: false, count: 0, sum: 0.0, min: 0.0, max: 0.0, oldest_time: time(v: "1970-01-01T00:00:00Z"), newest_time: time(v: "1970-01-01T00:00:00Z"), last_value: 0.0}},
    fn: (r, accumulator) => ({{
      seen: true,
      count: accumulator.count + 1,
      sum: accumulator.sum + float(v: r._value),
      min: if accumulator.seen == false then float(v: r._value) else if float(v: r._value) < accumulator.min then float(v: r._value) else accumulator.min,
      max: if accumulator.seen == false then float(v: r._value) else if float(v: r._value) > accumulator.max then float(v: r._value) else accumulator.max,
      oldest_time: if accumulator.seen == false then r._time else if r._time < accumulator.oldest_time then r._time else accumulator.oldest_time,
      newest_time: if accumulator.seen == false then r._time else if r._time > accumulator.newest_time then r._time else accumulator.newest_time,
      last_value: if accumulator.seen == false then float(v: r._value) else if r._time >= accumulator.newest_time then float(v: r._value) else accumulator.last_value,
    }})
  )
  |> map(fn: (r) => ({{
    _measurement: r._measurement,
    _field: r._field,
    entity_id: r.entity_id,
    friendly_name: r.friendly_name,
    count: r.count,
    min: r.min,
    max: r.max,
    mean: if r.count > 0 then r.sum / float(v: r.count) else 0.0,
    oldest_time: r.oldest_time,
    newest_time: r.newest_time,
    last_value: r.last_value,
  }}))
  |> keep(columns: ["_measurement","_field","entity_id","friendly_name","count","min","max","mean","oldest_time","newest_time","last_value"])
'''

    out_rows: list[dict[str, Any]] = []
    try:
        with v2_client(cfg) as c:
            tables = c.query_api().query(q, org=cfg["org"])
            for t in tables or []:
                for rec in getattr(t, "records", []) or []:
                    vals = getattr(rec, "values", {}) or {}
                    out_rows.append({
                        "measurement": str(vals.get("_measurement") or ""),
                        "field": str(vals.get("_field") or ""),
                        "entity_id": str(vals.get("entity_id") or ""),
                        "friendly_name": str(vals.get("friendly_name") or ""),
                        "count": int(vals.get("count") or 0),
                        "min": vals.get("min"),
                        "max": vals.get("max"),
                        "mean": vals.get("mean"),
                        "oldest_time": str(vals.get("oldest_time") or "") or None,
                        "newest_time": str(vals.get("newest_time") or "") or None,
                        "last_value": vals.get("last_value"),
                    })
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

    return jsonify({"ok": True, "rows": out_rows})


@app.post("/api/outliers")
def api_outliers():
    """Find outliers in a time window (raw points).

    Uses the graph time window (start/stop) and returns matching points.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}

    measurement = (body.get("measurement") or "").strip()
    field = (body.get("field") or "").strip()
    entity_id = (body.get("entity_id") or "").strip() or None
    friendly_name = (body.get("friendly_name") or "").strip() or None
    unit = (body.get("unit") or "").strip()

    LOG.info("api.outliers called from=%s measurement=%s field=%s",
        request.remote_addr, measurement, field)

    if not measurement or not field:
        LOG.warning("api.outliers rejected: missing measurement or field")
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    t0 = time.monotonic()
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "outliers currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    search_types = body.get("search_types") or []
    if isinstance(search_types, str):
        search_types = [t.strip() for t in search_types.split(",") if t.strip()]

    include_null = "null" in search_types or bool(body.get("include_null", False))
    include_zero = "zero" in search_types or bool(body.get("include_zero", False))
    include_gap = "gap" in search_types or bool(body.get("include_gap", False))
    bounds_enabled = "bounds" in search_types or bool(body.get("bounds_enabled", False))
    min_v = body.get("min")
    max_v = body.get("max")
    counter_enabled = "counter" in search_types or bool(body.get("counter_enabled", False))
    counter_decrease = "decrease" in search_types or bool(body.get("counter_decrease", True))
    counter_max_step = "counter" in search_types or bool(body.get("counter_max_step", True))
    fault_phase_enabled = "fault_phase" in search_types or bool(body.get("fault_phase_enabled", False))

    # Optional value filter mode (e.g. free filter on the dashboard).
    value_filter_enabled = bool(body.get("value_filter_enabled", False))
    value_mode = str(body.get("value_mode") or body.get("mode") or "or").strip().lower()
    value_mode = "and" if value_mode == "and" else "or"
    value_a_op = str(body.get("value_a_op") or body.get("a_op") or "").strip()
    value_b_op = str(body.get("value_b_op") or body.get("b_op") or "").strip()
    value_a_raw = body.get("value_a_val") if ("value_a_val" in body) else body.get("a_val")
    value_b_raw = body.get("value_b_val") if ("value_b_val" in body) else body.get("b_val")
    value_a_raw = "" if value_a_raw is None else str(value_a_raw).strip()
    value_b_raw = "" if value_b_raw is None else str(value_b_raw).strip()

    return_all = bool(body.get("return_all", False))

    try:
        min_num = float(min_v) if bounds_enabled and min_v is not None and str(min_v).strip() != "" else None
    except Exception:
        min_num = None
    try:
        max_num = float(max_v) if bounds_enabled and max_v is not None and str(max_v).strip() != "" else None
    except Exception:
        max_num = None

    if bounds_enabled and min_num is None and max_num is None:
        bounds_enabled = False

    max_step = _outlier_max_step(cfg, measurement, unit)
    try:
        if "max_step" in body and body.get("max_step") is not None and str(body.get("max_step")).strip() != "":
            max_step = float(body.get("max_step"))
    except Exception:
        pass
    gap_seconds = _outlier_gap_seconds(cfg)
    try:
        if "gap_seconds" in body and body.get("gap_seconds") is not None and str(body.get("gap_seconds")).strip() != "":
            gap_seconds = float(body.get("gap_seconds"))
    except Exception:
        pass

    extra = flux_tag_filter(entity_id, friendly_name)
    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    # Note: scanning is done chunked (see _scan_span_split below).

    # Always scan in chunks to support large time windows.
    # If a chunk still contains too many points, split it recursively.
    MAX_SCAN_CHUNK = 200000
    MAX_OUT = int(cfg.get("ui_raw_outlier_search_limit", 5000) or 5000)
    MIN_CHUNK_SECONDS = 5 * 60
    limit = MAX_OUT

    rows: list[dict[str, Any]] = []
    scanned = 0
    point_index = 0

    # Optional: compute raw-context windows (N points before/after) during the scan.
    # This avoids a later /api/outlier_windows full recompute and allows persisting windows
    # into analysis_cache rows.
    window_cfg = body.get("window_cfg") if isinstance(body.get("window_cfg"), dict) else None
    compute_windows = bool(window_cfg)
    try:
        win_n_before = int((window_cfg or {}).get("n_before") or 0)
    except Exception:
        win_n_before = 0
    try:
        win_n_after = int((window_cfg or {}).get("n_after") or 0)
    except Exception:
        win_n_after = 0
    win_n_before = max(0, min(5000, win_n_before))
    win_n_after = max(0, min(5000, win_n_after))
    compute_windows = compute_windows and win_n_before > 0 and win_n_after > 0
    win_algo_v = 1
    if compute_windows:
        try:
            win_algo_v = int((window_cfg or {}).get("algo_v") or 1)
        except Exception:
            win_algo_v = 1
        win_algo_v = 1

    window_state_in = body.get("window_state") if isinstance(body.get("window_state"), dict) else {}
    window_updates: list[dict[str, Any]] = []
    window_state_out: dict[str, Any] | None = None

    # Window computation state (carried across chunk requests)
    win_before_buf: list[str] = []
    win_pending: dict[int, list[dict[str, Any]]] = {}
    if compute_windows:
        try:
            point_index = int(window_state_in.get("point_index") or 0)
        except Exception:
            point_index = 0
        try:
            prev_buf = window_state_in.get("before_buf") if isinstance(window_state_in.get("before_buf"), list) else []
            win_before_buf = [str(x) for x in prev_buf if str(x).strip()][-win_n_before:]
        except Exception:
            win_before_buf = []
        try:
            pending_in = window_state_in.get("pending") if isinstance(window_state_in.get("pending"), dict) else {}
            for k, v in pending_in.items():
                try:
                    ti = int(k)
                except Exception:
                    continue
                if not isinstance(v, list):
                    continue
                items = []
                for it in v:
                    if not isinstance(it, dict):
                        continue
                    t = str(it.get("time") or "").strip()
                    if not t:
                        continue
                    items.append({
                        "time": t,
                        "center": str(it.get("center") or t).strip() or t,
                        "before_time": str(it.get("before_time") or "").strip() or None,
                        "before_count": int(it.get("before_count") or 0),
                    })
                if items:
                    win_pending[ti] = items
        except Exception:
            win_pending = {}

    def _win_flush_for_index(cur_idx: int, cur_iso: str) -> None:
        """Resolve any pending outliers whose target index is reached."""

        nonlocal window_updates
        if not compute_windows:
            return
        items = win_pending.pop(int(cur_idx), None)
        if not items:
            return
        for it in items:
            center_iso = str(it.get("center") or it.get("time") or "").strip()
            if not center_iso:
                continue
            before_iso = str(it.get("before_time") or "").strip() or None
            before_count = int(it.get("before_count") or 0)
            after_iso = cur_iso
            after_count = int(win_n_after)
            before_minutes = None
            after_minutes = None
            center_minutes = None
            try:
                if before_iso:
                    bd = _parse_iso_datetime(before_iso)
                    cd = _parse_iso_datetime(center_iso)
                    if bd and cd:
                        before_minutes = (cd - bd).total_seconds() / 60.0
            except Exception:
                before_minutes = None
            try:
                ad = _parse_iso_datetime(after_iso)
                cd2 = _parse_iso_datetime(center_iso)
                if ad and cd2:
                    after_minutes = (ad - cd2).total_seconds() / 60.0
            except Exception:
                after_minutes = None
            if before_minutes is not None and after_minutes is not None:
                center_minutes = max(before_minutes, after_minutes)
            elif before_minutes is not None:
                center_minutes = before_minutes
            elif after_minutes is not None:
                center_minutes = after_minutes
            window_updates.append({
                "time": center_iso,
                "window": {
                    "n_before": int(win_n_before),
                    "n_after": int(win_n_after),
                    "algo_v": int(win_algo_v),
                    "center_minutes": round(center_minutes, 2) if center_minutes is not None else None,
                    "before_minutes": round(before_minutes, 2) if before_minutes is not None else None,
                    "after_minutes": round(after_minutes, 2) if after_minutes is not None else None,
                    "before_count": int(before_count),
                    "after_count": int(after_count),
                    "before_time": before_iso,
                    "after_time": after_iso,
                },
            })
    return_checkpoints = bool(body.get("return_checkpoints", False))
    checkpoint_seconds = _analysis_cache_checkpoint_interval_seconds({
        "analysis_cache_checkpoint_seconds": body.get("checkpoint_seconds")
    })
    checkpoints: list[dict[str, Any]] = []
    next_checkpoint_dt = start_dt if return_checkpoints else None
    prev_val: float | None = body.get("prev_value")
    prev_time_dt: datetime | None = None
    last_time_iso: str | None = None
    counter_base_val: float | None = body.get("counter_base_value")
    try:
        pt = body.get("prev_time")
        if pt is not None and str(pt).strip() != "":
            prev_time_dt = _parse_iso_datetime(str(pt))
    except Exception:
        prev_time_dt = None

    scan_state_in = body.get("scan_state") or {}
    fault_state = {
        "status": str(scan_state_in.get("status") or "normal"),
        "last_valid_value": scan_state_in.get("last_valid_value"),
        "fault_started_at": str(scan_state_in.get("fault_started_at") or "") or None,
        "fault_count": int(scan_state_in.get("fault_count") or 0),
        "recovery_streak": int(scan_state_in.get("recovery_streak") or 0),
        "last_reason": str(scan_state_in.get("last_reason") or "") or None,
        "fault_ended_at": str(scan_state_in.get("fault_ended_at") or "") or None,
    }
    try:
        recovery_valid_streak = int(body.get("recovery_valid_streak") or 2)
    except Exception:
        recovery_valid_streak = 2
    recovery_valid_streak = max(1, recovery_valid_streak)

    LOG.info("api.outlier_search starting scan with types=%s", search_types)

    LOG.info("api.outlier_search starting scan with types=%s", search_types)

    def _cmp(op: str, v: float, ref: float) -> bool:
        if op == ">":
            return v > ref
        if op == ">=":
            return v >= ref
        if op == "<":
            return v < ref
        if op == "<=":
            return v <= ref
        return True

    def _append_checkpoint(at_dt: datetime, prev: float | None) -> None:
        if not return_checkpoints:
            return
        at_iso = _dt_to_rfc3339_utc_ms(at_dt)
        if checkpoints and str(checkpoints[-1].get("at") or "") == at_iso:
            return
        checkpoints.append({
            "at": at_iso,
            **_analysis_cache_state_snapshot(
                last_time_iso,
                prev,
                counter_base_val,
                fault_state if fault_phase_enabled else None,
            ),
        })

    def _scan_span(qapi: Any, a: datetime, b: datetime, prev: float | None) -> float | None:
        nonlocal scanned, rows, last_time_iso, counter_base_val, prev_time_dt, point_index, next_checkpoint_dt, win_before_buf

        span_s = (b - a).total_seconds()
        chunk_t0 = time.monotonic()

        if len(rows) >= limit:
            LOG.debug("api.outlier_search _scan_span LIMIT reached, returning early")
            return prev

        s_iso = _dt_to_rfc3339_utc(a)
        e_iso = _dt_to_rfc3339_utc(b)

        q_span = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{s_iso}"), stop: time(v: "{e_iso}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time", "_value"])
  |> group()
  |> sort(columns: ["_time"])
  |> limit(n: {MAX_SCAN_CHUNK + 1})
'''

        scanned_local = 0
        for rec in qapi.query_stream(q_span, org=cfg["org"]):
            scanned_local += 1
            scanned += 1
            point_index += 1
            if scanned_local > MAX_SCAN_CHUNK:
                LOG.warning("api.outlier_search _scan_span OVERFLOW at chunk a=%s b=%s scanned_local=%d",
                    _dt_to_rfc3339_utc(a), _dt_to_rfc3339_utc(b), scanned_local)
                raise OverflowError("too_many_points")

            t = rec.get_time()
            v = rec.get_value()
            while return_checkpoints and isinstance(t, datetime) and next_checkpoint_dt is not None and t >= next_checkpoint_dt:
                _append_checkpoint(next_checkpoint_dt, prev)
                next_checkpoint_dt = next_checkpoint_dt + timedelta(seconds=checkpoint_seconds)
            iso = _dt_to_rfc3339_utc_ms(t) if isinstance(t, datetime) else None
            if iso:
                last_time_iso = iso

            if compute_windows and iso:
                # First: resolve pending outliers whose after-target is this point.
                _win_flush_for_index(point_index, iso)

            gap_detected = False
            gap_label = ""
            prev_for_delta = prev
            if isinstance(t, datetime) and prev_time_dt is not None and gap_seconds is not None:
                gap_s = (t - prev_time_dt).total_seconds()
                if gap_s > float(gap_seconds):
                    gap_detected = True
                    gap_label = f"gap > {int(float(gap_seconds))}s ({int(gap_s)}s)"
                    prev_for_delta = None
                    if fault_phase_enabled:
                        fault_state["status"] = "normal"
                        fault_state["fault_started_at"] = None
                        fault_state["fault_count"] = 0
                        fault_state["recovery_streak"] = 0
                        fault_state["last_reason"] = None

            reasons: list[str] = []
            if v is None:
                if fault_phase_enabled:
                    reasons.append("ungueltiger Wert")
                    fault_state["status"] = "fault_active"
                    fault_state["fault_started_at"] = fault_state.get("fault_started_at") or iso
                    fault_state["fault_count"] = int(fault_state.get("fault_count") or 0) + 1
                    fault_state["recovery_streak"] = 0
                    fault_state["last_reason"] = "ungueltiger Wert"
                if include_null:
                    row_obj: dict[str, Any] = {"time": iso, "value": None, "reason": "NULL", "type": "null", "point_index": point_index}
                    if compute_windows and iso:
                        before_iso = win_before_buf[0] if win_before_buf else None
                        before_count = int(len(win_before_buf))
                        row_obj["window"] = {
                            "n_before": int(win_n_before),
                            "n_after": int(win_n_after),
                            "algo_v": int(win_algo_v),
                            "center_minutes": None,
                            "before_minutes": None,
                            "after_minutes": None,
                            "before_count": int(before_count),
                            "after_count": 0,
                            "before_time": before_iso,
                            "after_time": None,
                        }
                        target = int(point_index) + int(win_n_after)
                        win_pending.setdefault(target, []).append({
                            "time": iso,
                            "center": iso,
                            "before_time": before_iso,
                            "before_count": int(before_count),
                        })
                    rows.append(row_obj)
                    LOG.info("api.outlier_search found NULL at %s", iso)
                    if len(rows) >= limit:
                        return prev

                if compute_windows and iso:
                    # Include NULL points in the point-based context stream.
                    win_before_buf.append(iso)
                    if len(win_before_buf) > win_n_before:
                        win_before_buf = win_before_buf[-win_n_before:]
                continue

            if isinstance(v, bool) or not isinstance(v, (int, float)):
                if compute_windows and iso:
                    win_before_buf.append(iso)
                    if len(win_before_buf) > win_n_before:
                        win_before_buf = win_before_buf[-win_n_before:]
                continue

            fv = float(v)
            finite = math.isfinite(fv)

            if include_gap and gap_detected:
                reasons.append(gap_label)
            if include_zero and fv == 0.0:
                reasons.append("0")
                LOG.info("api.outlier_search found 0 at %s value=%s", iso, fv)
            if bounds_enabled:
                try:
                    min_num = float(min_v) if min_v is not None and str(min_v).strip() != "" else None
                except Exception:
                    min_num = None
                try:
                    max_num = float(max_v) if max_v is not None and str(max_v).strip() != "" else None
                except Exception:
                    max_num = None
                if min_num is not None and fv < min_num:
                    reasons.append(f"< min ({min_num})")
                if max_num is not None and fv > max_num:
                    reasons.append(f"> max ({max_num})")

            if counter_enabled and prev_for_delta is not None:
                d = fv - prev_for_delta
                if counter_decrease and d < 0:
                    reasons.append("counter decrease")
                    counter_base_val = float(prev_for_delta)
                if "decrease" not in search_types and counter_decrease is False:
                    pass
                if max_step is not None and d > float(max_step):
                    reasons.append(f"step > {max_step} {unit or ''}".strip())

            if fault_phase_enabled:
                phase_reasons: list[str] = []
                if not finite:
                    phase_reasons.append("ungueltiger Wert")
                elif fv == 0.0:
                    phase_reasons.append("0")
                if bounds_enabled:
                    try:
                        min_num2 = float(min_v) if min_v is not None and str(min_v).strip() != "" else None
                    except Exception:
                        min_num2 = None
                    try:
                        max_num2 = float(max_v) if max_v is not None and str(max_v).strip() != "" else None
                    except Exception:
                        max_num2 = None
                    if min_num2 is not None and finite and fv < min_num2:
                        if "< min ({})".format(min_num2) not in phase_reasons:
                            phase_reasons.append(f"< min ({min_num2})")
                    if max_num2 is not None and finite and fv > max_num2:
                        if "> max ({})".format(max_num2) not in phase_reasons:
                            phase_reasons.append(f"> max ({max_num2})")
                if prev_for_delta is not None and finite:
                    d = fv - prev_for_delta
                    if counter_decrease and d < 0:
                        phase_reasons.append("counter decrease")
                    if max_step is not None and d > float(max_step):
                        phase_reasons.append(f"step > {max_step} {unit or ''}".strip())

                status = str(fault_state.get("status") or "normal")
                last_valid_value = fault_state.get("last_valid_value")
                valid_candidate = finite and not phase_reasons
                plausible_return = valid_candidate
                if plausible_return and last_valid_value is not None and max_step is not None:
                    try:
                        plausible_return = abs(fv - float(last_valid_value)) <= float(max_step)
                    except Exception:
                        plausible_return = True

                if status == "normal":
                    if phase_reasons:
                        fault_state["status"] = "fault_active"
                        fault_state["fault_started_at"] = fault_state.get("fault_started_at") or iso
                        fault_state["fault_count"] = 1
                        fault_state["recovery_streak"] = 0
                        fault_state["last_reason"] = ", ".join(phase_reasons)
                        reasons = list(dict.fromkeys(reasons + phase_reasons))
                    elif finite:
                        fault_state["last_valid_value"] = fv
                        fault_state["fault_ended_at"] = None
                else:
                    if phase_reasons:
                        fault_state["status"] = "fault_active"
                        fault_state["fault_count"] = int(fault_state.get("fault_count") or 0) + 1
                        fault_state["recovery_streak"] = 0
                        fault_state["last_reason"] = ", ".join(phase_reasons)
                        reasons = list(dict.fromkeys(reasons + phase_reasons + ["fault_active"]))
                    elif plausible_return:
                        fault_state["status"] = "recovering"
                        fault_state["recovery_streak"] = int(fault_state.get("recovery_streak") or 0) + 1
                        if int(fault_state.get("recovery_streak") or 0) >= recovery_valid_streak:
                            fault_state["status"] = "normal"
                            fault_state["fault_ended_at"] = iso
                            fault_state["last_valid_value"] = fv
                            fault_state["fault_count"] = 0
                            fault_state["recovery_streak"] = 0
                            fault_state["last_reason"] = None
                        else:
                            reasons = list(dict.fromkeys(reasons + ["recovering"]))
                    else:
                        fault_state["status"] = "fault_active"
                        fault_state["fault_count"] = int(fault_state.get("fault_count") or 0) + 1
                        fault_state["recovery_streak"] = 0
                        reasons = list(dict.fromkeys(reasons + ["fault_active"]))

            if reasons:
                type_labels = []
                for r in reasons:
                    if "NULL" in r or "ungueltiger" in r:
                        type_labels.append("null")
                    elif r == "0":
                        type_labels.append("zero")
                    elif "< min" in r or "> max" in r:
                        type_labels.append("bounds")
                    elif "counter decrease" in r:
                        type_labels.append("counter")
                    elif "step >" in r:
                        type_labels.append("counter")
                    elif "fault_active" in r or "recovering" in r:
                        type_labels.append("fault_phase")
                    elif r.startswith("gap >"):
                        type_labels.append("gap")
                unique_types = list(dict.fromkeys(type_labels))

                cls = "primary"
                try:
                    if (
                        counter_base_val is not None
                        and any(r.startswith("step >") for r in reasons)
                        and max_step is not None
                        and abs(fv - float(counter_base_val)) <= float(max_step)
                        and not any(r == "counter decrease" for r in reasons)
                    ):
                        cls = "secondary"
                        counter_base_val = None
                except Exception:
                    cls = "primary"

                row_obj: dict[str, Any] = {
                    "time": iso,
                    "value": fv,
                    "reason": ", ".join(reasons),
                    "class": cls,
                    "types": unique_types,
                    "point_index": point_index,
                }
                if compute_windows and iso:
                    # before-context comes from points strictly before the center point.
                    before_iso = win_before_buf[0] if win_before_buf else None
                    before_count = int(len(win_before_buf))
                    row_obj["window"] = {
                        "n_before": int(win_n_before),
                        "n_after": int(win_n_after),
                        "algo_v": int(win_algo_v),
                        "center_minutes": None,
                        "before_minutes": None,
                        "after_minutes": None,
                        "before_count": int(before_count),
                        "after_count": 0,
                        "before_time": before_iso,
                        "after_time": None,
                    }
                    # after-context will be filled when N points after are reached.
                    target = int(point_index) + int(win_n_after)
                    win_pending.setdefault(target, []).append({
                        "time": iso,
                        "center": iso,
                        "before_time": before_iso,
                        "before_count": int(before_count),
                    })
                rows.append(row_obj)
                if len(rows) >= limit:
                    return fv

            if compute_windows and iso:
                # Update before-buffer after processing this center point.
                win_before_buf.append(iso)
                if len(win_before_buf) > win_n_before:
                    win_before_buf = win_before_buf[-win_n_before:]

            prev = fv
            if isinstance(t, datetime):
                prev_time_dt = t
            if isinstance(t, datetime):
                prev_time_dt = t

        chunk_dur = time.monotonic() - chunk_t0
        LOG.info("api.outlier_search _scan_span DONE a=%s b=%s span=%.0fs scanned_local=%d total_scanned=%d total_rows=%d dur=%.1fs",
            _dt_to_rfc3339_utc(a), _dt_to_rfc3339_utc(b), span_s, scanned_local, scanned, len(rows), chunk_dur)
        return prev

    def _scan_span_split(qapi: Any, a: datetime, b: datetime, prev: float | None) -> float | None:
        span_s = max(0.0, (b - a).total_seconds())
        try:
            LOG.debug("api.outlier_search _scan_span_split PROCESSING chunk a=%s b=%s span=%.0fs",
                _dt_to_rfc3339_utc(a), _dt_to_rfc3339_utc(b), span_s)
            return _scan_span(qapi, a, b, prev)
        except OverflowError:
            if span_s <= MIN_CHUNK_SECONDS:
                LOG.warning("api.outlier_search _scan_span_split OVERFLOW at min chunk a=%s b=%s span=%.0fs",
                    _dt_to_rfc3339_utc(a), _dt_to_rfc3339_utc(b), span_s)
                raise
            mid = a + timedelta(seconds=(span_s / 2.0))
            LOG.info("api.outlier_search _scan_span_split SPLITTING chunk a=%s b=%s span=%.0fs -> two halves",
                _dt_to_rfc3339_utc(a), _dt_to_rfc3339_utc(b), span_s)
            prev2 = _scan_span_split(qapi, a, mid, prev)
            return _scan_span_split(qapi, mid, b, prev2)

    try:
        LOG.info("api.outlier_search entering scan loop")
        with v2_client(cfg) as c:
            qapi = c.query_api()
            try:
                prev_val = _scan_span_split(qapi, start_dt, stop_dt, prev_val)
            except OverflowError:
                LOG.error("api.outlier_search OVERFLOW: too many points even in smallest chunks")
                return jsonify({
                    "ok": False,
                    "error": f"Zu viele Punkte im Zeitraum ({MAX_SCAN_CHUNK}+ in kleinstem Chunk). Bitte im Graph weiter reinzoomen.",
                }), 413

        dur_ms = int((time.monotonic() - t0) * 1000)
        LOG.info("api.outlier_search done from=%s scanned=%d found=%d dur=%dms limit=%d truncated=%s",
            request.remote_addr, scanned, len(rows), dur_ms, limit, len(rows) >= limit)
        LOG.info("api.outlier_search result: last_time=%s prev_val=%s counter_base=%s",
            last_time_iso, prev_val, counter_base_val)

        while return_checkpoints and next_checkpoint_dt is not None and next_checkpoint_dt < stop_dt:
            _append_checkpoint(next_checkpoint_dt, prev_val)
            next_checkpoint_dt = next_checkpoint_dt + timedelta(seconds=checkpoint_seconds)
        if return_checkpoints:
            _append_checkpoint(stop_dt, prev_val)

        if compute_windows:
            # Note: we don't flush remaining pending items; if the analysis window ends,
            # those outliers legitimately have no 'after' context within start/stop.
            window_state_out = {
                "algo_v": int(win_algo_v),
                "n_before": int(win_n_before),
                "n_after": int(win_n_after),
                "point_index": int(point_index),
                "before_buf": win_before_buf[-win_n_before:],
                "pending": {str(k): v for k, v in win_pending.items()},
            }

        try:
            _worklog_append_op(
                purpose="analysis",
                op="outliers_scan",
                status="ok",
                detail=f"Ausreisser-Suche: scanned={scanned} found={len(rows)} types={','.join([str(t) for t in (search_types or [])])}",
                measurement=str(measurement),
                field=str(field),
                entity_id=str(entity_id or ""),
                friendly_name=str(friendly_name or ""),
                window_start=str(start),
                window_stop=str(stop),
                source="db",
                reason_code="analysis_chunk",
                reason_label="Ausreisser-Suche (Chunk/Zeitraum).",
                duration_ms=dur_ms,
                counts={"scanned": scanned, "found": len(rows), "checkpoints": len(checkpoints)},
                extra={"search_types": search_types, "truncated": bool(len(rows) >= limit)},
            )
        except Exception:
            pass

        return jsonify({
            "ok": True,
            "rows": rows,
            "scanned": scanned,
            "start": start,
            "stop": stop,
            "limit": limit,
            "truncated": len(rows) >= limit,
            "last_time": last_time_iso,
            "last_value": prev_val,
            "counter_base_value": counter_base_val,
            "scan_state": fault_state if fault_phase_enabled else None,
            "checkpoints": checkpoints,
            "window_state": window_state_out,
            "window_updates": window_updates,
        })
    except Exception as e:
        dur_ms = int((time.monotonic() - t0) * 1000)
        LOG.error("api.outlier_search error: %s dur=%dms", e, dur_ms, exc_info=True)
        try:
            _worklog_append_op(
                purpose="analysis",
                op="outliers_scan",
                status="err",
                detail=f"Ausreisser-Suche Fehler: {_short_influx_error(e)}",
                measurement=str(measurement),
                field=str(field),
                entity_id=str(entity_id or ""),
                friendly_name=str(friendly_name or ""),
                window_start=str(start),
                window_stop=str(stop),
                source="db",
                reason_code="analysis_chunk",
                duration_ms=dur_ms,
                counts={"scanned": scanned, "found": len(rows)},
            )
        except Exception:
            pass
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/outlier_windows")
def api_outlier_windows():
    """Compute per-outlier time windows based on point-count distance.

    For each outlier (identified by time + point_index), finds the N-th point
    before and after it in the raw data stream and computes the corresponding
    time deltas (before_minutes, after_minutes, center_minutes).

    Called once after analysis completes.
    """
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    start_str = str(body.get("start") or "").strip()
    stop_str = str(body.get("stop") or "").strip()
    outliers = body.get("outliers") or []

    # Context in points (before/after). Keep backward compatibility with legacy `n`.
    try:
        n_before = int(body.get("n_before") or body.get("n") or 10)
    except Exception:
        n_before = 10
    try:
        n_after = int(body.get("n_after") or body.get("n") or 10)
    except Exception:
        n_after = 10
    n_before = max(1, min(5000, n_before))
    n_after = max(1, min(5000, n_after))

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400
    if not outliers:
        return jsonify({"ok": True, "windows": []})

    t0 = time.monotonic()
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        LOG.error("api.outlier_windows parse_error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 400

    extra = flux_tag_filter(entity_id, friendly_name)
    s_iso = _dt_to_rfc3339_utc(start_dt)
    e_iso = _dt_to_rfc3339_utc(stop_dt)

    LOG.info(
        "api.outlier_windows called measurement=%s field=%s outliers=%d n_before=%d n_after=%d span=%.0fs",
        measurement,
        field,
        len(outliers),
        n_before,
        n_after,
        (stop_dt - start_dt).total_seconds(),
    )

    windows: list[dict[str, Any]] = []
    query_count = 0
    expand_count = 0

    def _neighbors_for_time(qapi, center_dt: datetime, span_s: int) -> tuple[list[str], list[str]]:
        """Returns (older_times_desc, newer_times_asc) within a limited span.

        Important: do not rely on server-side sort/limit semantics for correctness.
        Tests use FakeQueryApi implementations that ignore the query string.
        """

        nonlocal query_count
        span = max(1, int(span_s))
        a = max(start_dt, center_dt - timedelta(seconds=span))
        b = min(stop_dt, center_dt + timedelta(seconds=span))
        c_iso = _dt_to_rfc3339_utc(center_dt)
        a_iso = _dt_to_rfc3339_utc(a)
        b_iso = _dt_to_rfc3339_utc(b)

        # Flux range stop is exclusive; keep explicit _time filters as well so
        # the center point is excluded deterministically.
        q_old = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{a_iso}"), stop: time(v: "{c_iso}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> filter(fn: (r) => r._time < time(v: "{c_iso}"))
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"], desc: true)
    |> limit(n: {n_before})
'''
        q_new = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{c_iso}"), stop: time(v: "{b_iso}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> filter(fn: (r) => r._time > time(v: "{c_iso}"))
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"], desc: false)
    |> limit(n: {n_after})
'''

        older_dts: list[datetime] = []
        newer_dts: list[datetime] = []
        query_count += 2
        for rec in qapi.query_stream(q_old, org=cfg["org"]):
            try:
                t = rec.get_time()
                if isinstance(t, datetime):
                    if t < center_dt:
                        older_dts.append(t)
            except Exception:
                continue
        for rec in qapi.query_stream(q_new, org=cfg["org"]):
            try:
                t = rec.get_time()
                if isinstance(t, datetime):
                    if t > center_dt:
                        newer_dts.append(t)
            except Exception:
                continue

        # Normalize order + trim locally (FakeQueryApi may ignore Flux sort/limit).
        older_sorted = sorted(older_dts, reverse=True)[:n_before]
        newer_sorted = sorted(newer_dts)[:n_after]
        older = [_dt_to_rfc3339_utc_ms(t) for t in older_sorted]
        newer = [_dt_to_rfc3339_utc_ms(t) for t in newer_sorted]
        return older, newer

    def _point_index_for_time(qapi, center_dt: datetime, span_s: int) -> int | None:
        """Resolve 0-based point index from the series start for center_dt.

        Uses a cheap range query and counts points strictly before the center.
        This is deterministic in tests (FakeQueryApi yields synthetic points).
        """

        nonlocal query_count
        span = max(1, int(span_s))
        # Only need the left side; cap to overall start/stop.
        a = max(start_dt, center_dt - timedelta(seconds=span))
        c_iso = _dt_to_rfc3339_utc(center_dt)
        a_iso = _dt_to_rfc3339_utc(a)

        q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{a_iso}"), stop: time(v: "{c_iso}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> filter(fn: (r) => r._time < time(v: "{c_iso}"))
  |> keep(columns: ["_time"])
'''

        query_count += 1
        before = 0
        for rec in qapi.query_stream(q, org=cfg["org"]):
            try:
                t = rec.get_time()
                if isinstance(t, datetime) and t < center_dt:
                    before += 1
            except Exception:
                continue
        return before

    # Heuristic: start with a limited span and expand until we have enough neighbors.
    try:
        gap_s = int(cfg.get("outlier_gap_seconds_default", 300) or 300)
    except Exception:
        gap_s = 300
    base_span_s = max(3600, min(7 * 86400, max(3600, max(n_before, n_after) * max(1, gap_s) * 4)))

    try:
        with v2_client(cfg) as client:
            qapi = client.query_api()
            for ol in outliers:
                ol_time = str(ol.get("time") or "").strip()
                if not ol_time:
                    continue
                try:
                    center_dt = _parse_iso_datetime(ol_time)
                except Exception:
                    continue
                if center_dt < start_dt or center_dt > stop_dt:
                    continue

                span_s = base_span_s
                older: list[str] = []
                newer: list[str] = []
                resolved_idx: int | None = None
                for attempt in range(0, 4):
                    older, newer = _neighbors_for_time(qapi, center_dt, span_s)
                    # Resolve point_index using the same span so we can expand for sparse data.
                    try:
                        resolved_idx = _point_index_for_time(qapi, center_dt, span_s)
                    except Exception:
                        resolved_idx = None
                    if len(older) >= n_before and len(newer) >= n_after:
                        break
                    # Expand span for sparse data.
                    span_s = min(int((stop_dt - start_dt).total_seconds()), span_s * 4)
                    expand_count += 1

                before_time = older[-1] if older else None
                after_time = newer[-1] if newer else None
                before_count = len(older)
                after_count = len(newer)

                before_minutes = None
                after_minutes = None
                center_minutes = None
                if before_time:
                    try:
                        before_dt = _parse_iso_datetime(before_time)
                        before_minutes = (center_dt - before_dt).total_seconds() / 60.0
                    except Exception:
                        before_minutes = None
                if after_time:
                    try:
                        after_dt = _parse_iso_datetime(after_time)
                        after_minutes = (after_dt - center_dt).total_seconds() / 60.0
                    except Exception:
                        after_minutes = None

        # Keep the UI context display monotonic even if inconsistent data slipped through.
                if before_time:
                    try:
                        before_dt2 = _parse_iso_datetime(before_time)
                        if before_dt2 > center_dt:
                            before_time = None
                            before_count = 0
                            before_minutes = None
                    except Exception:
                        pass
                if after_time:
                    try:
                        after_dt2 = _parse_iso_datetime(after_time)
                        if after_dt2 < center_dt:
                            after_time = None
                            after_count = 0
                            after_minutes = None
                    except Exception:
                        pass

                if before_minutes is not None and after_minutes is not None:
                    center_minutes = max(before_minutes, after_minutes)
                elif before_minutes is not None:
                    center_minutes = before_minutes
                elif after_minutes is not None:
                    center_minutes = after_minutes

                # Prefer resolved index; fall back to the provided point_index.
                point_index = int(ol.get("point_index") or -1)
                if resolved_idx is not None:
                    point_index = int(resolved_idx)

                windows.append({
                    "time": _dt_to_rfc3339_utc_ms(center_dt),
                    "point_index": point_index,
                    "center_minutes": round(center_minutes, 2) if center_minutes is not None else None,
                    "before_minutes": round(before_minutes, 2) if before_minutes is not None else None,
                    "after_minutes": round(after_minutes, 2) if after_minutes is not None else None,
                    "before_count": before_count,
                    "after_count": after_count,
                    "before_time": before_time,
                    "after_time": after_time,
                })
    except Exception as e:
        LOG.error("api.outlier_windows query error: %s", e, exc_info=True)
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

    LOG.info(
        "api.outlier_windows computed %d windows in %.1fs (queries=%d expansions=%d base_span_s=%d)",
        len(windows),
        time.monotonic() - t0,
        query_count,
        expand_count,
        base_span_s,
    )
    try:
        _worklog_append_op(
            purpose="analysis",
            op="outlier_windows",
            status="ok",
            detail=f"Raw-Fenster berechnet: windows={len(windows)} queries={query_count} expansions={expand_count}",
            measurement=str(measurement),
            field=str(field),
            entity_id=str(entity_id or ""),
            friendly_name=str(friendly_name or ""),
            window_start=str(start_str),
            window_stop=str(stop_str),
            source="db",
            reason_code="raw_windows",
            reason_label="Raw-Kontextfenster um Ausreisser (N davor/N danach).",
            duration_ms=int(max(0.0, (time.monotonic() - t0) * 1000.0)),
            counts={"windows": len(windows), "queries": query_count, "expansions": expand_count},
        )
    except Exception:
        pass
    return jsonify({"ok": True, "windows": windows})


@app.post("/api/series_oldest")
def api_series_oldest():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    resolve_if_missing = bool(body.get("resolve_if_missing", True))

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    key = _analysis_series_key(measurement, field, entity_id, friendly_name)
    cache = _analysis_start_cache_load()
    item = cache.get(key) if isinstance(cache, dict) else None
    if isinstance(item, dict) and str(item.get("oldest_time") or "").strip():
        return jsonify({
            "ok": True,
            "key": key,
            "oldest_time": item.get("oldest_time"),
            "resolved_at": item.get("resolved_at"),
            "cached": True,
        })

    if not resolve_if_missing:
        return jsonify({"ok": True, "key": key, "cached": False, "oldest_time": None, "resolved_at": None})

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "series_oldest currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({"ok": False, "error": "InfluxDB v2 requires token, org, bucket."}), 400

    extra = flux_tag_filter(entity_id, friendly_name)
    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: 0)
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: 1)
'''
    try:
        oldest_time = None
        with v2_client(cfg) as c:
            tables = c.query_api().query(q, org=cfg["org"])
            for t in tables or []:
                for r in getattr(t, "records", []) or []:
                    ts = r.get_time()
                    if isinstance(ts, datetime):
                        oldest_time = _dt_to_rfc3339_utc(ts)
                        break
                if oldest_time:
                    break
        resolved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        cache[key] = {"oldest_time": oldest_time, "resolved_at": resolved_at}
        _analysis_start_cache_save(cache)
        return jsonify({
            "ok": True,
            "key": key,
            "oldest_time": oldest_time,
            "resolved_at": resolved_at,
            "cached": False,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/series_oldest/reset")
def api_series_oldest_reset():
    body = request.get_json(force=True) or {}
    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400
    key = _analysis_series_key(measurement, field, entity_id, friendly_name)
    cache = _analysis_start_cache_load()
    if isinstance(cache, dict) and key in cache:
        cache.pop(key, None)
        _analysis_start_cache_save(cache)
    return jsonify({"ok": True, "key": key})


@app.post("/api/resolve_signal")
def resolve_signal():
    """Resolve a friendly_name/entity_id to a likely measurement+field."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    friendly_name = (body.get("friendly_name") or "").strip() or None
    entity_id = (body.get("entity_id") or "").strip() or None
    range_key = body.get("range")
    measurement_filter = (body.get("measurement_filter") or body.get("measurement") or "").strip() or None

    if not friendly_name and not entity_id:
        return jsonify({"ok": False, "error": "friendly_name or entity_id required"}), 400

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    selector_range = _selector_range_key(range_key, start_dt, stop_dt)

    # resolve_signal is a selector-like helper. This repo now defaults selectors
    # to full history when no explicit time filter is provided.
    eff_range = selector_range

    try:
        if int(cfg.get("influx_version", 2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400

            extra = flux_tag_filter(entity_id, friendly_name)
            range_clause = _flux_range_clause(str(eff_range), start_dt, stop_dt)
            mfilter = f" and r._measurement == {_flux_str(measurement_filter)}" if measurement_filter else ""
            with v2_client(cfg) as c:
                q = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => exists r._measurement and exists r._field{extra}{mfilter})
  |> keep(columns: ["_measurement", "_field"])
  |> group(columns: ["_measurement", "_field"])
  |> limit(n: 1)
  |> group()
  |> limit(n: 200)
'''
                log_query("api.resolve_signal (flux)", q)
                tables = c.query_api().query(q, org=cfg["org"])
                combos: set[tuple[str, str]] = set()
                for t in tables:
                    for r in t.records:
                        m = r.values.get("_measurement")
                        f = r.values.get("_field")
                        if m and f:
                            combos.add((str(m), str(f)))

            if not combos:
                return jsonify({"ok": False, "error": "No matching series found for selection."}), 404

            # Pick a sensible default
            preferred = None
            if measurement_filter:
                # We already filtered by measurement; pick best field.
                value_fields = sorted([c for c in combos if c[1] == "value"])
                preferred = value_fields[0] if value_fields else sorted(combos)[0]
            elif ("state", "value") in combos:
                preferred = ("state", "value")
            else:
                value_fields = sorted([c for c in combos if c[1] == "value"])
                preferred = value_fields[0] if value_fields else sorted(combos)[0]

            measurements = sorted({m for m, _ in combos})
            fields = sorted({f for m, f in combos if m == preferred[0]})
            _log_selector_debug("resolve_signal", {
                "filters": {"measurement_filter": measurement_filter or "", "entity_id": entity_id or "", "friendly_name": friendly_name or "", "range": selector_range},
                "preferred_measurement": preferred[0],
                "preferred_field": preferred[1],
                "measurements": measurements,
                "fields": fields,
            })
            return jsonify({
                "ok": True,
                "measurement": preferred[0],
                "field": preferred[1],
                "measurements": measurements,
                "fields": fields,
            })

        # v1
        if not cfg.get("database"):
            return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
        c = v1_client(cfg)

        where = []
        if entity_id:
            where.append(f'"entity_id"=\'{_influxql_escape(entity_id)}\'')
        if friendly_name:
            where.append(f'"friendly_name"=\'{_influxql_escape(friendly_name)}\'')
        where_clause = ("WHERE " + " AND ".join(where)) if where else ""

        q_series = f"SHOW SERIES {where_clause} LIMIT 2000"
        log_query("api.resolve_signal (influxql series)", q_series)
        res = c.query(q_series)
        ms: set[str] = set()
        for _, points in res.items():
            for p in points:
                key = p.get("key")
                if not key:
                    continue
                m = str(key).split(",", 1)[0]
                if m:
                    ms.add(m)
        if not ms:
            return jsonify({"ok": False, "error": "No matching series found for selection."}), 404

        if measurement_filter:
            if measurement_filter not in ms:
                return jsonify({"ok": False, "error": "No matching series found for selected measurement."}), 404
            measurement = measurement_filter
        else:
            measurement = "state" if "state" in ms else sorted(ms)[0]
        q_fields = f'SHOW FIELD KEYS FROM "{measurement}"'
        log_query("api.resolve_signal (influxql fields)", q_fields)
        res_f = c.query(q_fields)
        fs: list[str] = []
        for _, points in res_f.items():
            for p in points:
                if p.get("fieldKey"):
                    fs.append(str(p.get("fieldKey")))
        fs = sorted(set(fs))
        field = "value" if "value" in fs else (fs[0] if fs else "")
        return jsonify({
            "ok": True,
            "measurement": measurement,
            "field": field,
            "measurements": sorted(ms),
            "fields": fs,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


def _dt_to_rfc3339_utc_full(dt: datetime) -> str:
    s = dt.astimezone(timezone.utc).isoformat()
    return s.replace("+00:00", "Z")


def _count_decimals(s: str) -> int:
    m = re.search(r"\.(\d+)$", (s or "").strip())
    return len(m.group(1)) if m else 0


@app.post("/api/apply_edits")
def apply_edits():
    """Apply point edits by writing new values at the same timestamp.

    Safety: requires explicit UI confirmation.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", False)
    ok_confirm = confirm is True or str(confirm).strip().lower() in ("1", "true", "yes", "on")
    if not ok_confirm:
        return jsonify({"ok": False, "error": "Confirmation required"}), 400

    measurement = (body.get("measurement") or "").strip()
    field = (body.get("field") or "").strip()
    entity_id = (body.get("entity_id") or "").strip() or None
    friendly_name = (body.get("friendly_name") or "").strip() or None
    edits = body.get("edits")

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400
    if not isinstance(edits, list) or not edits:
        return jsonify({"ok": False, "error": "edits must be a non-empty list"}), 400

    try:
        LOG.debug(
            "apply_edits measurement=%s field=%s entity_id=%s friendly_name=%s edits=%s",
            measurement,
            field,
            bool(entity_id),
            bool(friendly_name),
            len(edits),
        )
    except Exception:
        pass

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "apply_edits currently supports InfluxDB v2 only"}), 400

    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    extra = flux_tag_filter(entity_id, friendly_name)

    def _parse_decimal_payload(v: object) -> int:
        try:
            return int(v)
        except Exception:
            return -1

    try:
        with v2_client(cfg) as c:
            qapi = c.query_api()
            wapi = c.write_api(write_options=SYNCHRONOUS)
            applied = 0

            for e in edits:
                if not isinstance(e, dict):
                    return jsonify({"ok": False, "error": "each edit must be an object"}), 400

                time_raw = (e.get("time") or "").strip()
                new_raw = (e.get("new_value") or "").strip()
                expected_decimals = _parse_decimal_payload(e.get("decimals"))

                if not time_raw or not new_raw:
                    return jsonify({"ok": False, "error": "edit requires time and new_value"}), 400
                if expected_decimals < 0 or expected_decimals > 12:
                    return jsonify({"ok": False, "error": "invalid decimals"}), 400

                # Strict decimal validation based on UI expectation
                if _count_decimals(new_raw) != expected_decimals:
                    return (
                        jsonify({"ok": False, "error": f"invalid decimals for {time_raw}: expected {expected_decimals}"}),
                        400,
                    )

                try:
                    dt = _parse_iso_datetime(time_raw)
                except Exception as ex:
                    return jsonify({"ok": False, "error": f"invalid time: {ex}"}), 400

                # Find the original point (to preserve full tag set)
                start = _dt_to_rfc3339_utc_full(dt - timedelta(seconds=2))
                stop = _dt_to_rfc3339_utc_full(dt + timedelta(seconds=2))
                q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> group()
  |> sort(columns: ["_time"])
  |> limit(n: 50)
'''
                log_query("apply_edits find_orig (flux)", q)
                tables = qapi.query(q, org=cfg["org"])

                best_rec = None
                best_dt = None
                best_abs = None
                for t in tables or []:
                    for rec in getattr(t, "records", []) or []:
                        rdt = rec.get_time()
                        if not isinstance(rdt, datetime):
                            continue
                        delta = abs((rdt.astimezone(timezone.utc) - dt).total_seconds())
                        if best_abs is None or delta < best_abs:
                            best_abs = delta
                            best_rec = rec
                            best_dt = rdt

                if best_rec is None or best_abs is None or best_abs > 1.0:
                    return (
                        jsonify({"ok": False, "error": f"original point not found near: {time_raw}"}),
                        404,
                    )

                orig_val = best_rec.get_value()
                if isinstance(orig_val, bool) or not isinstance(orig_val, (int, float)):
                    return (
                        jsonify({"ok": False, "error": f"unsupported field type at {time_raw}"}),
                        400,
                    )

                # Parse new value, keep field type consistent
                if isinstance(orig_val, int) and not isinstance(orig_val, bool):
                    if expected_decimals != 0 or "." in new_raw:
                        return (
                            jsonify({"ok": False, "error": f"field is integer at {time_raw}; decimals must be 0"}),
                            400,
                        )
                    try:
                        new_val: int | float = int(new_raw)
                    except Exception:
                        return jsonify({"ok": False, "error": f"invalid integer at {time_raw}"}), 400
                else:
                    try:
                        new_val = float(new_raw)
                    except Exception:
                        return jsonify({"ok": False, "error": f"invalid float at {time_raw}"}), 400

                tags: dict[str, str] = {}
                for k, v in (getattr(best_rec, "values", {}) or {}).items():
                    if k in ("result", "table"):
                        continue
                    if k.startswith("_"):
                        continue
                    if v is None:
                        continue
                    # Influx tags are strings; coerce here.
                    tags[str(k)] = str(v)

                p = Point(measurement)
                for tk, tv in tags.items():
                    p = p.tag(tk, tv)
                p = p.field(field, new_val).time(dt, WritePrecision.NS)
                log_details(
                    "apply_edits write point time=%s orig=%s new=%s tags=%s",
                    _dt_to_rfc3339_utc_full(dt),
                    orig_val,
                    new_val,
                    ",".join(sorted(tags.keys())),
                )
                wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=p)
                applied += 1

            try:
                if applied > 0:
                    _dash_cache_mark_dirty_series(measurement, field, entity_id, friendly_name, "apply_edits")
                    _stats_cache_mark_dirty_series(measurement, field, entity_id, friendly_name, "apply_edits")
                    patch_job_id = _analysis_cache_mark_dirty_series(cfg, measurement, field, entity_id, friendly_name, "apply_edits")
                else:
                    patch_job_id = None
            except Exception:
                patch_job_id = None
            return jsonify({"ok": True, "message": f"Applied edits: {applied}", "applied": applied, "patch_job_id": patch_job_id})
    except Exception as ex:
        return jsonify({"ok": False, "error": _short_influx_error(ex)}), 500


@app.post("/api/apply_changes")
def apply_changes():
    """Apply staged changes from the dashboard.

    Supports:
    - overwrite: write new value at timestamp (preserve tags)
    - delete: delete the point at timestamp (narrow window + tag predicate)

    Safety: requires explicit UI confirmation.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", False)
    ok_confirm = confirm is True or str(confirm).strip().lower() in ("1", "true", "yes", "on")
    if not ok_confirm:
        return jsonify({"ok": False, "error": "Confirmation required"}), 400

    measurement = (body.get("measurement") or "").strip()
    field = (body.get("field") or "").strip()
    entity_id = (body.get("entity_id") or "").strip() or None
    friendly_name = (body.get("friendly_name") or "").strip() or None
    changes = body.get("changes")
    trigger_page = str(body.get("trigger_page") or "").strip() or None
    trigger_source = str(body.get("trigger_source") or "").strip() or None
    trigger_action = str(body.get("trigger_action") or "").strip() or None
    trigger_button = str(body.get("trigger_button") or "").strip() or None
    unit_default = str(body.get("unit") or "").strip()
    force_raw = body.get("force", False)
    force_default = force_raw is True or str(force_raw).strip().lower() in ("1", "true", "yes", "on")

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400
    if not isinstance(changes, list) or not changes:
        return jsonify({"ok": False, "error": "changes must be a non-empty list"}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "apply_changes currently supports InfluxDB v2 only"}), 400

    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    extra = flux_tag_filter(entity_id, friendly_name)

    def _pred_escape(v: str) -> str:
        return (v or "").replace("\\", "\\\\").replace('"', '\\"')

    def _predicate(measurement_s: str, field_s: str, tags: dict[str, str]) -> str:
        parts = [f'_measurement="{_pred_escape(measurement_s)}"', f'_field="{_pred_escape(field_s)}"']
        for k, v in (tags or {}).items():
            if not k:
                continue
            parts.append(f'{k}="{_pred_escape(v)}"')
        return " AND ".join(parts)

    applied = 0
    with v2_client(cfg) as c:
        qapi = c.query_api()
        wapi = c.write_api(write_options=SYNCHRONOUS)
        dapi = c.delete_api()

        for ch in changes:
            if not isinstance(ch, dict):
                return jsonify({"ok": False, "error": "each change must be an object"}), 400

            action = str(ch.get("action") or "").strip().lower()
            if action not in ("overwrite", "delete"):
                return jsonify({"ok": False, "error": "invalid action"}), 400

            time_raw = (ch.get("time") or "").strip()
            if not time_raw:
                return jsonify({"ok": False, "error": "change requires time"}), 400

            reason = str(ch.get("reason") or "").strip()[:200]
            unit = str(ch.get("unit") or unit_default or "").strip()
            force_raw = ch.get("force", False)
            force = force_default or (force_raw is True or str(force_raw).strip().lower() in ("1", "true", "yes", "on"))
            try:
                expected_decimals = int(ch.get("decimals", 0))
            except Exception:
                expected_decimals = 0
            if expected_decimals < 0 or expected_decimals > 12:
                expected_decimals = 0

            try:
                dt = _parse_iso_datetime(time_raw)
            except Exception as ex:
                return jsonify({"ok": False, "error": f"invalid time: {ex}"}), 400

            # Find original point (preserve full tag set; get old value)
            start = _dt_to_rfc3339_utc_full(dt - timedelta(seconds=2))
            stop = _dt_to_rfc3339_utc_full(dt + timedelta(seconds=2))
            q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> group()
  |> sort(columns: ["_time"])
  |> limit(n: 50)
'''
            tables = qapi.query(q, org=cfg["org"])
            best_rec = None
            best_abs = None
            for t in tables or []:
                for rec in getattr(t, "records", []) or []:
                    rdt = rec.get_time()
                    if not isinstance(rdt, datetime):
                        continue
                    delta = abs((rdt.astimezone(timezone.utc) - dt).total_seconds())
                    if best_abs is None or delta < best_abs:
                        best_abs = delta
                        best_rec = rec

            if best_rec is None or best_abs is None or best_abs > 1.0:
                return (
                    jsonify({"ok": False, "error": f"original point not found near: {time_raw}"}),
                    404,
                )

            old_val = best_rec.get_value()
            if isinstance(old_val, bool) or not isinstance(old_val, (int, float)):
                return (
                    jsonify({"ok": False, "error": f"unsupported field type at {time_raw}"}),
                    400,
                )

            tags: dict[str, str] = {}
            for k, v in (getattr(best_rec, "values", {}) or {}).items():
                if k in ("result", "table"):
                    continue
                if str(k).startswith("_"):
                    continue
                if v is None:
                    continue
                tags[str(k)] = str(v)

            new_val: int | float | None = None
            if action == "overwrite":
                new_raw = (ch.get("new_value") or "").strip()
                if not new_raw:
                    return jsonify({"ok": False, "error": "overwrite requires new_value"}), 400
                if _count_decimals(new_raw) != expected_decimals:
                    return (
                        jsonify({"ok": False, "error": f"invalid decimals for {time_raw}: expected {expected_decimals}"}),
                        400,
                    )
                if isinstance(old_val, int) and not isinstance(old_val, bool):
                    if expected_decimals != 0 or "." in new_raw:
                        return (
                            jsonify({"ok": False, "error": f"field is integer at {time_raw}; decimals must be 0"}),
                            400,
                        )
                    try:
                        new_val = int(new_raw)
                    except Exception:
                        return jsonify({"ok": False, "error": f"invalid integer at {time_raw}"}), 400
                else:
                    try:
                        new_val = float(new_raw)
                    except Exception:
                        return jsonify({"ok": False, "error": f"invalid float at {time_raw}"}), 400

                # Outlier rule guardrails (can be overridden via force=true)
                try:
                    ts_eff = dt.astimezone(timezone.utc) if isinstance(dt, datetime) else dt
                    chk = _check_outlier_edit_rules(cfg, measurement, field, entity_id, friendly_name, ts_eff, float(new_val), unit, tags)
                    viol = chk.get("violations") or []
                    if viol and not force:
                        return (
                            jsonify({
                                "ok": False,
                                "error": "Outlier-Regel verletzt. Schreiben blockiert.",
                                "violations": viol,
                                "meta": {"time": time_raw, **(chk.get("meta") or {})},
                                "can_force": True,
                            }),
                            409,
                        )
                    if force and reason and "[FORCED]" not in reason:
                        reason = (reason + " [FORCED]")[:200]
                    elif force and not reason:
                        reason = "[FORCED]"
                except Exception:
                    pass

                p = Point(measurement)
                for tk, tv in tags.items():
                    p = p.tag(tk, tv)
                p = p.field(field, new_val).time(dt, WritePrecision.NS)
                wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=p)

            if action == "delete":
                # Narrow time window around the timestamp to delete the single point.
                s = _dt_to_rfc3339_utc_ms(dt - timedelta(milliseconds=2))
                e = _dt_to_rfc3339_utc_ms(dt + timedelta(milliseconds=2))
                pred = _predicate(measurement, field, tags)
                dapi.delete(start=s, stop=e, predicate=pred, bucket=cfg["bucket"], org=cfg["org"])

            _history_append({
                "kind": "change",
                "series": {
                    "measurement": measurement,
                    "field": field,
                    "entity_id": entity_id,
                    "friendly_name": friendly_name,
                    "tags": tags,
                },
                "time": time_raw,
                "action": action,
                "old_value": old_val,
                "new_value": new_val,
                "reason": reason,
                "trigger_page": trigger_page,
                "trigger_source": trigger_source,
                "trigger_action": trigger_action,
                "trigger_button": trigger_button,
                "ip": _req_ip(),
                "ua": _req_ua(),
            })

            applied += 1

    try:
        if applied > 0:
            _dash_cache_mark_dirty_series(measurement, field, entity_id, friendly_name, "apply_changes")
            _stats_cache_mark_dirty_series(measurement, field, entity_id, friendly_name, "apply_changes")
            patch_job_id = _analysis_cache_mark_dirty_series(cfg, measurement, field, entity_id, friendly_name, "apply_changes")
        else:
            patch_job_id = None
    except Exception:
        patch_job_id = None
    return jsonify({"ok": True, "applied": applied, "message": f"Applied changes: {applied}", "patch_job_id": patch_job_id})


@app.get("/api/history_list")
def api_history_list():
    try:
        q = str(request.args.get("q") or "").strip().lower()
        action = str(request.args.get("action") or "").strip().lower()
        measurement = str(request.args.get("measurement") or "").strip().lower()
        entity_id = str(request.args.get("entity_id") or "").strip().lower()
        reason = str(request.args.get("reason") or "").strip().lower()
        try:
            limit = int(request.args.get("limit") or 200)
        except Exception:
            limit = 200
        if limit < 1:
            limit = 1
        if limit > 2000:
            limit = 2000

        rows = _history_read_all()
        # newest first
        rows = list(reversed(rows))

        def _match(it: dict[str, Any]) -> bool:
            try:
                if action and str(it.get("action") or "").lower() != action:
                    return False
                s = it.get("series") or {}
                if measurement and measurement not in str(s.get("measurement") or "").lower():
                    return False
                if entity_id and entity_id not in str(s.get("entity_id") or "").lower():
                    return False
                if reason and reason not in str(it.get("reason") or "").lower():
                    return False
                if q:
                    blob = json.dumps(it, ensure_ascii=True).lower()
                    if q not in blob:
                        return False
                return True
            except Exception:
                return False

        out: list[dict[str, Any]] = []
        for it in rows:
            if not isinstance(it, dict):
                continue
            if not _match(it):
                continue
            out.append(it)
            if len(out) >= limit:
                break

        return jsonify({"ok": True, "rows": out})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500


@app.post("/api/raw_history_summary")
def api_raw_history_summary():
    try:
        body = request.get_json(force=True) or {}
        measurement = str(body.get("measurement") or "").strip()
        field = str(body.get("field") or "").strip()
        entity_id = str(body.get("entity_id") or "").strip() or None
        friendly_name = str(body.get("friendly_name") or "").strip() or None
        times = body.get("times")

        if not measurement or not field:
            return jsonify({"ok": False, "error": "measurement and field required"}), 400
        if not isinstance(times, list) or not times:
            return jsonify({"ok": False, "error": "times must be a non-empty list"}), 400

        raw_time_map: dict[str, str] = {}
        for it in times:
            raw_key = str(it or "").strip()
            norm = _history_time_key(raw_key)
            if raw_key and norm:
                raw_time_map[raw_key] = norm
        wanted_keys = set(raw_time_map.values())
        if not wanted_keys:
            return jsonify({"ok": True, "rows": {}, "undoable": {}})

        all_rows = _history_read_all()
        rolled_back_refs = {
            str(it.get("ref_id") or "").strip()
            for it in all_rows
            if isinstance(it, dict) and str(it.get("action") or "").strip().lower() == "rollback"
        }

        grouped: dict[str, list[dict[str, Any]]] = {k: [] for k in raw_time_map.keys()}
        undoable: dict[str, dict[str, Any]] = {}

        for it in reversed(all_rows):
            if not isinstance(it, dict):
                continue
            if not _history_series_matches(it, measurement, field, entity_id, friendly_name):
                continue
            time_key = _history_time_key(it.get("time"))
            if not time_key or time_key not in wanted_keys:
                continue

            trigger = _history_trigger_meta(it)
            pub = {
                "id": str(it.get("id") or ""),
                "at": str(it.get("at") or ""),
                "time": str(it.get("time") or ""),
                "action": str(it.get("action") or ""),
                "old_value": it.get("old_value"),
                "new_value": it.get("new_value"),
                "reason": str(it.get("reason") or ""),
                "ref_id": str(it.get("ref_id") or ""),
                **trigger,
            }
            is_raw_change = (
                trigger["trigger_page"] == "dashboard"
                and trigger["trigger_source"] == "raw"
                and str(it.get("action") or "").strip().lower() in ("overwrite", "delete")
                and trigger["trigger_button"] in ("raw_paste", "raw_delete")
                and str(it.get("id") or "").strip() not in rolled_back_refs
            )
            for raw_key, norm in raw_time_map.items():
                if norm != time_key:
                    continue
                grouped[raw_key].append(pub)
                if raw_key not in undoable and is_raw_change:
                    undoable[raw_key] = pub

        return jsonify({"ok": True, "rows": grouped, "undoable": undoable})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e) or e.__class__.__name__}), 500


@app.post("/api/history_rollback")
def api_history_rollback():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", False)
    ok_confirm = (
        confirm is True
        or str(confirm).strip().lower() in ("1", "true", "yes", "on")
    )
    if not ok_confirm:
        return jsonify({"ok": False, "error": "Confirmation required"}), 400

    ids = body.get("ids")
    since_seconds = body.get("since_seconds")

    rows = _history_read_all()

    wanted: list[dict[str, Any]] = []
    if isinstance(ids, list) and ids:
        idset = {str(x) for x in ids if str(x)}
        for it in rows:
            if isinstance(it, dict) and str(it.get("id") or "") in idset:
                wanted.append(it)
    elif since_seconds is not None:
        try:
            s = int(since_seconds)
        except Exception:
            s = 0
        if s <= 0:
            return jsonify({"ok": False, "error": "since_seconds must be > 0"}), 400
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=s)
        for it in rows:
            if not isinstance(it, dict):
                continue
            at = str(it.get("at") or "")
            try:
                dt_at = _parse_iso_datetime(at)
            except Exception:
                continue
            if dt_at >= cutoff:
                wanted.append(it)
    else:
        return jsonify({"ok": False, "error": "ids or since_seconds required"}), 400

    # Rollback newest first
    wanted.sort(key=lambda x: str(x.get("at") or ""), reverse=True)

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "history rollback currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    def _restore_backup_into_client(c: InfluxDBClient, backup_id: str) -> int:
        bdir = backup_dir(cfg)
        try:
            with _open_backup_lp_text(bdir, backup_id, is_fullbackup=False):
                pass
        except Exception:
            raise RuntimeError("backup not found")

        wapi = c.write_api(write_options=SYNCHRONOUS)
        batch: list[str] = []
        applied_local = 0
        with _open_backup_lp_text(bdir, backup_id, is_fullbackup=False) as f:
            for line in f:
                line = line.strip("\n")
                if not line.strip():
                    continue
                batch.append(line)
                if len(batch) >= 2000:
                    wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=batch, write_precision=WritePrecision.NS)
                    applied_local += len(batch)
                    batch = []
            if batch:
                wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=batch, write_precision=WritePrecision.NS)
                applied_local += len(batch)
        return applied_local

    applied = 0
    with v2_client(cfg) as c:
        wapi = c.write_api(write_options=SYNCHRONOUS)

        for it in wanted:
            action = str(it.get("action") or "").strip().lower()

            if action == "combine_copy":
                # Roll back by deleting the affected target range and restoring a range-backup.
                try:
                    s = it.get("series") or {}
                    measurement = str(s.get("measurement") or "").strip()
                    field = str(s.get("field") or "").strip()
                    entity_id = str(s.get("entity_id") or "").strip() or None
                    friendly_name = str(s.get("friendly_name") or "").strip() or None
                    if not measurement or not field:
                        continue
                    if not entity_id and not friendly_name:
                        continue

                    start_s = str(it.get("start") or "").strip()
                    stop_s = str(it.get("stop") or "").strip()
                    start_dt = _parse_iso_datetime(start_s)
                    stop_dt = _parse_iso_datetime(stop_s)
                    if not start_dt or not stop_dt:
                        continue

                    backup_id = str(it.get("backup_id") or "").strip()
                    if not backup_id:
                        continue

                    predicate = f"_measurement={_flux_str(measurement)} AND _field={_flux_str(field)}"
                    if entity_id:
                        predicate += f" AND entity_id={_flux_str(entity_id)}"
                    if friendly_name:
                        predicate += f" AND friendly_name={_flux_str(friendly_name)}"
                    c.delete_api().delete(start=start_dt, stop=stop_dt, predicate=predicate, bucket=cfg["bucket"], org=cfg["org"])

                    restored = _restore_backup_into_client(c, backup_id)

                    _history_append({
                        "kind": "rollback",
                        "ref_id": it.get("id"),
                        "series": {
                            "measurement": measurement,
                            "field": field,
                            "entity_id": entity_id,
                            "friendly_name": friendly_name,
                            "tags": {"entity_id": entity_id, "friendly_name": friendly_name},
                        },
                        "start": start_s,
                        "stop": stop_s,
                        "action": "rollback",
                        "reason": "Rollback combine_copy",
                        "backup_id": backup_id,
                        "restored": restored,
                        "ip": _req_ip(),
                        "ua": _req_ua(),
                    })

                    applied += restored
                    try:
                        dirty_series.add((measurement, field, entity_id, friendly_name))
                    except Exception:
                        pass
                except Exception:
                    continue
                continue

            if action not in ("overwrite", "delete"):
                # Ignore other entries (e.g., rollbacks)
                continue
            s = it.get("series") or {}
            measurement = str(s.get("measurement") or "").strip()
            field = str(s.get("field") or "").strip()
            tags = s.get("tags") or {}
            if not isinstance(tags, dict):
                tags = {}
            t_raw = str(it.get("time") or "").strip()
            try:
                dt = _parse_iso_datetime(t_raw)
            except Exception:
                continue
            old_val = it.get("old_value")
            if old_val is None:
                continue

            p = Point(measurement)
            for tk, tv in tags.items():
                if tk and tv is not None:
                    p = p.tag(str(tk), str(tv))
            p = p.field(field, old_val).time(dt, WritePrecision.NS)
            wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=p)

            _history_append({
                "kind": "rollback",
                "ref_id": it.get("id"),
                "series": {
                    "measurement": measurement,
                    "field": field,
                    "entity_id": s.get("entity_id"),
                    "friendly_name": s.get("friendly_name"),
                    "tags": tags,
                },
                "time": t_raw,
                "action": "rollback",
                "old_value": it.get("new_value"),
                "new_value": old_val,
                "reason": "Rollback",
                "ip": _req_ip(),
                "ua": _req_ua(),
            })

            applied += 1

            try:
                dirty_series.add((measurement, field, str(s.get("entity_id") or "").strip() or None, str(s.get("friendly_name") or "").strip() or None))
            except Exception:
                pass

    try:
        for m, f, eid, fn in dirty_series:
            _dash_cache_mark_dirty_series(m, f, eid, fn, "history_rollback")
            _stats_cache_mark_dirty_series(m, f, eid, fn, "history_rollback")
            _analysis_cache_mark_dirty_series(cfg, m, f, eid, fn, "history_rollback")
    except Exception:
        pass

    return jsonify({"ok": True, "applied": applied, "message": f"Rollback applied: {applied}"})


def _safe_data_file(root: Path, name: str) -> Path:
    """Resolve a user-provided filename safely within a root directory."""

    n = (name or "").strip()
    if not n or "/" in n or "\\" in n or ".." in n:
        raise ValueError("invalid file name")
    p = (root / n).resolve()
    rr = root.resolve()
    if rr not in p.parents and p != rr:
        raise ValueError("path traversal")
    return p


@app.post("/api/export")
def api_export():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}

    fmt = str(body.get("format") or "text").strip().lower()
    if fmt not in ("text", "xlsx"):
        return jsonify({"ok": False, "error": "format must be text or xlsx"}), 400

    delim = str(body.get("delimiter") or ";")
    if len(delim) != 1:
        delim = ";"

    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    tz_name = str(body.get("tz_name") or "").strip() or None
    try:
        tz_off = body.get("tz_offset_minutes")
        tz_offset_minutes = int(tz_off) if tz_off is not None and str(tz_off).strip() != "" else None
    except Exception:
        tz_offset_minutes = None

    # Export window: prefer explicit start/stop.
    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    if not start_dt or not stop_dt:
        return jsonify({"ok": False, "error": "start and stop required"}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "export currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    extra = flux_tag_filter(entity_id, friendly_name)
    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value","_measurement","_field","entity_id","friendly_name"])
  |> sort(columns: ["_time"], desc: false)
'''

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex
    ext = "xlsx" if fmt == "xlsx" else "csv"
    filename = f"export__{file_id}.{ext}"
    out_path = (EXPORT_DIR / filename)

    try:
        rows: list[tuple[str, object, str, str, str, str]] = []
        with v2_client(cfg) as c:
            for rec in c.query_api().query_stream(q, org=cfg["org"]):
                try:
                    t = rec.get_time()
                    v = rec.get_value()
                    if v is None or not isinstance(t, datetime):
                        continue
                    tv = t.astimezone(timezone.utc)
                    t_local = _fmt_ui_local_ts(tv, tz_name, tz_offset_minutes)
                    m = str(rec.values.get("_measurement") or measurement)
                    f = str(rec.values.get("_field") or field)
                    eid = str(rec.values.get("entity_id") or "")
                    fn = str(rec.values.get("friendly_name") or "")
                    rows.append((t_local, v, eid, fn, m, f))
                except Exception:
                    continue

        if fmt == "xlsx":
            try:
                import openpyxl  # type: ignore
            except Exception:
                return jsonify({"ok": False, "error": "openpyxl not available"}), 500

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "export"
            ws.append(["time", "value", "entity_id", "friendly_name", "_measurement", "_field"])
            for r in rows:
                ws.append(list(r))
            wb.save(out_path)
        else:
            with out_path.open("w", encoding="utf-8", newline="") as f:
                f.write(f"# timezone={tz_name or ''}\n")
                f.write(f"# tz_offset_minutes={tz_offset_minutes if tz_offset_minutes is not None else ''}\n")
                w = csv.writer(f, delimiter=delim)
                w.writerow(["time", "value", "entity_id", "friendly_name", "_measurement", "_field"])
                for r in rows:
                    w.writerow(list(r))

        return jsonify({
            "ok": True,
            "download_url": f"./api/export_download?file={filename}",
            "meta": {"rows": len(rows), "format": fmt, "delimiter": delim},
        })
    except Exception as e:
        try:
            if out_path.exists():
                out_path.unlink()
        except Exception:
            pass
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


def _export_job_public(job: dict[str, Any]) -> dict[str, Any]:
    written = int(job.get("rows_written") or 0)
    return {
        "id": job.get("id"),
        "state": job.get("state"),
        "message": job.get("message"),
        "started_at": job.get("started_at"),
        "elapsed": _job_elapsed_hms(job),
        "rows_written": written,
        "format": job.get("format"),
        "file": job.get("file"),
        "download_url": job.get("download_url"),
        "query": job.get("query") or "",
        "cancelled": bool(job.get("cancelled")),
        "error": job.get("error"),
        "ready": job.get("state") in ("done", "error", "cancelled"),
    }


def _export_job_thread(
    job_id: str,
    cfg: dict[str, Any],
    fmt: str,
    delim: str,
    measurement: str,
    field: str,
    entity_id: str | None,
    friendly_name: str | None,
    start_dt: datetime,
    stop_dt: datetime,
    tz_name: str | None,
    tz_offset_minutes: int | None,
    out_dir: str | None,
) -> None:
    with EXPORT_LOCK:
        job = EXPORT_JOBS.get(job_id)
    if not job:
        return

    def set_state(state: str, msg: str) -> None:
        with EXPORT_LOCK:
            if job_id in EXPORT_JOBS:
                EXPORT_JOBS[job_id]["state"] = state
                EXPORT_JOBS[job_id]["message"] = msg
                if state in ("done", "error", "cancelled"):
                    _job_set_finished(EXPORT_JOBS[job_id])

    def set_error(msg: str) -> None:
        with EXPORT_LOCK:
            if job_id in EXPORT_JOBS:
                EXPORT_JOBS[job_id]["error"] = msg

    def set_progress(**kw: Any) -> None:
        with EXPORT_LOCK:
            j = EXPORT_JOBS.get(job_id)
            if not j:
                return
            for k, v in kw.items():
                j[k] = v

    def is_cancelled() -> bool:
        with EXPORT_LOCK:
            j = EXPORT_JOBS.get(job_id) or {}
            if bool(j.get("cancelled")):
                return True

            try:
                max_s = int(cfg.get("jobs_max_runtime_seconds", 0) or 0)
            except Exception:
                max_s = 0
            if max_s <= 0:
                return False
            try:
                started_mono = float(j.get("started_mono") or 0.0)
            except Exception:
                started_mono = 0.0
            if started_mono > 0 and (time.monotonic() - started_mono) >= float(max_s):
                EXPORT_JOBS[job_id]["cancelled"] = True
                try:
                    LOG.warning("job_auto_cancel type=export job_id=%s reason=max_runtime_seconds exceeded (%s)", job_id, max_s)
                except Exception:
                    pass
                return True
            return False

    out_root = export_dir_from_target(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    ext = "xlsx" if fmt == "xlsx" else "csv"
    filename = f"export_job__{job_id}.{ext}"
    part = f"{filename}.part"
    out_path = (out_root / filename)
    part_path = (out_root / part)

    extra = flux_tag_filter(entity_id, friendly_name)
    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value","_measurement","_field","entity_id","friendly_name"])
  |> sort(columns: ["_time"], desc: false)
'''

    set_state("running", "Export laeuft...")
    set_progress(query=q.strip(), rows_written=0, file=None, download_url=None)

    count = 0
    last_tick = time.monotonic()

    try:
        with v2_client(cfg) as c:
            qapi = c.query_api()

            if fmt == "xlsx":
                try:
                    import openpyxl  # type: ignore
                except Exception as e:
                    raise RuntimeError("openpyxl not available") from e

                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "export"
                ws.append(["time", "value", "entity_id", "friendly_name", "_measurement", "_field"])

                for rec in qapi.query_stream(q, org=cfg["org"]):
                    if is_cancelled():
                        set_state("cancelled", "Abgebrochen")
                        raise RuntimeError("cancelled")
                    try:
                        t = rec.get_time()
                        v = rec.get_value()
                        if v is None or not isinstance(t, datetime):
                            continue
                        tv = t.astimezone(timezone.utc)
                        t_local = _fmt_ui_local_ts(tv, tz_name, tz_offset_minutes)
                        m = str(rec.values.get("_measurement") or measurement)
                        f = str(rec.values.get("_field") or field)
                        eid = str(rec.values.get("entity_id") or "")
                        fn = str(rec.values.get("friendly_name") or "")
                        ws.append([t_local, v, eid, fn, m, f])
                        count += 1
                    except Exception:
                        continue
                    now = time.monotonic()
                    if (now - last_tick) >= 0.25:
                        set_progress(rows_written=count)
                        last_tick = now

                if is_cancelled():
                    set_state("cancelled", "Abgebrochen")
                    raise RuntimeError("cancelled")
                wb.save(part_path)
            else:
                with part_path.open("w", encoding="utf-8", newline="") as f:
                    f.write(f"# timezone={tz_name or ''}\n")
                    f.write(f"# tz_offset_minutes={tz_offset_minutes if tz_offset_minutes is not None else ''}\n")
                    w = csv.writer(f, delimiter=delim)
                    w.writerow(["time", "value", "entity_id", "friendly_name", "_measurement", "_field"])
                    for rec in qapi.query_stream(q, org=cfg["org"]):
                        if is_cancelled():
                            set_state("cancelled", "Abgebrochen")
                            raise RuntimeError("cancelled")
                        try:
                            t = rec.get_time()
                            v = rec.get_value()
                            if v is None or not isinstance(t, datetime):
                                continue
                            tv = t.astimezone(timezone.utc)
                            t_local = _fmt_ui_local_ts(tv, tz_name, tz_offset_minutes)
                            m = str(rec.values.get("_measurement") or measurement)
                            fld = str(rec.values.get("_field") or field)
                            eid = str(rec.values.get("entity_id") or "")
                            fn = str(rec.values.get("friendly_name") or "")
                            w.writerow([t_local, v, eid, fn, m, fld])
                            count += 1
                        except Exception:
                            continue

                        now = time.monotonic()
                        if (now - last_tick) >= 0.25:
                            set_progress(rows_written=count)
                            last_tick = now

        if is_cancelled():
            set_state("cancelled", "Abgebrochen")
            raise RuntimeError("cancelled")

        try:
            if out_path.exists():
                out_path.unlink()
        except Exception:
            pass
        part_path.replace(out_path)

        dl = f"./api/export_job/download?job_id={job_id}"
        set_progress(rows_written=count, file=filename, download_url=dl)
        set_state("done", f"Export fertig. Zeilen: {count}")
        return
    except Exception as e:
        msg = str(e)
        if "cancelled" in msg:
            try:
                if part_path.exists():
                    part_path.unlink()
            except Exception:
                pass
            try:
                if out_path.exists():
                    out_path.unlink()
            except Exception:
                pass
            return

        set_state("error", "Fehler")
        set_error(_short_influx_error(e))
        try:
            if part_path.exists():
                part_path.unlink()
        except Exception:
            pass
        try:
            if out_path.exists():
                out_path.unlink()
        except Exception:
            pass
        return


@app.post("/api/export_job/start")
def api_export_job_start():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}

    target_dir = export_dir_from_target(body.get("target_dir"))

    fmt = str(body.get("format") or "text").strip().lower()
    if fmt not in ("text", "xlsx"):
        return jsonify({"ok": False, "error": "format must be text or xlsx"}), 400

    delim = str(body.get("delimiter") or ";")
    if len(delim) != 1:
        delim = ";"

    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    tz_name = str(body.get("tz_name") or "").strip() or None
    try:
        tz_off = body.get("tz_offset_minutes")
        tz_offset_minutes = int(tz_off) if tz_off is not None and str(tz_off).strip() != "" else None
    except Exception:
        tz_offset_minutes = None

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    if not start_dt or not stop_dt:
        return jsonify({"ok": False, "error": "start and stop required"}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "export currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "state": "queued",
        "message": "Warte...",
        "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "started_mono": time.monotonic(),
        "cancelled": False,
        "error": None,
        "rows_written": 0,
        "format": fmt,
        "file": None,
        "download_url": None,
        "query": "",
        "out_dir": str(target_dir),
    }

    with EXPORT_LOCK:
        EXPORT_JOBS[job_id] = job
        cutoff = time.monotonic() - (6 * 60 * 60)
        old = [k for k, v in EXPORT_JOBS.items() if float(v.get("started_mono") or 0) < cutoff]
        for k in old:
            if k != job_id:
                EXPORT_JOBS.pop(k, None)

    LOG.info(
        "job_start type=export job_id=%s ip=%s ua=%s fmt=%s measurement=%s field=%s entity_id=%s friendly_name=%s out_dir=%s",
        job_id,
        _req_ip(),
        _req_ua(),
        fmt,
        measurement,
        field,
        entity_id or "",
        friendly_name or "",
        str(target_dir),
    )

    t = threading.Thread(
        daemon=True,
        target=_export_job_thread,
        args=(
            job_id,
            cfg,
            fmt,
            delim,
            measurement,
            field,
            entity_id,
            friendly_name,
            start_dt,
            stop_dt,
            tz_name,
            tz_offset_minutes,
            str(target_dir),
        ),
    )
    t.start()
    return jsonify({"ok": True, "job_id": job_id})


@app.get("/api/export_job/status")
def api_export_job_status():
    job_id = (request.args.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with EXPORT_LOCK:
        job = EXPORT_JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    return jsonify({"ok": True, "status": _export_job_public(job)})


@app.post("/api/export_job/cancel")
def api_export_job_cancel():
    body = request.get_json(force=True) or {}
    job_id = (body.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with EXPORT_LOCK:
        job = EXPORT_JOBS.get(job_id)
        if not job:
            return jsonify({"ok": False, "error": "job not found"}), 404
        job["cancelled"] = True
    LOG.info("job_cancel type=export job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
    return jsonify({"ok": True})


@app.get("/api/export_job/download")
def api_export_job_download():
    job_id = (request.args.get("job_id") or "").strip()
    if not job_id:
        return jsonify({"ok": False, "error": "job_id required"}), 400
    with EXPORT_LOCK:
        job = EXPORT_JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    if str(job.get("state") or "") != "done":
        return jsonify({"ok": False, "error": "job not ready"}), 409
    name = str(job.get("file") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "file missing"}), 500
    try:
        root = export_dir_from_target(job.get("out_dir"))
        p = _safe_data_file(root, name)
    except Exception:
        return jsonify({"ok": False, "error": "invalid file"}), 400
    if not p.exists() or not p.is_file():
        return jsonify({"ok": False, "error": "file not found"}), 404
    return send_file(p, as_attachment=True, download_name=p.name)


@app.get("/api/export_download")
def api_export_download():
    name = (request.args.get("file") or "").strip()
    try:
        p = _safe_data_file(EXPORT_DIR, name)
    except Exception:
        return jsonify({"ok": False, "error": "invalid file"}), 400
    if not p.exists() or not p.is_file():
        return jsonify({"ok": False, "error": "file not found"}), 404
    return send_file(p, as_attachment=True, download_name=p.name)


def _detect_delimiter(sample: str) -> str:
    s = sample or ""
    # Prefer ; for HA-ish exports.
    cands = [";", ",", "\t"]
    best = ";"
    best_n = -1
    for d in cands:
        n = s.count(d)
        if n > best_n:
            best_n = n
            best = d
    return best


def _strip_utf8_bom(s: str) -> str:
    # Best-effort BOM removal for CSV headers.
    if not s:
        return s
    return s[1:] if s.startswith("\ufeff") else s


def _canon_col(s: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "", (s or "").strip().lower())


@app.post("/api/import_analyze")
def api_import_analyze():
    f = request.files.get("file")
    if not f:
        return jsonify({"ok": False, "error": "file required"}), 400

    tz_name = str(request.form.get("tz_name") or "").strip() or None
    try:
        tz_offset_minutes = int(request.form.get("tz_offset_minutes")) if request.form.get("tz_offset_minutes") else None
    except Exception:
        tz_offset_minutes = None

    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex
    filename = f"import__{file_id}.csv"
    path = (IMPORT_DIR / filename)
    try:
        f.save(path)
    except Exception as e:
        return jsonify({"ok": False, "error": f"save failed: {e}"}), 500

    try:
        prep = _prepare_import_rows(path, str(request.form.get("delimiter") or ""), tz_name, tz_offset_minutes)

        return jsonify({
            "ok": True,
            "file_id": filename,
            "delimiter": prep["delimiter"],
            "timezone": {"name": tz_name, "offset_minutes": tz_offset_minutes},
            "count": prep["count"],
            "oldest_utc": _dt_to_rfc3339_utc_ms(prep["oldest_utc"]) if prep["oldest_utc"] else None,
            "newest_utc": _dt_to_rfc3339_utc_ms(prep["newest_utc"]) if prep["newest_utc"] else None,
            "oldest_local": _fmt_ui_local_ts(prep["oldest_utc"], tz_name, tz_offset_minutes) if prep["oldest_utc"] else None,
            "newest_local": _fmt_ui_local_ts(prep["newest_utc"], tz_name, tz_offset_minutes) if prep["newest_utc"] else None,
            "columns": prep["columns"],
            "column_map": prep["column_map"],
            "sample": prep["sample"],
            "errors": prep["errors"],
            "error_samples": prep["error_samples"],
            "source_measurements": prep["source_measurements"],
            "source_fields": prep["source_fields"],
            "source_entity_ids": prep["source_entity_ids"],
            "source_friendly_names": prep["source_friendly_names"],
            "issue_counts": prep["issue_counts"],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/api/import_preview_transform")
def api_import_preview_transform():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    file_id = str(body.get("file_id") or "").strip()
    if not file_id:
        return jsonify({"ok": False, "error": "file_id required"}), 400
    try:
        path = _safe_data_file(IMPORT_DIR, file_id)
    except Exception:
        return jsonify({"ok": False, "error": "invalid file_id"}), 400
    if not path.exists() or not path.is_file():
        return jsonify({"ok": False, "error": "file not found"}), 404

    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None
    tz_name = str(body.get("tz_name") or "").strip() or None
    try:
        tz_offset_minutes = int(body.get("tz_offset_minutes")) if body.get("tz_offset_minutes") is not None and str(body.get("tz_offset_minutes")).strip() != "" else None
    except Exception:
        tz_offset_minutes = None

    try:
        prep = _prepare_import_rows(path, str(body.get("delimiter") or ";"), tz_name, tz_offset_minutes)
        plan = _build_import_transform_plan(cfg, prep["parsed_rows"], measurement, field, entity_id, friendly_name)
        preview_rows = _transform_import_preview_rows(prep["parsed_rows"], plan, measurement, field, entity_id, friendly_name, 10)
        return jsonify({
            "ok": True,
            "checks": plan["checks"],
            "compatible": plan["compatible"],
            "source_measurements": plan["source_measurements"],
            "source_fields": plan["source_fields"],
            "preview_rows": preview_rows,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/api/import_start")
def api_import_start():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "import currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    body = request.get_json(force=True) or {}
    file_id = str(body.get("file_id") or "").strip()
    if not file_id:
        return jsonify({"ok": False, "error": "file_id required"}), 400
    try:
        path = _safe_data_file(IMPORT_DIR, file_id)
    except Exception:
        return jsonify({"ok": False, "error": "invalid file_id"}), 400
    if not path.exists() or not path.is_file():
        return jsonify({"ok": False, "error": "file not found"}), 404

    measurement = str(body.get("measurement") or "").strip()
    field = str(body.get("field") or "").strip()
    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    entity_id = str(body.get("entity_id") or "").strip() or None
    friendly_name = str(body.get("friendly_name") or "").strip() or None

    delete_first = bool(body.get("delete_first", False))
    backup_before = bool(body.get("backup_before", True))
    confirm = str(body.get("confirm") or "").strip()

    tz_name = str(body.get("tz_name") or "").strip() or None
    try:
        tz_offset_minutes = int(body.get("tz_offset_minutes")) if body.get("tz_offset_minutes") is not None and str(body.get("tz_offset_minutes")).strip() != "" else None
    except Exception:
        tz_offset_minutes = None

    delim = str(body.get("delimiter") or ";")
    if len(delim) != 1:
        delim = ";"

    try:
        prep = _prepare_import_rows(path, delim, tz_name, tz_offset_minutes)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    plan = _build_import_transform_plan(cfg, prep["parsed_rows"], measurement, field, entity_id, friendly_name)
    if not plan["compatible"]:
        return jsonify({"ok": False, "error": "Transformationscheck fehlgeschlagen", "checks": plan["checks"]}), 400

    points: list[Point] = []
    oldest_utc = prep["oldest_utc"]
    newest_utc = prep["newest_utc"]
    factors = dict(plan.get("measurement_factors") or {})
    for row in prep["parsed_rows"]:
        dt_utc = row["dt_utc"]
        src_measurement = str(row.get("_measurement") or "")
        factor = float(factors.get(src_measurement, 1.0) or 1.0)
        v = float(row.get("value") or 0.0) * factor

        p = Point(str(measurement))
        eid_row = str(row.get("entity_id") or "").strip()
        fn_row = str(row.get("friendly_name") or "").strip()
        if entity_id or eid_row:
            p = p.tag("entity_id", str(entity_id or eid_row))
        if friendly_name or fn_row:
            p = p.tag("friendly_name", str(friendly_name or fn_row))
        p = p.field(str(field), v)
        p = p.time(dt_utc, WritePrecision.NS)
        points.append(p)

    if not points:
        return jsonify({"ok": False, "error": "no valid rows"}), 400

    if delete_first:
        if not (oldest_utc and newest_utc):
            return jsonify({"ok": False, "error": "cannot derive time range for delete"}), 400

    backup_meta = None
    if backup_before:
        # Create a range backup for the target series in the import time window.
        if not (entity_id or friendly_name):
            return jsonify({"ok": False, "error": "backup_before requires entity_id or friendly_name"}), 400
        if not (oldest_utc and newest_utc):
            return jsonify({"ok": False, "error": "cannot derive time range for backup"}), 400
        try:
            # Reuse the backup_create_range logic (inline).
            bdir = backup_dir(cfg)
            bdir.mkdir(parents=True, exist_ok=True)
            display = friendly_name or entity_id or f"{measurement}_{field}"
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_kind = "range"
            backup_id = _backup_safe(display) + "__" + backup_kind + "__" + ts
            meta_path, lp_path = _backup_files(bdir, backup_id)
            extra = flux_tag_filter(entity_id, friendly_name)
            start = _dt_to_rfc3339_utc(oldest_utc)
            stop = _dt_to_rfc3339_utc(newest_utc)
            q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> sort(columns: ["_time"])
'''
            count = 0
            with v2_client(cfg) as c:
                qapi = c.query_api()
                with lp_path.open("w", encoding="utf-8") as f:
                    for rec in qapi.query_stream(q, org=cfg["org"]):
                        try:
                            t = rec.get_time()
                            v = rec.get_value()
                            if v is None:
                                continue
                            m = rec.values.get("_measurement") or measurement
                            fld = rec.values.get("_field") or field
                            p = Point(str(m))
                            for k, tv in (rec.values or {}).items():
                                if k in ("result", "table"):
                                    continue
                                if str(k).startswith("_"):
                                    continue
                                if tv is None:
                                    continue
                                p = p.tag(str(k), str(tv))
                            p = p.field(str(fld), v)
                            if isinstance(t, datetime):
                                p = p.time(t, WritePrecision.NS)
                            lp = p.to_line_protocol()
                            if lp:
                                f.write(lp)
                                f.write("\n")
                                count += 1
                        except Exception:
                            continue
            bytes_size = int(lp_path.stat().st_size) if lp_path.exists() else 0
            backup_meta = {
                "id": backup_id,
                "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "kind": backup_kind,
                "display_name": display,
                "measurement": measurement,
                "field": field,
                "entity_id": entity_id,
                "friendly_name": friendly_name,
                "start": start,
                "stop": stop,
                "point_count": count,
                "bytes": bytes_size,
            }
            meta_path.write_text(json.dumps(backup_meta, indent=2, sort_keys=True), encoding="utf-8")
        except Exception as e:
            return jsonify({"ok": False, "error": f"backup_before failed: {_short_influx_error(e)}"}), 500

    try:
        with v2_client(cfg) as c:
            if delete_first:
                predicate = f"_measurement={_flux_str(measurement)} AND _field={_flux_str(field)}"
                if entity_id:
                    predicate += f" AND entity_id={_flux_str(entity_id)}"
                if friendly_name:
                    predicate += f" AND friendly_name={_flux_str(friendly_name)}"
                c.delete_api().delete(start=oldest_utc, stop=newest_utc, predicate=predicate, bucket=cfg["bucket"], org=cfg["org"])

            wapi = c.write_api(write_options=SYNCHRONOUS)
            batch: list[Point] = []
            imported = 0
            for p in points:
                batch.append(p)
                if len(batch) >= 500:
                    wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=batch, write_precision=WritePrecision.NS)
                    imported += len(batch)
                    batch = []
            if batch:
                wapi.write(bucket=cfg["bucket"], org=cfg["org"], record=batch, write_precision=WritePrecision.NS)
                imported += len(batch)

        _history_append({
            "kind": "import",
            "series": {
                "measurement": measurement,
                "field": field,
                "entity_id": entity_id,
                "friendly_name": friendly_name,
            },
            "count": imported,
            "delete_first": delete_first,
            "backup_before": backup_before,
            "backup_id": (backup_meta or {}).get("id") if backup_meta else None,
            "reason": "Import",
            "ip": _req_ip(),
            "ua": _req_ua(),
        })

        try:
            if imported > 0 or delete_first:
                _dash_cache_mark_dirty_series(measurement, field, entity_id, friendly_name, "import")
                _stats_cache_mark_dirty_series(measurement, field, entity_id, friendly_name, "import")
                _analysis_cache_mark_dirty_series(cfg, measurement, field, entity_id, friendly_name, "import")
        except Exception:
            pass

        return jsonify({
            "ok": True,
            "imported": imported,
            "deleted_first": delete_first,
            "backup": backup_meta,
            "checks": plan["checks"],
            "message": f"Import fertig. Zeilen: {imported}",
        })
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

@app.post("/api/delete")
def delete():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = body.get("measurement", "")
    field = body.get("field", "")
    range_key = body.get("range", "24h")
    confirm = body.get("confirm", "")
    entity_id = body.get("entity_id") or None
    friendly_name = body.get("friendly_name") or None

    rk = (range_key or "").strip().lower()
    if rk in ("all", "alle", "inf", "infinite", "infinity"):
        return jsonify({"ok": False, "error": "Delete not allowed for Zeitraum=Alle. Bitte Benutzerdefiniert waehlen."}), 400

    if not measurement:
        return jsonify({"ok": False, "error": "measurement required"}), 400

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400

    start, stop = (start_dt, stop_dt) if (start_dt and stop_dt) else parse_range_to_datetimes(range_key)

    try:
        if int(cfg.get("influx_version",2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400
            predicate = f"_measurement={_flux_str(measurement)}"
            if field:
                predicate += f" AND _field={_flux_str(field)}"
            if entity_id:
                predicate += f" AND entity_id={_flux_str(entity_id)}"
            if friendly_name:
                predicate += f" AND friendly_name={_flux_str(friendly_name)}"
            with v2_client(cfg) as c:
                c.delete_api().delete(start=start, stop=stop, predicate=predicate, bucket=cfg["bucket"], org=cfg["org"])
            try:
                _dash_cache_mark_dirty_series(measurement, field, str(entity_id) if entity_id else None, str(friendly_name) if friendly_name else None, "delete")
                _stats_cache_mark_dirty_series(measurement, field, str(entity_id) if entity_id else None, str(friendly_name) if friendly_name else None, "delete")
                _analysis_cache_mark_dirty_series(cfg, measurement, field, str(entity_id) if entity_id else None, str(friendly_name) if friendly_name else None, "delete")
            except Exception:
                pass
            return jsonify({"ok": True, "message": f"Deleted v2: {predicate} in {cfg['bucket']} from {start.isoformat()} to {stop.isoformat()}"})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            dur = range_to_influxql(range_key)
            c = v1_client(cfg)
            tag_where = influxql_tag_filter(entity_id, friendly_name)
            q = f'DELETE FROM "{measurement}" WHERE time > now() - {dur}{tag_where}'
            c.query(q)
            try:
                _dash_cache_mark_dirty_series(measurement, field, str(entity_id) if entity_id else None, str(friendly_name) if friendly_name else None, "delete")
                _stats_cache_mark_dirty_series(measurement, field, str(entity_id) if entity_id else None, str(friendly_name) if friendly_name else None, "delete")
                _analysis_cache_mark_dirty_series(cfg, measurement, field, str(entity_id) if entity_id else None, str(friendly_name) if friendly_name else None, "delete")
            except Exception:
                pass
            return jsonify({"ok": True, "message": f"Deleted v1: measurement={measurement}, last {dur}{' with tag filters' if tag_where else ''}."})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


_STATS_CACHE_SCHED_STARTED = False


def _stats_cache_scheduler_loop() -> None:
    """Nightly/incremental refresh loop for stats caches (best-effort)."""

    while True:
        try:
            cfg = _overlay_from_yaml_if_enabled(load_cfg())
            if not bool(cfg.get("stats_cache_enabled", True)) or not bool(cfg.get("stats_cache_auto_update", True)):
                time.sleep(60)
                continue

            metas = _stats_cache_list_meta()
            if not metas:
                time.sleep(60)
                continue

            def inflight(cache_id: str) -> bool:
                with GLOBAL_STATS_LOCK:
                    for j in GLOBAL_STATS_JOBS.values():
                        try:
                            if str(j.get("cache_id") or "") != cache_id:
                                continue
                            st = str(j.get("state") or "")
                            if st and st not in ("done", "error", "cancelled"):
                                return True
                        except Exception:
                            continue
                return False

            pick = None
            pick_prio = 999
            for m in metas:
                try:
                    cid = str(m.get("id") or "").strip()
                    if not cid:
                        continue
                    if inflight(cid):
                        continue
                    if bool(m.get("dirty")):
                        prio = 0
                    elif bool(m.get("mismatch")):
                        prio = 1
                    elif _stats_cache_is_stale(cfg, m):
                        prio = 5
                    else:
                        continue
                    if prio < pick_prio:
                        pick = cid
                        pick_prio = prio
                except Exception:
                    continue

            if pick:
                try:
                    job_id = _stats_cache_start_update_job(pick, trigger_page="scheduler", timer_id="stats_cache")
                    _timer_mark_started("stats_cache", job_id=job_id)
                except Exception:
                    pass
        except Exception:
            pass

        time.sleep(60)


def _stats_cache_scheduler_start() -> None:
    global _STATS_CACHE_SCHED_STARTED
    if _STATS_CACHE_SCHED_STARTED:
        return
    _STATS_CACHE_SCHED_STARTED = True
    t = threading.Thread(target=_stats_cache_scheduler_loop, daemon=True)
    t.start()
    try:
        LOG.info("stats_cache scheduler started")
    except Exception:
        pass


try:
    _stats_cache_scheduler_start()
except Exception:
    pass


_DASH_CACHE_SCHED_STARTED = False


def _dash_cache_scheduler_loop() -> None:
    """Background refresh loop for dashboard caches (best-effort)."""

    while True:
        try:
            cfg = _overlay_from_yaml_if_enabled(load_cfg())
            if not bool(cfg.get("dash_cache_enabled", True)) or not bool(cfg.get("dash_cache_auto_update", True)):
                time.sleep(60)
                continue

            metas = _dash_cache_list_meta()
            if not metas:
                time.sleep(60)
                continue

            def inflight(cache_id: str) -> bool:
                with DASH_CACHE_JOBS_LOCK:
                    for j in DASH_CACHE_JOBS.values():
                        try:
                            if str(j.get("cache_id") or "") != cache_id:
                                continue
                            st = str(j.get("state") or "")
                            if st and st not in ("done", "error", "cancelled"):
                                return True
                        except Exception:
                            continue
                return False

            # Pick one due cache per tick (rate limit).
            pick = None
            pick_prio = 999
            for m in metas:
                try:
                    cid = str(m.get("id") or "").strip()
                    if not cid:
                        continue
                    if inflight(cid):
                        continue
                    if bool(m.get("dirty")):
                        prio = 0
                    elif bool(m.get("mismatch")):
                        prio = 1
                    elif _dash_cache_is_stale(cfg, m):
                        prio = 5
                    else:
                        continue
                    if prio < pick_prio:
                        pick = cid
                        pick_prio = prio
                except Exception:
                    continue

            if pick:
                try:
                    job_id = _dash_cache_start_job("update", pick, trigger_page="scheduler", timer_id="dash_cache")
                    _timer_mark_started("dash_cache", job_id=job_id)
                except Exception:
                    pass
        except Exception:
            # Never crash the loop
            pass

        time.sleep(60)


def _dash_cache_scheduler_start() -> None:
    global _DASH_CACHE_SCHED_STARTED
    if _DASH_CACHE_SCHED_STARTED:
        return
    _DASH_CACHE_SCHED_STARTED = True
    t = threading.Thread(target=_dash_cache_scheduler_loop, daemon=True)
    t.start()
    try:
        LOG.info("dash_cache scheduler started")
    except Exception:
        pass


try:
    _dash_cache_scheduler_start()
except Exception:
    pass


_STATS_FULL_SCHED_STARTED = False


def _stats_full_due_now(cfg: dict[str, Any]) -> bool:
    try:
        mode = str(cfg.get("stats_full_refresh_mode") or "manual").strip().lower()
        if mode not in ("hours", "daily", "weekly", "manual"):
            mode = "manual"
        if mode == "manual":
            return False

        st = _timers_state_get("stats_full")
        last_run = _parse_iso_datetime(str(st.get("last_run_at") or "").strip())
        last_ts = last_run.timestamp() if last_run else 0.0

        if mode == "hours":
            try:
                h = int(cfg.get("stats_full_refresh_hours") or 24)
            except Exception:
                h = 24
            if h <= 0:
                return False
            if last_ts <= 0:
                return True
            return (datetime.now(timezone.utc).timestamp() - last_ts) >= float(h * 3600)

        at = str(cfg.get("stats_full_refresh_daily_at") or "03:00:00").strip() or "03:00:00"
        hh, mm, ss = _timer_parse_hms(at, (3, 0, 0))
        wd = _timer_parse_weekday(cfg.get("stats_full_refresh_weekday"), default=0)

        now_local = datetime.now().astimezone()
        boundary = _timer_last_boundary_local(now_local, mode=mode, hh=hh, mm=mm, ss=ss, weekday=wd)
        if not boundary:
            return False

        if last_ts <= 0:
            return True
        last_local = datetime.fromtimestamp(last_ts, tz=timezone.utc).astimezone(now_local.tzinfo)
        return last_local < boundary
    except Exception:
        return False


def _stats_full_inflight() -> bool:
    try:
        with GLOBAL_STATS_LOCK:
            for j in GLOBAL_STATS_JOBS.values():
                try:
                    if str(j.get("timer_id") or "").strip() != "stats_full":
                        continue
                    st = str(j.get("state") or "")
                    if st and st not in ("done", "error", "cancelled"):
                        return True
                except Exception:
                    continue
    except Exception:
        return False
    return False


def _stats_full_scheduler_loop() -> None:
    """Scheduled trigger for stats_full global stats job (best-effort)."""

    while True:
        try:
            cfg = _overlay_from_yaml_if_enabled(load_cfg())
            if not _stats_full_due_now(cfg):
                time.sleep(30)
                continue
            if _stats_full_inflight():
                time.sleep(30)
                continue

            # Start the full global stats job.
            stop_dt = datetime.now(timezone.utc)
            try:
                max_days = int(cfg.get("stats_full_max_days") or 3650)
            except Exception:
                max_days = 3650
            max_days = min(36500, max(1, max_days))
            start_dt = stop_dt - timedelta(days=max_days)
            cols = ["last_value", "oldest_time", "newest_time", "count", "min", "max", "mean"]
            job_id = _global_stats_start_job(
                cfg=cfg,
                start_dt=start_dt,
                stop_dt=stop_dt,
                field_filter=None,
                measurement_filter=None,
                entity_id_filter=None,
                friendly_name_filter=None,
                series_list=None,
                columns=cols,
                page_limit=200,
                trigger_page="scheduler",
                timer_id="stats_full",
                cache_id=None,
                cache_key=None,
            )
            _timer_mark_started("stats_full", job_id=job_id)
        except Exception:
            pass

        time.sleep(30)


def _stats_full_scheduler_start() -> None:
    global _STATS_FULL_SCHED_STARTED
    if _STATS_FULL_SCHED_STARTED:
        return
    _STATS_FULL_SCHED_STARTED = True
    t = threading.Thread(target=_stats_full_scheduler_loop, daemon=True)
    t.start()
    try:
        LOG.info("stats_full scheduler started")
    except Exception:
        pass


try:
    _stats_full_scheduler_start()
except Exception:
    pass


_ANALYSIS_NIGHTLY_SCHED_STARTED = False


def _analysis_nightly_scheduler_loop() -> None:
    """Scheduled trigger for analysis_nightly series refresh (best-effort)."""

    while True:
        try:
            cfg = _overlay_from_yaml_if_enabled(load_cfg())
            if not bool(cfg.get("analysis_nightly_enabled", True)) or not bool(cfg.get("analysis_nightly_auto_update", True)):
                time.sleep(60)
                continue

            pick = _analysis_nightly_pick_series(cfg)
            if pick:
                try:
                    job_id = _analysis_nightly_start_job(pick, trigger_page="scheduler", timer_id="analysis_nightly")
                    try:
                        _timer_event_append("analysis_nightly", "scheduler_start", {
                            "job_id": job_id,
                            "series_key": str(pick.get("series_key") or ""),
                        })
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

        time.sleep(60)


def _analysis_nightly_scheduler_start() -> None:
    global _ANALYSIS_NIGHTLY_SCHED_STARTED
    if _ANALYSIS_NIGHTLY_SCHED_STARTED:
        return
    _ANALYSIS_NIGHTLY_SCHED_STARTED = True
    t = threading.Thread(target=_analysis_nightly_scheduler_loop, daemon=True)
    t.start()
    try:
        LOG.info("analysis_nightly scheduler started")
    except Exception:
        pass


try:
    _analysis_nightly_scheduler_start()
except Exception:
    pass

_VERSION_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._-]*$")


def _read_addon_version() -> str:
    env = (os.environ.get("ADDON_VERSION") or "").strip()
    if env and env not in ("0", "null") and _VERSION_RE.match(env):
        return env

    # Fallback to the metadata file baked into the image.
    try:
        meta = Path(__file__).resolve().parent / "addon_config.yaml"
        if meta.exists():
            data = yaml.safe_load(meta.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                v = (data.get("version") or "").strip()
                if v and _VERSION_RE.match(v):
                    return v
    except Exception:
        pass

    return "dev"


ADDON_VERSION = _read_addon_version()


@app.context_processor
def _inject_globals():
    return {"addon_version": ADDON_VERSION}


@app.get("/api/info")
def api_info():
    return jsonify({
        "ok": True,
        "version": ADDON_VERSION,
        "ha_platform": _ha_platform(),
        "influx_cli_available": _influx_cli_available(),
    })


@app.get("/api/sysinfo")
def api_sysinfo():
    cfg = load_cfg()
    rss = _process_rss_bytes()
    data_bytes = _addon_data_usage_bytes()

    # Add-on process uptime (best-effort)
    uptime_s = None
    try:
        uptime_s = int(max(0.0, time.monotonic() - float(PROCESS_STARTED_MONO)))
    except Exception:
        uptime_s = None

    disk_total = None
    disk_free = None
    try:
        du = shutil.disk_usage(str(DATA_DIR))
        disk_total = int(du.total)
        disk_free = int(du.free)
    except Exception:
        pass

    load1 = None
    load5 = None
    load15 = None
    try:
        a, b, c = os.getloadavg()
        load1, load5, load15 = float(a), float(b), float(c)
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "sys": {
            "started_at": PROCESS_STARTED_AT,
            "uptime_seconds": uptime_s,
            "uptime": _hms(uptime_s) if isinstance(uptime_s, int) else None,
            "rss_bytes": rss,
            "rss": _fmt_bytes(rss),
            "addon_data_bytes": data_bytes,
            "addon_data": _fmt_bytes(data_bytes),
            "disk_total_bytes": disk_total,
            "disk_free_bytes": disk_free,
            "disk_total": _fmt_bytes(disk_total),
            "disk_free": _fmt_bytes(disk_free),
            "cpu_count": os.cpu_count(),
            "loadavg_1": load1,
            "loadavg_5": load5,
            "loadavg_15": load15,
            "ui_status_show_sysinfo": bool(cfg.get("ui_status_show_sysinfo", False)),
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
