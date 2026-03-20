from __future__ import annotations

from io import BytesIO
from contextlib import contextmanager
from pathlib import Path


def test_dashboard_selection_labels_and_order():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert "<div style=\"font-weight:800;\">Quelle</div>" in body
    assert "<label class=\"ib_sel_label\">_measurement</label>" in body
    assert "<label class=\"ib_sel_label\">_field</label>" in body
    assert "<span>friendly_name</span>" in body
    assert "<span>entity_id</span>" in body
    assert 'id="measurement"' not in body
    assert "Zeitraum (Graph/Tabelle)" in body


def test_dashboard_selector_sync_is_no_longer_time_filtered():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'data-ui="filter_measurement_input"' in body
    assert 'data-ui="filter_friendly_input"' in body
    assert 'data-ui="filter_field_select"' in body
    assert 'data-ui="filter_entity_input"' in body
    assert 'id="measurement_filter" list="measurement_filter_list" placeholder="optional" data-ui="filter_measurement_input" autocomplete="off"' in body
    assert 'id="field" list="field_list" placeholder="optional" data-ui="filter_field_select" title="filter_field_select" autocomplete="off"' in body
    assert 'id="friendly_name" list="friendly_list" placeholder="optional" data-ui="filter_friendly_input" autocomplete="off"' in body
    assert 'id="entity_id" list="entity_list" placeholder="optional" data-ui="filter_entity_input" autocomplete="off"' in body
    assert 'measurement_filter: s.measurement || null,' in body
    assert 'async function refreshDashboardSuggestions(opts)' in body
    assert 'async function loadDashboardFields(measurement, opts)' in body
    assert 'async function resolveDashboardSource()' in body
    assert 'const $m = $mf;' in body
    assert 'async function dashboardLoadTagValues(tag, params)' in body
    assert "const common = { range: '24h' };" in body
    assert "const common = { range: '24h' };" in body
    assert 'ALL_ENTITY = await dashboardLoadTagValues(\'entity_id\'' in body
    assert 'syncSelectionFilters(' not in body
    assert 'const _debRefreshDashboardSrc = debounce' in body
    assert 'const _debAutoResolveDashboardSrc = debounce' in body
    assert 'async function triggerDashboardMeasurementRefresh()' in body
    assert 'async function triggerDashboardTagRefresh()' in body
    assert '$mf.addEventListener("input", ()=>{' in body
    assert '$mf.addEventListener("change", ()=>{' in body
    assert '$mf.addEventListener("blur", ()=>{ triggerDashboardMeasurementRefresh().catch(()=>{}); });' in body
    assert '$n.addEventListener("change", ()=>{' in body
    assert '$n.addEventListener("blur", ()=>{ triggerDashboardTagRefresh().catch(()=>{}); });' in body
    assert '$e.addEventListener("change", ()=>{' in body
    assert '$e.addEventListener("blur", ()=>{ triggerDashboardTagRefresh().catch(()=>{}); });' in body
    assert "function logSelectorLoad(name, items, filters)" in body
    assert "function logSelectorAction(name, value)" in body
    assert 'if(tf && tf.range) q.push("range=" + encodeURIComponent(tf.range));' not in body
    assert 'if(tf && tf.range) qs.set("range", String(tf.range || ""));' not in body


def test_dashboard_has_resolved_selection_info_box():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'id="selection_info"' in body
    assert 'data-ui="dashboard.selection"' in body
    assert 'function refreshSelectionInfo()' in body
    assert 'Quelle (aufgeloest)' in body
    assert 'role: source' in body
    assert 'measurement_filter: ${measurementFilter || \'-\'}' in body
    assert 'friendly_name: ${friendly || \'-\'}' in body
    assert 'entity_id: ${entity || \'-\'}' in body


def test_import_ui_has_transform_preview_controls():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "import.html").read_text()
    assert 'id="preview_transform"' in body
    assert 'id="transform_status"' in body
    assert 'id="transform_preview"' in body
    assert "./api/import_preview_transform" in body


def test_config_ui_has_import_transform_settings():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'id="import_measurement_transforms"' in body
    assert 'import_measurement_transforms' in body


def test_logs_follow_uses_restored_checkbox_state():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "logs.html").read_text()
    assert 'setFollow(!!($follow && $follow.checked));' in body


def test_download_and_export_buttons_use_updated_icons():
    export_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "export.html").read_text()
    topbar_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'button id="run" data-ui="export.run"' in export_body
    assert 'button id="export_save" type="button" data-ui="export.save"' in export_body
    assert 'button id="ib_error_git" type="button" data-ui="errors.git_bugreport"' in topbar_body


def test_global_filter_clear_buttons_are_available():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'window.InfluxBroFieldClear' in body
    assert 'function eligible(el)' in body
    assert 'Feld leeren' in body
    assert 'ib_clear_row' in body


def test_export_field_loader_no_longer_forces_value_without_available_field():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "export.html").read_text()
    assert "addOpt('value');" not in body
    assert "if(preferred && xs.includes(preferred)) $f.value = preferred;" in body
    assert "else if(xs.includes('value')) $f.value = 'value';" in body
    assert "if(!measurement && !friendly && !entity){ $f.value = ''; return; }" in body
    assert "if(entity) q.push('entity_id=' + encodeURIComponent(entity));" in body
    assert "if(friendly) q.push('friendly_name=' + encodeURIComponent(friendly));" in body


def test_export_uses_browser_directory_or_save_as_flow():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "export.html").read_text()
    assert "window.showDirectoryPicker" in body
    assert "SAVE_DIR_HANDLE" in body
    assert "_writeDirectoryFile" in body
    assert "const chosenTarget = await showTargetModal();" in body
    assert "target_dir: targetDirValue," in body
    assert 'id="target_entries"' in body
    assert 'id="target_pick_root"' in body
    assert 'CLIENT_TARGET_HANDLE = await CLIENT_TARGET_HANDLE.getDirectoryHandle(name, { create: false });' in body


def test_export_queries_are_no_longer_point_limited():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert "|> limit(n: {max_points})" not in body[body.index('@app.post("/api/export")'):body.index('@app.get("/api/export_job/status")')]


def test_selector_debug_logging_is_present_in_backend():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert 'def _log_selector_debug(kind: str, payload: dict[str, Any]) -> None:' in body
    assert '_log_selector_debug("measurements"' in body
    assert '_log_selector_debug("fields"' in body
    assert '_log_selector_debug("tag_values"' in body
    assert '_log_selector_debug("resolve_signal"' in body


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


def test_measurements_selector_filters_default_to_all_time(load_app_module, tmp_path, monkeypatch):
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

    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {
        **cfg,
        "influx_version": 2,
        "token": "t",
        "org": "o",
        "bucket": "b",
    })
    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    client = app_mod.app.test_client()
    r = client.get("/api/measurements?friendly_name=X")
    assert r.status_code == 200
    q = captured["q"]
    assert isinstance(q, str)
    assert '1970-01-01T00:00:00Z' in q
    assert "-24h" not in q


def test_fields_endpoint_uses_direct_query_for_unicode_measurement(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    captured: dict[str, object] = {"q": None}

    class _FakeRecord:
        def __init__(self, value: str):
            self._value = value

        def get_value(self):
            return self._value

    class _FakeTable:
        def __init__(self, records):
            self.records = records

    class _FakeQueryAPI:
        def query(self, q: str, org: str | None = None):
            captured["q"] = q
            return [_FakeTable([_FakeRecord("value")])]

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
    r = client.get("/api/fields?measurement=%C2%B0F")
    assert r.status_code == 200
    assert r.get_json()["fields"] == ["value"]
    q = captured["q"]
    assert isinstance(q, str)
    assert 'r._measurement == "\u00b0F"' in q
    assert "schema.measurementFieldKeys" not in q


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


def test_resolve_signal_defaults_to_all_time_without_explicit_range(load_app_module, tmp_path, monkeypatch):
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
            return [_FakeTable([_FakeRecord("kWh", "value")])]

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
    r = client.post("/api/resolve_signal", json={"friendly_name": "X"})
    assert r.status_code == 200
    q = captured["q"]
    assert isinstance(q, str)
    assert '1970-01-01T00:00:00Z' in q
    assert "-24h" not in q


def test_import_analyze_returns_source_fields_and_samples(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    payload = (
        b"time;value;entity_id;friendly_name;_measurement;_field\n"
        b"07.01.2025 13:50:21.524;1000;sensor.energy;Energy;kWh;value\n"
        b"07.01.2025 13:55:21.524;1100;sensor.energy;Energy;kWh;value\n"
        b"07.01.2025 14:00:21.524;1200;sensor.energy;Energy;kWh;value\n"
    )
    r = client.post(
        "/api/import_analyze",
        data={"file": (BytesIO(payload), "import.csv"), "delimiter": ";", "tz_name": "Europe/Berlin"},
        content_type="multipart/form-data",
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 3
    assert j["source_measurements"] == ["kWh"]
    assert j["source_fields"] == ["value"]
    assert len(j["sample"]) == 3


def test_import_preview_transform_uses_configured_measurement_factor(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    cfg = app_mod.load_cfg()
    cfg["import_measurement_transforms"] = "Wh;kWh;0.001"
    app_mod.save_cfg(cfg)
    client = app_mod.app.test_client()

    payload = (
        b"time;value;entity_id;friendly_name;_measurement;_field\n"
        b"07.01.2025 13:50:21.524;1000;sensor.energy;Energy;Wh;value\n"
    )
    ra = client.post(
        "/api/import_analyze",
        data={"file": (BytesIO(payload), "import.csv"), "delimiter": ";", "tz_name": "Europe/Berlin"},
        content_type="multipart/form-data",
    )
    file_id = ra.get_json()["file_id"]
    rp = client.post(
        "/api/import_preview_transform",
        json={
            "file_id": file_id,
            "delimiter": ";",
            "measurement": "kWh",
            "field": "value",
            "entity_id": "sensor.energy_total",
            "friendly_name": "Energy total",
            "tz_name": "Europe/Berlin",
        },
    )
    assert rp.status_code == 200
    j = rp.get_json()
    assert j["compatible"] is True
    assert j["checks"]["measurement"]["status"] == "transform"
    assert j["preview_rows"][0]["value"] == 1.0
    assert j["preview_rows"][0]["entity_id"] == "sensor.energy_total"


def test_import_start_applies_measurement_transform_factor(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    cfg = app_mod.load_cfg()
    cfg.update({
        "token": "t",
        "org": "o",
        "bucket": "b",
        "import_measurement_transforms": "Wh;kWh;0.001",
    })
    app_mod.save_cfg(cfg)

    written = []

    class _FakeDeleteApi:
        def delete(self, **kwargs):
            return None

    class _FakeWriteApi:
        def write(self, bucket=None, org=None, record=None, write_precision=None):
            written.extend(record or [])

    class _FakeClient:
        def delete_api(self):
            return _FakeDeleteApi()

        def write_api(self, write_options=None):
            return _FakeWriteApi()

        def close(self):
            return None

    @contextmanager
    def _fake_v2_client(cfg: dict):
        yield _FakeClient()

    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    client = app_mod.app.test_client()
    payload = (
        b"time;value;entity_id;friendly_name;_measurement;_field\n"
        b"07.01.2025 13:50:21.524;1000;sensor.energy;Energy;Wh;value\n"
    )
    ra = client.post(
        "/api/import_analyze",
        data={"file": (BytesIO(payload), "import.csv"), "delimiter": ";", "tz_name": "Europe/Berlin"},
        content_type="multipart/form-data",
    )
    file_id = ra.get_json()["file_id"]
    rs = client.post(
        "/api/import_start",
        json={
            "file_id": file_id,
            "delimiter": ";",
            "measurement": "kWh",
            "field": "value",
            "entity_id": "sensor.energy_total",
            "friendly_name": "Energy total",
            "backup_before": False,
            "delete_first": False,
            "tz_name": "Europe/Berlin",
        },
    )
    assert rs.status_code == 200
    assert rs.get_json()["imported"] == 1
    assert len(written) == 1
    lp = written[0].to_line_protocol()
    assert "kWh" in lp
    assert "value=1" in lp


def test_api_jobs_includes_recent_history(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    app_mod._jobs_history_upsert({
        "id": "job-1",
        "type": "export",
        "state": "done",
        "message": "fertig",
        "started_at": "2026-03-20T10:00:00Z",
        "updated_at": "2026-03-20T10:05:00Z",
        "finished_at": "2026-03-20T10:05:00Z",
    })

    client = app_mod.app.test_client()
    r = client.get("/api/jobs?limit=20")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert any(str(x.get("id") or "") == "job-1" for x in j.get("jobs", []))


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
