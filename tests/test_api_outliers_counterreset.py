from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace


def _rec(ts: datetime, value):
    return SimpleNamespace(get_time=lambda: ts, get_value=lambda: value)


def test_api_outliers_detects_counterreset_with_prefault_spike(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    cfg = app_mod.load_cfg()
    cfg.update({"influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    app_mod.save_cfg(cfg)

    start = datetime(2026, 4, 23, 9, 0, tzinfo=timezone.utc)
    values = [100.0, 105.0, 4294967295.0, 10.0, 11.0, 12.0]
    stream = [_rec(start + timedelta(minutes=i), v) for i, v in enumerate(values)]

    class DummyClient:
        def __enter__(self):
            return SimpleNamespace(query_api=lambda: SimpleNamespace(query_stream=lambda q, org=None: stream))

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(app_mod, "v2_client", lambda *args, **kwargs: DummyClient())

    r = client.post(
        "/api/outliers",
        json={
            "measurement": "state",
            "field": "value",
            "entity_id": "sensor.counter",
            "start": start.isoformat().replace("+00:00", "Z"),
            "stop": (start + timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
            "search_types": ["counterreset"],
            "max_step": 50,
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True

    rows = j.get("rows") or []
    assert any("counterreset" in (row.get("types") or []) for row in rows)

    begin = [row for row in rows if row.get("counterreset_role") == "reset_begin"]
    assert begin
    assert "counterreset" in (begin[0].get("types") or [])
    assert begin[0].get("counterreset_before_value") == 105.0

    prefault = [row for row in rows if row.get("counterreset_role") == "pre_fault"]
    assert prefault
    assert "counterreset" in (prefault[0].get("types") or [])
    assert str(prefault[0].get("counterreset_begin_time") or "").endswith("Z")
