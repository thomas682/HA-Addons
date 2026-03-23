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
