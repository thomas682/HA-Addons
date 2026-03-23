from __future__ import annotations

from pathlib import Path


def test_bugreport_meta_includes_recent_ui_actions(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    r = client.post(
        "/api/ui_event",
        json={
            "page": "dashboard",
            "ui": "raw.paste",
            "text": "Einfuegen",
            "extra": {"kind": "change", "value": "42"},
        },
    )
    assert r.status_code == 200
    assert r.get_json()["ok"] is True

    r = client.get("/api/bugreport_meta")
    j = r.get_json()

    assert r.status_code == 200
    assert j["ok"] is True
    assert isinstance(j["recent_actions"], list)
    assert j["recent_actions"][-1]["ui"] == "raw.paste"
    assert "github_repo_base" in j


def test_debug_report_contains_recent_ui_actions(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    client.post("/api/ui_event", json={"page": "dashboard", "ui": "dashboard.load", "text": "Aktualisieren"})

    r = client.post("/api/debug_report", json={"tail": 0, "client": {}, "issue": {}})
    text = r.get_data(as_text=True)

    assert r.status_code == 200
    assert "## Recent UI Actions" in text
    assert "dashboard.load" in text


def test_config_clamps_new_ui_fields(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    r = client.post(
        "/api/config",
        json={
            "ui_pagecard_title_px": 99,
            "ui_raw_center_max_points": 0,
            "ui_raw_center_range_default": -5,
        },
    )
    assert r.status_code == 200
    assert r.get_json()["ok"] is True

    cfg = app_mod.load_cfg()
    assert cfg["ui_pagecard_title_px"] == 48
    assert cfg["ui_raw_center_max_points"] == 1
    assert cfg["ui_raw_center_range_default"] == 0


def test_raw_autotune_link_uses_timezone_aware_custom_range_payload():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert "const startIso = $start && $start.value ? localToIsoUtc($start.value) : null;" in body
    assert "const stopIso = $stop && $stop.value ? localToIsoUtc($stop.value) : null;" in body
    assert "start: startIso," in body
    assert "stop: stopIso," in body


def test_settings_numeric_fields_keep_values_visible():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'main.content input.cfg_num_wide[type="number"]{' in body
    assert 'id="ui_filter_label_width_px" class="cfg_num_wide"' in body
    assert 'id="ui_filter_control_width_px" class="cfg_num_wide"' in body
    assert 'id="ui_filter_search_width_px" class="cfg_num_wide"' in body
    assert 'id="ui_sel_field_font_px" class="cfg_num_wide"' in body


def test_info_popup_decodes_escaped_linebreaks():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "function _decodeEscapedInfoText(text){" in body
    assert ".replace(/\\\\n/g, '\\n')" in body
    assert "const normalizedMsg = _decodeEscapedInfoText(String(msg || ''));" in body


def test_bugreport_flow_offers_bug_or_enhancement_with_labels():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'id="influxbro_issue_kind"' in body
    assert '<option value="bug">Bug</option>' in body
    assert '<option value="enhancement">Erweiterung</option>' in body
    assert "const labels = (kind === 'enhancement') ? 'type/enhancement' : 'type/bug';" in body
    assert "if(kind === 'bug'){" in body
    assert "defaultBugText = 'siehe automatisch angehaengtes Logging / Bei Bedarf hier eigene Fehlerbeschreibung einfuegen....'" in body
    assert 'id="influxbro_issue_attach_help"' in body
    assert 'issue_addFile.png' in body


def test_raw_center_range_uses_minutes_in_ui():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'Bereich +- (Minuten)' in body
    assert 'payload.center_minutes = centerMinutes;' in body
    assert 'Zeitfenster um den selektierten Messwert herum in Minuten.' in body


def test_dashboard_raw_buttons_show_feedback_and_last_error_button_removed():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'function showRawActionFeedback(title, text)' in body
    assert "showRawActionFeedback('Raw Daten kopiert'" in body
    assert "showRawActionFeedback('Raw Query'" in body
    assert "showRawActionFeedback('Raw Wert kopiert'" in body
    assert 'id="last_error"' not in body
    assert "dashboard.last_error" not in body


def test_dashboard_collapsible_sections_have_info_icons():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'data-info-title="Dashboard: Gesamtstatistik (Alles)"' in body
    assert 'data-info-title="Dashboard: Graph"' in body
    assert 'data-info-title="Dashboard: Statistik Zeitraum"' in body
    assert 'data-info-title="Dashboard: Bearbeitungsliste"' in body


def test_raw_paste_can_stage_rows_from_raw_table():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert "if(!row) row = (RAW_ROWS || []).find(r => rowKey(r) === key);" in body
    assert "if(!EDIT_LIST.has(String(target))){ err('Ziel-Zeile konnte nicht fuer die Bearbeitungsliste vorgemerkt werden.'); return; }" in body


def test_issue_composer_requires_function_and_keeps_text_on_type_change():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'id="influxbro_issue_function"' in body
    assert "Bitte Funktion / Menueeintrag auswaehlen." in body
    assert "const textState = { bug: '', enhancement: '' };" in body
    assert "textState[prevMode] = String(textEl.value || '');" in body


def test_info_popup_persists_size_per_dialog():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "const POPUP_SIZE_PREFIX = 'influxbro.popup.size.v1.';" in body
    assert "function _popupSizeStorageKey(title)" in body
    assert "const ro = new ResizeObserver(()=>{ _savePopupSize(); });" in body
    assert "_applyPopupSize(title || 'Hinweis');" in body


def test_settings_include_bugreport_log_history_hours():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'id="bugreport_log_history_hours"' in body
    assert 'bugreport_log_history_hours' in body


def test_monitor_page_does_not_force_topbar_search_to_full_width():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "monitor.html").read_text()
    assert 'main.content input, main.content select, main.content textarea { width:100%; }' in body
    assert 'input, select, textarea { width:100%; }' not in body
