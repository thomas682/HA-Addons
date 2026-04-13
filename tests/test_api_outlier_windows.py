from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_outlier_windows_returns_exact_counts_and_bounds(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    cfg = app_mod.load_cfg()
    cfg.update({"influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    app_mod.save_cfg(cfg)

    base = datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc)
    points = [base + timedelta(minutes=idx) for idx in range(5)]

    class FakeRec:
        def __init__(self, ts):
            self.ts = ts

        def get_time(self):
            return self.ts

        def get_value(self):
            return 1.0

    class FakeQueryApi:
        def query_stream(self, query, org=None):
            for ts in points:
                yield FakeRec(ts)

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def query_api(self):
            return FakeQueryApi()

    monkeypatch.setattr(app_mod, "v2_client", lambda cfg: FakeClient())

    r = client.post(
        "/api/outlier_windows",
        json={
            "measurement": "state",
            "field": "value",
            "entity_id": "sensor.demo",
            "start": "2026-04-13T08:00:00Z",
            "stop": "2026-04-13T08:10:00Z",
            "n": 2,
            "outliers": [
                {
                    "time": "2026-04-13T08:01:00.000Z",
                    "point_index": 1,
                }
            ],
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert len(j["windows"]) == 1
    assert j["windows"][0] == {
        "time": "2026-04-13T08:01:00.000Z",
        "point_index": 1,
        "center_minutes": 2.0,
        "before_minutes": 1.0,
        "after_minutes": 2.0,
        "before_count": 1,
        "after_count": 2,
        "before_time": "2026-04-13T08:00:00.000Z",
        "after_time": "2026-04-13T08:03:00.000Z",
    }
