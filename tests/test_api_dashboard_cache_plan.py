from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def test_cache_plan_reports_exact_cache_and_changes(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    start = datetime(2026, 4, 6, 8, 0, tzinfo=timezone.utc)
    stop = datetime(2026, 4, 6, 10, 0, tzinfo=timezone.utc)
    body = {
        "measurement": "m",
        "field": "value",
        "entity_id": "sensor.demo",
        "friendly_name": "Demo",
        "range": "custom",
        "start": _iso(start),
        "stop": _iso(stop),
        "unit": "W",
        "detail_mode": "dynamic",
        "manual_density_pct": 100,
    }
    key = app_mod._dash_cache_key(app_mod.load_cfg(), body, "m", "value", "custom", "sensor.demo", "Demo", "W", "dynamic", 100, start, stop)
    cache_id = app_mod._dash_cache_id(key)
    payload = {
        "ok": True,
        "rows": [
            {"time": _iso(start), "value": 1.0},
            {"time": _iso(stop), "value": 2.0},
        ],
        "query": "q",
        "meta": {
            "mode": "dynamic",
            "jump_spans": [{"start": _iso(start), "stop": _iso(start + timedelta(minutes=5)), "delta": 12.0}],
            "outlier_count": 1,
            "covered_start": _iso(start),
            "covered_stop": _iso(stop),
            "query_ms_original": 1200,
        },
    }
    app_mod._dash_cache_store(cache_id, key, payload, trigger_page="dashboard")
    meta = app_mod._dash_cache_load_meta(cache_id)
    meta["created_at"] = _iso(start - timedelta(minutes=30))
    meta["updated_at"] = _iso(start - timedelta(minutes=20))
    app_mod._dash_cache_write_meta(meta)
    app_mod._history_append({
        "at": _iso(start + timedelta(minutes=20)),
        "time": _iso(start + timedelta(minutes=10)),
        "action": "overwrite",
        "old_value": 1.0,
        "new_value": 3.0,
        "reason": "manual fix",
        "series": {
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "friendly_name": "Demo",
        },
    })

    r = client.post("/api/cache/plan", json=body)
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["plan"]["has_cache"] is True
    assert j["plan"]["exact"] is True
    assert j["plan"]["cached_outlier_count"] == 1
    assert len(j["plan"]["changes"]) == 1


def test_cache_plan_reports_partial_segments_and_gap(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()
    cfg = app_mod.load_cfg()

    req_start = datetime(2026, 4, 6, 8, 0, tzinfo=timezone.utc)
    req_stop = datetime(2026, 4, 6, 11, 0, tzinfo=timezone.utc)

    segments = [
        (datetime(2026, 4, 6, 8, 0, tzinfo=timezone.utc), datetime(2026, 4, 6, 9, 0, tzinfo=timezone.utc)),
        (datetime(2026, 4, 6, 10, 0, tzinfo=timezone.utc), datetime(2026, 4, 6, 11, 0, tzinfo=timezone.utc)),
    ]
    for idx, (start, stop) in enumerate(segments):
        body = {
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "friendly_name": "Demo",
            "range": "custom",
            "start": _iso(start),
            "stop": _iso(stop),
            "unit": "W",
            "detail_mode": "dynamic",
            "manual_density_pct": 100,
        }
        key = app_mod._dash_cache_key(cfg, body, "m", "value", "custom", "sensor.demo", "Demo", "W", "dynamic", 100, start, stop)
        cache_id = app_mod._dash_cache_id(key)
        payload = {
            "ok": True,
            "rows": [
                {"time": _iso(start), "value": float(idx + 1)},
                {"time": _iso(stop - timedelta(minutes=1)), "value": float(idx + 2)},
            ],
            "query": "q",
            "meta": {
                "mode": "dynamic",
                "jump_spans": [],
                "covered_start": _iso(start),
                "covered_stop": _iso(stop),
                "query_ms_original": 900,
            },
        }
        app_mod._dash_cache_store(cache_id, key, payload, trigger_page="dashboard")

    r = client.post(
        "/api/cache/plan",
        json={
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "friendly_name": "Demo",
            "range": "custom",
            "start": _iso(req_start),
            "stop": _iso(req_stop),
            "unit": "W",
            "detail_mode": "dynamic",
            "manual_density_pct": 100,
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["plan"]["has_cache"] is True
    assert j["plan"]["exact"] is False
    assert len(j["plan"]["segments"]) == 2
    assert len(j["plan"]["gaps"]) == 1


def test_cache_plan_reports_reason_when_no_matching_cache(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    r = client.post(
        "/api/cache/plan",
        json={
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "friendly_name": "Demo",
            "range": "custom",
            "start": _iso(datetime(2026, 4, 6, 8, 0, tzinfo=timezone.utc)),
            "stop": _iso(datetime(2026, 4, 6, 10, 0, tzinfo=timezone.utc)),
            "unit": "W",
            "detail_mode": "dynamic",
            "manual_density_pct": 100,
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["plan"]["has_cache"] is False
    assert j["plan"]["reason"] == "no_matching_cache"


def test_query_reuses_partial_cache_and_merges_gap(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()
    cfg = app_mod.load_cfg()

    start = datetime(2026, 4, 6, 8, 0, tzinfo=timezone.utc)
    mid = datetime(2026, 4, 6, 9, 0, tzinfo=timezone.utc)
    stop = datetime(2026, 4, 6, 10, 0, tzinfo=timezone.utc)
    body_seg = {
        "measurement": "m",
        "field": "value",
        "entity_id": "sensor.demo",
        "friendly_name": "Demo",
        "range": "custom",
        "start": _iso(start),
        "stop": _iso(mid),
        "unit": "W",
        "detail_mode": "dynamic",
        "manual_density_pct": 100,
    }
    key = app_mod._dash_cache_key(cfg, body_seg, "m", "value", "custom", "sensor.demo", "Demo", "W", "dynamic", 100, start, mid)
    cache_id = app_mod._dash_cache_id(key)
    app_mod._dash_cache_store(
        cache_id,
        key,
        {
            "ok": True,
            "rows": [
                {"time": _iso(start), "value": 1.0},
                {"time": _iso(mid - timedelta(minutes=1)), "value": 2.0},
            ],
            "query": "q",
            "meta": {
                "mode": "dynamic",
                "jump_spans": [],
                "covered_start": _iso(start),
                "covered_stop": _iso(mid),
            },
        },
        trigger_page="dashboard",
    )

    def fake_query_payload(*args, **kwargs):
        gap_start = args[9]
        gap_stop = args[10]
        return {
            "ok": True,
            "rows": [
                {"time": _iso(gap_start), "value": 3.0},
                {"time": _iso(gap_stop - timedelta(minutes=1)), "value": 4.0},
            ],
            "query": "gap",
            "meta": {
                "mode": "dynamic",
                "jump_spans": [{"start": _iso(gap_start), "stop": _iso(gap_stop), "delta": 5.0}],
                "covered_start": _iso(gap_start),
                "covered_stop": _iso(gap_stop),
                "total_points": 2,
            },
        }

    app_mod._query_payload = fake_query_payload

    r = client.post(
        "/api/query",
        json={
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "friendly_name": "Demo",
            "range": "custom",
            "start": _iso(start),
            "stop": _iso(stop),
            "unit": "W",
            "detail_mode": "dynamic",
            "manual_density_pct": 100,
            "cache_strategy": "reuse",
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["cached"] is True
    assert j["cache"]["strategy"] == "partial_merge"
    assert len(j["rows"]) == 4
    assert j["cache_plan"]["segments_used"] == 1
    assert j["cache_plan"]["gaps_loaded"] == 1
