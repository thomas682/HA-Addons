from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_outliers_window_state_resolves_across_chunks(load_app_module, tmp_path):
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

    t0 = datetime(2026, 4, 17, 7, 0, 0, tzinfo=timezone.utc)
    times = [t0 + timedelta(minutes=i) for i in range(0, 5)]
    vals = [1.0, 0.0, 1.0, 1.0, 1.0]  # outlier at index 1 (0.0)

    class FakeRec:
        def __init__(self, ts, val):
            self.ts = ts
            self.val = val

        def get_time(self):
            return self.ts

        def get_value(self):
            return self.val

    request_no = {"i": 0}

    def _fake_client_for_request(idx: int):
        class FakeQueryApi:
            def query_stream(self, query, org=None):
                # First request returns points 0..2, second returns 3..4.
                if idx == 0:
                    start, stop = 0, 3
                else:
                    start, stop = 3, 5
                for ts, val in zip(times[start:stop], vals[start:stop]):
                    yield FakeRec(ts, val)

        class FakeClient:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def query_api(self):
                return FakeQueryApi()

        return FakeClient()

    def fake_v2_client(_cfg):
        idx = request_no["i"]
        request_no["i"] += 1
        return _fake_client_for_request(idx)

    app_mod.v2_client = fake_v2_client

    payload0 = {
        "measurement": "m",
        "field": "value",
        "start": times[0].isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "stop": times[-1].isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "search_types": ["zero"],
        "window_cfg": {"n_before": 1, "n_after": 2, "algo_v": 1},
    }

    r0 = client.post("/api/outliers", json=payload0)
    j0 = r0.get_json()
    assert r0.status_code == 200
    assert j0["ok"] is True
    assert j0["window_state"] is not None

    # Outlier row exists and has a partial window (before known, after not yet).
    out0 = [r for r in j0["rows"] if r.get("value") == 0.0]
    assert len(out0) == 1
    assert out0[0]["window"]["before_time"] is not None
    assert out0[0]["window"]["after_time"] is None

    # Second chunk resolves after_time via window_updates.
    payload1 = dict(payload0)
    payload1["window_state"] = j0["window_state"]
    r1 = client.post("/api/outliers", json=payload1)
    j1 = r1.get_json()
    assert r1.status_code == 200
    assert j1["ok"] is True
    ups = j1.get("window_updates") or []
    assert len(ups) >= 1

    center_iso = times[1].isoformat(timespec="milliseconds").replace("+00:00", "Z")
    after_iso = times[3].isoformat(timespec="milliseconds").replace("+00:00", "Z")
    match = [u for u in ups if u.get("time") == center_iso]
    assert match
    assert match[0]["window"]["after_time"] == after_iso
