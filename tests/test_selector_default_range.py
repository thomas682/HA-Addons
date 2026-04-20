def test_selector_default_range_is_bounded(load_app_module):
    app_mod = load_app_module()
    assert app_mod._selector_range_key(None, None, None) == "all"
    assert app_mod._selector_range_key("", None, None) == "all"
    assert app_mod._selector_range_key("all", None, None) == "all"
