def test_storage_usage_endpoint_exists(load_app_module):
    mod = load_app_module()
    app = getattr(mod, "app")
    client = app.test_client()
    r = client.get("/api/storage_usage")
    assert r.status_code == 200
    j = r.get_json()
    assert j and j.get("ok") is True
    assert "items" in j


def test_worklog_alias_endpoint_exists(load_app_module):
    mod = load_app_module()
    app = getattr(mod, "app")
    client = app.test_client()
    r = client.get("/api/worklog?limit=5")
    assert r.status_code == 200
    j = r.get_json()
    assert j and j.get("ok") is True
