from __future__ import annotations


def test_stats_scope_ignores_partial_start_stop(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    # For non-current scopes, start/stop should be ignored (no validation error).
    r = client.post(
        "/api/stats",
        json={
            "measurement": "state",
            "field": "value",
            "stats_scope": "1y",
            "start": "2026-01-01T00:00:00Z",
        },
    )
    j = r.get_json()
    assert r.status_code in (400, 500)
    assert j["ok"] is False
    assert "invalid start/stop" not in (j.get("error") or "")


def test_stats_current_rejects_partial_start_stop(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    r = client.post(
        "/api/stats",
        json={
            "measurement": "state",
            "field": "value",
            "stats_scope": "current",
            "start": "2026-01-01T00:00:00Z",
        },
    )
    j = r.get_json()
    assert r.status_code == 400
    assert j["ok"] is False
    assert "invalid start/stop" in (j.get("error") or "")


def test_query_rejects_partial_start_stop(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    r = client.post(
        "/api/query",
        json={
            "measurement": "state",
            "field": "value",
            "start": "2026-01-01T00:00:00Z",
        },
    )
    j = r.get_json()
    assert r.status_code == 400
    assert j["ok"] is False
    assert "invalid start/stop" in (j.get("error") or "")
