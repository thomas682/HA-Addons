from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_debug_report_respects_configured_log_history_hours(load_app_module, tmp_path, monkeypatch):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"
    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    cfg = app_mod.load_cfg()
    cfg["bugreport_log_history_hours"] = 1
    app_mod.save_cfg(cfg)

    log_file = data_root / "influxbro.log"
    now = datetime.now(timezone.utc)
    old_ts = (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S,000")
    keep_ts = (now - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S,000")
    log_file.write_text(f"{old_ts} INFO old-entry\n{keep_ts} INFO keep-entry\n", encoding="utf-8")
    monkeypatch.setattr(app_mod, "LOG_FILE", log_file)
    monkeypatch.setattr(app_mod, "_supervisor_get", lambda *args, **kwargs: (200, f"{old_ts} old\n{keep_ts} keep\n"))

    r = client.post("/api/debug_report", json={"tail": 2000, "client": {}, "issue": {"function": "Dashboard"}})
    text = r.get_data(as_text=True)

    assert r.status_code == 200
    assert "keep-entry" in text
    assert "old-entry" not in text
    assert "Function: Dashboard" in text
    assert "letzte 1h" in text


def test_debug_report_default_hours_config_present(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    cfg = app_mod.load_cfg()
    assert cfg["bugreport_log_history_hours"] == 1
