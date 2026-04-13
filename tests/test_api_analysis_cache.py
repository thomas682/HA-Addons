from __future__ import annotations

from datetime import datetime, timezone


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def test_analysis_cache_plan_reports_segments_and_dirty_ranges(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()
    cfg = app_mod.load_cfg()

    seg1_start = datetime(2026, 4, 6, 8, 0, tzinfo=timezone.utc)
    seg1_stop = datetime(2026, 4, 6, 9, 0, tzinfo=timezone.utc)
    seg2_start = datetime(2026, 4, 6, 9, 0, tzinfo=timezone.utc)
    seg2_stop = datetime(2026, 4, 6, 10, 0, tzinfo=timezone.utc)

    app_mod._analysis_cache_store_segment(
        cfg,
        "m",
        "value",
        "sensor.demo",
        "Demo",
        _iso(seg1_start),
        _iso(seg1_stop),
        [{"time": _iso(seg1_start), "value": 1.0, "reason": "NULL", "types": ["null"]}],
        5,
    )
    meta2 = app_mod._analysis_cache_store_segment(
        cfg,
        "m",
        "value",
        "sensor.demo",
        "Demo",
        _iso(seg2_start),
        _iso(seg2_stop),
        [],
        8,
    )
    assert meta2 is not None
    meta2["updated_at"] = _iso(datetime(2026, 4, 6, 8, 30, tzinfo=timezone.utc))
    app_mod._analysis_cache_write_meta(meta2)
    app_mod._history_append({
        "at": _iso(datetime(2026, 4, 6, 8, 45, tzinfo=timezone.utc)),
        "time": _iso(datetime(2026, 4, 6, 9, 15, tzinfo=timezone.utc)),
        "action": "overwrite",
        "old_value": 1.0,
        "new_value": 2.0,
        "reason": "manual fix",
        "series": {
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "friendly_name": "Demo",
        },
    })

    r = client.post(
        "/api/analysis_cache/plan",
        json={
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "friendly_name": "Demo",
            "start": _iso(seg1_start),
            "stop": _iso(seg2_stop),
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert len(j["plan"]["segments"]) == 1
    assert len(j["plan"]["dirty_ranges"]) == 1
    assert len(j["plan"]["changes"]) == 1


def test_analysis_cache_combine_merges_contiguous_segments(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()
    cfg = app_mod.load_cfg()

    a = app_mod._analysis_cache_store_segment(
        cfg, "m", "value", "sensor.demo", "Demo",
        "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z",
        [{"time": "2026-01-01T12:00:00Z", "value": 1.0, "reason": "NULL", "types": ["null"]}], 5,
    )
    b = app_mod._analysis_cache_store_segment(
        cfg, "m", "value", "sensor.demo", "Demo",
        "2026-01-02T00:00:00Z", "2026-01-03T00:00:00Z",
        [{"time": "2026-01-02T12:00:00Z", "value": 2.0, "reason": "0", "types": ["zero"]}], 7,
    )
    assert a and b
    r = client.post("/api/analysis_cache/combine", json={"series_key": a["series_key"]})
    j = r.get_json()
    assert r.status_code == 200
    assert j["ok"] is True
    assert j["groups_combined"] == 1
    series = app_mod._analysis_cache_group_list(cfg)
    assert len(series) == 1
    assert series[0]["segment_count"] == 1


def test_analysis_cache_combine_returns_json_error_on_merge_exception(load_app_module, tmp_path, monkeypatch):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()
    cfg = app_mod.load_cfg()

    a = app_mod._analysis_cache_store_segment(
        cfg, "m", "value", "sensor.demo", "Demo",
        "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z",
        [{"time": "2026-01-01T12:00:00Z", "value": 1.0, "reason": "NULL", "types": ["null"]}], 5,
    )
    b = app_mod._analysis_cache_store_segment(
        cfg, "m", "value", "sensor.demo", "Demo",
        "2026-01-02T00:00:00Z", "2026-01-03T00:00:00Z",
        [{"time": "2026-01-02T12:00:00Z", "value": 2.0, "reason": "0", "types": ["zero"]}], 7,
    )
    assert a and b

    def _boom(_cfg, _group):
        raise app_mod._ApiError("combine exploded", 500)

    monkeypatch.setattr(app_mod, "_analysis_cache_merge_group", _boom)

    r = client.post("/api/analysis_cache/combine", json={"series_key": a["series_key"]})
    j = r.get_json()

    assert r.status_code == 500
    assert j == {"ok": False, "error": "combine exploded"}


def test_analysis_cache_store_segment_persists_checkpoints(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    cfg = app_mod.load_cfg()

    meta = app_mod._analysis_cache_store_segment(
        cfg, "m", "value", "sensor.demo", "Demo",
        "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z",
        [{"time": "2026-01-01T12:00:00Z", "value": 1.0, "reason": "NULL", "types": ["null"]}], 5,
        checkpoints=[{
            "at": "2026-01-01T06:00:00.000Z",
            "last_time": "2026-01-01T05:59:00.000Z",
            "last_value": 1.0,
            "counter_base_value": None,
            "scan_state": {"status": "normal"},
        }],
        final_state={"last_time": "2026-01-01T23:59:00.000Z", "last_value": 1.0},
    )
    assert meta is not None

    payload = app_mod._analysis_cache_load_payload(str(meta["id"]))

    assert payload is not None
    assert len(payload["checkpoints"]) == 1
    assert payload["checkpoints"][0]["at"] == "2026-01-01T06:00:00.000Z"
    assert payload["final_state"]["last_time"] == "2026-01-01T23:59:00.000Z"


def test_analysis_cache_combine_skips_dirty_segments_without_refetch(load_app_module, tmp_path, monkeypatch):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()
    cfg = app_mod.load_cfg()

    a = app_mod._analysis_cache_store_segment(
        cfg, "m", "value", "sensor.demo", "Demo",
        "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z",
        [{"time": "2026-01-01T12:00:00Z", "value": 1.0, "reason": "NULL", "types": ["null"]}], 5,
    )
    b = app_mod._analysis_cache_store_segment(
        cfg, "m", "value", "sensor.demo", "Demo",
        "2026-01-02T00:00:00Z", "2026-01-03T00:00:00Z",
        [{"time": "2026-01-02T12:00:00Z", "value": 2.0, "reason": "0", "types": ["zero"]}], 7,
    )
    assert a and b

    b["updated_at"] = "2026-01-02T00:30:00Z"
    app_mod._analysis_cache_write_meta(b)
    app_mod._history_append({
        "at": "2026-01-02T01:00:00Z",
        "time": "2026-01-02T12:00:00Z",
        "action": "overwrite",
        "old_value": 2.0,
        "new_value": 3.0,
        "reason": "manual fix",
        "series": {
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "friendly_name": "Demo",
        },
    })

    def _fake_api_outliers():
        raise AssertionError("combine must not refetch dirty segments")

    monkeypatch.setattr(app_mod, "api_outliers", _fake_api_outliers)

    r = client.post("/api/analysis_cache/combine", json={"series_key": a["series_key"]})
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["groups_combined"] == 0
    assert len(j["skipped_dirty_segments"]) == 1
    assert j["note"] == "no clean contiguous segments to combine"

    series = app_mod._analysis_cache_group_list(cfg)
    assert len(series) == 1
    assert series[0]["segment_count"] == 2
