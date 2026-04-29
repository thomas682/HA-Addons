def test_selector_default_range_is_bounded(load_app_module):
    app_mod = load_app_module()
    assert app_mod._selector_range_key(None, None, None) == "all"
    assert app_mod._selector_range_key("", None, None) == "all"
    assert app_mod._selector_range_key("all", None, None) == "all"


def test_selector_limit_bounds_all_but_not_custom(load_app_module):
    from datetime import datetime, timezone

    app_mod = load_app_module()
    cfg = {"selector_query_limit_enabled": True, "selector_query_limit_days": 30}
    rk, start_dt, stop_dt = app_mod._selector_effective_time_filter(cfg, "all", None, None)
    assert rk == "30d"
    assert start_dt is None
    assert stop_dt is None

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    stop = datetime(2026, 1, 2, tzinfo=timezone.utc)
    rk, start_dt, stop_dt = app_mod._selector_effective_time_filter(cfg, "custom", start, stop)
    assert rk == "custom"
    assert start_dt == start
    assert stop_dt == stop
