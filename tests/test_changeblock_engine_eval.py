import uuid


def _item(mod, *, op: str, ts: str, old_v=None, new_v=None):
    bid = uuid.uuid4().hex
    pid = {
        "bucket": "b",
        "org": "o",
        "measurement": "m",
        "field": "f",
        "timestamp": ts,
        "tag_set": {"entity_id": "sensor.x"},
    }
    old_p = None if old_v is None else {"_time": ts, "_measurement": "m", "_field": "f", "_value": old_v, "entity_id": "sensor.x"}
    new_p = None if new_v is None else {"_time": ts, "_measurement": "m", "_field": "f", "_value": new_v, "entity_id": "sensor.x"}
    return {
        "schema_version": 1,
        "item_id": uuid.uuid4().hex,
        "block_id": bid,
        "op": op,
        "point_identity": pid,
        "old_point": old_p,
        "new_point": new_p,
        "expected_current_point": new_p,
        "conflict_policy": "strict",
    }


def test_eval_execute_update_ok_missing_conflict(load_app_module):
    mod = load_app_module()
    ts = mod._utc_now_iso_ms()
    it = _item(mod, op="update", ts=ts, old_v=1, new_v=2)
    it = mod.normalize_change_item(it)

    # current matches old -> ok for execute
    cur = {"_time": ts, "_measurement": "m", "_field": "f", "_value": 1, "entity_id": "sensor.x"}
    r = mod._cb_eval_item_state("execute", it, cur)
    assert r["state"] == "ok"

    # current missing -> missing
    r = mod._cb_eval_item_state("execute", it, None)
    assert r["state"] == "missing"

    # current matches new -> already_applied
    cur2 = {"_time": ts, "_measurement": "m", "_field": "f", "_value": 2, "entity_id": "sensor.x"}
    r = mod._cb_eval_item_state("execute", it, cur2)
    assert r["state"] == "already_applied"

    # current wrong -> conflict
    cur3 = {"_time": ts, "_measurement": "m", "_field": "f", "_value": 9, "entity_id": "sensor.x"}
    r = mod._cb_eval_item_state("execute", it, cur3)
    assert r["state"] == "conflict"


def test_eval_undo_delete_idempotent(load_app_module):
    mod = load_app_module()
    ts = mod._utc_now_iso_ms()
    it = _item(mod, op="delete", ts=ts, old_v=5, new_v=None)
    it = mod.normalize_change_item(it)

    # undo expects missing; if missing -> already_applied
    r = mod._cb_eval_item_state("undo", it, None)
    assert r["state"] == "already_applied"

    # if current exists (should be missing) -> conflict
    cur = {"_time": ts, "_measurement": "m", "_field": "f", "_value": 5, "entity_id": "sensor.x"}
    r = mod._cb_eval_item_state("undo", it, cur)
    assert r["state"] == "conflict" or r["state"] == "already_applied"


def test_eval_undo_create(load_app_module):
    mod = load_app_module()
    ts = mod._utc_now_iso_ms()
    it = _item(mod, op="create", ts=ts, old_v=None, new_v=7)
    it = mod.normalize_change_item(it)

    # undo expects current == new; if current new -> ok
    cur = {"_time": ts, "_measurement": "m", "_field": "f", "_value": 7, "entity_id": "sensor.x"}
    r = mod._cb_eval_item_state("undo", it, cur)
    assert r["state"] == "ok"

    # if missing -> already_applied (already undone)
    r = mod._cb_eval_item_state("undo", it, None)
    assert r["state"] == "already_applied"
