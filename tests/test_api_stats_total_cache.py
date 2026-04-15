from datetime import datetime, timezone


def test_api_stats_total_uses_incremental_cache(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    cfg = app_mod.load_cfg()
    cfg.update({"influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    app_mod.save_cfg(cfg)

    calls = []

    def fake_compute(cfg, measurement, field, entity_id, friendly_name, start_dt, stop_dt):
        # record whether this is a full compute (start_dt None) or delta compute
        calls.append({"start_dt": start_dt, "measurement": measurement, "field": field, "entity_id": entity_id})
        if start_dt is None:
            return {
                "count": 10,
                "oldest_time": "2020-01-01T00:00:00.000Z",
                "newest_time": "2020-01-02T00:00:00.000Z",
                "first_value": 1.0,
                "last_value": 2.0,
                "min": 1.0,
                "max": 2.0,
                "mean": 1.5,
                "_sum": 15.0,
            }
        # delta range: pretend no new points
        return {
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

    monkeypatch.setattr(app_mod, "_stats_total_compute_v2", fake_compute)

    r1 = client.post(
        "/api/stats",
        json={
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "stats_scope": "inf",
        },
    )
    j1 = r1.get_json()
    assert r1.status_code == 200
    assert j1["ok"] is True
    assert j1.get("cached") is False

    r2 = client.post(
        "/api/stats",
        json={
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "stats_scope": "inf",
        },
    )
    j2 = r2.get_json()
    assert r2.status_code == 200
    assert j2["ok"] is True
    assert j2.get("cached") is True

    assert len(calls) == 2
    assert calls[0]["start_dt"] is None  # full compute
    assert isinstance(calls[1]["start_dt"], datetime)
    assert calls[1]["start_dt"].tzinfo is timezone.utc

    # Mark dirty and ensure we recompute from scratch.
    app_mod._stats_cache_mark_dirty_series("m", "value", "sensor.demo", None, "test")
    r3 = client.post(
        "/api/stats",
        json={
            "measurement": "m",
            "field": "value",
            "entity_id": "sensor.demo",
            "stats_scope": "inf",
        },
    )
    j3 = r3.get_json()
    assert r3.status_code == 200
    assert j3["ok"] is True
    assert len(calls) == 3
    assert calls[2]["start_dt"] is None
