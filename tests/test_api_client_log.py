from __future__ import annotations


def test_client_log_endpoint_exists(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    r = client.post(
        "/api/client_log",
        json={
            "message": "analysis_debug step=fetch_start",
            "extra": {"kind": "analysis_debug", "step": "fetch_start"},
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
