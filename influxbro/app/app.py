import json
import math
import os
import re
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request
from influxdb_client import InfluxDBClient
from influxdb import InfluxDBClient as InfluxDBClientV1

import yaml

CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "/config"))
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))

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

def env_bool(key: str, default: bool) -> bool:
    v = os.environ.get(key, str(default)).lower()
    return v in ("1", "true", "yes", "on")

ALLOW_DELETE = env_bool("ALLOW_DELETE", False)
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
}

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


def save_cfg(cfg: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_CFG_FILE.write_text(json.dumps(cfg, indent=2, sort_keys=True), encoding="utf-8")


def _parse_range_key(range_key: str) -> tuple[int, str]:
    s = (range_key or "").strip().lower()
    if not s:
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
    n, u = _parse_range_key(range_key)
    return f"-{n}{u}"


def range_to_influxql(range_key: str) -> str:
    n, u = _parse_range_key(range_key)
    return f"{n}{u}"


def parse_range_to_datetimes(range_key: str) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
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


def _flux_range_clause(range_key: str, start: datetime | None, stop: datetime | None) -> str:
    if start and stop:
        s = _dt_to_rfc3339_utc(start)
        e = _dt_to_rfc3339_utc(stop)
        return f'|> range(start: time(v: "{s}"), stop: time(v: "{e}"))'
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
def v2_client(cfg: dict):
    """Context-managed InfluxDB v2 client."""
    url = cfg.get("url") or f'{cfg.get("scheme","http")}://{cfg.get("host","localhost")}:{int(cfg.get("port",8086))}'
    token = cfg.get("token")
    org = cfg.get("org")
    timeout_ms = int(cfg.get("timeout_seconds", 10)) * 1000
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
    return render_template(
        "index.html",
        allow_delete=ALLOW_DELETE,
        delete_phrase=DELETE_CONFIRM_PHRASE,
    )

@app.get("/config")
def config_page():
    cfg = load_cfg()
    return render_template("config.html", cfg=cfg, allow_delete=ALLOW_DELETE, delete_phrase=DELETE_CONFIRM_PHRASE, autodetect_source=LAST_AUTODETECT_SOURCE)


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
    return jsonify({"ok": True, "config": redacted, "allow_delete": ALLOW_DELETE, "delete_confirm_phrase": DELETE_CONFIRM_PHRASE, "autodetect_source": LAST_AUTODETECT_SOURCE})

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

    save_cfg(cfg)
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
                tables = c.query_api().query(q, org=cfg["org"])
                rows = []
                for t in tables:
                    for r in t.records:
                        ts = r.get_time()
                        val = r.get_value()
                        if isinstance(ts, datetime):
                            ts = ts.astimezone(timezone.utc).isoformat()
                        rows.append({"time": ts, "value": val})
                if len(rows) > 5000:
                    step = math.ceil(len(rows) / 5000)
                    rows = rows[::step]
                return jsonify({"ok": True, "rows": rows})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database. Bitte konfigurieren."}), 400
            c = v1_client(cfg)
            tag_where = influxql_tag_filter(entity_id, friendly_name)
            time_where = _influxql_time_where(range_key, start_dt, stop_dt)
            q = f'SELECT "{field}" FROM "{measurement}" WHERE {time_where}{tag_where} ORDER BY time ASC'
            res = c.query(q)
            rows = []
            for _, points in res.items():
                for p in points:
                    rows.append({"time": p.get("time"), "value": p.get(field)})
            if len(rows) > 5000:
                step = math.ceil(len(rows) / 5000)
                rows = rows[::step]
            return jsonify({"ok": True, "rows": rows})
    except Exception as e:
        return jsonify({"ok": False, "error": _short_influx_error(e)}), 500

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
                    tables = c.query_api().query(_q_one("data |> count() |> limit(n:1)"), org=cfg["org"])
                    rec = _first_record(tables)
                    if rec is not None:
                        out["count"] = int(rec.get_value() or 0)
                except Exception:
                    pass

                # oldest/newest (+ first/last values)
                try:
                    tables = c.query_api().query(_q_one('data |> sort(columns: ["_time"]) |> limit(n:1)'), org=cfg["org"])
                    rec = _first_record(tables)
                    if rec is not None:
                        ts = rec.get_time()
                        out["oldest_time"] = ts.astimezone(timezone.utc).isoformat() if isinstance(ts, datetime) else ts
                        out["first_value"] = rec.get_value()
                except Exception:
                    pass

                try:
                    tables = c.query_api().query(
                        _q_one('data |> sort(columns: ["_time"], desc: true) |> limit(n:1)'),
                        org=cfg["org"],
                    )
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
                            tables = c.query_api().query(_q_one(flux_tail), org=cfg["org"])
                            rec = _first_record(tables)
                            if rec is not None:
                                out[name] = rec.get_value()
                        except Exception:
                            return

                    _try_stat("min", "data |> min() |> limit(n:1)")
                    _try_stat("max", "data |> max() |> limit(n:1)")
                    _try_stat("mean", "data |> mean() |> limit(n:1)")
                    _try_stat("stddev", "data |> stddev() |> limit(n:1)")
                    _try_stat("p05", "data |> quantile(q: 0.05) |> limit(n:1)")
                    _try_stat("p50", "data |> quantile(q: 0.50) |> limit(n:1)")
                    _try_stat("p95", "data |> quantile(q: 0.95) |> limit(n:1)")

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
            res = c.query(f'SELECT COUNT("{field}") as count FROM "{measurement}" {where_clause}')
            for _, points in res.items():
                if points:
                    out["count"] = int(points[0].get("count") or 0)
                    break

            # Oldest/newest timestamps + values
            ro = c.query(f'SELECT FIRST("{field}") FROM "{measurement}" {where_clause}')
            rn = c.query(f'SELECT LAST("{field}") FROM "{measurement}" {where_clause}')
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
                        f'SELECT MIN("{field}") as min, MAX("{field}") as max, MEAN("{field}") as mean, '
                        f'STDDEV("{field}") as stddev, PERCENTILE("{field}", 5) as p05, '
                        f'PERCENTILE("{field}", 50) as p50, PERCENTILE("{field}", 95) as p95 '
                        f'FROM "{measurement}" {where_clause}'
                    )
                    res2 = c.query(q_num)
                    for _, points in res2.items():
                        if not points:
                            continue
                        p = points[0]
                        out["min"] = p.get("min")
                        out["max"] = p.get("max")
                        out["mean"] = p.get("mean")
                        out["stddev"] = p.get("stddev")
                        out["p05"] = p.get("p05")
                        out["p50"] = p.get("p50")
                        out["p95"] = p.get("p95")
                        break
                except Exception:
                    pass

            return jsonify({"ok": True, "stats": out, "stats_scope": stats_scope})
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

@app.post("/api/delete")
def delete():
    cfg = _overlay_from_yaml_if_enabled(load_cfg())
    if not ALLOW_DELETE:
        return jsonify({"ok": False, "error": "Deletion is disabled. Enable allow_delete in add-on options."}), 403

    body = request.get_json(force=True) or {}
    measurement = body.get("measurement", "")
    field = body.get("field", "")
    range_key = body.get("range", "24h")
    confirm = body.get("confirm", "")
    entity_id = body.get("entity_id") or None
    friendly_name = body.get("friendly_name") or None

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

@app.get("/api/info")
def api_info():
    return jsonify({"ok": True, "version": ADDON_VERSION})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
