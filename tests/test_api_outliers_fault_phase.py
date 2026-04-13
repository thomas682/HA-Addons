from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace


def _rec(ts: datetime, value):
    return SimpleNamespace(get_time=lambda: ts, get_value=lambda: value)


def test_api_outliers_fault_phase_persists_across_values(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    cfg = app_mod.load_cfg()
    cfg.update({"influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    app_mod.save_cfg(cfg)

    start = datetime(2026, 3, 24, 8, 0, tzinfo=timezone.utc)
    values = [10.0, 100.0, 101.0, 102.0, 11.0, 10.5]
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
            "entity_id": "sensor.demo",
            "start": start.isoformat().replace("+00:00", "Z"),
            "stop": (start + timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
            "fault_phase_enabled": True,
            "counter_enabled": True,
            "counter_decrease": True,
            "counter_max_step": True,
            "max_step": 5,
            "recovery_valid_streak": 2,
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert len(j["rows"]) >= 3
    assert any("fault_active" in str(row.get("reason") or "") for row in j["rows"])
    assert j["scan_state"]["status"] in ("fault_active", "recovering", "normal")
    assert j["scan_state"]["fault_count"] >= 1


def test_fault_phase_preset_present_in_dashboard_ui():
    from pathlib import Path

    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert '<option value="fault_phase">Stoerphasensuche</option>' in body
    assert 'fault_phase_enabled: preset === "fault_phase"' in body


def test_api_outliers_uses_recovery_valid_streak_override(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    cfg = app_mod.load_cfg()
    cfg.update({"influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    app_mod.save_cfg(cfg)

    start = datetime(2026, 3, 24, 8, 0, tzinfo=timezone.utc)
    values = [10.0, 100.0, 10.0, 10.0]
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
            "entity_id": "sensor.demo",
            "start": start.isoformat().replace("+00:00", "Z"),
            "stop": (start + timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
            "fault_phase_enabled": True,
            "counter_enabled": True,
            "counter_decrease": False,
            "counter_max_step": True,
            "max_step": 5,
            "recovery_valid_streak": 3,
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["scan_state"]["status"] == "recovering"
    assert j["scan_state"]["recovery_streak"] == 2
