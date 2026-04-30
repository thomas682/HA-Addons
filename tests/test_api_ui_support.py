from __future__ import annotations

from pathlib import Path
import re


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
            "ui_gui_title_px": 99,
            "ui_gui_body_px": 1,
            "ui_raw_center_max_points": 0,
            "ui_raw_center_range_default": -5,
            "ui_raw_center_min_points": 0,
            "ui_timer_disabled_opacity": 999,
            "selector_query_limit_days": 0,
        },
    )
    assert r.status_code == 200
    assert r.get_json()["ok"] is True

    cfg = app_mod.load_cfg()
    assert cfg["ui_gui_title_px"] == 16
    assert cfg["ui_gui_body_px"] == 8
    assert cfg["ui_pagecard_title_px"] == 16
    assert cfg["ui_raw_center_max_points"] == 1
    assert cfg["ui_raw_center_range_default"] == 0
    assert cfg["ui_raw_center_min_points"] == 1
    assert cfg["ui_timer_disabled_opacity"] == 100
    assert cfg["selector_query_limit_days"] == 1


def test_config_logging_batch_endpoint_acks_and_persists(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"
    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    r = client.post(
        "/api/client_log_batch",
        json={
            "events": [
                {
                    "event_id": "clientA-1",
                    "page": "Dashboard",
                    "area": "dashboard_state",
                    "field": "saveState",
                    "source": "localStorage",
                    "storage_key": "influxbro_ui_state_v1",
                    "changes": [{"field": "raw_open", "old": False, "new": True}],
                }
            ]
        },
    )
    j = r.get_json()
    assert r.status_code == 200
    assert j["ok"] is True
    assert j["acked"] == ["clientA-1"]
    queue_path = data_root / "influxbro_config_log_queue.jsonl"
    ack_path = data_root / "influxbro_config_log_acks.json"
    assert queue_path.exists()
    assert ack_path.exists()
    assert 'clientA-1' in ack_path.read_text()


def test_app_state_set_logs_config_save_when_enabled(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"
    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    r = client.post(
        "/api/app_state/set",
        json={
            "scope": "dashboard_selection",
            "state": {"range": "7d", "measurement": "EUR"},
        },
    )
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_dashboard_raw_removed_legacy_buttons_and_added_min_points_setting():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    config = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'id="raw_copy_query"' not in body
    assert 'id="raw_more"' not in body
    assert 'id="raw_tune_link"' not in body
    assert 'rawAutoTuneMaxPoints' not in body
    assert 'id="ui_raw_center_min_points"' in config


def test_settings_numeric_fields_keep_values_visible():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    # Spacing around the opening brace is not semantically relevant.
    assert 'main.content input.cfg_num_wide[type="number"]' in body
    assert 'id="ui_filter_label_width_px" class="cfg_num_wide"' in body
    assert 'id="ui_filter_control_width_px" class="cfg_num_wide"' in body
    assert 'id="ui_filter_search_width_px" class="cfg_num_wide"' in body
    assert 'id="ui_gui_body_px" class="cfg_num_wide"' in body


def test_info_popup_decodes_escaped_linebreaks():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "window.InfluxBroDecodeInfoText = function(text){" in body
    assert ".replace(/\\\\n/g, '\\n')" in body
    assert "const normalizedMsg = (window.InfluxBroDecodeInfoText ? window.InfluxBroDecodeInfoText(String(msg || '')) : String(msg || ''));" in body


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
    assert 'Zeitfenster um den selektierten Messwert herum in Minuten.' in body
    assert 'Bereich +-:' in body
    assert 'clampRawCenterRange(RAW_CENTER_RANGE))} min' in body
    assert 'Mindestdatenpunkte je Seite' in body
    assert 'function countCenteredRows(rows, anchorIso){' in body


def test_dashboard_raw_buttons_show_feedback_and_last_error_button_removed():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'function showRawActionFeedback(title, text)' in body
    assert "showRawActionFeedback('Raw Daten kopiert'" in body
    assert "showRawActionFeedback('Raw Wert kopiert'" in body
    assert 'id="last_error"' not in body
    assert "dashboard.last_error" not in body


def test_dashboard_collapsible_sections_have_info_icons():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'data-info-title="Dashboard: Gesamtstatistik (Alles)"' not in body
    assert 'data-info-title="Dashboard: Graph"' in body
    assert 'data-info-title="Dashboard: Statistik Zeitraum"' not in body
    # Bearbeitungsliste was removed; keep test aligned with current UI.
    assert 'data-info-title="Dashboard: Bearbeitungsliste"' not in body


def test_raw_paste_overwrites_directly_with_confirmation_and_dragdrop():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert "await api('./api/apply_changes'" in body
    assert "function confirmRawOverwrite(sourceRow, targetRow)" in body
    assert "tr.addEventListener('drop', async (ev)=>{" in body
    assert "RAW_COPIED = { key, raw_value: row.value, value_str: rawNumericValueString(row.value), time: row.time };" in body


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


def test_query_test_dialog_includes_query_history_panel():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'influxbro_querytest_history_toggle' in body
    assert 'influxbro_querytest_history_panel' in body
    assert "./api/query_history?limit=500" in body
    assert "Einfuegen oben" in body
    assert "selectedOrFull(area)" in body
    assert "applyMiniCheckboxStyleSafe" in body


def test_dashboard_restores_global_selection_before_initial_measurements_load():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    restore_idx = body.index("if(globalSel.measurement_filter)")
    load_idx = body.index("await loadMeasurements({silent: true});")
    assert restore_idx < load_idx


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
    assert 'top: calc(var(--ib-topbar-h, 0px) + var(--ib-pagecard-live-h, 0px) + 20px);' in body
    assert (
        'height: calc(100vh - (var(--ib-topbar-h, 0px) + var(--ib-pagecard-live-h, 0px) + 20px));' in body
        or 'height: max(240px, calc(100vh - (var(--ib-topbar-h, 0px) + var(--ib-pagecard-live-h, 0px) + 20px)));' in body
    )


def test_topbar_updates_pagecard_height_css_var():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert "const pc = document.getElementById('ib_pagecard');" in body
    assert "document.documentElement.style.setProperty('--ib-pagecard-live-h', String(Math.max(0, ph)) + 'px');" in body


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
    assert '<span>Einheit</span><span id="cnt_measurement_filter" class="muted"></span>' in body
    assert '<span>Feld</span><span id="cnt_field" class="muted"></span>' in body
    assert '<span>Entity</span>' in body
    assert '<span>Name</span>' in body
    assert 'width: auto;' in body
    assert 'max-width: 60%;' in body
    assert "inputEl.style.width = '';" in body


def test_dashboard_load_supports_cache_plan_prompt_and_time_savings():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert "async function maybePromptDashboardCacheUse(filters){" in body
    assert "./api/cache/plan" in body
    assert "Geschaetzte Zeitersparnis" in body
    assert "Cache-Ausreisser" in body
    assert "cache_strategy" in body
    assert "Kein Cache-Dialog" in body
    assert "dashboard_cache_plan', step: 'no_cache_dialog'" in body


def test_raw_and_outlier_tables_share_same_font_size_rule():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert '#raw_tbl, #raw_tbl th, #raw_tbl td,' in body
    assert '#raw_outlier_tbl, #raw_outlier_tbl th, #raw_outlier_tbl td {' in body
    assert 'font-size: var(--ib-font-tbl-cell) !important;' in body
    assert "tdO.style.fontSize = '11px';" not in body
    assert "selEl.style.width = '';" in body
    assert "inputEl.style.width = px + 'px';" not in body
    assert "selEl.style.width = px + 'px';" not in body


def test_raw_outlier_table_uses_template_structure_and_helpers():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'id="raw_outlier_table_wrap"' in body
    assert 'id="raw_outlier_tbl" class="list_tbl ib_tbl"' in body
    assert '>Raw-Kontext<' in body
    assert "function _rawOutlierContextInfo(row){" in body
    assert "kein Raw-Fenster" in body
    assert 'id="raw_outlier_autowidth"' in body
    assert 'id="raw_outlier_windowwidth"' in body
    assert 'id="raw_outlier_wrap"' in body
    assert 'id="raw_outlier_colfilter"' in body
    assert "window.InfluxBroTableCols.init('#raw_outlier_tbl');" in body
    assert "window.InfluxBroTableFilter.init('#raw_outlier_tbl', {startHidden: true});" in body
    assert "window.InfluxBroTableHeight.attach($rawOutlierBox, 'raw_outlier_tbl', {minPx: 120});" in body
    assert 'button[data-table-colvis="raw_outlier_tbl"]' in body


def test_raw_outlier_params_dialog_has_explanations_and_recovery_override():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'id="raw_outlier_params_reset"' in body
    assert 'id="raw_param_max_step_w"' in body
    assert 'id="raw_param_max_step_kw"' in body
    assert 'id="raw_param_max_step_wh"' in body
    assert 'id="raw_param_max_step_kwh"' in body
    assert 'placeholder="Default"' in body
    assert 'placeholder="leer = keine Untergrenze"' in body
    assert 'placeholder="leer = keine Obergrenze"' in body
    assert 'placeholder="leer = Standard 2"' in body
    assert 'placeholder="leer = Standard aus Einstellungen"' in body
    assert 'Anzahl gueltiger Werte in Folge, bis eine aktive Stoerphase wieder als beendet gilt.' in body
    assert 'recovery_valid_streak: params.recovery_streak || \'\'' in body
    assert 'async function saveOutlierParamsDialog({useDefaults}' in body
    assert 'saveOutlierParamsDialog({useDefaults:true})' in body
    assert 'function _ensureOutlierWindows(base, win, source){' in body
    assert "kind: 'analysis_cache_window'" in body
    assert "_logOutlierWindowStats('status_before'" in body
    assert "_logOutlierWindowStats('status_after'" in body


def test_dashboard_outlier_section_is_separate_and_above_raw_section():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'id="outlier_section"' in body
    assert 'data-ui="dashboard_outliers.section_root"' in body
    assert '<span>Ausreißer</span>' in body
    assert body.index('id="outlier_section"') < body.index('id="raw_section"')
    assert 'id="raw_outlier_row_count"' in body
    assert 'style="--max-rows: 15; min-width:0; width:100%; box-sizing:border-box;"' in body


def test_outlier_table_header_is_explicitly_sticky_and_search_bar_tracks_outlier_section():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert '#raw_outlier_tbl thead { position: sticky; top: 0; z-index: 2; }' in body
    assert 'var(--ib-table-head-bg' in body
    assert '#raw_outlier_tbl thead th { background: var(--ib-table-head-bg, #0B1F3A); color: var(--ib-table-head-fg, #FFFFFF); }' in body
    assert 'Ausreißer-Suchleiste (#raw_search_bar) wurde entfernt (Issue #330).' in body
    assert "$outlierSection.addEventListener('toggle', ()=>{" in body


def test_outlier_table_uses_column_filter_suggestions_and_context_rows_save_immediately():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert '>Markieren<' not in body
    assert 'id="raw_outlier_reason_options"' in body
    assert "_updateRawOutlierReasonFilterOptions(filtered);" in body
    assert "inp.setAttribute('list', 'raw_outlier_reason_options');" in body
    # Context rows are currently config-driven; there is no dashboard override input.
    assert "const $rawOutlierContextRows = document.getElementById('raw_outlier_context_rows');" in body
    assert "$rawOutlierParamsAction" in body


def test_analysis_history_uses_event_log_and_dashboard_actions_params_button():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "const ANALYSIS_EVENT_HISTORY_KEY = 'influxbro_analysis_event_history_v1'" in body
    assert "Durchfuehrungsprotokolle" in body
    assert 'id="raw_outlier_params_action"' in body
    assert "fetch('./api/client_log'" in body
    assert "fetch('./api/analysis_history_event'" in body
    assert "await api('./api/analysis_history?limit=500'" in body
    assert "function _analysisEventHtml(entry){" in body
    assert "window.InfluxBroPopup.show('Analyse-Verlauf (' + (history.length + events.length) + ' Eintraege)', text);" in body
    assert "const htmlMode = !!(opts && opts.bodyHtml);" in tooltips
    assert "if(htmlMode) pre.innerHTML = normalizedMsg;" in tooltips


def test_analysis_cache_hit_summary_replaces_interval_hint_line():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'id="analysis_interval_info"' not in body
    assert 'dashboard_analysis.txt_interval_info' not in tooltips
    assert 'function _analysisCacheReasonSummary(plan){' in body
    assert "dirty Segment(e) lokal bereinigt" in body


def test_table_template_and_dashboard_actions_support_copy_selected_row_and_point_based_raw_context():
    table_helpers = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_table_cols.html").read_text()
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'window.InfluxBroTableRowCopy = { copySelectedRow };' in table_helpers
    assert "const text = ['...', headers.join('\\t'), cells.join('\\t'), '...'].join('\\n');" in table_helpers
    assert 'id="raw_copy_row"' in body
    assert 'id="raw_outlier_copy_row"' in body
    assert 'RAW_OUTLIER_SELECTED_TIME' in body
    assert "payload.before_limit = minPoints + 1;" in body
    assert "payload.after_limit = minPoints;" in body
    assert "payload.center_minutes = cachedWindow.center_minutes;" not in body
    assert 'dashboard_raw.btn_zeile_kopieren' in tooltips
    assert 'dashboard_outliers.btn_zeile_kopieren' in tooltips


def test_summary_actions_are_inline_in_topbar_and_back_icon_uses_return_svg():
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    config = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'margin-left: auto;' in topbar
    assert "let actions = row.querySelector(':scope > .ib_summary_actions');" in topbar
    assert 'ib_cfg_back_icon' not in config


def test_picker_supports_disabled_targets_and_angle_bracket_labels():
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'document.elementsFromPoint' in topbar
    # Picker prefers canonical pickkeys and copies <PICK:...|...>
    assert "data-ib-pickkey" in topbar
    # v=1 pick format contains pk + ik
    assert "_fmtPickV1" in topbar
    assert "v=1;pk=" in topbar
    assert "data-ib-instancekey" in topbar
    assert "Fallback:" in topbar
    assert "'(kein data-ui)'" in topbar


def test_outlier_table_rowcount_is_opt_out():
    table_helpers = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_table_cols.html").read_text()
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'data-ib-hide-rowcounts="1"' in body
    assert "tbl.getAttribute('data-ib-hide-rowcounts') === '1'" in table_helpers


def test_dashboard_load_runs_cache_path_and_stats_reload():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'async function runDashboardAnalysisFlow(){' in body
    assert 'await refreshAll({ cacheStrategy: planChoice && planChoice.cacheStrategy ? planChoice.cacheStrategy : \'default\' });' in body
    assert 'await runDashboardAnalysisFlow();' in body
    assert 'try{ await loadStats(); }catch(e){}' in body


def test_settings_layout_and_null_safe_bindings_are_present():
    config = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'details.card > summary:after' not in config
    assert 'main.content button:not(.ib_info_icon):not(.btn_sm) { width:100%; }' in config
    assert '.color_pick_row input[type="text"] { flex:1 1 auto; min-width:0; }' in config
    assert '_setVal(el.ui_filter_control_width_px' in config
    assert '_setVal(el.ui_job_color_running' in config
    assert "ui_timer_disabled_color" in config
    assert "ui_timer_disabled_opacity" in config
    assert "selector_query_limit_enabled" in config
    assert "selector_query_limit_days" in config
    assert 'window.__InfluxBroEarlyClientLogInstalled' in config
    assert 'function reportConfigError(message, extra, stack){' in config
    assert 'function _getEl(id){' in config
    assert "_safeSetById('ui_log_error_bg', 'value', cfg.ui_log_error_bg ?? '#ffe0e0');" in config
    assert "ui_log_error_bg: _getEl('ui_log_error_bg') ? String(_getEl('ui_log_error_bg').value || '').trim() : ''," in config
    assert "reportConfigError('Settings initial load failed'" in config
    assert "reportConfigError('Settings action binding failed'" in config


def test_timer_table_shows_status_column_and_disabled_style_settings():
    jobs = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "jobs.html").read_text()
    assert '--ui-timer-disabled-fg:' in jobs
    assert '--ui-timer-disabled-opacity:' in jobs
    assert 'tr.timer_disabled td {' in jobs
    assert '<th style="width: 120px;">Status</th>' in jobs
    assert "isDisabled ? 'deaktiviert' : ''" in jobs
    assert "tr.classList.add('timer_disabled');" in jobs


def test_dashboard_name_timeline_panel_and_merge_action_exist():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    selection_close_idx = body.index('</details>')
    panel_idx = body.index('<details id="name_timeline_panel" class="section"')
    caching_idx = body.index('<details id="caching_section" class="section"')
    assert selection_close_idx < panel_idx < caching_idx
    assert '<details id="name_timeline_panel" class="section"' in body
    assert '<summary><span class="ib_summary_row"><span data-ui="dashboard_selection.section_multi_name_title"' in body
    assert 'Messwertinfos von Homeassistant' in body
    assert 'id="measurement_profile_desc"' in body
    assert 'id="measurement_profile_panel"' in body
    assert 'id="measurement_profile_sections"' in body
    assert 'id="name_merge_latest_btn"' in body
    assert 'Mehrere Messwertnamen' in body
    assert 'id="name_timeline_summary"' in body
    assert 'id="name_timeline_axis"' in body
    assert 'function renderNameTimeline(rows)' in body
    assert 'function _nameTimelinePct(' in body
    assert 'function _nameTimelineBadge(' in body
    assert 'function _nameTimelineDaysText(' in body
    assert 'function _nameTimelineFmtTick(' in body
    assert 'function _nameTimelineFmtDateTime(' in body
    assert 'function _nameTimelinePickKey(' in body
    assert 'function renderMeasurementProfilePanel(profile)' in body
    assert 'async function refreshMeasurementProfilePanel()' in body
    assert './api/measurement_profile?' in body or './api/measurement_profile' in body
    assert 'class="ib-namepanel"' in body
    assert 'class="ib-namepanel-header"' in body
    assert 'class="ib-namepanel-summarybar"' in body
    assert 'class="ib-namepanel-timeline"' in body
    assert 'class="ib-namepanel-list"' in body
    assert 'class="ib-namepanel-row' in body
    assert "const rowPick = _nameTimelinePickKey(row, idx);" in body
    assert "card.setAttribute('data-ib-pickkey', rowPick);" in body
    assert "card.setAttribute('data-ib-instancekey', rowPick);" in body
    assert '$nameTimelinePanel.open = true;' in body
    assert '$nameTimelinePanel.open = false;' in body
    assert 'function mergeFriendlyNamesToLatest()' in body
    assert './api/friendly_name_merge_latest' in body


def test_audit_page_and_nav_entry_exist():
    audit = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "audit.html").read_text()
    nav = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_nav.html").read_text()
    assert 'data-ui="audit_page.main"' in audit
    assert 'id="profile_id"' in audit
    assert 'id="export_json"' in audit
    assert 'id="export_csv"' in audit
    assert './api/audit?' in audit
    assert 'data-ui="nav_main.panel_audit"' in nav


def test_dashboard_abort_buttons_and_search_width_are_updated():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'id="cancel_load"' in body
    assert 'aria-label="Laufende Dashboard-Abfrage abbrechen">Laden abbrechen</button>' in body
    assert 'flex:1 1 140px; min-width:110px; max-width:320px;' in topbar


def test_navigation_helper_controls_and_config_exist():
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    nav = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_nav.html").read_text()
    config = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'id="ib_nav_back"' in topbar
    assert 'id="ib_nav_forward"' in topbar
    assert 'id="ib_param_help_toggle"' in topbar
    assert 'const NAV_HISTORY_KEY = ' in topbar
    assert 'const PARAM_LINKS = {' in topbar
    assert "sessionStorage.setItem('influxbro_nav_context_v1'" in nav
    assert 'function _pendingNavContext(){' in topbar
    assert 'keepalive: true,' in topbar
    assert 'pending_nav: pendingNav,' in topbar
    assert 'ui_nav_helper_history_limit' in config
    assert 'ui_nav_helper_highlight_color' in config
    assert 'ui_nav_helper_highlight_duration_ms' in config


def test_navigation_helper_uses_pending_target_and_html_badges():
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'const NAV_PENDING_KEY = ' in topbar
    assert 'function _consumePendingNav(){' in topbar
    assert 'function _renderParamHelpBadges(){' in topbar
    assert 'ib_param_hint_badge' in topbar
    assert "_navigateToEntry(entry);" in topbar


def test_settings_restructure_script_and_general_navigation_params_exist():
    config = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'function restructureSettings(){' in config
    assert "_cfgMakeSection('Datenbank', 'settings.section.database'" in config
    assert "_cfgMakeSection('Allgemein', 'settings.section.general'" in config
    assert 'ui_nav_helper_history_limit' in config
    assert 'ui_nav_helper_highlight_color' in config
    assert 'ui_nav_helper_highlight_duration_ms' in config
    assert "_cfgLinkRow('Globale Darstellung & Auswahl', '#ui_gui_body_px')" in config


def test_dashboard_raw_actions_and_titles_are_updated():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'Grafische Analyse' in body
    assert 'Raw Daten Analyse' in body
    assert 'id="raw_delete"' in body
    assert 'id="raw_undo"' in body
    assert 'data-ui="dashboard_raw.row_actions_smart"' in body
    assert 'id="raw_linear_range"' in body
    assert 'id="raw_copy_first_range"' in body
    assert 'id="raw_info_btn"' in body
    assert '>Änderung<' in body


def test_dashboard_graph_refresh_uses_refresh_all_with_status():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'id="graph_refresh"' in body
    assert 'refreshAllWithStatus()' in body


def test_popup_copy_icon_and_font_setting_are_present():
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    config = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    app_py = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert 'stroke="#1C274C"' in tooltips
    assert 'ui_popup_pre_font_px' in tooltips
    assert 'ui_popup_history_font_px' in tooltips
    assert 'Popup-Text und Query-History folgen jetzt der Schriftgroesse aus "GUI Gruppe 4: Meta / Hilfetext".' in config
    assert 'ui_popup_pre_font_px' in app_py
    assert 'ui_popup_history_font_px' in app_py


def test_query_history_uses_existing_popup_history_area():
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "let _openHistoryInPopup = ()=>{};" in tooltips
    assert "_openHistoryInPopup = function(scope){" in tooltips
    assert "autoOpenHistory: true" in tooltips
    assert "forceHistoryVisible: !!o.scope" in tooltips
    assert "if(CURRENT_HISTORY_SCOPE && opts && (opts.autoOpenHistory || opts.forceHistoryVisible)){" in tooltips
    assert "influxbro_popup_history_search" in tooltips
    assert "influxbro_popup_history_wrap" in tooltips
    assert "influxbro_popup_history_client_time" in tooltips
    assert "influxbro_popup_history_pre" in tooltips
    assert "HISTORY_WRAP_KEY = 'influxbro.popup.history.wrap.v1'" in tooltips
    assert "HISTORY_CLIENT_TIME_KEY = 'influxbro.popup.history.client_time.v1'" in tooltips
    assert "window.InfluxBroPopup.show('Query History', 'Wähle unten einen History-Eintrag aus.'" in tooltips or "window.InfluxBroPopup.show('Query History', 'Waehle unten einen History-Eintrag aus.'" in tooltips


def test_popup_search_uses_current_visible_text():
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'CURRENT_POPUP_VISIBLE_TEXT' in tooltips


def test_dashboard_raw_query_button_and_query_history_metadata_exist():
    index_html = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'id="raw_query_open"' in index_html
    assert "'dashboard.load'" in index_html
    assert "trigger_program: 'raw load'" in index_html
    assert "trigger_program: 'edit graph refresh'" in index_html


def test_raw_history_summary_endpoint_and_trigger_metadata_exist():
    app_py = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert '@app.post("/api/raw_history_summary")' in app_py
    assert '"trigger_page": trigger_page' in app_py
    assert '"trigger_source": trigger_source' in app_py
    assert '"trigger_button": trigger_button' in app_py


def test_popup_remains_mouse_resizable():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "document.createElement('dialog')" in body
    assert "root.showModal()" in body
    assert "card.style.resize = 'both';" in body


def test_query_logging_covers_selector_and_backup_routes():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert 'log_query("api.measurements (flux)", q)' in body
    assert 'log_query("api.fields (flux)", q)' in body
    assert 'log_query("api.tag_values (flux)", q)' in body
    assert 'log_query("api.resolve_signal (flux)", q)' in body
    assert 'log_query("api.backup_create (flux)", q)' in body
    assert 'log_query("api.backup_create_range (flux)", q)' in body
    assert 'log_query(f"backup.job {backup_kind} (flux)", q)' in body


def test_stats_page_uses_finish_status_and_shared_table_height_helper():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "stats.html").read_text()
    assert 'function finishStatus(lines)' in body
    assert "$tblResize.classList.add('ib_tbl_resize');" in body
    assert "window.InfluxBroTableHeight.attach($tblBox, 'tbl', {minPx: 160})" in body
    assert '$influxDbRefresh' not in body


def test_stats_backend_can_short_circuit_fresh_cache_hits():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert 'def _global_stats_start_cached_job(' in body
    assert 'cache_hit": True' in body
    assert 'def _stats_cache_append_supported(range_key: str) -> bool:' in body
    assert 'def _stats_cache_merge_rows(base_rows: list[dict[str, Any]], delta_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:' in body
    assert '"covered_start": str(j.get("cache_merge_start") or start),' in body
    assert '"covered_stop": stop,' in body
    assert 'cache_append": True' in body
    assert 'cache_prefill": bool(stale_prefill)' in body


def test_stats_ui_can_show_cache_prefill_while_background_job_runs():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "stats.html").read_text()
    assert 'async function tryLoadPrefillCache(cacheId)' in body
    assert "if(job && job.cache_prefill && job.cache_id) await tryLoadPrefillCache(job.cache_id);" in body
    assert "setStatus([`Cache-Vorabansicht geladen. Zeilen: ${ROWS.length}${spanTxt}`" in body


def test_stats_backend_reuses_cached_series_for_stale_prefill_rebuilds():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert '"cache_discover_after": str(cache_discover_after or "").strip() or None,' in body
    assert 'stale_seed_series = [' in body
    assert 'set_state("query", "Ergaenze Serienliste aus Cache-Fortsetzung...")' in body
    assert 'stale_seed_series or series_list' in body


def test_stats_backend_supports_sliding_trim_append_updates():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert 'def _stats_cache_sliding_supported(range_key: str) -> bool:' in body
    assert 'def _stats_cache_discover_series_span(' in body
    assert 'meta["dirty_reason"] = "sliding_trim_append"' in body
    assert 'return jsonify({"ok": True, "job_id": job_id, "cache_id": cache_id, "cache_slide": True, "cache_prefill": True})' in body


def test_import_analyze_shows_success_and_error_popups():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "import.html").read_text()
    assert "window.InfluxBroPopup.show('Import Analyse erfolgreich', msg);" in body
    assert "window.InfluxBroPopup.show('Import Analyse Fehler', msg);" in body
    assert 'id="cnt_src_measurement"' in body
    assert 'id="cnt_src_field"' in body
    assert 'function updateImportActionState()' in body


def test_logs_page_has_collapsible_title_and_short_button_texts():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "logs.html").read_text()
    assert 'data-ui="logs_page.section_root"' in body
    assert '<span style="margin-left:6px;">Neu</span>' in body
    assert '<span style="margin-left:6px;">Report</span>' in body


def test_timer_table_uses_mode_button_in_action_column():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "jobs.html").read_text()
    assert 'id="timers_mode_btn"' in body
    assert 'const TIMER_MODE_UI = {};' in body
    assert "modeText.textContent = currentModeText();" in body


def test_jobs_and_cache_tables_use_selection_toolbar_actions():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "jobs.html").read_text()
    assert 'id="jobs_details_btn"' in body
    assert 'id="cache_info_btn"' in body
    assert "SELECTED_JOB_ID" in body
    assert "SELECTED_CACHE_ID" in body
    assert "tr.setAttribute('data-job-id', id);" in body
    assert "tr.setAttribute('data-cache-id', cid);" in body
    assert 'id="jobs_details_btn"' in body
    assert 'id="cache_info_btn"' in body
    assert 'id="timers_mode_btn"' in body


def test_jobs_page_has_analysis_cache_section_and_actions():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "jobs.html").read_text()
    assert 'data-ui="jobs_analysis_cache.section_root"' in body
    assert 'id="analysis_cache_tbl"' in body
    assert 'id="analysis_cache_rebuild_btn"' in body
    assert 'id="analysis_cache_delete_btn"' in body
    assert '<option value="analysis_cache_patch">analysis_cache_patch</option>' in body
    assert "Patch pending:" in body
    assert "patch_failed_count" in body
    assert "Checkpoint:" in body
    assert "last_patch_mode" in body or "Modus:" in body
    assert "./api/analysis_cache/list" in body
    assert "./api/analysis_cache/rebuild" in body
    assert "./api/analysis_cache/delete" in body


def test_dashboard_issue219_analysis_controls_and_limits_exist():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    app_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert 'data-ui="dashboard_caching.section_root"' in body
    assert 'id="analysis_start_info"' in body
    assert 'id="analysis_run_with_cache"' in body
    assert 'id="analysis_run_without_cache"' in body
    # Type selection lives in the outliers section (Issue #362)
    assert 'id="analysis_types_selected"' in body
    assert 'dashboard_outliers.row_types' in body
    assert 'function getDisplayedOutliers()' in body
    assert 'function aggregateFaultPhaseRows(rows)' in body
    assert 'for(let i = rows.length; i < 5; i++){' in body
    assert 'for(let i = filtered.length; i < 5; i++){' in body
    assert 'ui_raw_outlier_display_limit_per_type' in config_body
    assert '"ui_raw_outlier_display_limit_per_type": 100' in app_body


def test_dashboard_caching_section_has_visible_cache_targets_and_no_old_dialog():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'id="analysis_cache_box"' in body
    assert 'id="analysis_confirm_cache_summary"' in body
    assert 'id="analysis_confirm_cache_timeline"' in body
    assert 'id="analysis_confirm_cache_changes"' in body
    assert 'id="analysis_confirm_dialog"' not in body


def test_dashboard_cache_restore_renders_timeline_and_changes_from_restored_plan():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    # Hybrid restore (#347) must restore not only the summary HTML but also
    # re-render timeline + changes from the restored plan (no extra server hit).
    assert "function cacheRestoreIfAvailable()" in body
    assert "document.getElementById('analysis_confirm_cache_timeline')" in body
    assert "document.getElementById('analysis_confirm_cache_changes')" in body
    assert "_analysisCacheTimelineHtml(plan)" in body
    assert "(plan && Array.isArray(plan.changes)) ? plan.changes.slice(0, 8)" in body


def test_dashboard_caching_section_has_info_button_timeline_labels_and_summary_actions():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert '<div class="ib_summary_actions"><button type="button" class="ib_info_icon" id="caching_summary_info"' in body
    assert 'id="caching_changed_info"' in body
    assert 'function showCachingSummaryInfo()' in body
    assert 'fmtTs(req.start)' in body and 'fmtTs(req.stop)' in body


def test_cache_timeline_hidden_color_and_jobs_analysis_table_features_exist():
    index_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    jobs_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "jobs.html").read_text()
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    app_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert 'ANALYSIS_CACHE_SEGMENT_COLORS' in index_body
    assert 'ui_analysis_cache_hidden_color' in config_body
    assert 'ui_analysis_cache_hidden_color' in app_body
    assert 'data-cache-hl=' in index_body
    assert 'data-cache-ac=' in index_body
    assert 'id="analysis_cache_autowidth"' in jobs_body
    assert 'id="analysis_cache_windowwidth"' in jobs_body
    assert 'id="analysis_cache_wrap"' in jobs_body
    assert 'id="analysis_cache_colfilter"' in jobs_body
    assert '>Pfad<' in jobs_body


def test_dashboard_cache_timeline_has_hl_ac_toggles_and_combine_buttons():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'id="analysis_cache_combine"' in body
    assert 'id="analysis_cache_delete_series"' in body
    assert 'data-cache-hl=' in body
    assert 'data-cache-ac=' in body
    assert 'async function combineAnalysisCacheForCurrentSelection(' in body
    assert 'function deleteAnalysisCacheForCurrentSelection()' in body
    assert '>Messwertauswahl<' in body
    assert '>Messwert Cache Analyse<' in body
    assert 'data-cache-ol=' in body
    assert 'data-cache-oltype=' in body
    assert 'gap|' in body
    assert 'cursor:not-allowed' in body
    assert 'cached_outlier_type_counts' in body
    assert 'data-ib-pickkey="dashboard.cache_timeline.btn_hl.' in body
    assert 'data-ib-pickkey="dashboard.cache_timeline.btn_ac.' in body
    assert 'data-ib-pickkey="dashboard.cache_timeline.btn_ol.' in body
    assert 'data-ib-pickkey="dashboard.cache_timeline.btn_info.' in body
    assert 'data-ib-itemkey="' in body


def test_dashboard_caching_panel_has_logs_button_progress_and_range_details():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    agents = (Path(__file__).resolve().parents[1] / "AGENTS.md").read_text()
    assert 'id="caching_logs_open"' in body
    assert 'id="load_progress_fill"' in body
    assert 'id="load_progress_text"' in body
    assert "const LOAD_STEP_ORDER = ['start', 'dash_plan', 'analysis_plan', 'areas', 'result'];" in body
    assert 'function _formatCachePlanRanges(gaps, dirtyRanges){' in body
    assert "openFilteredAnalysisLogsDialog('dashboard_caching', 'cache_check')" in body
    assert 'dashboard_caching.btn_logs' in tooltips
    assert 'scope: \'dashboard_caching\'' in body
    assert "curl -s -H \"Authorization: Bearer $SUPERVISOR_TOKEN\" http://192.168.2.200:8123/api/config | jq -r '.version'" in agents
    assert 'unknown` ist nur als Fallback erlaubt' in agents
    assert 'data-ib-pickkey' in agents
    assert 'data-ib-instancekey' in agents
    assert 'v=1;pk=' in agents


def test_dashboard_flow_checklist_controls_persist_and_use_explicit_pickkeys():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'const FLOW_UI_KEY_PREFIX = "influxbro_flow_ui_v1:";' in body
    assert 'if(!window.__IB_FLOW_UI[id]) window.__IB_FLOW_UI[id] = _loadFlowUiState(id);' in body
    assert "const fallbackStepKey = key || ('step_' + String(stepIdx + 1));" in body
    assert "btnToggle.setAttribute('data-ui', id + '.btn_toggle_all');" in body
    assert "btnErr.setAttribute('data-ui', id + '.btn_only_errors');" in body
    assert "row.setAttribute('data-ib-pickkey', flowPickBase + '.row_step.' + keyPick);" in body
    assert "det.setAttribute('data-ib-pickkey', flowPickBase + '.panel_step_details.' + keyPick);" in body
    assert '_saveFlowUiState(id, ui);' in body


def test_dialog_actions_use_bottom_right_footer_and_explicit_pickkeys():
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    export_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "export.html").read_text()
    assert 'display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;' in config_body
    assert 'data-ui="config_test_success.btn_ok" data-ib-pickkey="config_test_success.btn_ok"' in config_body
    assert 'class="actions"' in export_body
    assert 'data-ui="export_target.btn_close" data-ib-pickkey="export_target.btn_close"' in export_body
    assert 'data-ui="export_target.btn_cancel" data-ib-pickkey="export_target.btn_cancel"' in export_body
    assert 'data-ui="export_target.btn_ok" data-ib-pickkey="export_target.btn_ok"' in export_body


def test_dialogs_expose_superpicker_and_footer_normalizer():
    index_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    logs_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "logs.html").read_text()
    dq_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "dq.html").read_text()
    jobs_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "jobs.html").read_text()
    topbar_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    tooltips_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'data-dialog-root="1"' in index_body
    assert 'data-open-superpicker="1"' in index_body
    assert 'data-ui="config_icon_svg.btn_superpicker"' in config_body
    assert 'data-ui="logs_support_bundle.btn_superpicker"' in logs_body
    assert 'data-ui="dq_detail.btn_superpicker"' in dq_body
    assert 'data-ui="jobs_timers_history.btn_superpicker"' in jobs_body
    assert 'window.InfluxBroOpenSuperpickerFromDialog = function(dialogRoot)' in topbar_body
    assert "btn.closest('[data-dialog-root=\"1\"], dialog, [role=\"dialog\"], .dlg_backdrop, .modal')" in topbar_body
    assert "_ensureDialogFooter('#ib_page_search_modal', '#ib_page_search_modal_close');" in topbar_body
    assert "_ensureDialogFooter('#analysis_log_modal', '#analysis_log_modal_close'" in topbar_body
    assert 'data-ui="docs_modal.btn_superpicker"' in tooltips_body
    assert 'data-ui="issue_composer.btn_superpicker"' in tooltips_body


def test_dashboard_outlier_params_dialog_is_global_config_based():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert "./api/config_defaults" in body
    assert "outlier_recovery_valid_streak_default" in body
    assert "outlier_bounds_min_default" in body
    assert "localStorage.getItem('raw_outlier_params')" not in body
    assert "localStorage.setItem('raw_outlier_params'" not in body


def test_analysis_does_not_refresh_caching_section_ui():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert "prepare_cache_check" not in body
    assert "combineAnalysisCacheForCurrentSelection({silent: true})" in body


def test_analysis_has_separate_raw_windows_step_and_does_not_compute_windows_inside_raw_search():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert "raw_windows" in body
    assert "Raw-Fenster berechnen" in body
    # Raw search function should not call _ensureOutlierWindows anymore.
    raw_search_pos = body.find("async function runRawOutlierSearchWithProgress")
    assert raw_search_pos >= 0
    tail = body[raw_search_pos: raw_search_pos + 120000]
    assert "_ensureOutlierWindows" not in tail


def test_dashboard_caching_status_panel_is_always_visible_and_has_text_fields():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'data-ui="dashboard_caching.panel_status"' in body
    assert 'id="load_status_txt"' in body
    assert 'id="load_status_time"' in body
    assert 'align-items: flex-start' in body
    assert 'text-align: left' in body
    assert '$loadStatus.style.display = "none"' not in body
    assert 'if($loadStatus) $loadStatus.style.display = "none"' not in body


def test_global_unhandledrejection_suppresses_tabs_outgoing_ready_noise():
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert "No Listener: tabs:outgoing.message.ready" in topbar
    assert "preventDefault" in topbar


def test_dashboard_uses_structured_data_ui_naming_scheme_samples():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    tmpl = (Path(__file__).resolve().parents[1] / "influxbro" / "Template.md").read_text()
    assert 'data-ui="dashboard_caching.btn_cache_pruefen"' in body
    assert 'data-ui="dashboard_analysis.btn_analyse_mit_cache"' in body
    assert 'data-ui="dashboard_outliers.tbl_ausreisser"' in body
    assert 'data-ui="dashboard_raw.tbl_rohdaten"' in body
    assert 'data-ui="dashboard_graph.btn_aktualisieren"' in body
    assert 'data-ui="dashboard_selection.section_root"' in body
    assert '`page_section.role_action`' in tmpl
    assert 'data-ib-pickkey' in tmpl
    assert '<PICK:' in tmpl


def test_dashboard_static_sections_pair_data_ui_with_explicit_pickkeys():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'data-ui="dashboard_page.main" data-ib-pickkey="dashboard_page.main"' in body
    assert 'data-ui="dashboard_selection.section_root" data-ib-pickkey="dashboard_selection.section_root"' in body
    assert 'data-ui="dashboard_selection.input_measurement_filter_value" data-ib-pickkey="dashboard_selection.input_measurement_filter_value"' in body
    assert 'data-ui="dashboard_caching.btn_cache_pruefen" data-ib-pickkey="dashboard_caching.btn_cache_pruefen"' in body
    assert 'data-ui="dashboard_caching.panel_query_details" data-ib-pickkey="dashboard_caching.panel_query_details"' in body
    assert 'data-ui="dashboard_analysis.btn_analyse_mit_cache" data-ib-pickkey="dashboard_analysis.btn_analyse_mit_cache"' in body
    assert 'data-ui="dashboard_analysis.panel_checklist" data-ib-pickkey="dashboard_analysis.panel_checklist"' in body
    assert 'data-ui="dashboard_outliers.tbl_ausreisser" data-ib-pickkey="dashboard_outliers.tbl_ausreisser"' in body
    assert 'data-ui="dashboard_raw.btn_kopieren" data-ib-pickkey="dashboard_raw.btn_kopieren"' in body
    assert 'data-ui="dashboard_raw.tbl_rohdaten" data-ib-pickkey="dashboard_raw.tbl_rohdaten"' in body
    assert 'data-ui="dashboard_graph.btn_aktualisieren" data-ib-pickkey="dashboard_graph.btn_aktualisieren"' in body
    assert 'data-ui="dashboard_graph.panel_query" data-ib-pickkey="dashboard_graph.panel_query"' in body
    assert 'data-ui="dashboard_graph.handle_resize" data-ib-pickkey="dashboard_graph.handle_resize"' in body


def test_dashboard_raw_graph_context_tooltip_uses_full_point_info():
    app_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    index_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert '"time_full": _dt_to_rfc3339_utc_full(ts.astimezone(timezone.utc))' in app_body
    assert '"measurement": measurement' in app_body
    assert '"field": field' in app_body
    assert '"entity_id": entity_id' in app_body
    assert '"friendly_name": friendly_name' in app_body
    assert 'function _graphCtxHoverText(point, aggName)' in index_body
    assert "parts.push('Measurement: ' + String(p.measurement));" in index_body
    assert "parts.push('Field: ' + String(p.field));" in index_body
    assert "parts.push('entity_id: ' + String(p.entity_id));" in index_body
    assert "parts.push('friendly_name: ' + String(p.friendly_name));" in index_body
    assert "hovertemplate: '%{text}<extra></extra>'" in index_body


def test_stats_uses_shared_measurement_selection_template():
    stats_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "stats.html").read_text()
    shared_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_measurement_selection.html").read_text()
    template_md = (Path(__file__).resolve().parents[1] / "influxbro" / "Template.md").read_text()
    assert "{% include '_measurement_selection.html' %}" in stats_body
    assert "sel_root_ui = 'stats_selection.section_root'" in stats_body
    assert '## Measurement Selection' in template_md
    assert 'Das Dashboard ist das Referenzlayout.' in template_md
    assert 'sel_section_id' in shared_body


def test_dashboard_raw_action_bars_follow_two_row_layout_and_refresh_keeps_window():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    template_md = (Path(__file__).resolve().parents[1] / "influxbro" / "Template.md").read_text()
    assert 'data-ui="dashboard_raw.row_customer_actions" data-ib-pickkey="dashboard_raw.row_customer_actions"' in body
    assert '>Abbruch</button>' in body
    assert '>Reparatur-Assistent</button>' in body
    assert '>Automatikkorrektur</button>' in body
    assert 'aria-label="Raw-Zeile kopieren">Zeile kopieren</button>' in body
    assert 'loadRawFromGraph(false).then(()=>' in body
    assert 'const disabled = !hasRows || _RAW_INFLIGHT;' in body
    assert 'Standard Actions' in template_md
    assert 'Customer Actions' in template_md


def test_all_template_data_ui_literals_have_explicit_pickkeys():
    templates_dir = Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates"
    missing = []
    for template_path in sorted(templates_dir.glob("*.html")):
        for line_no, line in enumerate(template_path.read_text().splitlines(), 1):
            if 'data-ui="' in line and 'data-ib-pickkey="' not in line:
                missing.append(f"{template_path.name}:{line_no}")
    assert missing == []


def test_dashboard_issue223_removed_tip_selection_and_moved_start_info():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'data-ui="tip.selection"' not in body
    assert 'id="analysis_start_info" class="muted"' in body
    assert 'const preloadSegments = Array.isArray(serverPlan && serverPlan.segments) ? serverPlan.segments : [];' in body


def test_dashboard_cache_analysis_keeps_preloaded_results_before_search():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'const preloadSegments = Array.isArray(serverPlan && serverPlan.segments) ? serverPlan.segments : [];' in body
    assert 'RAW_OUTLIER_RESULTS = [];' in body  # initial reset exists
    assert 'startRawOutlierUi(baseMeta);\n  RAW_OUTLIER_SEARCHING = true;\n  RAW_OUTLIER_INDEX = -1;' in body
    assert 'startRawOutlierUi(baseMeta);\n  RAW_OUTLIER_SEARCHING = true;\n  RAW_OUTLIER_RESULTS = [];' not in body


def test_non_dashboard_pages_use_structured_data_ui_samples():
    jobs = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "jobs.html").read_text()
    config = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    stats = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "stats.html").read_text()
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'data-ui="jobs_main.btn_refresh"' in jobs
    assert 'data-ui="jobs_cache.tbl_table"' in jobs
    assert 'data-ui="config_settings.panel_autosave"' in config
    assert 'data-ui="config_settings.chk_dash_cache_enabled"' in config
    assert 'data-ui="stats_main.btn_load"' in stats
    assert 'data-ui="stats_table.panel_wrap"' in stats
    assert 'data-ui="nav_main.btn_ui_picker"' in topbar


def test_settings_outliers_table_has_add_delete_buttons_and_tooltips():
    config = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'id="outliers_add_row"' in config
    assert 'id="outliers_delete_row"' in config
    assert 'settings.outliers.add_row' in tooltips
    assert 'settings.outliers.delete_row' in tooltips
    assert 'settings.outliers.windowfit' in tooltips


def test_nav_includes_performance_page_link():
    nav = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_nav.html").read_text()
    assert 'href="./performance"' in nav
    assert 'data-ui="nav_main.panel_performance"' in nav


def test_settings_has_tracing_controls():
    config = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'id="trace_enabled"' in config
    assert 'id="trace_persist"' in config
    assert 'id="trace_max_entries"' in config


def test_stats_page_clears_expired_last_job_ids_before_cache_fallback():
    stats = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "stats.html").read_text()
    assert 'function clearLastJobIds()' in stats
    assert "Stored global_stats job expired, falling back to cache/snapshot" in stats
    assert 'Vorheriger Statistik-Job abgelaufen, Cache wird geladen.' in stats


def test_tooltip_template_uses_short_description_plus_key_and_mentions_picker_suppression():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    tmpl = (Path(__file__).resolve().parents[1] / "influxbro" / "Template.md").read_text()
    assert "return (t ? (t + '\\n' + suffix) : suffix);" in body
    assert 'base = _short(base, 110);' in body
    assert 'Tooltips must not be shown while `Picker` or `S-Picker` is active' in tmpl


def test_dashboard_cache_summary_lists_type_counts_and_has_outlier_toggle():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'cached_outlier_type_counts' in body
    assert 'Gefunden: Counter:' in body
    assert 'data-cache-ol=' in body


def test_dashboard_issue235_controls_exist():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'combineAnalysisCacheForCurrentSelection({silent: true})' in body
    assert 'id="outlier_ignore"' in body
    assert 'id="outlier_unignore"' in body
    assert 'Format: alle sichtbaren Spalten als TSV' in body


def test_dashboard_and_settings_expose_gap_outlier_controls():
    index_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    app_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert "{value: 'gap', label: 'Messwertlücke'}" in index_body
    assert 'id="raw_param_gap_seconds"' in index_body
    assert 'Messwertlücke' in index_body
    assert 'id="outlier_gap_seconds_default"' in config_body
    assert '"outlier_gap_seconds_default": 300' in app_body
    assert 'checklist_icon" style="background:#eef2ff;color:#5d86d6;">i</span>' in index_body


def test_picker_suppresses_titles_and_handles_disabled_elements_via_mousedown():
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'function suppressTitles()' in topbar
    assert 'function restoreTitles()' in topbar
    assert "document.addEventListener('mousedown', onMouseDown, true);" in topbar
    assert 'async function _copyCurrentTarget(target, ev)' in topbar


def test_table_helpers_strip_ingress_token_from_storage_keys():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_table_cols.html").read_text()
    assert "replace(/\\/api\\/hassio_ingress\\/[0-9a-fA-F]+/g, '')" in body


def test_history_and_restore_sections_are_collapsible():
    history = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "history.html").read_text()
    restore = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "restore.html").read_text()
    backup = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "backup.html").read_text()
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'data-ui="history_page.section_root"' in history
    assert 'title="restore.source"' in restore and 'title="restore.target"' in restore
    assert 'id="space" data-ui="backup_main.panel_space" title="backup.space"' in backup
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


def test_page_search_supports_direct_pick_string_input():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'function _parsePickString' in body
    assert 'function _handlePickInput' in body
    assert 'Page-Mismatch' in body
    assert 'data-ib-instancekey' in body


def test_dashboard_field_label_has_count_span():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert '<span id="cnt_field" class="muted"></span>' in body


def test_dashboard_issue137_modal_and_toolbar_updates():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'function _countDecimals(s)' in body
    assert 'function confirmRawOverwrite(sourceRow, targetRow)' in body
    assert 'id="stats_current_open"' not in body
    # Toolbar elements may be conditionally rendered; keep test stable by checking the JS bindings.
    assert "document.getElementById('edit_toolbar_overwrite')" in body
    assert "document.getElementById('edit_toolbar_apply_one')" in body
    assert 'id="raw_refresh"' in body
    assert 'id="raw_query_open"' in body
    assert 'id="raw_query_section"' not in body
    assert 'id="err" class="err"' not in body
    assert 'id="ok" class="ok"' not in body
    assert 'data-ui="tip.stats_total"' not in body


def test_dashboard_uses_outlier_visible_rows_setting_and_no_stats_current_toggle():
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    index_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    app_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert 'id="ui_outlier_visible_rows"' in config_body
    assert 'ui_open_stats_current' not in config_body
    assert 'let UI_OUTLIER_VISIBLE_ROWS = 10;' in index_body
    assert 'function applyFilterTableVisibleRows()' in index_body
    assert '"ui_outlier_visible_rows": 10,' in app_body


def test_dashboard_reloads_graph_and_outliers_after_data_mutation():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert 'async function refreshAfterDataMutation(opts)' in body
    assert 'await refreshAfterDataMutation({ rerunOutliers: true });' in body


def test_dashboard_tables_use_shared_height_resizers():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert "window.InfluxBroTableHeight.attach($tableBox, 'tbl', {minPx: 180})" in body
    assert "window.InfluxBroTableHeight.attach($detailsBox, 'details_box', {minPx: 180})" in body


def test_quality_page_exists_with_tabs_and_cleanup_actions(load_app_module, tmp_path):
    app_mod = load_app_module(config_dir=tmp_path / "config", data_dir=tmp_path / "data")
    client = app_mod.app.test_client()
    r = client.get('/quality')
    text = r.get_data(as_text=True)
    assert r.status_code == 200
    assert 'Datenqualitaet & Langzeitdaten' in text
    assert 'quality.tab.cleanup' in text
    assert 'quality_buckets_apply' in text
    assert 'quality_tasks_apply' in text
    assert 'id="cleanup_run"' in text


def test_quality_nav_and_material_button_tokens_exist():
    nav = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_nav.html").read_text()
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert 'href="./quality"' in nav
    assert '--ib-btn-bg: #eef3ff;' in topbar
    assert 'body button {' in topbar
    assert 'border-radius: 999px;' in topbar


def test_topbar_uses_separate_pagecard_min_and_live_heights():
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert '--ib-pagecard-min-h: 74px;' in topbar
    assert '--ib-pagecard-live-h: 74px;' in topbar
    assert 'padding-top: calc(env(safe-area-inset-top, 0px) + var(--ib-topbar-h) + var(--ib-pagecard-live-h));' in topbar
    assert 'min-height: var(--ib-pagecard-min-h);' in topbar
    assert "pc.style.minHeight = 'var(--ib-pagecard-min-h)';" in topbar
    assert "document.documentElement.style.setProperty('--ib-pagecard-live-h'" in topbar
    assert 'window.InfluxBroTopbarLayout = { update: _scheduleTopbarHeightUpdate };' in topbar


def test_picker_supports_superpicker_fallback_mode():
    topbar = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert "id=\"ui_superpicker_toggle\"" in topbar
    # UI switched to icon-only buttons (aria-label is the stable text anchor).
    assert 'aria-label="S-Picker"' in topbar
    assert "const LS_SUPER = 'influxbro.ui_picker.super.v1';" in topbar
    assert "if(el && el.nodeType === Node.TEXT_NODE) el = el.parentElement;" in topbar
    assert "if(readSuper()){" in topbar
    assert "if(ui) return { el, name: ui, kind: 'data-ui' };" in topbar
    assert "function _fallbackTextSnippetFor(el){" in topbar
    assert "const css = _fallbackCssFor(el);" in topbar
    assert "kind: 'fallback'" in topbar
    assert "target.kind === 'pickkey'" in topbar
    assert "fallback:" in topbar
    assert "badge.textContent = display;" in topbar
    assert "if(readSuper()){ if($superBtn) $superBtn.classList.add('active');" in topbar


def test_global_button_logging_and_button_error_reporting_exist():
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'window.InfluxBroDecodeInfoText' in tooltips
    assert 'if(window.InfluxBroButtons) return;' in tooltips
    assert "document.addEventListener('click', (ev)=>{" in tooltips
    assert "_log('button_press', btn, { pointer: 'click' });" in tooltips
    assert "reportError(err, 'button.click', btn, { async: false });" in tooltips
    assert "window.InfluxBroButtons = { log: _log, reportError };" in tooltips


def test_tooltips_use_custom_html_tooltip_layer():
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "ib_html_tooltip" in tooltips
    assert "HTML custom tooltip" in tooltips


def test_popup_uses_global_decode_helper_for_query_and_meta_texts():
    tooltips = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "window.InfluxBroDecodeInfoText ? window.InfluxBroDecodeInfoText(String(msg || '')) : String(msg || '')" in tooltips
    assert "window.InfluxBroDecodeInfoText ? window.InfluxBroDecodeInfoText(String(opts && opts.meta ? opts.meta : ''))" in tooltips
    assert "historyBox.id = 'influxbro_popup_history';" in tooltips
    assert "split.id = 'influxbro_popup_split';" in tooltips
    assert "root.addEventListener('click'" not in tooltips
    assert "onClick: ()=>{ try{ _renderHistory(String(o.scope)); }catch(e){} }," in tooltips
    assert "window.InfluxBroQueryHistory = { add, show, list };" in tooltips


def test_table_sort_parses_de_datetime_format():
    tbl = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_table_cols.html").read_text()
    assert "de-DE datetime" in tbl
    assert "dd.mm.yyyy" in tbl
    assert r"(\d{2})\.(\d{2})\.(\d{4})" in tbl


def test_dashboard_query_and_stats_buttons_report_dialog_errors_instead_of_swallowing():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    assert "throw new Error('Dialogsystem fuer Dashboard Query ist nicht verfuegbar');" in body
    assert "window.InfluxBroButtons.reportError(e, 'dashboard.query_details', $dashboardQueryOpen);" in body
    assert "throw new Error('Dialogsystem fuer Gesamtstatistik ist nicht verfuegbar');" in body
    assert "window.InfluxBroButtons.reportError(e, 'section.stats_total', $statsTotalOpen);" in body


def test_template_requires_standard_checkbox_scale_for_toolbar_checkboxes():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "Template.md").read_text()
    assert 'Checkbox size must stay consistent across pages and topbars.' in body
    assert 'Preferred pattern: add class `row_sel` to the checkbox' in body
    assert 'must always return to the smallest height that still fully shows all currently visible controls.' in body
    assert 'Modales Fenster / Query Fenster' in body
    assert 'Sie duerfen sich nicht automatisch schliessen' in body
    assert 'horizontalen Hoehen-Splitter' in body


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


def test_settings_iconbilder_section_exists():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'id="ui_iconbilder"' in body
    assert 'id="icons_tbl"' in body
    assert 'id="icons_edit"' in body
    assert 'id="icons_undo"' in body
    assert 'id="icons_jump"' in body
    assert 'id="icon_svg_modal"' in body
    assert "initIconbilder" in body


def test_tooltips_expose_icon_override_apply_hook():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert "window.InfluxBroApplyIconOverrides" in body
    assert "fetch('./api/icon_svg')" in body


def test_api_icon_svg_sanitizes_and_persists(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    # Start empty
    r = client.get("/api/icon_svg")
    assert r.status_code == 200
    assert r.get_json()["ok"] is True
    assert r.get_json()["items"] == {}

    svg = '<svg viewBox="0 0 24 24" onload="alert(1)"><script>alert(1)</script><path d="M4 7h16" fill="none" stroke="currentColor" stroke-width="2"/></svg>'
    r = client.post("/api/icon_svg/set", json={"key": "dashboard_raw.btn_kopieren", "svg": svg})
    assert r.status_code == 200
    assert r.get_json()["ok"] is True

    r = client.get("/api/icon_svg")
    j = r.get_json()
    assert j["ok"] is True
    saved = j["items"]["dashboard_raw.btn_kopieren"]
    assert "script" not in saved.lower()
    assert "onload" not in saved.lower()
    assert "<svg" in saved.lower()
    assert "<path" in saved.lower()

    # Delete
    r = client.post("/api/icon_svg/set", json={"key": "dashboard_raw.btn_kopieren", "svg": None})
    assert r.status_code == 200
    r = client.get("/api/icon_svg")
    assert r.get_json()["items"] == {}


def test_api_ui_inventory_returns_items(load_app_module, tmp_path):
    cfg_root = tmp_path / "config"
    data_root = tmp_path / "data"

    app_mod = load_app_module(config_dir=cfg_root, data_dir=data_root)
    client = app_mod.app.test_client()

    r = client.get("/api/ui_inventory")
    assert r.status_code == 200
    j = r.get_json()
    assert j["ok"] is True
    assert isinstance(j["items"], list)
    assert j["total"] == len(j["items"])
    # Must include at least a few known keys.
    keys = {str(x.get("key") or "") for x in j["items"] if isinstance(x, dict)}
    assert "config_page.main" in keys
    assert "config_icon_svg.btn_close" in keys
    assert "config_icon_svg.btn_superpicker" in keys
    assert "dialog_change_preview.btn_close" in keys
    assert "dialog_change_preview.btn_superpicker" in keys
    assert "dialog_repair_wizard.btn_close" in keys
    assert "dialog_repair_wizard.btn_superpicker" in keys
    assert "export_target.btn_close" in keys
    assert "export_target.btn_superpicker" in keys
    assert "logs_support_bundle.btn_close" in keys
    assert "logs_support_bundle.btn_superpicker" in keys
    assert "dq_detail.btn_close" in keys
    assert "dq_detail.btn_superpicker" in keys
    assert "jobs_timers_history.btn_close" in keys
    assert "jobs_timers_history.btn_superpicker" in keys
    assert "docs_modal.btn_close" in keys
    assert "docs_modal.btn_superpicker" in keys
    assert "issue_composer.btn_close" in keys
    assert "issue_composer.btn_superpicker" in keys
    assert "settings_organizer.btn_close" in keys
    assert "settings_organizer.btn_superpicker" in keys
    assert "ib_page_search_modal.btn_close" in keys
    assert "ib_page_search_modal.btn_superpicker" in keys
    assert "analysis_log_modal.btn_close" in keys
    assert "analysis_log_modal.btn_superpicker" in keys
    assert "picker_multi.panel_bar" in keys


def test_readable_picker_fallback_uses_data_ui_and_explicit_dynamic_pickkeys():
    topbar_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    nav_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_nav.html").read_text()
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    table_cols_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_table_cols.html").read_text()
    index_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()

    assert "if(ui) return ui;" in topbar_body
    assert "if(ui){ el.setAttribute('data-ib-pickkey', ui);" in topbar_body
    assert "if(id){ el.setAttribute('data-ib-pickkey', 'id.' + id);" in topbar_body
    assert "multiBar.setAttribute('data-ib-pickkey', 'picker_multi.panel_bar');" in topbar_body
    assert "closeBtn.setAttribute('data-ui', 'ib_page_search_modal.btn_close');" in topbar_body
    assert "closeBtn.setAttribute('data-ib-pickkey', 'ib_page_search_modal.btn_close');" in topbar_body

    assert "splitter.setAttribute('data-ib-pickkey', 'nav_main.handle_sidebar_split');" in nav_body
    assert "if(!el.getAttribute('data-ib-pickkey')) el.setAttribute('data-ib-pickkey', 'id.' + id);" in nav_body

    assert "details.setAttribute('data-ib-pickkey', dataUi);" in config_body
    assert "section.setAttribute('data-ib-pickkey', dataUi);" in config_body

    assert "if(tid) host.setAttribute('data-ib-instancekey', 'table.' + tid + '.rowcount');" in table_cols_body

    assert "close.setAttribute('data-ui', 'analysis_log_modal.btn_close');" in index_body
    assert "close.setAttribute('data-ib-pickkey', 'analysis_log_modal.btn_close');" in index_body
    assert "refresh.setAttribute('data-ui', 'analysis_log_modal.btn_refresh');" in index_body
    assert "refresh.setAttribute('data-ib-pickkey', 'analysis_log_modal.btn_refresh');" in index_body
    assert "el.setAttribute('data-ib-instancekey', _autoInstancekeyFor(el, pk));" in topbar_body
    assert "return basePk + '.auto.' + tag + '.' + h;" in topbar_body
    assert "el.setAttribute('data-ib-instancekey', _autoInstancekeyFor(el, pk, 'dedupe:' + idx));" in topbar_body
    assert "ik + '.auto.' + tag + '.' + h" not in topbar_body


def test_config_sections_use_unique_readable_pickkeys():
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'data-ui="config_settings.section_yaml" data-ib-pickkey="config_settings.section_yaml"' in config_body
    assert 'data-ui="config_settings.section_conn" data-ib-pickkey="config_settings.section_conn"' in config_body
    assert 'data-ui="config_settings.section_v2" data-ib-pickkey="config_settings.section_v2"' in config_body
    assert 'data-ui="config_settings.section_v1" data-ib-pickkey="config_settings.section_v1"' in config_body
    assert 'data-ui="config_settings.section_ui" data-ib-pickkey="config_settings.section_ui"' in config_body
    assert 'data-ui="config_settings.section_ui_dashboard" data-ib-pickkey="config_settings.section_ui_dashboard"' in config_body
    assert 'data-ui="config_settings.section_ui_icons" data-ib-pickkey="config_settings.section_ui_icons"' in config_body
    assert 'data-ui="config_settings.section_ui_table" data-ib-pickkey="config_settings.section_ui_table"' in config_body
    assert 'data-ui="config_settings.section_ui_cache" data-ib-pickkey="config_settings.section_ui_cache"' in config_body
    assert 'data-ui="config_settings.section_logs" data-ib-pickkey="config_settings.section_logs"' in config_body
    assert 'data-ui="config_settings.section_outliers" data-ib-pickkey="config_settings.section_outliers"' in config_body
    assert 'data-ui="config_settings.section_root" data-ib-pickkey="config_settings.section_root"' not in config_body


def test_config_icon_manager_has_sticky_header_palette_and_explicit_button_widths():
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert '#icons_tbl thead th { position: sticky; top: 0; z-index: 4;' in config_body
    assert 'id="icons_palette_box"' in config_body
    assert 'id="icons_palette_grid"' in config_body
    assert 'id="icons_edit" class="btn_sm"' in config_body and 'style="width:auto;"' in config_body
    assert 'id="icons_undo" class="btn_sm"' in config_body and 'style="width:auto;"' in config_body
    assert 'id="icons_jump" class="btn_sm"' in config_body and 'style="width:auto;"' in config_body
    assert '#icons_tbl th:nth-child(1), #icons_tbl td:nth-child(1) { position: sticky; left: 0;' in config_body
    assert '#icons_tbl th:nth-child(4), #icons_tbl td:nth-child(4) { position: sticky; left: 62ch;' in config_body
    assert 'id="icons_status_panel"' in config_body
    assert 'data-ui="config_settings.panel_icons_status"' in config_body
    assert 'id="icons_customer_actions_panel"' in config_body
    assert 'data-ui="config_settings.row_icons_customer_actions"' in config_body
    assert 'Es werden nur die geaenderten Iconsaetze angezeigt' in config_body
    assert 'data-ib-hide-rowcounts="1"' in config_body


def test_config_icon_manager_edit_and_dragdrop_logic_present():
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    assert 'let _ICON_DND_KEY = \'\'' in config_body
    assert 'let _ICON_DND_SVG = \'\'' in config_body
    assert 'let _ICON_INLINE_SAVE_BUSY = false;' in config_body
    assert 'function _iconsPaletteRender()' in config_body
    assert 'async function _iconsApplySvgToKey(targetKey, svg, sourceKey)' in config_body
    assert 'const seenSvg = {};' in config_body
    assert "item.setAttribute('data-ib-pickkey', 'config_settings.icon_palette_item.' + safeKey);" in config_body
    assert "tr.setAttribute('data-ib-pickkey', 'config_settings.row_icons_entry.' + safeRowKey);" in config_body
    assert "ta.value = String(eff || '');" in config_body
    assert "if(ev && ev.key === 'Enter' && !ev.shiftKey){" in config_body
    assert "_iconsSaveInlineEdit(String(ta.value || ''));" in config_body
    assert '_iconsRender();' in config_body
    assert "tr.draggable = true;" in config_body
    assert "tr.addEventListener('drop', async (ev)=>{" in config_body
    assert "_iconsSelect(r.key);" in config_body


def test_backup_query_details_use_panel_pickkeys_not_button_pickkeys():
    body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "backup.html").read_text()
    assert 'data-ui="backup_main.btn_query_details" data-ib-pickkey="backup_main.btn_query_details"' in body
    assert 'data-ui="backup_main.panel_query_details" data-ib-pickkey="backup_main.panel_query_details"' in body
    assert 'data-ui="backup_fullbackup.btn_query_details" data-ib-pickkey="backup_fullbackup.btn_query_details"' in body
    assert 'data-ui="backup_fullbackup.panel_query_details" data-ib-pickkey="backup_fullbackup.panel_query_details"' in body


def test_buttons_do_not_use_width_100_specific_rules():
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()
    topbar_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    export_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "export.html").read_text()
    assert 'main.content button:not(.ib_info_icon):not(.btn_sm) { width:auto; }' in config_body
    assert '.ib_pagecard_results button { display:block; width:auto;' in topbar_body
    assert 'style="display:block; width:auto; text-align:left;' in export_body


def test_logs_page_has_config_logging_checkbox_and_handler():
    logs_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "logs.html").read_text()
    assert '>Configuration<' in logs_body
    assert 'id="server_config_logging"' in logs_body
    assert 'data-ui="logs_main.chk_server_config_logging"' in logs_body
    assert 'cfg.log_config_changes !== false' in logs_body
    assert 'setServerConfigLogging(on)' in logs_body


def test_support_bundle_dialog_has_snapshot_controls_and_metadata():
    logs_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "logs.html").read_text()
    app_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "app.py").read_text()
    assert 'id="support_bundle_snapshot"' in logs_body
    assert 'id="support_bundle_snapshot_create"' in logs_body
    assert 'id="sb_support_snapshot"' in logs_body
    assert 'pk: logs_support_bundle.dialog | tpl: dialog_info_popup' in logs_body
    assert 'function loadSupportSnapshots()' in logs_body
    assert 'function createSupportSnapshot()' in logs_body
    assert '@app.get("/api/support_bundle/snapshots")' in app_body
    assert '@app.post("/api/support_bundle/snapshot/create")' in app_body
    assert 'support_snapshot' in app_body


def test_client_config_log_queue_helper_and_instrumented_persist_paths_exist():
    topbar_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    index_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    table_cols_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_table_cols.html").read_text()
    config_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "config.html").read_text()

    assert "const CFG_LOG_QUEUE_KEY = 'influxbro.config_log_queue.v1';" in topbar_body
    assert 'window.InfluxBroConfigLog = {' in topbar_body
    assert 'queue: _cfgLogQueueEvent' in topbar_body
    assert 'fetch(\'./api/client_log_batch\'' in topbar_body or 'fetch("./api/client_log_batch"' in topbar_body

    assert "window.InfluxBroConfigLog.queue({page:'Dashboard', area:'dashboard_state'" in index_body
    assert "window.InfluxBroConfigLog.queue({page:'Dashboard', area:String(id || 'flow')" in index_body

    assert "window.InfluxBroConfigLog.queue({page: 'table', area: 'table_cols.' + id" in table_cols_body
    assert "window.InfluxBroConfigLog.queue({page:'table', area:'table_wrap.' + tid" in table_cols_body
    assert "window.InfluxBroConfigLog.queue({page:'table', area:'table_filter.' + tid" in table_cols_body

    assert "window.InfluxBroConfigLog.queue({page:'Settings', area:'config_icons_table'" in config_body
    assert "window.InfluxBroConfigLog.queue({page:'Settings', area:'config_outliers_table'" in config_body


def test_table_helper_defaults_to_window_fit_and_template_documents_it():
    table_cols_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_table_cols.html").read_text()
    template_md = (Path(__file__).resolve().parents[1] / "influxbro" / "Template.md").read_text()
    assert 'const hadSaved = !!_readWidths(tbl);' in table_cols_body
    assert 'if(!hadSaved){' in table_cols_body
    assert "windowFit(tbl, {minW: 80});" in table_cols_body
    assert 'Dies ist der Standardzustand fuer Tabellen ohne gespeicherte Spaltenbreiten.' in template_md
    assert 'Status-/Infotext für eine Tabelle gebraucht wird' in template_md


def test_jobs_table_info_specs_cover_toolbar_controls_and_sticky_rule_documented():
    jobs_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "jobs.html").read_text()
    template_md = (Path(__file__).resolve().parents[1] / "influxbro" / "Template.md").read_text()
    assert 'Selektiere alle / keine: markieren sichtbare Zeilen gesammelt.' in jobs_body
    assert 'Spaltenbreite automatisch / Fensterbreite: passen die Tabelle an Inhalte bzw. die verfügbare Breite an.' in jobs_body
    assert '.table_title { position: sticky; top: 0;' in jobs_body
    assert '.table_head { display:flex; justify-content:space-between; gap: 12px; align-items:flex-end; flex-wrap:wrap; position: sticky; top: 24px;' in jobs_body
    assert 'All applicable toolbar actions/buttons/checkboxes/filter toggles/window-fit controls for this table; no table-specific control may be omitted' in template_md
    assert 'The table title line (`.table_title`) and the table action/title header (`.table_head`) must remain fixed above the scroll area' in template_md


def test_confirm_dialog_template_and_popup_metadata_exist():
    tooltips_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_tooltips.html").read_text()
    assert 'let CONFIRM_REFS = null;' in tooltips_body
    assert "function _dialogMetaText(pk, tpl)" in tooltips_body
    assert "popupMetaFooter.id = 'influxbro_popup_meta_footer';" in tooltips_body
    assert "confirmRoot.id = 'influxbro_confirm_root';" in tooltips_body
    assert "confirmCancel.setAttribute('data-ui', 'dialog_confirm_action.btn_cancel');" in tooltips_body
    assert "confirmOk.setAttribute('data-ui', 'dialog_confirm_action.btn_ok');" in tooltips_body
    assert "window.InfluxBroConfirm = {" in tooltips_body
    assert "composer.style.overflow = 'auto';" in tooltips_body
    assert "composerCard.style.maxHeight = 'calc(100vh - 16vh - 24px)';" in tooltips_body
    assert "GitHub: im neuen Issue rechts bzw. unten <code>Add files</code> verwenden" in tooltips_body


def test_destructive_flows_use_confirm_dialog_api():
    index_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "index.html").read_text()
    jobs_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "jobs.html").read_text()
    backup_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "backup.html").read_text()
    restore_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "restore.html").read_text()
    assert "window.InfluxBroConfirm.ask({" in index_body
    assert "pickerKey: 'dialog_raw_overwrite_confirm.root'" in index_body
    assert "pickerKey: 'dialog_raw_delete_confirm.root'" in index_body
    assert "pickerKey: 'dialog_analysis_cache_delete_confirm.root'" in index_body
    assert "pickerKey: 'dialog_job_cancel_confirm.root'" in jobs_body
    assert "pickerKey: 'dialog_job_delete_confirm.root'" in jobs_body
    assert "pickerKey: 'dialog_cache_delete_confirm.root'" in jobs_body
    assert "pickerKey: 'dialog_analysis_cache_delete_selected_confirm.root'" in jobs_body
    assert "pickerKey: 'dialog_name_merge_latest_confirm.root'" in index_body
    assert "pickerKey: 'dialog_fullbackup_delete_confirm.root'" in backup_body
    assert "pickerKey: 'dialog_backup_delete_confirm.root'" in backup_body
    assert "pickerKey: 'dialog_fullrestore_confirm.root'" in restore_body
    assert "pickerKey: 'dialog_restore_confirm.root'" in restore_body


def test_pick_registry_skips_template_blueprints_and_static_duplicate_keys_are_bounded():
    topbar_body = (Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates" / "_topbar.html").read_text()
    assert "function _isInertPickNode(el)" in topbar_body
    assert "if(el.closest('template')) return true;" in topbar_body
    assert "if(el.closest('[data-ib-template=\"1\"]')) return true;" in topbar_body

    templates_dir = Path(__file__).resolve().parents[1] / "influxbro" / "app" / "templates"
    counts = {}
    for template_path in sorted(templates_dir.glob("*.html")):
        for line_no, line in enumerate(template_path.read_text().splitlines(), 1):
            for marker in re.finditer(r'<[^>]+data-ib-pickkey="([^"]+)"', line):
                key = marker.group(1)
                counts.setdefault(key, []).append(f"{template_path.name}:{line_no}")

    def _allowed_duplicate_key(k: str) -> bool:
        if k == 'config_test_success.btn_ok':
            return True
        return (
            k.startswith("dashboard.cache_timeline.btn_hl.")
            or k.startswith("dashboard.cache_timeline.btn_ac.")
            or k.startswith("dashboard.cache_timeline.btn_ol.")
        )

    disallowed = {k: v for k, v in counts.items() if len(v) > 1 and not _allowed_duplicate_key(k)}
    assert disallowed == {}
