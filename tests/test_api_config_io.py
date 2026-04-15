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

    assert d.get("ui_section_title_font_px") == 13
    assert d.get("ui_section_level2_bg") == "#8BA293"
    assert d.get("ui_section_level2_fg") == "#FFFFFF"
    assert d.get("ui_section_level2_font_px") == 12
    assert d.get("ui_section_level3_bg") == "#B8B17F"
    assert d.get("ui_section_level3_fg") == "#FFFFFF"
    assert d.get("ui_section_level3_font_px") == 11

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


def test_trace_recent_endpoint_exists(load_app_module):
    mod = load_app_module()
    client = mod.app.test_client()
    r = client.get("/api/trace/recent?limit=5")
    assert r.status_code == 200
    j = r.get_json()
    assert j and j.get("ok") is True
