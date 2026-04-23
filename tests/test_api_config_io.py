import json


def test_config_defaults_endpoint_exposes_section_title_defaults_without_secrets(load_app_module):
    mod = load_app_module()
    client = mod.app.test_client()
    r = client.get("/api/config_defaults")
    assert r.status_code == 200
    j = r.get_json()
    assert j and j.get("ok") is True
    d = j.get("defaults")
    assert isinstance(d, dict)

    assert d.get("ui_section_title_font_px") == 14
    assert d.get("ui_section_level2_bg") == "#8BA293"
    assert d.get("ui_section_level2_fg") == "#FFFFFF"
    assert d.get("ui_section_level2_font_px") == 12
    assert d.get("ui_section_level3_bg") == "#B8B17F"
    assert d.get("ui_section_level3_fg") == "#FFFFFF"
    assert d.get("ui_section_level3_font_px") == 10

    # Grouped font defaults
    assert d.get("ui_gui_title_px") == 16
    assert d.get("ui_gui_heading_px") == 14
    assert d.get("ui_gui_body_px") == 12
    assert d.get("ui_gui_meta_px") == 10
    assert d.get("ui_tbl_title_px") == 12
    assert d.get("ui_tbl_head_px") == 11
    assert d.get("ui_tbl_cell_px") == 10

    assert d.get("outlier_bounds_min_default") == ""
    assert d.get("outlier_bounds_max_default") == ""
    assert d.get("outlier_recovery_valid_streak_default") == 2

    # No secrets via defaults endpoint
    assert d.get("token") == ""
    assert d.get("admin_token") == ""
    assert d.get("password") == ""


def test_config_export_endpoint_returns_json(load_app_module):
    mod = load_app_module()
    client = mod.app.test_client()
    r = client.get("/api/config_export")
    assert r.status_code == 200
    assert "application/json" in (r.headers.get("Content-Type") or "")
    data = json.loads(r.data.decode("utf-8"))
    assert isinstance(data, dict)
    assert "influx_version" in data
    # Export includes visible /config UI settings
    assert "ui_nav_helper_history_limit" in data
    assert "ui_log_error_bg" in data
    assert "ui_tooltip_doc_open_mode" in data
    # Transient/internal keys must not be exported
    assert "backup_migrated_to_config" not in data
    assert "ui_open_graph" not in data


def test_config_export_import_roundtrip_is_stable_and_filters_transient_keys(load_app_module, tmp_path):
    cfg1 = tmp_path / "cfg1"
    dat1 = tmp_path / "dat1"
    cfg2 = tmp_path / "cfg2"
    dat2 = tmp_path / "dat2"

    mod1 = load_app_module(config_dir=cfg1, data_dir=dat1)
    c1 = mod1.app.test_client()

    # Apply some settings, including an internal marker and an unknown transient key.
    r = c1.post(
        "/api/config",
        json={
            "ui_tooltip_doc_open_mode": "same_tab",
            "ui_nav_helper_history_limit": 13,
            "ui_log_error_bg": "#123456",
            "backup_migrated_to_config": True,
            "ui_open_graph": True,
        },
    )
    assert r.status_code == 200

    e1 = c1.get("/api/config_export")
    assert e1.status_code == 200
    exported = json.loads(e1.data.decode("utf-8"))
    assert exported.get("ui_tooltip_doc_open_mode") == "same_tab"
    assert exported.get("ui_nav_helper_history_limit") == 13
    assert exported.get("ui_log_error_bg") == "#123456"
    assert "backup_migrated_to_config" not in exported
    assert "ui_open_graph" not in exported

    mod2 = load_app_module(config_dir=cfg2, data_dir=dat2)
    c2 = mod2.app.test_client()
    r2 = c2.post("/api/config", json=exported)
    assert r2.status_code == 200

    e2 = c2.get("/api/config_export")
    assert e2.status_code == 200
    exported2 = json.loads(e2.data.decode("utf-8"))

    # Roundtrip stability: for a representative subset, values must match.
    for k in ("ui_tooltip_doc_open_mode", "ui_nav_helper_history_limit", "ui_log_error_bg"):
        assert exported2.get(k) == exported.get(k)


def test_trace_recent_endpoint_exists(load_app_module):
    mod = load_app_module()
    client = mod.app.test_client()
    r = client.get("/api/trace/recent?limit=5")
    assert r.status_code == 200
    j = r.get_json()
    assert j and j.get("ok") is True
