import json
import os
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Flask, render_template, jsonify, request

from influxdb_client import InfluxDBClient
from influxdb import InfluxDBClient as InfluxDBClientV1

import yaml

AUTODETECT_PATHS = [
    "/config/influx.yaml",
    "/config/homeassistant/influx.yaml",
]

def autodetect_influx_cfg():
    """Read Home Assistant's InfluxDB YAML config from /config (if present).

    Returns (detected_cfg_dict, source_path) or (None, None).
    """
    for p in AUTODETECT_PATHS:
        try:
            fp = Path(p)
            if not fp.exists():
                continue
            data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                continue

            # Sometimes configs are nested (e.g., {"influxdb": {...}})
            cfg_block = data.get("influxdb") if isinstance(data.get("influxdb"), dict) else data

            # Heuristic: must contain at least some typical keys
            if not any(k in cfg_block for k in ("host", "port", "token", "organization", "bucket", "database", "api_version")):
                continue

            api_version = cfg_block.get("api_version", 2)
            api_version = int(api_version) if str(api_version) in ("1", "2") else 2

            ssl = bool(cfg_block.get("ssl", False))
            scheme = "https" if ssl else "http"

            detected = {
                "influx_version": api_version,
                "scheme": scheme,
                "host": cfg_block.get("host", DEFAULT_CFG["host"]),
                "port": int(cfg_block.get("port", DEFAULT_CFG["port"])),
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

            return detected, p
        except Exception:
            continue
    return None, None

def apply_autodetect_defaults(cfg: dict):
    """Fill missing/empty config values from autodetect (does not overwrite user values)."""
    detected, src = autodetect_influx_cfg()
    if not detected:
        return cfg, None

    def is_empty(v):
        return v is None or (isinstance(v, str) and v.strip() == "")

    merged = dict(cfg)
    for k, v in detected.items():
        if k not in merged or is_empty(merged.get(k)):
            merged[k] = v
    return merged, src


app = Flask(__name__)

DATA_DIR = Path("/data")
RUNTIME_CFG_FILE = DATA_DIR / "influx_browser_config.json"

def env_bool(key: str, default: bool) -> bool:
    v = os.environ.get(key, str(default)).lower()
    return v in ("1", "true", "yes", "on")

ALLOW_DELETE = env_bool("ALLOW_DELETE", False)
DELETE_CONFIRM_PHRASE = os.environ.get("DELETE_CONFIRM_PHRASE", "DELETE")

LAST_AUTODETECT_SOURCE = None

DEFAULT_CFG = {
    "influx_version": 2,
    "scheme": "http",
    "host": "a0d7b954-influxdb",
    "port": 8086,
    "verify_ssl": True,
    "timeout_seconds": 10,
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
            cfg.update(disk)
        except Exception:
            pass
    return cfg
    
@app.get("/")
def index():
    return render_template("index.html", allow_delete=ALLOW_DELETE)

@app.get("/config")
def config_page():
    cfg = load_cfg()
    return render_template("config.html", cfg=cfg, allow_delete=ALLOW_DELETE, delete_phrase=DELETE_CONFIRM_PHRASE, autodetect_source=LAST_AUTODETECT_SOURCE)


@app.post("/api/autodetect")
def api_autodetect():
    """Detect InfluxDB settings from /config/influx.yaml (or /config/homeassistant/influx.yaml).
    Does NOT persist anything. UI must call /api/config (POST) to save.
    """
    detected, src = autodetect_influx_cfg()
    if not detected:
        return jsonify({"ok": False, "error": "Keine influx.yaml gefunden oder Inhalt nicht erkennbar.", "source": None, "config": None})
    return jsonify({"ok": True, "source": src, "config": detected})

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
    cfg = load_cfg()
    try:
        if int(cfg.get("influx_version",2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({"ok": False, "error": "v2 needs token, org, bucket"}), 400
            with v2_client(cfg) as c:
                q = f'import "influxdata/influxdb/schema"\\nschema.measurements(bucket: "{cfg["bucket"]}") |> limit(n:1)'
                c.query_api().query(q, org=cfg["org"])
                return jsonify({"ok": True, "message": "Connection OK (v2)."})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "v1 needs database"}), 400
            c = v1_client(cfg)
            c.ping()
            return jsonify({"ok": True, "message": "Connection OK (v1)."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/api/measurements")
def measurements():
    cfg = load_cfg()
    try:
        if int(cfg.get("influx_version",2)) == 2:
            if not (cfg.get("token") and cfg.get("org") and cfg.get("bucket")):
                return jsonify({"ok": False, "error": "InfluxDB v2 requires token, org, bucket"}), 400
            with v2_client(cfg) as c:
                q = f'import "influxdata/influxdb/schema"\\nschema.measurements(bucket: "{cfg["bucket"]}")'
                tables = c.query_api().query(q, org=cfg["org"])
                items = []
                for t in tables:
                    for r in t.records:
                        items.append(str(r.get_value()))
                return jsonify({"ok": True, "measurements": sorted(set(items))})
        else:
            if not cfg.get("database"):
                return jsonify({"ok": False, "error": "InfluxDB v1 requires database"}), 400
            c = v1_client(cfg)
            res = c.query("SHOW MEASUREMENTS")
            items = []
            for _, points in res.items():
                for p in points:
                    items.append(p.get("name"))
            return jsonify({"ok": True, "measurements": sorted(set(items))})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/api/fields")
def fields():
    cfg = load_cfg()
    measurement = request.args.get("measurement", "")
    if not measurement:
        return jsonify({"ok": False, "error": "measurement required"}), 400
    try:
        if int(cfg.get("influx_version",2)) == 2:
            with v2_client(cfg) as c:
                q = f'''
import "influxdata/influxdb/schema"
schema.measurementFieldKeys(bucket: "{cfg["bucket"]}", measurement: "{measurement}")
'''
                tables = c.query_api().query(q, org=cfg["org"])
                fs = []
                for t in tables:
                    for r in t.records:
                        fs.append(str(r.get_value()))
                return jsonify({"ok": True, "fields": sorted(set(fs))})
        else:
            c = v1_client(cfg)
            res = c.query(f'SHOW FIELD KEYS FROM "{measurement}"')
            fs = []
            for _, points in res.items():
                for p in points:
                    fs.append(p.get("fieldKey"))
            return jsonify({"ok": True, "fields": sorted(set(fs))})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/api/tag_values")
def tag_values():
    cfg = load_cfg()
    tag = request.args.get("tag", "")
    measurement = request.args.get("measurement", "")
    range_key = request.args.get("range", "24h")
    entity_id = request.args.get("entity_id", "") or None

    if not tag:
        return jsonify({"ok": False, "error": "tag required"}), 400

    try:
        if int(cfg.get("influx_version",2)) == 2:
            start = range_to_flux(range_key)
            predicate_parts = []
            if measurement:
                predicate_parts.append(f'r._measurement == "{measurement}"')
            if entity_id:
                predicate_parts.append(f'r.entity_id == "{entity_id}"')
            predicate = " and ".join(predicate_parts) if predicate_parts else "true"

            with v2_client(cfg) as c:
                q = f'''
import "influxdata/influxdb/schema"
schema.tagValues(
  bucket: "{cfg["bucket"]}",
  tag: "{tag}",
  predicate: (r) => {predicate},
  start: {start}
)
'''
                tables = c.query_api().query(q, org=cfg["org"])
                vals = []
                for t in tables:
                    for r in t.records:
                        vals.append(str(r.get_value()))
                return jsonify({"ok": True, "values": sorted(set(vals))})
        else:
            dur = range_to_influxql(range_key)
            c = v1_client(cfg)
            where = f"WHERE time > now() - {dur}"
            if entity_id:
                safe_entity_id = entity_id.replace("'", "\\'")
                where += f' AND "entity_id"=\'{safe_entity_id}\''
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
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/query")
def query():
    cfg = load_cfg()
    body = request.get_json(force=True) or {}
    measurement = body.get("measurement", "")
    field = body.get("field", "")
    range_key = body.get("range", "24h")
    entity_id = body.get("entity_id") or None
    friendly_name = body.get("friendly_name") or None

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    try:
        if int(cfg.get("influx_version",2)) == 2:
            flux_range = range_to_flux(range_key)
            extra = flux_tag_filter(entity_id, friendly_name)
            with v2_client(cfg) as c:
                q = f'''
from(bucket: "{cfg["bucket"]}")
  |> range(start: {flux_range})
  |> filter(fn: (r) => r._measurement == "{measurement}" and r._field == "{field}"{extra})
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
            dur = range_to_influxql(range_key)
            c = v1_client(cfg)
            tag_where = influxql_tag_filter(entity_id, friendly_name)
            q = f'SELECT "{field}" FROM "{measurement}" WHERE time > now() - {dur}{tag_where} ORDER BY time ASC'
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
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/stats")
def stats():
    cfg = load_cfg()
    body = request.get_json(force=True) or {}
    measurement = body.get("measurement", "")
    field = body.get("field", "")
    range_key = body.get("range", "24h")
    entity_id = body.get("entity_id") or None
    friendly_name = body.get("friendly_name") or None

    if not measurement or not field:
        return jsonify({"ok": False, "error": "measurement and field required"}), 400

    try:
        if int(cfg.get("influx_version",2)) == 2:
            flux_range = range_to_flux(range_key)
            extra = flux_tag_filter(entity_id, friendly_name)
            with v2_client(cfg) as c:
                q = f'''
data = from(bucket: "{cfg["bucket"]}")
  |> range(start: {flux_range})
  |> filter(fn: (r) => r._measurement == "{measurement}" and r._field == "{field}"{extra})

countT = data |> count() |> map(fn: (r) => ({{ _value: r._value, _field: "count" }}))
minT   = data |> min()   |> map(fn: (r) => ({{ _value: r._value, _time: r._time, _field: "min" }}))
maxT   = data |> max()   |> map(fn: (r) => ({{ _value: r._value, _time: r._time, _field: "max" }}))
firstT = data |> first() |> map(fn: (r) => ({{ _value: r._value, _time: r._time, _field: "first" }}))
lastT  = data |> last()  |> map(fn: (r) => ({{ _value: r._value, _time: r._time, _field: "last" }}))

union(tables: [countT, minT, maxT, firstT, lastT])
'''
                tables = c.query_api().query(q, org=cfg["org"])
                out = {"count": 0, "min": None, "max": None, "oldest_time": None, "newest_time": None}
                for t in tables:
                    for r in t.records:
                        k = r.get_field()
                        if k == "count":
                            out["count"] = int(r.get_value() or 0)
                        elif k == "min":
                            out["min"] = r.get_value()
                        elif k == "max":
                            out["max"] = r.get_value()
                        elif k == "first":
                            ts = r.get_time()
                            out["oldest_time"] = ts.astimezone(timezone.utc).isoformat() if isinstance(ts, datetime) else ts
                        elif k == "last":
                            ts = r.get_time()
                            out["newest_time"] = ts.astimezone(timezone.utc).isoformat() if isinstance(ts, datetime) else ts
                return jsonify({"ok": True, "stats": out})
        else:
            dur = range_to_influxql(range_key)
            c = v1_client(cfg)
            tag_where = influxql_tag_filter(entity_id, friendly_name)
            q = f'SELECT COUNT("{field}") as count, MIN("{field}") as min, MAX("{field}") as max FROM "{measurement}" WHERE time > now() - {dur}{tag_where}'
            res = c.query(q)
            out = {"count": 0, "min": None, "max": None, "oldest_time": None, "newest_time": None}
            for _, points in res.items():
                if points:
                    p = points[0]
                    out["count"] = int(p.get("count") or 0)
                    out["min"] = p.get("min")
                    out["max"] = p.get("max")
            q_old = f'SELECT FIRST("{field}") FROM "{measurement}" WHERE time > now() - {dur}{tag_where}'
            q_new = f'SELECT LAST("{field}") FROM "{measurement}" WHERE time > now() - {dur}{tag_where}'
            ro = c.query(q_old)
            rn = c.query(q_new)
            for _, pts in ro.items():
                if pts:
                    out["oldest_time"] = pts[0].get("time")
                    break
            for _, pts in rn.items():
                if pts:
                    out["newest_time"] = pts[0].get("time")
                    break
            return jsonify({"ok": True, "stats": out})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/delete")
def delete():
    cfg = load_cfg()
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

    start, stop = parse_range_to_datetimes(range_key)

    try:
        if int(cfg.get("influx_version",2)) == 2:
            predicate = f'_measurement="{measurement}"'
            if field:
                predicate += f' AND _field="{field}"'
            if entity_id:
                predicate += f' AND entity_id="{entity_id}"'
            if friendly_name:
                predicate += f' AND friendly_name="{friendly_name}"'
            with v2_client(cfg) as c:
                c.delete_api().delete(start=start, stop=stop, predicate=predicate, bucket=cfg["bucket"], org=cfg["org"])
            return jsonify({"ok": True, "message": f"Deleted v2: {predicate} in {cfg['bucket']} from {start.isoformat()} to {stop.isoformat()}"})
        else:
            dur = range_to_influxql(range_key)
            c = v1_client(cfg)
            tag_where = influxql_tag_filter(entity_id, friendly_name)
            q = f'DELETE FROM "{measurement}" WHERE time > now() - {dur}{tag_where}'
            c.query(q)
            return jsonify({"ok": True, "message": f"Deleted v1: measurement={measurement}, last {dur}{' with tag filters' if tag_where else ''}."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

ADDON_VERSION = os.environ.get("ADDON_VERSION", "dev")

@app.get("/api/info")
def api_info():
    return jsonify({"ok": True, "version": ADDON_VERSION})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
