from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path


def _write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def test_find_influx_yaml_prefers_homeassistant_path(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    _write(cfg_root / "homeassistant" / "influx.yaml", "influxdb: {}\n")
    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)

    client = app_mod.app.test_client()
    r = client.get("/api/find_influx_yaml")
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["path"] == "homeassistant/influx.yaml"
    assert j["resolved"].endswith("/config/homeassistant/influx.yaml")


def test_load_influx_yaml_resolves_secret(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    _write(
        cfg_root / "homeassistant" / "secrets.yaml",
        "influx_token: abc123\n",
    )
    _write(
        cfg_root / "homeassistant" / "influx.yaml",
        """
influxdb:
  api_version: 2
  host: localhost
  port: 8086
  ssl: false
  organization: myorg
  bucket: mybucket
  token: !secret influx_token
""".lstrip(),
    )

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    r = client.post("/api/load_influx_yaml", json={"influx_yaml_path": "homeassistant/influx.yaml"})
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert j["config"]["influx_version"] == 2
    assert j["config"]["host"] == "localhost"
    assert j["config"]["port"] == 8086
    assert j["config"]["org"] == "myorg"
    assert j["config"]["bucket"] == "mybucket"
    assert j["config"]["token"] == "abc123"


def test_api_test_v2_overlays_from_yaml(load_app_module, tmp_path, monkeypatch):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    _write(cfg_root / "homeassistant" / "secrets.yaml", "influx_token: abc123\n")
    _write(
        cfg_root / "homeassistant" / "influx.yaml",
        """
influxdb:
  api_version: 2
  host: localhost
  port: 8086
  ssl: false
  organization: myorg
  bucket: mybucket
  token: !secret influx_token
""".lstrip(),
    )

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)

    class _FakeQueryAPI:
        def query(self, q: str, org: str | None = None):
            return []

    class _FakeClient:
        def query_api(self):
            return _FakeQueryAPI()

        def close(self):
            return None

    @contextmanager
    def _fake_v2_client(cfg: dict):
        yield _FakeClient()

    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    client = app_mod.app.test_client()
    r = client.post(
        "/api/test",
        json={
            "influx_version": 2,
            "influx_yaml_path": "homeassistant/influx.yaml",
            "scheme": "http",
            "host": "",
            "port": 0,
            "verify_ssl": True,
            "timeout_seconds": 10,
            "org": "",
            "bucket": "",
            "token": "",
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True


def test_api_test_v1_overlays_from_yaml(load_app_module, tmp_path, monkeypatch):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    _write(
        cfg_root / "homeassistant" / "influx.yaml",
        """
influxdb:
  api_version: 1
  host: localhost
  port: 8086
  ssl: false
  database: ha
""".lstrip(),
    )

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)

    class _FakeV1Client:
        def ping(self):
            return True

    def _fake_v1_client(cfg: dict):
        return _FakeV1Client()

    monkeypatch.setattr(app_mod, "v1_client", _fake_v1_client)

    client = app_mod.app.test_client()
    r = client.post(
        "/api/test",
        json={
            "influx_version": 1,
            "influx_yaml_path": "homeassistant/influx.yaml",
            "scheme": "http",
            "host": "",
            "port": 0,
            "verify_ssl": True,
            "timeout_seconds": 10,
            "database": "",
        },
    )
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
