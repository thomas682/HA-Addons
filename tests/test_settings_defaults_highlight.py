def test_config_defaults_include_page_search_highlight_defaults(load_app_module):
    mod = load_app_module()
    client = mod.app.test_client()

    r = client.get("/api/config_defaults")
    assert r.status_code == 200
    j = r.get_json()
    assert j and j.get("ok") is True
    d = j.get("defaults")
    assert isinstance(d, dict)

    assert d.get("ui_page_search_highlight_width_px") == 5
    assert d.get("ui_page_search_highlight_duration_ms") == 8000
