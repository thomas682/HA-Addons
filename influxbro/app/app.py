import json
import logging
import logging.handlers
import math
import os
import re
import shutil
import socket
import ssl
import sys
import threading
import time
import uuid
import urllib.error
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request
from influxdb_client import InfluxDBClient
from influxdb_client import Point
from influxdb_client import WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb import InfluxDBClient as InfluxDBClientV1

import yaml # pyright: ignore[reportMissingModuleSource]

CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "/config"))
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))

APP_DIR = Path(__file__).resolve().parent
DEFAULT_BACKUP_DIR = CONFIG_DIR / "influxbro" / "backup"
OLD_DEFAULT_BACKUP_DIR = DATA_DIR / "backups"

# default; may be overridden via UI config
BACKUP_DIR = DEFAULT_BACKUP_DIR

GLOBAL_STATS_JOBS: dict[str, dict[str, Any]] = {}
GLOBAL_STATS_LOCK = threading.RLock()

HISTORY_LOCK = threading.RLock()
HISTORY_PATH = DATA_DIR / "influxbro_history.jsonl"

RESTORE_COPY_JOBS: dict[str, dict[str, Any]] = {}
RESTORE_COPY_LOCK = threading.RLock()

BACKUP_JOBS: dict[str, dict[str, Any]] = {}
BACKUP_LOCK = threading.RLock()


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
    return merged


app = Flask(__name__)
RUNTIME_CFG_FILE = DATA_DIR / "influx_browser_config.json"

LOG_FILE = DATA_DIR / "influxbro.log"


def _redact_secrets(s: str) -> str:
    if not s:
        return ""
    out = s
    # Bearer tokens
    out = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)([^\s\"]+)", r"\1***", out)
    # Common key=value patterns
    out = re.sub(r"(?i)\b(token|password|passwd|api_key|apikey)\s*[:=]\s*([^\s,;\"]+)", r"\1=***", out)
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


def log_details(msg: str, *args: object) -> None:
    if not DETAILS_ENABLED:
        return
    try:
        DETAIL_LOG.debug(msg, *args)
    except Exception:
        return


def log_query(label: str, query: str) -> None:
    """Log an Influx query string under TRACE when enabled."""

    if not (DETAILS_ENABLED and INFLUX_QUERY_LOGGING):
        return
    q = (query or "").strip()
    if not q:
        return
    try:
        DETAIL_LOG.debug("%s:\n%s", label, q)
    except Exception:
        return


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

def env_bool(key: str, default: bool) -> bool:
    v = os.environ.get(key, str(default)).lower()
    return v in ("1", "true", "yes", "on")

# Writing/editing/deleting is controlled via runtime config (UI settings).
# Keep env var unused for backward compatibility (do not rely on it).
_ALLOW_DELETE_ENV = env_bool("ALLOW_DELETE", False)
DELETE_CONFIRM_PHRASE = os.environ.get("DELETE_CONFIRM_PHRASE", "DELETE")

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
    "org": "",
    "bucket": "",
    # v1
    "username": "",
    "password": "",
    "database": "",

    # UI defaults
    "ui_table_visible_rows": 20,
    "ui_table_row_height_px": 13,
    "ui_edit_neighbors_n": 5,
    "ui_edit_details_visible_rows": 12,
    "ui_edit_graph_buffer_minutes": 30,
    "ui_edit_graph_max_points": 50000,
    "ui_query_max_points": 5000,
    "ui_raw_max_points": 20000,
    "ui_decimals": 3,

    "ui_font_size_px": 14,
    "ui_font_small_px": 11,
    "ui_checkbox_scale": 0.85,
    "ui_filter_label_width_px": 170,
    "ui_filter_control_width_px": 320,
    "ui_filter_search_width_px": 160,

    # Restore
    "restore_preview_lines": 5,

    # Tooltips
    "ui_tooltips_enabled": True,

    # Links / Info
    "ui_repo_url": "https://github.com/thomas682/HA-Addons",
    "ui_paypal_donate_url": "https://www.paypal.com/donate/?hosted_button_id=ZWZE3WM4NBUW6",

    # Backups (must live under /config or /data)
    "backup_dir": str(DEFAULT_BACKUP_DIR),
    # One-time migration marker when moving from the old default (/data/backups)
    "backup_migrated_to_config": False,

    # Default collapsed sections
    "ui_open_selection": False,
    "ui_open_graph": False,
    "ui_open_filterlist": False,
    "ui_open_editlist": False,
    "ui_open_stats_total": False,
    "ui_open_stats_current": True,

    # Outlier scan defaults (max jump per point)
    # Based on a typical household connection: 3-phase 400V, 35A -> ~24.2kW; use 30kW as practical ceiling.
    "outlier_max_step_w": 30000,
    "outlier_max_step_kw": 30,
    # Energy deltas depend on sampling interval; defaults assume coarse (hour-ish) steps.
    "outlier_max_step_wh": 30000,
    "outlier_max_step_kwh": 30,

    # Logging (stdout + optional /data log file)
    "log_to_file": True,
    # Log profiles (standard-ish): error, debug, trace
    "log_profile": "debug",
    # Backward-compat / advanced (ignored if log_profile is set)
    "log_level": "DEBUG",
    "log_max_mb": 5,
    "log_backup_count": 5,
    "log_max_age_days": 14,
    "log_http_requests": False,
    "log_influx_queries": False,

    # Safety: allow writes/deletes from UI
    "writes_enabled": True,
}


def writes_enabled(cfg: dict[str, Any]) -> bool:
    try:
        v = cfg.get("writes_enabled", True)
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        return s in ("1", "true", "yes", "on")
    except Exception:
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


# Configure logging early from persisted config.
try:
    configure_logging(load_cfg())
except Exception:
    # Worst case: Flask still logs to stderr.
    pass


def save_cfg(cfg: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_CFG_FILE.write_text(json.dumps(cfg, indent=2, sort_keys=True), encoding="utf-8")


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


def _flux_range_clause(range_key: str, start: datetime | None, stop: datetime | None) -> str:
    if start and stop:
        s = _dt_to_rfc3339_utc(start)
        e = _dt_to_rfc3339_utc(stop)
        return f'|> range(start: time(v: "{s}"), stop: time(v: "{e}"))'
    rk = (range_key or "").strip().lower()
    if rk in ("all", "alle", "inf", "infinite", "infinity"):
        return '|> range(start: time(v: "1970-01-01T00:00:00Z"))'
    return f"|> range(start: {range_to_flux(range_key)})"


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
    # Try to extract the JSON {"message":"..."} part from influxdb-client exception strings.
    m = re.search(r'"message"\s*:\s*"([^"]+)"', s)
    if m:
        return m.group(1)
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


@contextmanager
def v2_client(cfg: dict, timeout_seconds_override: int | None = None):
    """Context-managed InfluxDB v2 client."""
    url = cfg.get("url") or f'{cfg.get("scheme","http")}://{cfg.get("host","localhost")}:{int(cfg.get("port",8086))}'
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
    
@app.get("/")
def index():
    cfg = load_cfg()
    return render_template(
        "index.html",
        cfg=cfg,
        allow_delete=writes_enabled(cfg),
        delete_phrase=DELETE_CONFIRM_PHRASE,
        nav="dashboard",
    )


@app.get("/stats")
def stats_page():
    cfg = load_cfg()
    return render_template("stats.html", cfg=cfg, allow_delete=writes_enabled(cfg), nav="stats")


@app.get("/logs")
def logs_page():
    cfg = load_cfg()
    return render_template("logs.html", cfg=cfg, allow_delete=writes_enabled(cfg), nav="logs")


@app.get("/jobs")
def jobs_page():
    cfg = load_cfg()
    return render_template("jobs.html", cfg=cfg, allow_delete=writes_enabled(cfg), nav="jobs")


@app.get("/history")
def history_page():
    cfg = load_cfg()
    return render_template(
        "history.html",
        cfg=cfg,
        allow_delete=writes_enabled(cfg),
        delete_phrase=DELETE_CONFIRM_PHRASE,
        nav="history",
    )


@app.get("/backup")
def backup_page():
    cfg = load_cfg()
    return render_template("backup.html", cfg=cfg, allow_delete=writes_enabled(cfg), nav="backup")


@app.get("/restore")
def restore_page():
    cfg = load_cfg()
    return render_template(
        "restore.html",
        cfg=cfg,
        allow_delete=writes_enabled(cfg),
        delete_phrase=DELETE_CONFIRM_PHRASE,
        nav="restore",
    )


@app.get("/info")
def info_page():
    cfg = load_cfg()
    repo_url = (cfg.get("ui_repo_url") or "").strip()
    changelog = ""
    try:
        changelog = (APP_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    except Exception:
        changelog = ""
    return render_template(
        "info.html",
        cfg=cfg,
        allow_delete=writes_enabled(cfg),
        nav="info",
        repo_url=repo_url,
        changelog_text=changelog,
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
        allow_delete=writes_enabled(cfg),
        nav="manual",
        manual_text=manual,
    )

@app.get("/config")
def config_page():
    cfg = load_cfg()
    return render_template(
        "config.html",
        cfg=cfg,
        allow_delete=writes_enabled(cfg),
        delete_phrase=DELETE_CONFIRM_PHRASE,
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
    if redacted.get("password"):
        redacted["password"] = "********"
    return jsonify({
        "ok": True,
        "config": redacted,
        # Backward-compat key; now reflects writes_enabled from config.
        "allow_delete": writes_enabled(cfg),
        "writes_enabled": writes_enabled(cfg),
        "delete_confirm_phrase": DELETE_CONFIRM_PHRASE,
        "autodetect_source": LAST_AUTODETECT_SOURCE,
    })


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
        "bucket_count": None,
        "database_count": None,
        "ha_database": (cfg.get("bucket") if int(cfg.get("influx_version", 2)) == 2 else cfg.get("database")) or None,
        "note": "Hinweis: Speicherplatz/Freiplatz/Memory der InfluxDB sind ueber die Influx HTTP API nicht verlaesslich abrufbar. Anzeige ist best-effort.",
    }

    # Health endpoint (v2 + some v1 builds)
    try:
        st, js, err = _http_get_json(base_url.rstrip("/") + "/health", verify_ssl=verify_ssl, timeout_s=min(8, timeout_s))
        if js:
            info["health"] = str(js.get("status") or "") or (f"HTTP {st}" if st else None)
            info["influx_version"] = str(js.get("version") or js.get("build") or "") or None
        elif err:
            info["health"] = (f"HTTP {st}" if st else None) or ""
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


def _backup_safe(s: str) -> str:
    out = re.sub(r"[^A-Za-z0-9_.-]+", "_", (s or "").strip())
    out = out.strip("_.-")
    return out[:80] if out else "backup"


def _backup_files(dir_path: Path, backup_id: str) -> tuple[Path, Path]:
    stem = _backup_safe(backup_id)
    return dir_path / f"{stem}.json", dir_path / f"{stem}.lp"


def _norm_unit(u: str) -> str:
    return (u or "").strip().lower().replace(" ", "")


def _outlier_max_step(cfg: dict[str, Any], unit: str) -> float:
    u = _norm_unit(unit)
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


def _list_backups(dir_path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not dir_path.exists():
        return out
    for p in sorted(dir_path.glob("*.json")):
        try:
            meta = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(meta, dict):
                continue
            backup_id = str(meta.get("id") or p.stem)
            lp = dir_path / (p.stem + ".lp")
            out.append({
                **meta,
                "id": backup_id,
                "file": p.stem,
                "bytes": int(lp.stat().st_size) if lp.exists() else int(meta.get("bytes") or 0),
            })
        except Exception:
            continue
    # newest first
    out.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return out


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
        "elapsed": _hms(time.monotonic() - float(job.get("started_mono") or time.monotonic())),
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
            return bool(j.get("cancelled"))

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
        return


def _lp_escape_key(v: str) -> str:
    # For measurement, tag keys, and field keys.
    return (v or "").replace("\\", "\\\\").replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def _lp_escape_tag_value(v: str) -> str:
    return (v or "").replace("\\", "\\\\").replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


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


@app.post("/api/backup_create")
def api_backup_create():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    bdir = backup_dir(cfg)
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
    if meta_path.exists() or lp_path.exists():
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
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.get("/api/backup_location")
def api_backup_location():
    cfg = load_cfg()
    bdir = backup_dir(cfg)
    return jsonify({"ok": True, "container_path": str(bdir), "slug": "influxbro"})


@app.post("/api/backup_job/start")
def api_backup_job_start():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}

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
    if meta_path.exists() or lp_path.exists():
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
    if meta_path.exists() or lp_path.exists():
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
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/backup_delete")
def api_backup_delete():
    body = request.get_json(force=True) or {}
    backup_id = (body.get("id") or "").strip()
    if not backup_id:
        return jsonify({"ok": False, "error": "id required"}), 400
    cfg = load_cfg()
    bdir = backup_dir(cfg)
    bdir.mkdir(parents=True, exist_ok=True)
    meta_path, lp_path = _backup_files(bdir, backup_id)
    removed = 0
    for p in (meta_path, lp_path):
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
    if not writes_enabled(cfg):
        return jsonify({"ok": False, "error": "Writes are disabled. Enable writes in Settings."}), 403

    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", False)
    ok_confirm = confirm is True or str(confirm).strip().lower() in ("1", "true", "yes", "on")
    if not ok_confirm:
        return jsonify({"ok": False, "error": "Confirmation required"}), 400

    backup_id = (body.get("id") or "").strip()
    if not backup_id:
        return jsonify({"ok": False, "error": "id required"}), 400

    if int(cfg.get("influx_version", 2)) != 2:
        return jsonify({"ok": False, "error": "restore currently supports InfluxDB v2 only"}), 400
    if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
        return jsonify({
            "ok": False,
            "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
        }), 400

    bdir = backup_dir(cfg)
    meta_path, lp_path = _backup_files(bdir, backup_id)
    if not lp_path.exists():
        return jsonify({"ok": False, "error": "backup not found"}), 404

    try:
        with v2_client(cfg) as c:
            wapi = c.write_api(write_options=SYNCHRONOUS)
            batch: list[str] = []
            applied = 0
            with lp_path.open("r", encoding="utf-8") as f:
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
    if not writes_enabled(cfg):
        return jsonify({"ok": False, "error": "Writes are disabled. Enable writes in Settings."}), 403

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
    meta_path, lp_path = _backup_files(bdir, backup_id)
    if not lp_path.exists():
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
            with lp_path.open("r", encoding="utf-8") as f:
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
        "elapsed": _hms(time.monotonic() - float(job.get("started_mono") or time.monotonic())),
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
        set_state("done", f"Copied points: {applied}")
    except Exception as e:
        set_error(_short_influx_error(e))
        set_state("error", "Fehler")


@app.post("/api/restore_job/start")
def api_restore_job_start():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if not writes_enabled(cfg):
        return jsonify({"ok": False, "error": "Writes are disabled. Enable writes in Settings."}), 403

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

    with GLOBAL_STATS_LOCK:
        g_items = list(GLOBAL_STATS_JOBS.items())
    for _, j in g_items:
        pub = _job_public(j)
        pub["type"] = "global_stats"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        out.append(pub)

    with RESTORE_COPY_LOCK:
        r_items = list(RESTORE_COPY_JOBS.items())
    for _, j in r_items:
        pub = _restore_copy_job_public(j)
        pub["type"] = "restore_copy"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        out.append(pub)

    with BACKUP_LOCK:
        b_items = list(BACKUP_JOBS.items())
    for _, j in b_items:
        pub = _backup_job_public(j)
        pub["type"] = "backup"
        pub["trigger_page"] = j.get("trigger_page")
        pub["trigger_ip"] = j.get("trigger_ip")
        pub["trigger_ua"] = j.get("trigger_ua")
        out.append(pub)

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

    with BACKUP_LOCK:
        if job_id in BACKUP_JOBS:
            BACKUP_JOBS[job_id]["cancelled"] = True
            try:
                LOG.info("job_cancel type=backup job_id=%s ip=%s ua=%s", job_id, _req_ip(), _req_ua())
            except Exception:
                pass
            return jsonify({"ok": True})

    return jsonify({"ok": False, "error": "job not found"}), 404

@app.post("/api/config")
def api_set_config():
    body = request.get_json(force=True) or {}
    cfg = load_cfg()
    allowed = set(DEFAULT_CFG.keys())
    for k, v in body.items():
        if k not in allowed:
            continue
        if k in ("token","password") and v == "********":
            continue
        cfg[k] = v

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
    _clamp_int("ui_table_row_height_px", 13, 9, 60)
    _clamp_int("ui_edit_neighbors_n", 5, 1, 50)
    _clamp_int("ui_edit_details_visible_rows", 12, 4, 80)
    _clamp_int("ui_edit_graph_buffer_minutes", 30, 0, 24 * 60)
    _clamp_int("ui_edit_graph_max_points", 50000, 1000, 200000)
    _clamp_int("ui_query_max_points", 5000, 500, 200000)
    _clamp_int("ui_raw_max_points", 20000, 1000, 200000)
    _clamp_float("ui_checkbox_scale", 0.85, 0.5, 1.6)
    _clamp_int("ui_filter_label_width_px", 170, 80, 360)
    _clamp_int("ui_filter_control_width_px", 320, 180, 900)
    _clamp_int("ui_filter_search_width_px", 160, 80, 420)

    # Optional link
    try:
        cfg["ui_repo_url"] = str(cfg.get("ui_repo_url") or "").strip()
    except Exception:
        cfg["ui_repo_url"] = ""

    try:
        cfg["ui_paypal_donate_url"] = str(cfg.get("ui_paypal_donate_url") or "").strip()
    except Exception:
        cfg["ui_paypal_donate_url"] = ""
    if len(cfg["ui_paypal_donate_url"]) > 600:
        cfg["ui_paypal_donate_url"] = cfg["ui_paypal_donate_url"][:600]

    # Backups directory (must stay under /data)
    try:
        cfg["backup_dir"] = str(cfg.get("backup_dir") or "").strip()
    except Exception:
        cfg["backup_dir"] = str(DEFAULT_CFG.get("backup_dir") or "/data/backups")
    cfg["backup_dir"] = str(backup_dir(cfg))

    def _bool(key: str, default: bool = False) -> None:
        v = cfg.get(key, default)
        if isinstance(v, bool):
            cfg[key] = v
            return
        s = str(v).strip().lower()
        cfg[key] = s in ("1", "true", "yes", "on")

    _bool("ui_open_selection", False)
    _bool("ui_open_graph", False)
    _bool("ui_open_filterlist", False)
    _bool("ui_open_editlist", False)
    _bool("ui_open_stats", False)

    _bool("ui_tooltips_enabled", True)

    # Safety
    _bool("writes_enabled", True)

    # Logging
    _bool("log_to_file", True)
    _bool("log_http_requests", False)
    _bool("log_influx_queries", False)
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

    save_cfg(cfg)
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
                return jsonify({"ok": True, "message": "Connection OK (v2)."})
        else:
            if not cfg.get("database"):
                cfg = _overlay_from_yaml_if_possible(cfg)

            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "v1 needs database (oder gültige influx.yaml im angegebenen Pfad)."}), 400

            c = v1_client(cfg)
            c.ping()
            return jsonify({"ok": True, "message": "Connection OK (v1)."})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500
@app.get("/api/measurements")
def measurements():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    try:
        if int(cfg.get("influx_version",2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400
            with v2_client(cfg) as c:
                q = f'import "influxdata/influxdb/schema"\nschema.measurements(bucket: "{cfg["bucket"]}")'
                tables = c.query_api().query(q, org=cfg["org"])
                items = []
                for t in tables:
                    for r in t.records:
                        items.append(str(r.get_value()))
                return jsonify({"ok": True, "measurements": sorted(set(items))})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            c = v1_client(cfg)
            res = c.query("SHOW MEASUREMENTS")
            items = []
            for _, points in res.items():
                for p in points:
                    items.append(p.get("name"))
            return jsonify({"ok": True, "measurements": sorted(set(items))})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

@app.get("/api/fields")
def fields():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    measurement = request.args.get("measurement", "")
    if not measurement:
        return jsonify({"ok": False, "error": "measurement required"}), 400
    try:
        if int(cfg.get("influx_version",2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400
            with v2_client(cfg) as c:
                q = f'''
 import "influxdata/influxdb/schema"
  schema.measurementFieldKeys(bucket: "{cfg["bucket"]}", measurement: "{_flux_escape(measurement)}")
 '''
                tables = c.query_api().query(q, org=cfg["org"])
                fs = []
                for t in tables:
                    for r in t.records:
                        fs.append(str(r.get_value()))
                return jsonify({"ok": True, "fields": sorted(set(fs))})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            c = v1_client(cfg)
            res = c.query(f'SHOW FIELD KEYS FROM "{measurement}"')
            fs = []
            for _, points in res.items():
                for p in points:
                    fs.append(p.get("fieldKey"))
            return jsonify({"ok": True, "fields": sorted(set(fs))})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

@app.get("/api/tag_values")
def tag_values():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    tag = request.args.get("tag", "")
    measurement = request.args.get("measurement", "")
    range_key = request.args.get("range", "24h")
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
            if entity_id:
                predicate_parts.append(f"r.entity_id == {_flux_str(entity_id)}")
            if friendly_name:
                predicate_parts.append(f"r.friendly_name == {_flux_str(friendly_name)}")
            predicate = " and ".join(predicate_parts) if predicate_parts else "true"

            with v2_client(cfg) as c:
                # schema.tagValues does not support stop; for custom ranges we use a direct query.
                if stop_dt and start_dt:
                    range_clause = _flux_range_clause(range_key, start_dt, stop_dt)
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
  |> limit(n: 5000)
'''
                else:
                    start_arg = range_to_flux(range_key)
                    q = f'''
import "influxdata/influxdb/schema"
schema.tagValues(
  bucket: "{cfg["bucket"]}",
  tag: "{tag}",
  predicate: (r) => {predicate},
  start: {start_arg}
)
'''
                tables = c.query_api().query(q, org=cfg["org"])
                vals = []
                for t in tables:
                    for r in t.records:
                        vals.append(str(r.get_value()))
                return jsonify({"ok": True, "values": sorted(set(vals))})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            c = v1_client(cfg)
            where = f"WHERE {_influxql_time_where(range_key, start_dt, stop_dt)}"
            if entity_id:
                safe_entity_id = entity_id.replace("'", "\\'")
                where += f' AND "entity_id"=\'{safe_entity_id}\''
            if friendly_name:
                safe_name = friendly_name.replace("'", "\\'")
                where += f' AND "friendly_name"=\'{safe_name}\''
            q = f'SHOW TAG VALUES WITH KEY = "{tag}" {where}'
            res = c.query(q)
            vals = []
            for _, points in res.items():
                for p in points:
                    v = p.get("value")
                    if v is not None:
                        vals.append(str(v))
            return jsonify({"ok": True, "values": sorted(set(vals))})
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

@app.post("/api/query")
def query():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    measurement = body.get("measurement", "")
    field = body.get("field", "")
    range_key = body.get("range", "24h")
    entity_id = body.get("entity_id") or None
    friendly_name = body.get("friendly_name") or None

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

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

    try:
        if int(cfg.get("influx_version",2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400
            extra = flux_tag_filter(entity_id, friendly_name)
            with v2_client(cfg) as c:
                range_clause = _flux_range_clause(range_key, start_dt, stop_dt)
                q = f'''
from(bucket: "{cfg["bucket"]}")
  {range_clause}
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"])
'''
                log_query("api.query (flux)", q)
                tables = c.query_api().query(q, org=cfg["org"])
                rows = []
                for t in tables:
                    for r in t.records:
                        ts = r.get_time()
                        val = r.get_value()
                        if isinstance(ts, datetime):
                            ts = ts.astimezone(timezone.utc).isoformat()
                        rows.append({"time": ts, "value": val})
                max_points = int(cfg.get("ui_query_max_points", 5000) or 5000)
                if max_points < 500:
                    max_points = 500
                if max_points > 200000:
                    max_points = 200000
                if len(rows) > max_points:
                    step = math.ceil(len(rows) / max_points)
                    rows = rows[::step]
                return jsonify({"ok": True, "rows": rows, "query": q.strip()})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            c = v1_client(cfg)
            tag_where = influxql_tag_filter(entity_id, friendly_name)
            time_where = _influxql_time_where(range_key, start_dt, stop_dt)
            q = f'SELECT "{field}" FROM "{measurement}" WHERE {time_where}{tag_where} ORDER BY time ASC'
            log_query("api.query (influxql)", q)
            res = c.query(q)
            rows = []
            for _, points in res.items():
                for p in points:
                    rows.append({"time": p.get("time"), "value": p.get(field)})
            max_points = int(cfg.get("ui_query_max_points", 5000) or 5000)
            if max_points < 500:
                max_points = 500
            if max_points > 200000:
                max_points = 200000
            if len(rows) > max_points:
                step = math.ceil(len(rows) / max_points)
                rows = rows[::step]
            return jsonify({"ok": True, "rows": rows, "query": q.strip()})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


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

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
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

    try:
        LOG.debug(
            "api.raw_points measurement=%s field=%s entity_id=%s friendly_name=%s limit=%s offset=%s",
            measurement,
            field,
            bool(entity_id),
            bool(friendly_name),
            limit,
            offset,
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

            q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: {limit}, offset: {offset})
'''

            log_query("api.raw_points (flux)", q)

            q_count = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
  |> keep(columns: ["_value"])
  |> group()
  |> count(column: "_value")
'''

            if include_total:
                log_query("api.raw_points (flux count)", q_count)

            rows: list[dict[str, Any]] = []
            total_count: int | None = None
            with v2_client(cfg) as c:
                qapi = c.query_api()
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

            return jsonify({
                "ok": True,
                "rows": rows,
                "meta": {
                    "start": start,
                    "stop": stop,
                    "limit": limit,
                    "offset": offset,
                    "returned": len(rows),
                    "total_count": total_count,
                    "query_language": "flux",
                    "query": q.strip(),
                    "query_count": q_count.strip() if include_total else None,
                },
            })

        # v1
        if not cfg.get("database"):
            return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400

        c = v1_client(cfg)
        start = _dt_to_rfc3339_utc(start_dt)
        stop = _dt_to_rfc3339_utc(stop_dt)
        tag_where = influxql_tag_filter(entity_id, friendly_name)
        time_where = f"time >= '{start}' AND time <= '{stop}'"
        q = f'SELECT "{field}" FROM "{measurement}" WHERE {time_where}{tag_where} ORDER BY time ASC LIMIT {limit} OFFSET {offset}'
        log_query("api.raw_points (influxql)", q)
        res = c.query(q)
        rows: list[dict[str, Any]] = []
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

        return jsonify({
            "ok": True,
            "rows": rows,
            "meta": {
                "start": start,
                "stop": stop,
                "limit": limit,
                "offset": offset,
                "returned": len(rows),
                "total_count": total_count,
                "query_language": "influxql",
                "query": q,
                "query_count": q2 if include_total else None,
            },
        })

    except Exception as e:
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
    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400
    if not start_dt or not stop_dt:
        return jsonify({"ok": False, "error": "start and stop required"}), 400

    try:
        max_points = int(body.get("max_points") or cfg.get("ui_edit_graph_max_points") or 50000)
    except Exception:
        max_points = int(cfg.get("ui_edit_graph_max_points") or 50000)
    if max_points < 1000:
        max_points = 1000
    if max_points > 200000:
        max_points = 200000

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
        agg = f'  |> aggregateWindow(every: {every_ms}ms, fn: mean, createEmpty: false)\n'
        mode = "downsample"

    q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
  |> filter(fn: (r) => r._measurement == {_flux_str(measurement)} and r._field == {_flux_str(field)}{extra})
{agg}  |> keep(columns: ["_time","_value"])
  |> sort(columns: ["_time"], desc: false)
  |> limit(n: {max_points})
'''

    try:
        log_query("api.window_points (flux)", q)
        rows: list[dict[str, Any]] = []
        with v2_client(cfg) as c:
            tables = c.query_api().query(q, org=cfg["org"])
            for t in tables or []:
                for r in getattr(t, "records", []) or []:
                    ts = r.get_time()
                    val = r.get_value()
                    if isinstance(ts, datetime):
                        rows.append({"time": _dt_to_rfc3339_utc_ms(ts), "value": val})
        return jsonify({"ok": True, "rows": rows, "meta": {"mode": mode, "every_ms": every_ms, "max_points": max_points}})
    except Exception as e:
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
    log_query("api.point_neighbors (flux older)", q_older)
    log_query("api.point_neighbors (flux newer)", q_newer)
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
                    q_old = _q_one('data |> sort(columns: ["_time"]) |> limit(n:1)')
                    log_query("api.stats (flux oldest)", q_old)
                    tables = c.query_api().query(q_old, org=cfg["org"])
                    rec = _first_record(tables)
                    if rec is not None:
                        ts = rec.get_time()
                        out["oldest_time"] = ts.astimezone(timezone.utc).isoformat() if isinstance(ts, datetime) else ts
                        out["first_value"] = rec.get_value()
                except Exception:
                    pass

                try:
                    q_new = _q_one('data |> sort(columns: ["_time"], desc: true) |> limit(n:1)')
                    log_query("api.stats (flux newest)", q_new)
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

            return jsonify({"ok": True, "stats": out, "stats_scope": stats_scope})
    except Exception as e:
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
        "elapsed": _hms(time.monotonic() - float(job.get("started_mono") or time.monotonic())),
        "total_points": total,
        "scanned_points": scanned,
        "percent": pct,
        "groups": groups,
        "total_series": total_series,
        "current": job.get("current") or "",
        "last_query_label": job.get("last_query_label") or "",
        "last_query": job.get("last_query") or "",
        "cancelled": bool(job.get("cancelled")),
        "error": job.get("error"),
        "ready": job.get("state") == "done",
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

    want_cols = [str(c).strip() for c in (columns or []) if str(c).strip()]
    if not want_cols:
        want_cols = ["last_value", "newest_time", "count", "min", "max", "mean", "oldest_time"]
    want_set = set(want_cols)

    want_details = any(c in want_set for c in ("count", "min", "max", "mean", "oldest_time"))
    want_last = ("last_value" in want_set) or ("newest_time" in want_set)

    def _is_timeout_error(e: Exception) -> bool:
        s = str(e).lower()
        return ("timed out" in s) or ("timeout" in s) or ("read timed out" in s)

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
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["state"] = state
                GLOBAL_STATS_JOBS[job_id]["message"] = msg

    def should_cancel() -> bool:
        with GLOBAL_STATS_LOCK:
            j = GLOBAL_STATS_JOBS.get(job_id)
            return bool(j and j.get("cancelled"))

    def set_query(label: str, q: str) -> None:
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["last_query_label"] = label
                GLOBAL_STATS_JOBS[job_id]["last_query"] = (q or "").strip()

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

        min_chunk_seconds = 5 * 60

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

        def add_row(m: str, f: str, eid: str, fn: str, base_last: dict[str, Any] | None = None, det: dict[str, Any] | None = None) -> None:
            r: dict[str, Any] = {
                "measurement": m,
                "field": f,
                "entity_id": eid,
                "friendly_name": fn,
            }
            if base_last:
                if "newest_time" in base_last:
                    r["newest_time"] = base_last.get("newest_time")
                if "last_value" in base_last:
                    r["last_value"] = base_last.get("last_value")
            if det:
                for k in ("count", "min", "max", "mean", "oldest_time"):
                    if k in det:
                        r[k] = det.get(k)
                # det may also include newest/last
                if "newest_time" in det and "newest_time" not in r:
                    r["newest_time"] = det.get("newest_time")
                if "last_value" in det and "last_value" not in r:
                    r["last_value"] = det.get("last_value")
            rows.append(r)

        with v2_client(cfg_local) as c:
            qapi = c.query_api()

            # If series_list is provided: enrich only these series.
            if series_list is not None:
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
                        scanned_points += max(0, cnum)
                        add_row(m, f, eid, fn, None, det)
                    elif want_last:
                        set_state("query", f"Letzter Wert {idx+1}: {fn or eid or (m + '/' + f)}")
                        base_last = _series_last(qapi, cfg_local["bucket"], m, f, eid, fn)
                        add_row(m, f, eid, fn, base_last, None)
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

                # Load series list for the whole window in a single pass, chunking further on timeouts.
                # This avoids the previous paging approach which repeated a full scan per page.
                min_chunk_seconds = 5 * 60

                def _series_last_span(a: datetime, b: datetime) -> list[dict[str, Any]]:
                    s_iso = _dt_to_rfc3339_utc(a)
                    e_iso = _dt_to_rfc3339_utc(b)
                    q_last = f'''
from(bucket: "{cfg_local["bucket"]}")
  |> range(start: time(v: "{s_iso}"), stop: time(v: "{e_iso}"))
  |> filter(fn: (r) => exists r._measurement and exists r._field)
  {mf_clause}
  {ff_clause}
  {tag_clause.strip()}
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
                    span_s = max(0.0, (b - a).total_seconds())
                    try:
                        return _series_last_span(a, b)
                    except Exception as e:
                        if _is_timeout_error(e) and span_s > min_chunk_seconds:
                            mid = a + timedelta(seconds=(span_s / 2.0))
                            left = _series_last_span_split(a, mid)
                            right = _series_last_span_split(mid, b)
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

                    base_last = {"newest_time": srow.get("newest_time"), "last_value": srow.get("last_value")}
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

        rows.sort(key=lambda r: int(r.get("count") or 0), reverse=True)
        with GLOBAL_STATS_LOCK:
            if job_id in GLOBAL_STATS_JOBS:
                GLOBAL_STATS_JOBS[job_id]["rows"] = rows
                GLOBAL_STATS_JOBS[job_id]["scanned_points"] = scanned_points
                GLOBAL_STATS_JOBS[job_id]["groups_count"] = len(rows)

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

    job_id = uuid.uuid4().hex
    ip = _req_ip()
    ua = _req_ua()
    job = {
        "id": job_id,
        "state": "queued",
        "message": "Start...",
        "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "started_mono": time.monotonic(),
        "trigger_page": "stats",
        "trigger_ip": ip,
        "trigger_ua": ua,
        "total_points": None,
        "scanned_points": 0,
        "total_series": None,
        "groups_count": 0,
        "current": "",
        "last_query_label": "",
        "last_query": "",
        "rows": [],
        "cancelled": False,
        "error": None,
        "field_filter": ff,
        "measurement": measurement_filter,
        "entity_id": entity_id_filter,
        "friendly_name": friendly_name_filter,
        "columns": columns or [],
    }

    try:
        LOG.info(
            "job_start type=global_stats job_id=%s ip=%s ua=%s start=%s stop=%s field_filter=%s measurement=%s entity_id=%s friendly_name=%s cols=%s",
            job_id,
            ip,
            ua,
            _dt_to_rfc3339_utc(start_dt),
            _dt_to_rfc3339_utc(stop_dt),
            ff or "",
            measurement_filter or "",
            entity_id_filter or "",
            friendly_name_filter or "",
            ",".join(columns or []),
        )
    except Exception:
        pass

    # Cleanup old jobs
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
            ff,
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
    return jsonify({"ok": True, "job_id": job_id})


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
    job = _job_get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    if job.get("state") != "done":
        return jsonify({"ok": True, "ready": False, "rows": []})

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

    rows = job.get("rows") or []
    return jsonify({"ok": True, "ready": True, "rows": rows[offset : offset + limit], "total": len(rows)})


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

        ip = request.headers.get("X-Forwarded-For") or request.remote_addr or ""
        ua = request.headers.get("User-Agent") or ""
        LOG.debug("ui_event page=%s ui=%s text=%s ip=%s ua=%s extra=%s", page, ui, text, ip, ua[:80], extra_s)
    except Exception:
        pass

    return jsonify({"ok": True})


@app.post("/api/client_error")
def api_client_error():
    """Receive client-side errors from the browser and write them to the server log.

    This is important because network errors (e.g. "Failed to fetch") and JS errors
    otherwise never show up in the add-on logs.
    """

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

        LOG.error(
            "client_error page=%s msg=%s href=%s ua=%s stack=%s extra=%s",
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

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

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

    include_null = bool(body.get("include_null", False))
    include_zero = bool(body.get("include_zero", False))
    bounds_enabled = bool(body.get("bounds_enabled", False))
    min_v = body.get("min")
    max_v = body.get("max")
    counter_enabled = bool(body.get("counter_enabled", False))
    counter_decrease = bool(body.get("counter_decrease", True))
    counter_max_step = bool(body.get("counter_max_step", True))

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

    max_step = _outlier_max_step(cfg, unit)
    try:
        if "max_step" in body and body.get("max_step") is not None and str(body.get("max_step")).strip() != "":
            max_step = float(body.get("max_step"))
    except Exception:
        pass

    extra = flux_tag_filter(entity_id, friendly_name)
    start = _dt_to_rfc3339_utc(start_dt)
    stop = _dt_to_rfc3339_utc(stop_dt)
    # Note: scanning is done chunked (see _scan_span_split below).

    # Always scan in chunks to support large time windows.
    # If a chunk still contains too many points, split it recursively.
    MAX_SCAN_CHUNK = 200000
    MAX_OUT = 5000
    MIN_CHUNK_SECONDS = 5 * 60

    rows: list[dict[str, Any]] = []
    scanned = 0
    prev_val: float | None = None
    last_time_iso: str | None = None

    try:
        pv = body.get("prev_value")
        if pv is not None and str(pv).strip() != "":
            prev_val = float(pv)
    except Exception:
        prev_val = None

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

    allowed_ops = {">", ">=", "<", "<="}
    has_a = value_a_raw != "" and value_a_op in allowed_ops
    has_b = value_b_raw != "" and value_b_op in allowed_ops
    try:
        a_num = float(value_a_raw) if has_a else None
    except Exception:
        a_num = None
        has_a = False
    try:
        b_num = float(value_b_raw) if has_b else None
    except Exception:
        b_num = None
        has_b = False

    def value_filter_hit(v: float) -> bool:
        if not value_filter_enabled:
            return False
        if not has_a and not has_b:
            return False
        ok_a = True if not has_a else _cmp(value_a_op, v, float(a_num))
        ok_b = True if not has_b else _cmp(value_b_op, v, float(b_num))
        return (ok_a and ok_b) if value_mode == "and" else (ok_a or ok_b)

    def value_filter_reason() -> str:
        if not value_filter_enabled or (not has_a and not has_b):
            return ""
        a_txt = f"({value_a_op} {value_a_raw})" if has_a else ""
        b_txt = f"({value_b_op} {value_b_raw})" if has_b else ""
        if has_a and has_b:
            return f"Filter: {a_txt} {value_mode} {b_txt}"
        return f"Filter: {a_txt or b_txt}"

    def _scan_span(qapi: Any, a: datetime, b: datetime, prev: float | None) -> float | None:
        nonlocal scanned
        nonlocal rows
        nonlocal last_time_iso

        if len(rows) >= MAX_OUT:
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
            if scanned_local > MAX_SCAN_CHUNK:
                # too dense for this span; caller will split
                raise OverflowError("too_many_points")

            t = rec.get_time()
            v = rec.get_value()
            iso = _dt_to_rfc3339_utc(t) if isinstance(t, datetime) else None
            if iso:
                last_time_iso = iso

            reasons: list[str] = []
            if v is None:
                if return_all or include_null:
                    rows.append({"time": iso, "value": None, "reason": "NULL" if not return_all else ""})
                    if len(rows) >= MAX_OUT:
                        return prev
                continue

            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue

            fv = float(v)

            if return_all:
                rows.append({"time": iso, "value": fv, "reason": ""})
                if len(rows) >= MAX_OUT:
                    return fv
                prev = fv
                continue

            if value_filter_enabled and value_filter_hit(fv):
                r = value_filter_reason()
                reasons.append(r or "Filter")
            if include_zero and fv == 0.0:
                reasons.append("0")
            if bounds_enabled:
                if min_num is not None and fv < min_num:
                    reasons.append(f"< min ({min_num})")
                if max_num is not None and fv > max_num:
                    reasons.append(f"> max ({max_num})")

            if counter_enabled and prev is not None:
                d = fv - prev
                if counter_decrease and d < 0:
                    reasons.append("counter decrease")
                if counter_max_step and max_step is not None and d > float(max_step):
                    reasons.append(f"step > {max_step} {unit or ''}".strip())

            if reasons:
                rows.append({"time": iso, "value": fv, "reason": ", ".join(reasons)})
                if len(rows) >= MAX_OUT:
                    return fv

            prev = fv

        return prev

    def _scan_span_split(qapi: Any, a: datetime, b: datetime, prev: float | None) -> float | None:
        span_s = max(0.0, (b - a).total_seconds())
        try:
            return _scan_span(qapi, a, b, prev)
        except OverflowError:
            if span_s <= MIN_CHUNK_SECONDS:
                raise
            mid = a + timedelta(seconds=(span_s / 2.0))
            prev2 = _scan_span_split(qapi, a, mid, prev)
            return _scan_span_split(qapi, mid, b, prev2)

    try:
        with v2_client(cfg) as c:
            qapi = c.query_api()
            try:
                prev_val = _scan_span_split(qapi, start_dt, stop_dt, prev_val)
            except OverflowError:
                return jsonify({
                    "ok": False,
                    "error": f"Zu viele Punkte im Zeitraum ({MAX_SCAN_CHUNK}+ in kleinstem Chunk). Bitte im Graph weiter reinzoomen.",
                }), 413

        return jsonify({
            "ok": True,
            "rows": rows,
            "scanned": scanned,
            "start": start,
            "stop": stop,
            "max_step": max_step,
            "unit": unit,
            "chunked": True,
            "last_time": last_time_iso,
            "last_value": prev_val,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500


@app.post("/api/resolve_signal")
def resolve_signal():
    """Resolve a friendly_name/entity_id to a likely measurement+field."""

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    body = request.get_json(force=True) or {}
    friendly_name = (body.get("friendly_name") or "").strip() or None
    entity_id = (body.get("entity_id") or "").strip() or None
    range_key = body.get("range", "24h")
    measurement_filter = (body.get("measurement_filter") or body.get("measurement") or "").strip() or None

    if not friendly_name and not entity_id:
        return jsonify({"ok": False, "error": "friendly_name or entity_id required"}), 400

    try:
        start_dt, stop_dt = _get_start_stop_from_payload(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"invalid start/stop: {e}"}), 400

    try:
        if int(cfg.get("influx_version", 2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({
                    "ok": False,
                    "error": "InfluxDB v2 requires token, org, bucket. Bitte in /config YAML einlesen und speichern.",
                }), 400

            extra = flux_tag_filter(entity_id, friendly_name)
            range_clause = _flux_range_clause(range_key, start_dt, stop_dt)
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

        res = c.query(f"SHOW SERIES {where_clause} LIMIT 2000")
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
        res_f = c.query(f'SHOW FIELD KEYS FROM "{measurement}"')
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

    Safety: gated behind allow_delete + delete_confirm_phrase.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if not writes_enabled(cfg):
        try:
            LOG.error("apply_edits blocked: writes disabled")
        except Exception:
            pass
        return jsonify({"ok": False, "error": "Writes are disabled. Enable writes in Settings."}), 403

    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", "")
    if confirm != DELETE_CONFIRM_PHRASE:
        return (
            jsonify({"ok": False, "error": f"Confirmation phrase mismatch. Type exactly: {DELETE_CONFIRM_PHRASE}"}),
            400,
        )

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

            return jsonify({"ok": True, "message": f"Applied edits: {applied}", "applied": applied})
    except Exception as ex:
        return jsonify({"ok": False, "error": _short_influx_error(ex)}), 500


@app.post("/api/apply_changes")
def apply_changes():
    """Apply staged changes from the dashboard.

    Supports:
    - overwrite: write new value at timestamp (preserve tags)
    - delete: delete the point at timestamp (narrow window + tag predicate)

    Safety: gated behind writes_enabled + delete_confirm_phrase.
    """

    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if not writes_enabled(cfg):
        return jsonify({"ok": False, "error": "Writes are disabled. Enable writes in Settings."}), 403

    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", "")
    if confirm != DELETE_CONFIRM_PHRASE:
        return (
            jsonify({"ok": False, "error": f"Confirmation phrase mismatch. Type exactly: {DELETE_CONFIRM_PHRASE}"}),
            400,
        )

    measurement = (body.get("measurement") or "").strip()
    field = (body.get("field") or "").strip()
    entity_id = (body.get("entity_id") or "").strip() or None
    friendly_name = (body.get("friendly_name") or "").strip() or None
    changes = body.get("changes")

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
                "ip": _req_ip(),
                "ua": _req_ua(),
            })

            applied += 1

    return jsonify({"ok": True, "applied": applied, "message": f"Applied changes: {applied}"})


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


@app.post("/api/history_rollback")
def api_history_rollback():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if not writes_enabled(cfg):
        return jsonify({"ok": False, "error": "Writes are disabled. Enable writes in Settings."}), 403

    body = request.get_json(force=True) or {}
    confirm = body.get("confirm", "")
    if confirm != DELETE_CONFIRM_PHRASE:
        return (
            jsonify({"ok": False, "error": f"Confirmation phrase mismatch. Type exactly: {DELETE_CONFIRM_PHRASE}"}),
            400,
        )

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

    applied = 0
    with v2_client(cfg) as c:
        wapi = c.write_api(write_options=SYNCHRONOUS)

        for it in wanted:
            action = str(it.get("action") or "").strip().lower()
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

    return jsonify({"ok": True, "applied": applied, "message": f"Rollback applied: {applied}"})

@app.post("/api/delete")
def delete():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if not writes_enabled(cfg):
        return jsonify({"ok": False, "error": "Writes are disabled. Enable writes in Settings."}), 403

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

    if confirm != DELETE_CONFIRM_PHRASE:
        return jsonify({"ok": False, "error": f"Confirmation phrase mismatch. Type exactly: {DELETE_CONFIRM_PHRASE}"}), 400
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
            return jsonify({"ok": True, "message": f"Deleted v2: {predicate} in {cfg['bucket']} from {start.isoformat()} to {stop.isoformat()}"})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            dur = range_to_influxql(range_key)
            c = v1_client(cfg)
            tag_where = influxql_tag_filter(entity_id, friendly_name)
            q = f'DELETE FROM "{measurement}" WHERE time > now() - {dur}{tag_where}'
            c.query(q)
            return jsonify({"ok": True, "message": f"Deleted v1: measurement={measurement}, last {dur}{' with tag filters' if tag_where else ''}."})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

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
    return jsonify({"ok": True, "version": ADDON_VERSION})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
