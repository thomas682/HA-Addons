from __future__ import annotations

from contextlib import contextmanager


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


def test_measurements_flux_has_real_newline(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")

    captured: dict[str, object] = {"q": None}

    class _FakeQueryAPI:
        def query(self, q: str, org: str | None = None):
            captured["q"] = q
            return []

    class _FakeClient:
        def query_api(self):
            return _FakeQueryAPI()

        def close(self):
            return None

    @contextmanager
    def _fake_v2_client(cfg: dict):
        yield _FakeClient()

    # Ensure endpoint takes v2 path.
    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {
        **cfg,
        "influx_version": 2,
        "token": "t",
        "org": "o",
        "bucket": "b",
    })
    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    client = app_mod.app.test_client()
    r = client.get("/api/measurements")
    assert r.status_code == 200
    q = captured["q"]
    assert isinstance(q, str)
    assert "\\n" not in q
    assert "\n" in q


def test_resolve_signal_does_not_require_value_column(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    captured: dict[str, object] = {"q": None}

    class _FakeRecord:
        def __init__(self, m: str, f: str):
            self.values = {"_measurement": m, "_field": f}

    class _FakeTable:
        def __init__(self, records):
            self.records = records

    class _FakeQueryAPI:
        def query(self, q: str, org: str | None = None):
            captured["q"] = q
            return [_FakeTable([_FakeRecord("state", "value")])]

    class _FakeClient:
        def query_api(self):
            return _FakeQueryAPI()

        def close(self):
            return None

    @contextmanager
    def _fake_v2_client(cfg: dict):
        yield _FakeClient()

    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {
        **cfg,
        "influx_version": 2,
        "token": "t",
        "org": "o",
        "bucket": "b",
    })
    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    client = app_mod.app.test_client()
    r = client.post(
        "/api/resolve_signal",
        json={"friendly_name": "X", "range": "24h", "measurement_filter": "W"},
    )
    j = r.get_json()
    assert r.status_code == 200
    assert j["ok"] is True
    q = captured["q"]
    assert isinstance(q, str)
    assert "first()" not in q


def test_stats_v2_flux_avoids_time_label_literal(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    captured: list[str] = []

    class _FakeQueryAPI:
        def query(self, q: str, org: str | None = None):
            captured.append(q)
            return []

    class _FakeClient:
        def query_api(self):
            return _FakeQueryAPI()

        def close(self):
            return None

    @contextmanager
    def _fake_v2_client(cfg: dict):
        yield _FakeClient()

    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {
        **cfg,
        "influx_version": 2,
        "token": "t",
        "org": "o",
        "bucket": "b",
    })
    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    client = app_mod.app.test_client()
    r = client.post(
        "/api/stats",
        json={
            "measurement": "state",
            "field": "value",
            "range": "24h",
            "friendly_name": "X",
            "entity_id": "Y",
            "stats_scope": "current",
        },
    )
    j = r.get_json()
    assert r.status_code == 200
    assert j["ok"] is True
    assert captured
    q = "\n".join(captured)
    assert "_time:" not in q
    assert "union(" not in q
