def test_resolve_signal_bounds_all_time_range(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    cfg = app_mod.load_cfg()
    cfg.update({"influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    app_mod.save_cfg(cfg)

    seen = {"q": None}

    class _FakeQueryApi:
        def query(self, q, org=None):
            seen["q"] = str(q)
            return []

    class _FakeClient:
        def query_api(self):
            return _FakeQueryApi()

    class _FakeCtx:
        def __enter__(self):
            return _FakeClient()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(app_mod, "v2_client", lambda _cfg: _FakeCtx())

    r = client.post(
        "/api/resolve_signal",
        json={
            "entity_id": "sensor.demo",
            "measurement_filter": "Wh",
            "range": "all",
        },
    )

    # No combos returned by fake client => 404, but we still validated the generated query.
    assert r.status_code == 404
    q = seen["q"] or ""
    assert "range(start: -30d" in q
