def test_config_defaults_include_storage_budget_and_backup_min_defaults(load_app_module):
    mod = load_app_module()
    client = mod.app.test_client()
    r = client.get("/api/config_defaults")
    assert r.status_code == 200
    j = r.get_json()
    assert j and j.get("ok") is True
    d = j.get("defaults")
    assert isinstance(d, dict)
    assert d.get("storage_budget_mb") == 5
    assert d.get("backup_min_free_mb") == 10


def test_config_save_rejects_backup_min_free_not_above_budget(load_app_module):
    mod = load_app_module()
    client = mod.app.test_client()
    r = client.post("/api/config", json={"storage_budget_mb": 50, "backup_min_free_mb": 10})
    assert r.status_code == 400
    j = r.get_json()
    assert j and j.get("ok") is False
