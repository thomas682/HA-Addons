from __future__ import annotations

from datetime import datetime
from io import BytesIO
from contextlib import contextmanager
from pathlib import Path


def test_dashboard_selection_labels_and_order():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    # Source selection uses the structured dashboard_selection data-ui scheme.
    assert 'data-ui="dashboard_selection.section_root"' in body
    assert 'data-ui="dashboard_selection.input_measurement_filter"' in body
    assert '<span>Einheit</span>' in body
    assert '<span>Feld</span>' in body
    assert '<span>Name</span>' in body
    assert '<span>Entity</span>' in body
    assert 'id="measurement"' not in body
    assert "Zeitraum (Graph/Tabelle)" in body


def test_stats_selection_uses_combine_source_controls():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "stats.html").read_text()
    assert 'id="src_measurement"' in body
    assert 'id="src_field"' in body
    assert 'id="src_entity_id"' in body
    assert 'id="src_friendly_name"' in body
    assert 'id="measurement_filter" data-ui="stats.measurement_filter"' not in body
    assert 'id="friendly_filter" data-ui="stats.friendly_filter"' not in body
    assert 'id="entity_filter" data-ui="stats.entity_filter"' not in body
    assert 'function src(){' in body
    assert 'async function refreshSuggestions(){' in body


def test_dashboard_selector_sync_is_no_longer_time_filtered():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    # Ensure selector inputs exist and use structured dashboard_selection data-ui tokens.
    assert 'id="measurement_filter"' in body
    assert 'data-ui="dashboard_selection.input_measurement_filter_value"' in body
    assert 'id="field"' in body
    assert 'data-ui="dashboard_selection.input_field_value"' in body
    assert 'id="friendly_name"' in body
    assert 'data-ui="dashboard_selection.input_friendly_name_value"' in body
    assert 'id="entity_id"' in body
    assert 'data-ui="dashboard_selection.input_entity_value"' in body

    # Selector refresh helpers should exist.
    assert 'async function refreshDashboardSuggestions' in body
    assert 'async function loadDashboardFields' in body
    assert 'async function resolveDashboardSource' in body
    assert 'async function dashboardLoadTagValues' in body
    assert 'function logSelectorLoad(name, items, filters)' in body
    assert 'function logSelectorAction(name, value)' in body


def test_dashboard_no_longer_has_resolved_selection_info_box():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'id="selection_info"' not in body
    assert 'data-ui="dashboard.selection"' not in body
    assert 'Quelle (aufgeloest)' not in body
    assert 'function refreshSelectionInfo()' not in body


def test_dashboard_actions_are_below_filters_and_reason_filter_has_data_ui():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    # Dashboard main actions live in the Caching section toolbar.
    assert 'data-ui="dashboard_caching.row_actions"' in body
    assert 'id="load"' in body
    # Reason filter is part of the dashboard graph controls.
    assert "dashboard_graph.select_grund_filter" in body
    assert '<span class="section_title" style="margin:0;">Gesamtstatistik (Alles)</span>' not in body
    assert 'Tipps: Messwert = <code>friendly_name</code>' not in body


def test_dashboard_sections_are_direct_children_of_dashboard_page():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert '<div class="main">' not in body
    # Core dashboard sections.
    assert '<details id="selection_details"' in body
    assert '<details id="caching_section"' in body
    assert '<details id="analysis_section"' in body
    assert '<details id="outlier_section"' in body
    assert '<details id="raw_section"' in body
    # The legacy filter list section is no longer present.
    assert 'id="filterlist_section"' not in body


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


def test_import_selection_uses_combine_source_controls():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "import.html").read_text()
    assert 'id="src_measurement"' in body
    assert 'id="src_field"' in body
    assert 'id="src_entity_id"' in body
    assert 'id="src_friendly_name"' in body
    assert 'id="measurement_filter"' not in body
    assert 'id="measurement" data-ui="import.measurement"' not in body
    assert 'id="field" data-ui="import.field"' not in body
    assert 'function src(){' in body
    assert 'async function refreshSuggestions(){' in body


def test_logs_follow_uses_restored_checkbox_state():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "logs.html").read_text()
    assert 'setFollow(!!($follow && $follow.checked));' in body


def test_download_and_export_buttons_use_updated_icons():
    export_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "export.html").read_text()
    topbar_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'button id="run" data-ui="export_main.btn_run" title="export.run"' in export_body
    assert 'button id="export_save" type="button" data-ui="export_main.btn_save" title="export.save"' in export_body
    assert 'button id="ib_error_git" type="button" data-ui="errors_main.btn_git_bugreport" title="errors.git_bugreport"' in topbar_body


def test_topbar_has_ui_picker_button_and_hover_inspector():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'id="ui_picker_toggle"' in body
    assert 'id="ib_pagecard"' in body
    assert 'id="ib_page_search"' in body
    assert 'data-ui="topbar_main.panel_profile"' in body
    assert 'data-ui="topbar_main.panel_zoom"' in body
    assert 'title="nav.donate"' in body
    assert 'id="ib_open_all"' in body
    assert 'id="ib_close_all"' in body
    assert 'id="ib_page_search_clear"' not in body
    assert '#ui_profile_sel { width: 80px; min-width: 80px; max-width: 80px;' in body
    assert 'class="iconbtn" type="button" data-ui="sections_main.btn_open_all" title="sections.open_all"' in body
    assert 'class="iconbtn" type="button" data-ui="sections_main.btn_close_all" title="sections.close_all"' in body
    assert 'function initZoom(){' in body
    assert "$m.dataset.ibZoomReady = '1';" in body
    assert "$p.dataset.ibZoomReady = '1';" in body
    assert "function initPageCard(){" in body
    assert "$card.dataset.ibPagecardReady = '1';" in body
    assert 'class="meta hintline" id="ui_profile_hint"' in body
    assert 'class="branddonate" data-ui="nav_main.panel_donate"' in body
    assert "function pickTarget(el, ev)" in body
    assert "function currentPageLabel()" in body
    assert "function initPicker(){" in body
    assert "$btn.dataset.ibPickerReady = '1';" in body
    # Picker copy now optionally includes data-cache-oltype (value only) as 4th part.
    assert "const parts = [page, dataUi, id];" in body
    assert "if(olType) parts.push(olType);" in body
    # Picker copy supports fallback targets (no data-ui/id) and still uses angle brackets.
    assert "let text = ''" in body
    assert "text = '<' + parts.join(',') + '>'" in body
    assert "Kopiert: " in body
    assert "document.addEventListener('mousemove', onMove, true);" in body


def test_export_advanced_measurement_field_removed():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "export.html").read_text()
    assert 'data-ui="export.advanced"' not in body
    assert 'data-ui="export.measurement"' not in body
    assert 'measurement_adv_list' not in body
    assert '<span>_field</span>' in body


def test_history_extra_filters_removed():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "history.html").read_text()
    assert 'id="measurement"' not in body
    assert 'id="entity_id"' not in body
    assert 'id="reason"' not in body


def test_config_has_status_bar_color_pickers():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'id="ui_status_bar_bg_color"' in body
    assert 'id="ui_status_bar_fg_color"' in body
    assert 'function _syncStatusBarColorPickersFromText()' in body


def test_settings_page_uses_only_shared_title_card():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'settings_search' not in body
    assert 'version_box' not in body
    assert 'main.content button:not(.ib_info_icon):not(.btn_sm) { width:100%; }' in body
    assert 'main.content .ib_info_icon {' in body


def test_sidebar_starts_below_pagecard():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_nav.html").read_text()
    assert 'top: calc(var(--ib-topbar-h, 0px) + var(--ib-pagecard-live-h, 0px) + 20px);' in body
    assert 'id = \'influxbro_sections_bar\'' not in body


def test_global_filter_clear_buttons_are_available():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'window.InfluxBroFieldClear' in body
    assert 'function scan(root)' in body
    assert 'data-clear-for' in body
    assert 'ib_clear_row' in body


def test_delete_confirm_phrase_removed_from_runtime_config_and_templates():
    config_yaml = (Path(__file__).resolve().parents[1] / "influxbro" / "config.yaml").read_text()
    import_html = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "import.html").read_text()
    combine_html = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "combine.html").read_text()
    restore_html = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "restore.html").read_text()
    assert 'delete_confirm_phrase' not in config_yaml
    assert 'id="confirm"' not in import_html
    assert 'id="confirm_phrase"' not in combine_html
    assert 'id="native_confirm_phrase"' not in restore_html


def test_export_field_loader_no_longer_forces_value_without_available_field():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "export.html").read_text()
    assert "addOpt('value');" not in body
    assert "if(preferred && xs.includes(preferred)) $f.value = preferred;" in body
    assert "else if(xs.includes('value')) $f.value = 'value';" in body
    assert "if(!measurement && !friendly && !entity){ if($f) $f.value = ''; return; }" in body
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


def test_measurements_all_without_filters_uses_schema_measurements(load_app_module, tmp_path, monkeypatch):
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
    r = client.get("/api/measurements?range=all")
    assert r.status_code == 200
    q = captured["q"]
    assert isinstance(q, str)
    assert 'schema.measurements(bucket: "b")' in q
    assert 'distinct(column: "_measurement")' not in q


def test_tag_values_respects_selector_limit_setting(load_app_module, tmp_path, monkeypatch):
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
        "selector_query_limit_enabled": True,
        "selector_query_limit_days": 30,
    })
    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    client = app_mod.app.test_client()
    r = client.get("/api/tag_values?tag=friendly_name&entity_id=sensor.demo&range=all")
    assert r.status_code == 200
    q = captured["q"]
    assert isinstance(q, str)
    assert "start: -30d" in q
    assert '1970-01-01T00:00:00Z' not in q


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


def test_resolve_signal_keeps_custom_range_when_selector_limit_enabled(load_app_module, tmp_path, monkeypatch):
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
        "selector_query_limit_enabled": True,
        "selector_query_limit_days": 30,
    })
    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    client = app_mod.app.test_client()
    r = client.post(
        "/api/resolve_signal",
        json={
            "friendly_name": "X",
            "range": "custom",
            "start": "2026-01-01T00:00:00Z",
            "stop": "2026-01-02T00:00:00Z",
        },
    )
    assert r.status_code == 200
    q = captured["q"]
    assert isinstance(q, str)
    assert '2026-01-01T00:00:00Z' in q
    assert '2026-01-02T00:00:00Z' in q
    assert "-30d" not in q


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


def test_api_jobs_includes_analysis_cache_patch_jobs(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    with app_mod.ANALYSIS_CACHE_PATCH_LOCK:
        app_mod.ANALYSIS_CACHE_PATCH_JOBS["patch-job-1"] = {
            "id": "patch-job-1",
            "series_key": "m|value|sensor.demo|Demo",
            "state": "running",
            "message": "patch running",
            "started_at": "2026-03-20T10:00:00Z",
            "updated_at": "2026-03-20T10:01:00Z",
            "started_mono": 1.0,
            "patched": 1,
            "skipped": 0,
            "cancelled": False,
            "error": None,
        }

    client = app_mod.app.test_client()
    r = client.get("/api/jobs?limit=20")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert any(str(x.get("type") or "") == "analysis_cache_patch" for x in j.get("jobs", []))


def test_api_jobs_delete_removes_history_only(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    app_mod._jobs_history_upsert({
        "id": "job-old-1",
        "type": "export",
        "state": "done",
        "started_at": "2026-03-20T10:00:00Z",
        "updated_at": "2026-03-20T10:05:00Z",
        "finished_at": "2026-03-20T10:05:00Z",
    })
    app_mod._jobs_history_upsert({
        "id": "job-old-2",
        "type": "export",
        "state": "error",
        "started_at": "2026-03-20T11:00:00Z",
        "updated_at": "2026-03-20T11:05:00Z",
        "finished_at": "2026-03-20T11:05:00Z",
    })

    client = app_mod.app.test_client()
    r = client.post("/api/jobs/delete", json={"job_ids": ["job-old-1"]})
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert j["deleted"] == 1
    rows = app_mod._jobs_history_load()
    assert [str(row.get("id") or "") for row in rows] == ["job-old-2"]


def test_api_jobs_delete_rejects_active_jobs(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    with app_mod.EXPORT_LOCK:
        app_mod.EXPORT_JOBS["job-live-1"] = {
            "id": "job-live-1",
            "state": "running",
            "started_at": "2026-03-20T10:00:00Z",
            "updated_at": "2026-03-20T10:01:00Z",
            "started_mono": 1.0,
        }

    client = app_mod.app.test_client()
    r = client.post("/api/jobs/delete", json={"job_ids": ["job-live-1"]})
    assert r.status_code == 409
    j = r.get_json()
    assert j["ok"] is False
    assert j["blocked_job_ids"] == ["job-live-1"]


def test_api_tag_combo_ranges_uses_flux_accumulator_name(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    captured: dict[str, object] = {"q": None}

    class _FakeRecord:
        def __init__(self):
            self.values = {
                "friendly_name": "Disk Write",
                "oldest_time": "2026-01-01T00:00:00Z",
                "newest_time": "2026-01-02T00:00:00Z",
                "count": 12,
            }

    class _FakeTable:
        def __init__(self):
            self.records = [_FakeRecord()]

    class _FakeQueryAPI:
        def query(self, q: str, org: str | None = None):
            captured["q"] = q
            return [_FakeTable()]

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
        "/api/tag_combo_ranges",
        json={
            "measurement": "MB/s",
            "field": "value",
            "group_tag": "friendly_name",
            "entity_id": "g3_flex_garage_disk_write_rate",
            "friendly_name": None,
            "limit": 80,
            "range": "all",
        },
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    q = captured["q"]
    assert isinstance(q, str)
    assert "fn: (r, accumulator)" in q
    assert "acc.oldest_time" not in q


def test_api_tag_values_uses_direct_query_for_friendly_name_with_entity_id(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    captured: dict[str, object] = {"q": None}

    class _FakeRecord:
        def get_value(self):
            return "Disk Write"

    class _FakeTable:
        def __init__(self):
            self.records = [_FakeRecord()]

    class _FakeQueryAPI:
        def query(self, q: str, org: str | None = None):
            captured["q"] = q
            return [_FakeTable()]

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
    r = client.get(
        "/api/tag_values?tag=friendly_name&measurement=MB%2Fs&field=value&entity_id=g3_flex_garage_disk_write_rate&range=all"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    q = captured["q"]
    assert isinstance(q, str)
    assert "schema.tagValues(" not in q
    assert 'r._measurement == "MB/s"' in q
    assert 'r._field == "value"' in q
    assert 'r.entity_id == "g3_flex_garage_disk_write_rate"' in q
    assert 'distinct(column: "friendly_name")' in q


def test_friendly_name_merge_latest_creates_change_block(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")

    class _FakeRecord:
        def __init__(self, ts: str, value: float, friendly_name: str):
            from datetime import datetime, timezone

            self._time = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
            self._value = value
            self.values = {
                "entity_id": "sensor.demo",
                "friendly_name": friendly_name,
                "host": "ha",
            }

        def get_time(self):
            return self._time

        def get_value(self):
            return self._value

    class _FakeQueryAPI:
        def query_stream(self, q: str, org: str | None = None):
            return iter([
                _FakeRecord("2026-01-01T00:00:00Z", 1.0, "Alt A"),
                _FakeRecord("2026-01-02T00:00:00Z", 2.0, "Alt B"),
                _FakeRecord("2026-01-03T00:00:00Z", 3.0, "Neu"),
            ])

    class _FakeClient:
        def query_api(self):
            return _FakeQueryAPI()

        def close(self):
            return None

    @contextmanager
    def _fake_v2_client(cfg: dict):
        yield _FakeClient()

    saved_blocks: list[tuple[dict, list[dict] | None]] = []

    def _save_change_block(block: dict, *, items=None):
        saved_blocks.append((dict(block), list(items) if items is not None else None))
        return block

    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {
        **cfg,
        "influx_version": 2,
        "token": "t",
        "org": "o",
        "bucket": "b",
    })
    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)
    monkeypatch.setattr(app_mod, "save_change_block", _save_change_block)
    monkeypatch.setattr(app_mod, "execute_change_block", lambda _bid: {"ok": True, "applied": 2})
    monkeypatch.setattr(app_mod, "_cb_patch_block_meta", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_mod, "_history_append", lambda payload: None)
    monkeypatch.setattr(app_mod, "_dash_cache_mark_dirty_series", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_mod, "_stats_cache_mark_dirty_series", lambda *args, **kwargs: None)

    class _Undo:
        def register_action(self, **kwargs):
            return None

    monkeypatch.setattr(app_mod, "_undo_mgr", lambda cfg: _Undo())

    client = app_mod.app.test_client()
    r = client.post(
        "/api/friendly_name_merge_latest",
        json={
            "measurement": "kWh",
            "field": "value",
            "entity_id": "sensor.demo",
            "target_friendly_name": "Neu",
            "source_friendly_names": ["Alt A", "Alt B"],
            "range": "all",
        },
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert j["updated"] == 2
    child_items = [items for block, items in saved_blocks if items]
    assert len(child_items) == 1
    assert len(child_items[0]) == 2
    assert all(item["op"] == "update" for item in child_items[0])
    assert all(item["new_point"]["friendly_name"] == "Neu" for item in child_items[0])


def test_api_measurement_profile_returns_grouped_payload(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {**cfg, "influx_version": 2, "bucket": "homeassistant_db", "token": "t", "org": "o"})
    monkeypatch.setattr(app_mod, "_measurement_profile_ha", lambda eid: {
        "available": True,
        "entity_id": eid,
        "friendly_name": "Demo Sensor",
        "domain": "sensor",
        "unique_id": "demo_unique",
        "device": "Demo Device",
        "area": "Keller",
        "integration": "modbus",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit_of_measurement": "Wh",
        "native_unit_of_measurement": "Wh",
        "suggested_display_precision": 0,
        "icon": "mdi:flash",
        "entity_category": None,
        "supported_features": 0,
        "state": "123",
    })
    monkeypatch.setattr(app_mod, "_measurement_profile_yaml_search", lambda eid, fn, uid: {
        "found": True,
        "match_count": 1,
        "source_file": "configuration.yaml",
        "type": "modbus",
        "path": "modbus/0/sensors/0",
        "data": {"slave": 3, "address": 30581, "unit_of_measurement": "Wh"},
    })
    monkeypatch.setattr(app_mod, "_measurement_profile_references", lambda *args, **kwargs: {
        "count": 1,
        "items": [{"kind": "automation", "source_file": "automations.yaml", "line": 12, "match": "sensor.demo", "snippet": "entity_id: sensor.demo", "open_target": "/config/automation/dashboard"}],
    })

    class _FakeRecord:
        def __init__(self, value, time_iso=None):
            self._value = value
            self._time = None if time_iso is None else datetime.fromisoformat(time_iso.replace("Z", "+00:00"))

        def get_value(self):
            return self._value

        def get_time(self):
            return self._time

    class _FakeTable:
        def __init__(self, records):
            self.records = records

    class _FakeQueryAPI:
        def query(self, q: str, org: str | None = None):
            if "|> count()" in q:
                return [_FakeTable([_FakeRecord(42)])]
            if "|> first()" in q:
                return [_FakeTable([_FakeRecord(1.0, "2026-01-01T00:00:00Z")])]
            if "|> last()" in q:
                return [_FakeTable([_FakeRecord(9.0, "2026-01-02T00:00:00Z")])]
            if "|> min()" in q:
                return [_FakeTable([_FakeRecord(1.0)])]
            if "|> max()" in q:
                return [_FakeTable([_FakeRecord(9.0)])]
            if "|> mean()" in q:
                return [_FakeTable([_FakeRecord(5.0)])]
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
    r = client.get("/api/measurement_profile?entity_id=sensor.demo&measurement=Wh&field=value&friendly_name=Demo%20Sensor&range=all")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert j["ha"]["friendly_name"] == "Demo Sensor"
    assert j["yaml"]["found"] is True
    assert j["references"]["count"] == 1
    assert j["influx"]["field_type"] == "float"
    assert j["influx"]["count"] == 42
    assert j["influx"]["first_value"] == 1.0
    assert j["influx"]["last_value"] == 9.0
    assert j["influx"]["oldest_time"] == "2026-01-01T00:00:00.000Z"
    assert j["influx"]["newest_time"] == "2026-01-02T00:00:00.000Z"
    assert "min_time" in j["influx"]
    assert "max_time" in j["influx"]
    assert j["derived"]["internal_type"] == "counter_increasing"
    assert isinstance(j["quality"]["warnings"], list)


def test_query_payload_prefers_v2_when_v1_database_missing(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")

    class _FakeRecord:
        def __init__(self, value, time_iso):
            self._value = value
            self._time = datetime.fromisoformat(time_iso.replace("Z", "+00:00"))

        def get_value(self):
            return self._value

        def get_time(self):
            return self._time

    class _FakeQueryAPI:
        def query_stream(self, q: str, org: str | None = None):
            if "count(column: \"_value\")" in q:
                return iter([_FakeRecord(2, "2026-01-01T00:00:00Z")])
            return iter([
                _FakeRecord(1.0, "2026-01-01T00:00:00Z"),
                _FakeRecord(2.0, "2026-01-02T00:00:00Z"),
            ])

    class _FakeClient:
        def query_api(self):
            return _FakeQueryAPI()

        def close(self):
            return None

    @contextmanager
    def _fake_v2_client(cfg: dict):
        yield _FakeClient()

    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    cfg = {
        "influx_version": 1,
        "database": "",
        "token": "t",
        "org": "o",
        "bucket": "b",
        "ui_query_max_points": 5000,
        "ui_query_manual_max_points": 200000,
    }
    out = app_mod._query_payload(cfg, "MB/s", "value", "all", "sensor.demo", None, "MB/s", "dynamic", 100, None, None)
    assert out["ok"] is True
    assert len(out["rows"]) == 2
    assert out["meta"]["mode"] == "dynamic"


def test_api_outlier_strategy_derives_effective_types(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {**cfg, "influx_version": 2, "bucket": "homeassistant_db", "token": "t", "org": "o"})
    monkeypatch.setattr(app_mod, "_measurement_profile_build", lambda cfg, **kwargs: {
        "entity_id": kwargs["entity_id"],
        "ha": {"available": True, "entity_id": kwargs["entity_id"], "device_class": "energy", "state_class": "total_increasing", "unit_of_measurement": "Wh", "domain": "sensor"},
        "yaml": {"found": True, "data": {}},
        "influx": {"measurement": kwargs["measurement"], "field": kwargs["field"], "field_type": "float"},
        "derived": {"internal_type": "counter_increasing", "confidence": "high"},
        "quality": {"warnings": []},
    })
    monkeypatch.setattr(app_mod, "_outlier_strategy_load_store", lambda: {
        "strategies": [
            {
                "id": "custom.counter_override",
                "name": "Counter Override",
                "description": "Override for counters",
                "priority": 110,
                "match": {"internal_types": ["counter_increasing"]},
                "enable_types": ["rate_jump", "reset_event", "negative_jump"],
                "disable_types": ["range_violation", "fault_cluster", "time_gap", "null_value", "zero_value"],
            }
        ],
        "overrides": {
            "sensor.demo|Wh|value": {"manual_enable_types": ["time_gap"], "manual_disable_types": ["negative_jump"]}
        },
    })

    client = app_mod.app.test_client()
    r = client.get("/api/outlier_strategy?entity_id=sensor.demo&measurement=Wh&field=value&range=all")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert j["strategy"]["id"] == "custom.counter_override"
    assert "rate_jump" in j["effective_selected"]
    assert "reset_event" in j["effective_selected"]
    assert "time_gap" in j["effective_selected"]
    assert "negative_jump" not in j["effective_selected"]
    assert j["profile"]["derived"]["internal_type"] == "counter_increasing"


def test_api_outlier_strategy_override_modes(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()

    r = client.post(
        "/api/outlier_strategy/override",
        json={
            "entity_id": "sensor.demo",
            "measurement": "Wh",
            "field": "value",
            "mode": "all_off",
        },
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert j["override"]["mode"] == "all_off"
    assert j["override"]["manual_enable_types"] == []
    assert j["override"]["manual_disable_types"] == []


def test_api_outlier_strategy_reads_legacy_keys_and_returns_new_keys(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {**cfg, "influx_version": 2, "bucket": "homeassistant_db", "token": "t", "org": "o"})
    monkeypatch.setattr(app_mod, "_measurement_profile_build", lambda cfg, **kwargs: {
        "entity_id": kwargs["entity_id"],
        "ha": {"available": True, "entity_id": kwargs["entity_id"], "device_class": "energy", "state_class": "total_increasing", "unit_of_measurement": "Wh", "domain": "sensor"},
        "yaml": {"found": True, "data": {}},
        "influx": {"measurement": kwargs["measurement"], "field": kwargs["field"], "field_type": "float"},
        "derived": {"internal_type": "counter_increasing", "confidence": "high"},
        "quality": {"warnings": []},
    })
    monkeypatch.setattr(app_mod, "_outlier_strategy_load_store", lambda: {
        "strategies": [
            {
                "id": "legacy.counter_override",
                "name": "Legacy Counter Override",
                "description": "Legacy keys",
                "priority": 100,
                "match": {"internal_types": ["counter_increasing"]},
                "enable_types": ["counter", "counterreset", "decrease"],
                "disable_types": ["bounds", "fault_phase", "gap", "null", "zero"],
            }
        ],
        "overrides": {
            "sensor.demo|Wh|value": {"manual_enable_types": ["gap"], "manual_disable_types": ["decrease"]}
        },
    })
    client = app_mod.app.test_client()
    r = client.get("/api/outlier_strategy?entity_id=sensor.demo&measurement=Wh&field=value&range=all")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert "rate_jump" in j["strategy"]["enable_types"]
    assert "reset_event" in j["strategy"]["enable_types"]
    assert "time_gap" in j["effective_selected"]


def test_api_outliers_accepts_new_search_type_names(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")

    class _FakeRecord:
        def __init__(self, time_iso: str, value: float):
            self._time = datetime.fromisoformat(time_iso.replace("Z", "+00:00"))
            self._value = value

        def get_time(self):
            return self._time

        def get_value(self):
            return self._value

    class _FakeQueryAPI:
        def query_stream(self, q: str, org: str | None = None):
            return iter([
                _FakeRecord("2026-01-01T00:00:00Z", 10.0),
                _FakeRecord("2026-01-01T00:10:00Z", 9999.0),
            ])

    class _FakeClient:
        def query_api(self):
            return _FakeQueryAPI()

        def close(self):
            return None

    @contextmanager
    def _fake_v2_client(cfg: dict):
        yield _FakeClient()

    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {**cfg, "influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    client = app_mod.app.test_client()
    r = client.post(
        "/api/outliers",
        json={
            "measurement": "Wh",
            "field": "value",
            "entity_id": "sensor.demo",
            "start": "2026-01-01T00:00:00Z",
            "stop": "2026-01-01T00:20:00Z",
            "search_types": ["range_violation"],
            "min": "",
            "max": "100",
        },
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert any("range_violation" in (row.get("types") or []) for row in j.get("rows", []))


def test_fields_all_time_uses_schema_measurement_field_keys(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    captured = {"q": None}

    class _FakeRecord:
        def get_value(self):
            return "value"

    class _FakeTable:
        def __init__(self):
            self.records = [_FakeRecord()]

    class _FakeQueryAPI:
        def query(self, q: str, org: str | None = None):
            captured["q"] = q
            return [_FakeTable()]

    class _FakeClient:
        def query_api(self):
            return _FakeQueryAPI()

        def close(self):
            return None

    @contextmanager
    def _fake_v2_client(cfg: dict):
        yield _FakeClient()

    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {**cfg, "influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    monkeypatch.setattr(app_mod, "v2_client", _fake_v2_client)

    client = app_mod.app.test_client()
    r = client.get("/api/fields?measurement=%C2%B0C&range=all")
    assert r.status_code == 200
    q = captured["q"]
    assert isinstance(q, str)
    assert 'schema.measurementFieldKeys(bucket: "b", measurement: "°C")' in q
    assert 'distinct(column: "_field")' not in q


def test_verify_measurement_start_returns_job_id(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {**cfg, "influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    monkeypatch.setattr(app_mod.threading, "Thread", lambda target, args=(), daemon=None: type("T", (), {"start": lambda self: None})())
    client = app_mod.app.test_client()
    r = client.post("/api/verify/measurement", json={"entity_id": "sensor.demo", "measurement": "Wh", "field": "value", "backup_mode": "existing", "backup_id": "demo_backup", "profile": "fast"})
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert j["mode"] == "measurement"
    assert str(j["job_id"]).startswith("verify_measurement_")


def test_verify_fullbackup_start_returns_job_id(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    monkeypatch.setattr(app_mod, "_overlay_from_yaml_if_enabled", lambda cfg: {**cfg, "influx_version": 2, "token": "t", "org": "o", "bucket": "b"})
    monkeypatch.setattr(app_mod.threading, "Thread", lambda target, args=(), daemon=None: type("T", (), {"start": lambda self: None})())
    client = app_mod.app.test_client()
    r = client.post("/api/verify/fullbackup", json={"bucket": "b", "backup_mode": "existing", "backup_id": "demo_fullbackup", "profile": "fast"})
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert j["mode"] == "fullbackup"
    assert str(j["job_id"]).startswith("verify_full_")


def test_measurement_profile_derived_includes_strategy_explanation_fields(load_app_module):
    app_mod = load_app_module()
    derived = app_mod._measurement_profile_derived(
        {"domain": "sensor", "device_class": "energy", "state_class": "total_increasing", "unit_of_measurement": "Wh", "available": True},
        {"field_type": "float"},
        {"found": True},
    )
    assert derived["internal_type"] == "counter_increasing"
    assert derived["unit_group"] == "energy_total"
    assert derived["type_unit_consistency"] == "consistent"
    assert derived["counter_semantics"] == "monotonic_expected"
    assert isinstance(derived["strategy_explanation"], list)
    assert len(derived["strategy_explanation"]) >= 2


def test_api_audit_aggregates_counts_and_backup_status(load_app_module, tmp_path, monkeypatch):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")

    class _FakeRecord:
        def __init__(self, value, values=None):
            self._value = value
            self.values = values or {}

        def get_value(self):
            return self._value

    class _FakeQueryAPI:
        def query_stream(self, q: str, org: str | None = None):
            if 'from(bucket: "raw")' in q and 'group(columns: ["entity_id"])' not in q:
                return iter([_FakeRecord(100)])
            if 'from(bucket: "rollup")' in q and 'group(columns: ["entity_id"])' not in q:
                return iter([_FakeRecord(20)])
            if 'from(bucket: "raw")' in q and 'group(columns: ["entity_id"])' in q:
                return iter([
                    _FakeRecord(60, {"entity_id": "sensor.a"}),
                    _FakeRecord(40, {"entity_id": "sensor.b"}),
                ])
            if 'from(bucket: "rollup")' in q and 'group(columns: ["entity_id"])' in q:
                return iter([
                    _FakeRecord(12, {"entity_id": "sensor.a"}),
                    _FakeRecord(8, {"entity_id": "sensor.b"}),
                ])
            return iter([])

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
    monkeypatch.setattr(app_mod, "_rollup_profiles_load", lambda cfg: [{"id": "default", "source_bucket": "raw", "target_bucket": "rollup"}])
    monkeypatch.setattr(app_mod, "_rollup_runs_list", lambda limit=200: [{"profile_id": "default", "backup_id": "b1", "created_at": "2026-04-29T10:00:00Z"}])
    monkeypatch.setattr(app_mod, "_rollup_backup_validate", lambda backup_id: {"backup_id": backup_id, "created_at": "2026-04-29T10:00:00Z"})

    client = app_mod.app.test_client()
    r = client.get("/api/audit?profile_id=default&tag_key=entity_id&field=value")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert j["point_counts"]["raw"] == 100
    assert j["point_counts"]["agg"] == 20
    assert j["cardinality"]["raw"] == 2
    assert j["backup"]["exists"] is True
    assert j["backup"]["restore_available"] is True
    assert len(j["per_tag"]) == 2
    assert j["per_tag"][0]["backup_exists"] is True


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
