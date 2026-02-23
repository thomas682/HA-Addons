import importlib.util
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def load_app_module(tmp_path, monkeypatch):
    """Load influxbro/app/app.py as a fresh module with isolated /config and /data."""

    repo_root = Path(__file__).resolve().parents[1]
    app_py = repo_root / "influxbro" / "app" / "app.py"

    def _load(*, config_dir: Path | None = None, data_dir: Path | None = None):
        cfg = config_dir or (tmp_path / "config")
        dat = data_dir or (tmp_path / "data")
        cfg.mkdir(parents=True, exist_ok=True)
        dat.mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("CONFIG_DIR", str(cfg))
        monkeypatch.setenv("DATA_DIR", str(dat))

        name = f"influxbro_app_{uuid.uuid4().hex}"
        spec = importlib.util.spec_from_file_location(name, app_py)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    return _load
