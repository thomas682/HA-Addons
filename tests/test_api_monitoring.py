from __future__ import annotations


def _save_monitor(client, *, critical_threshold: int = 2, streak: int = 2):
    r = client.post(
        "/api/monitoring/config",
        json={
            "global": {
                "critical_repeat_threshold": critical_threshold,
                "default_recovery_valid_streak": streak,
            },
            "monitors": [
                {
                    "key": "sensor.temp",
                    "label": "Temp",
                    "min_value": 10,
                    "max_value": 50,
                    "max_rise": 5,
                    "max_fall": 5,
                    "invalid_zero": True,
                    "mode": "pending",
                    "recovery_mode": "range",
                    "recovery_valid_streak": streak,
                    "critical_repeat_threshold": critical_threshold,
                }
            ],
        },
    )
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_monitoring_config_roundtrip(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    _save_monitor(client)
    r = client.get("/api/monitoring/config")
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["config"]["monitors"][0]["key"] == "sensor.temp"


def test_monitoring_fault_phase_and_recovery(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()
    _save_monitor(client, critical_threshold=2, streak=2)

    ok0 = client.post("/api/monitoring/evaluate", json={"key": "sensor.temp", "raw_value": 20}).get_json()
    out1 = client.post("/api/monitoring/evaluate", json={"key": "sensor.temp", "raw_value": 40}).get_json()
    out2 = client.post("/api/monitoring/evaluate", json={"key": "sensor.temp", "raw_value": 41}).get_json()
    rec1 = client.post("/api/monitoring/evaluate", json={"key": "sensor.temp", "raw_value": 22}).get_json()
    rec2 = client.post("/api/monitoring/evaluate", json={"key": "sensor.temp", "raw_value": 21}).get_json()

    assert ok0["result"]["status"] == "normal"
    assert out1["result"]["outlier"] is True
    assert out1["result"]["status"] == "fault_active"
    assert out2["result"]["critical"] is True
    assert rec1["result"]["status"] == "recovering"
    assert rec1["result"]["outlier"] is True
    assert rec2["result"]["recovered"] is True
    assert rec2["result"]["status"] == "normal"


def test_monitoring_pending_apply_and_templates(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()
    _save_monitor(client, critical_threshold=1, streak=1)

    client.post("/api/monitoring/evaluate", json={"key": "sensor.temp", "raw_value": 20})
    client.post("/api/monitoring/evaluate", json={"key": "sensor.temp", "raw_value": 0})

    pending = client.get("/api/monitoring/pending").get_json()
    assert pending["total"] == 1
    pending_id = pending["rows"][0]["id"]

    applied = client.post("/api/monitoring/pending/apply", json={"id": pending_id, "manual_value": 19}).get_json()
    assert applied["ok"] is True
    assert applied["row"]["status"] == "applied"

    templates = client.get("/api/monitoring/templates").get_json()
    assert templates["ok"] is True
    assert templates["global"]["pending_count"] == 0
    assert templates["global"]["critical_count"] == 1
    assert templates["items"][0]["corrected_value"] == 19.0
