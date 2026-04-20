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

    # /api/outlier_search was removed; outlier scanning is exposed via /api/outliers.
    r = client.post(
        "/api/outliers",
        json={
            "measurement": "m",
            "field": "value",
            "start": "2026-04-06T08:00:00.000Z",
            "stop": "2026-04-06T09:00:00.000Z",
            "search_types": ["zero"],
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["rows"][0]["time"].endswith(".123Z")


def test_outlier_search_treats_large_time_gap_as_gap_not_step(load_app_module, tmp_path):
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
        "outlier_gap_seconds_default": 300,
    })
    app_mod.load_cfg = lambda: dict(cfg)

    times = [
        datetime(2025, 3, 9, 18, 56, 38, 903000, tzinfo=timezone.utc),
        datetime(2025, 3, 16, 13, 39, 35, 0, tzinfo=timezone.utc),
    ]
    vals = [33550027.0, 33784835.0]

    class FakeRec:
        def __init__(self, ts, val):
            self.ts = ts
            self.val = val

        def get_time(self):
            return self.ts

        def get_value(self):
            return self.val

    class FakeQueryApi:
        def query_stream(self, query, org=None):
            for ts, val in zip(times, vals):
                yield FakeRec(ts, val)

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def query_api(self):
            return FakeQueryApi()

    app_mod.v2_client = lambda cfg: FakeClient()

    # /api/outlier_search was removed; outlier scanning is exposed via /api/outliers.
    r = client.post(
        "/api/outliers",
        json={
            "measurement": "Wh",
            "field": "value",
            "start": "2025-03-09T18:56:00Z",
            "stop": "2025-03-16T13:40:00Z",
            "search_types": ["counter", "gap", "fault_phase"],
            "max_step": 30,
            "gap_seconds": 300,
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert len(j["rows"]) == 1
    assert "gap > 300s" in j["rows"][0]["reason"]
    assert "step >" not in j["rows"][0]["reason"]
    assert "fault_active" not in j["rows"][0]["reason"]
    assert "gap" in j["rows"][0]["types"]


def test_outliers_filter_scan_treats_large_gap_as_gap_not_step(load_app_module, tmp_path):
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
        "outlier_gap_seconds_default": 300,
    })
    app_mod.load_cfg = lambda: dict(cfg)

    times = [
        datetime(2025, 3, 9, 18, 56, 38, 903000, tzinfo=timezone.utc),
        datetime(2025, 3, 16, 13, 39, 35, 0, tzinfo=timezone.utc),
    ]
    vals = [33550027.0, 33784835.0]

    class FakeRec:
        def __init__(self, ts, val):
            self.ts = ts
            self.val = val

        def get_time(self):
            return self.ts

        def get_value(self):
            return self.val

    class FakeQueryApi:
        def query_stream(self, query, org=None):
            for ts, val in zip(times, vals):
                yield FakeRec(ts, val)

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def query_api(self):
            return FakeQueryApi()

    app_mod.v2_client = lambda cfg: FakeClient()

    r = client.post(
        "/api/outliers",
        json={
            "measurement": "Wh",
            "field": "value",
            "start": "2025-03-09T18:56:00Z",
            "stop": "2025-03-16T13:40:00Z",
            "counter_enabled": True,
            "counter_decrease": True,
            "counter_max_step": True,
            "fault_phase_enabled": True,
            "include_gap": True,
            "max_step": 30,
            "gap_seconds": 300,
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert len(j["rows"]) == 1
    assert "gap > 300s" in j["rows"][0]["reason"]
    assert "step >" not in j["rows"][0]["reason"]
    assert "fault_active" not in j["rows"][0]["reason"]
