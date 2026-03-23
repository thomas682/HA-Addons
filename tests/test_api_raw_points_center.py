from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace


def test_raw_points_center_minutes_meta_for_v2(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    cfg = app_mod.load_cfg()
    cfg.update({"influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    app_mod.save_cfg(cfg)

    center = datetime(2026, 3, 23, 10, 0, tzinfo=timezone.utc)
    rows = [
        SimpleNamespace(get_time=lambda: center - timedelta(minutes=5), get_value=lambda: 1.0),
        SimpleNamespace(get_time=lambda: center, get_value=lambda: 2.0),
        SimpleNamespace(get_time=lambda: center + timedelta(minutes=5), get_value=lambda: 3.0),
    ]
    query_api = SimpleNamespace(query=lambda q, org=None: [SimpleNamespace(records=rows)])

    class DummyClient:
        def __enter__(self):
            return SimpleNamespace(query_api=lambda: query_api)

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(app_mod, "v2_client", lambda *args, **kwargs: DummyClient())

    r = client.post(
        "/api/raw_points",
        json={
            "measurement": "state",
            "field": "value",
            "entity_id": "sensor.demo",
            "start": "2026-03-23T09:00:00Z",
            "stop": "2026-03-23T11:00:00Z",
            "mode": "center",
            "anchor_time": "2026-03-23T10:00:00Z",
            "center_minutes": 15,
            "include_total": False,
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["meta"]["center_minutes"] == 15
    assert j["meta"]["mode"] == "center"
    assert j["meta"]["has_more_before"] is True
    assert j["meta"]["has_more_after"] is True
