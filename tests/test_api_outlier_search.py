from __future__ import annotations

from datetime import datetime, timezone


def test_outlier_search_keeps_millisecond_precision(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    cfg = app_mod.load_cfg()
    cfg.update({
        "influx_version": 2,
        "token": "t",
        "org": "o",
        "bucket": "b",
    })
    app_mod.load_cfg = lambda: dict(cfg)

    ts = datetime(2026, 4, 6, 8, 0, 0, 123000, tzinfo=timezone.utc)

    class FakeRec:
        def get_time(self):
            return ts

        def get_value(self):
            return 0.0

    class FakeQueryApi:
        def query_stream(self, query, org=None):
            yield FakeRec()

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def query_api(self):
            return FakeQueryApi()

    app_mod.v2_client = lambda cfg: FakeClient()

    r = client.post(
        "/api/outlier_search",
        json={
            "measurement": "m",
            "field": "value",
            "range": "custom",
            "start": "2026-04-06T08:00:00.000Z",
            "stop": "2026-04-06T09:00:00.000Z",
            "search_types": ["zero"],
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["rows"][0]["time"].endswith(".123Z")
