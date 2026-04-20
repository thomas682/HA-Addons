from __future__ import annotations


def test_analysis_history_event_endpoint_and_fetch(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    r1 = client.post(
        "/api/analysis_history_event",
        json={
            "kind": "analysis",
            "step": "validate",
            "page": "dashboard",
            "measurement": "m",
            "field": "value",
            "detail": "validate ok",
            "trace_id": "t-123",
            "dur_ms": 42,
        },
    )
    j1 = r1.get_json()
    assert r1.status_code == 200
    assert j1["ok"] is True

    r2 = client.post(
        "/api/analysis_history_event",
        json={
            "kind": "analysis_summary",
            "step": "summary",
            "summary": {"status": "ok", "measurement": "m", "field": "value"},
        },
    )
    j2 = r2.get_json()
    assert r2.status_code == 200
    assert j2["ok"] is True

    r3 = client.get("/api/analysis_history?limit=10")
    j3 = r3.get_json()
    assert r3.status_code == 200
    assert j3["ok"] is True
    assert len(j3["rows"]) >= 2
    assert any(str(row.get("kind")) == "analysis" for row in j3["rows"])
    assert any(str(row.get("kind")) == "analysis_summary" for row in j3["rows"])

    # trace_id + dur_ms must be stored as top-level fields.
    row0 = next((row for row in j3["rows"] if str(row.get("kind")) == "analysis"), None)
    assert row0 is not None
    assert str(row0.get("trace_id")) == "t-123"
    assert int(row0.get("dur_ms") or 0) == 42
