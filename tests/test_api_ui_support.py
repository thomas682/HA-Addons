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


def test_nav_uses_dynamic_pagecard_height_for_desktop_layout():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_nav.html").read_text()
    assert 'top: calc(var(--ib-topbar-h, 0px) + var(--ib-pagecard-h, 0px) + 20px);' in body
    assert 'height: calc(100vh - (var(--ib-topbar-h, 0px) + var(--ib-pagecard-h, 0px) + 20px));' in body


def test_topbar_updates_pagecard_height_css_var():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert "const pc = document.getElementById('ib_pagecard');" in body
    assert "document.documentElement.style.setProperty('--ib-pagecard-h', String(ph) + 'px');" in body


def test_page_search_highlight_is_global_and_configurable():
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    config = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    app_py = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert '.jump_hl {' in topbar
    assert '--ib-page-search-hl-color:' in topbar
    assert '--ib-page-search-hl-width:' in topbar
    assert '--ib-page-search-hl-duration-ms:' in topbar
    assert 'ui_page_search_highlight_color' in config
    assert 'ui_page_search_highlight_width_px' in config
    assert 'ui_page_search_highlight_duration_ms' in config
    assert '"ui_page_search_highlight_color": "#FF9900"' in app_py


def test_summary_rows_use_full_summary_bar_style():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'main.content details > summary {' in body
    assert 'border: 1px solid #cfd5e2;' in body
    assert 'border-radius: 10px;' in body
    assert 'background: var(--ib-section-title-bg);' in body
    assert 'width: 20px;' in body


def test_dashboard_selection_labels_and_widths_are_updated():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert '<label class="ib_sel_label">Einheit</label>' in body
    assert '<span>Feld</span><span id="cnt_field" class="muted"></span>' in body
    assert '<span>Entity</span>' in body
    assert '<span>Name</span>' in body
    assert 'width: auto;' in body
    assert 'max-width: 60%;' in body
    assert "inputEl.style.width = '';" in body
    assert "selEl.style.width = '';" in body
    assert "inputEl.style.width = px + 'px';" not in body
    assert "selEl.style.width = px + 'px';" not in body


def test_popup_remains_mouse_resizable():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "card.style.resize = 'both';" in body


def test_import_analyze_shows_success_and_error_popups():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "import.html").read_text()
    assert "window.InfluxBroPopup.show('Import Analyse erfolgreich', msg);" in body
    assert "window.InfluxBroPopup.show('Import Analyse Fehler', msg);" in body
    assert 'id="cnt_src_measurement"' in body
    assert 'id="cnt_src_field"' in body
    assert 'function updateImportActionState()' in body


def test_logs_page_has_collapsible_title_and_short_button_texts():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "logs.html").read_text()
    assert 'data-ui="logs.page.card"' in body
    assert '<span style="margin-left:6px;">Neu</span>' in body
    assert '<span style="margin-left:6px;">Report</span>' in body


def test_timer_table_uses_mode_button_in_action_column():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "jobs.html").read_text()
    assert "bMode.textContent = 'Modus';" in body
    assert "tdMode.textContent = currentModeText();" in body


def test_table_helpers_strip_ingress_token_from_storage_keys():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_table_cols.html").read_text()
    assert "replace(/\\/api\\/hassio_ingress\\/[0-9a-fA-F]+/g, '')" in body


def test_history_and_restore_sections_are_collapsible():
    history = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "history.html").read_text()
    restore = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "restore.html").read_text()
    backup = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "backup.html").read_text()
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'data-ui="history.page.card"' in history
    assert 'data-ui="restore.source"' in restore and 'data-ui="restore.target"' in restore
    assert 'id="space" data-ui="backup.space"' in backup
    assert 'function _ensureSummarySettingsButtons()' in tooltips


def test_page_search_has_navigation_and_filter_dialog():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'id="ib_page_search_prev"' in body
    assert 'id="ib_page_search_next"' in body
    assert 'id="ib_page_search_settings"' in body
    assert 'const SEARCH_CFG_KEY = ' in body
    assert 'function renderSearchSettings()' in body
    assert 'Tooltiptexte' in body
    assert 'function previewSearchIndex()' in body
    assert '$searchModal.onclick = null;' in body
    assert 'direct_text' in body
    assert "addEventListener('focus', ()=>{ if(String($search.value || '').trim()) runSearch(); });" in body


def test_dashboard_field_label_has_count_span():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert '<span id="cnt_field" class="muted"></span>' in body


def test_info_and_manual_pages_have_local_search_controls():
    info = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "info.html").read_text()
    manual = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "manual.html").read_text()
    assert 'id="info_search"' in info
    assert 'id="info_search_prev"' in info
    assert 'id="info_search_next"' in info
    assert 'mark.ib_search_hit.active' in info
    assert 'id="manual_search"' in manual
    assert 'id="manual_search_prev"' in manual
    assert 'id="manual_search_next"' in manual
    assert 'function runManualSearch()' in manual


def test_config_tooltips_include_page_search_highlight_settings():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "settings.ui_page_search_highlight_color" in body
    assert "settings.ui_page_search_highlight_width_px" in body
    assert "settings.ui_page_search_highlight_duration_ms" in body
