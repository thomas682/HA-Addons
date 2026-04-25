import uuid


def _mk_block(mod, *, block_id: str | None = None):
    bid = block_id or uuid.uuid4().hex
    return {
        "block_id": bid,
        "created_at": mod._utc_now_iso_ms(),
        "source": {"user_id": None, "ip": "127.0.0.1", "ua": "pytest"},
        "operation_source": "raw_edit",
        "reason": "test",
        "status": "created",
        "undo_status": "not_run",
        "repeat_status": "not_run",
        "affected_count": 0,
    }


def _mk_update_item(mod, *, block_id: str, ts: str):
    return {
        "item_id": uuid.uuid4().hex,
        "block_id": block_id,
        "op": "update",
        "point_identity": {
            "bucket": "b",
            "org": "o",
            "measurement": "m",
            "field": "f",
            "timestamp": ts,
            "tag_set": {"entity_id": "sensor.x", "friendly_name": "X"},
        },
        "old_point": {"_time": ts, "_measurement": "m", "_field": "f", "_value": 1, "entity_id": "sensor.x"},
        "new_point": {"_time": ts, "_measurement": "m", "_field": "f", "_value": 2, "entity_id": "sensor.x"},
        "expected_current_point": {"_time": ts, "_measurement": "m", "_field": "f", "_value": 2, "entity_id": "sensor.x"},
        "conflict_policy": "strict",
    }


def test_change_item_validate_create_update_delete(load_app_module):
    mod = load_app_module()

    bid = uuid.uuid4().hex
    ts = mod._utc_now_iso_ms()
    base_pid = {
        "bucket": "b",
        "org": "o",
        "measurement": "m",
        "field": "f",
        "timestamp": ts,
        "tag_set": {"a": "1"},
    }

    # update
    it_u = {
        "schema_version": 1,
        "item_id": uuid.uuid4().hex,
        "block_id": bid,
        "op": "update",
        "point_identity": base_pid,
        "old_point": {"_time": ts, "_measurement": "m", "_field": "f", "_value": 1},
        "new_point": {"_time": ts, "_measurement": "m", "_field": "f", "_value": 2},
        "expected_current_point": {"_time": ts, "_measurement": "m", "_field": "f", "_value": 2},
        "conflict_policy": "strict",
    }
    mod.validate_change_item_schema(it_u)

    # delete
    it_d = dict(it_u)
    it_d["op"] = "delete"
    it_d["new_point"] = None
    it_d["expected_current_point"] = None
    mod.validate_change_item_schema(it_d)

    # create
    it_c = dict(it_u)
    it_c["op"] = "create"
    it_c["old_point"] = None
    it_c["expected_current_point"] = it_c["new_point"]
    mod.validate_change_item_schema(it_c)


def test_save_load_inline_payload(load_app_module):
    mod = load_app_module()

    b = _mk_block(mod)
    ts = mod._utc_now_iso_ms()
    items = [_mk_update_item(mod, block_id=b["block_id"], ts=ts)]
    saved = mod.save_change_block(b, items=items)

    assert saved["block_id"] == b["block_id"]
    assert saved["payload_mode"] == "inline"
    assert isinstance(saved.get("payload_inline"), list)
    assert saved["affected_count"] == 1

    loaded = mod.load_change_block(b["block_id"], include_items=False)
    assert loaded and loaded["block_id"] == b["block_id"]
    assert loaded["payload_mode"] == "inline"
    assert isinstance(loaded.get("payload_inline"), list)

    loaded2 = mod.load_change_block(b["block_id"], include_items=True)
    assert loaded2 and "items" in loaded2
    assert isinstance(loaded2["items"], list)
    assert loaded2["items"][0]["op"] == "update"


def test_save_load_gzip_payload(load_app_module):
    mod = load_app_module()

    # Force gzip payload for tiny blocks
    mod.CHANGE_BLOCK_INLINE_MAX_ITEMS = 0

    b = _mk_block(mod)
    ts = mod._utc_now_iso_ms()
    items = [_mk_update_item(mod, block_id=b["block_id"], ts=ts)]
    saved = mod.save_change_block(b, items=items)

    assert saved["payload_mode"] == "gzip"
    assert saved.get("payload_inline") is None
    assert isinstance(saved.get("payload_ref"), str) and saved["payload_ref"].endswith(".json.gz")

    loaded = mod.load_change_block(b["block_id"], include_items=False)
    assert loaded and loaded["payload_mode"] == "gzip"
    assert loaded.get("payload_inline") is None
    assert isinstance(loaded.get("payload_ref"), str)

    loaded2 = mod.load_change_block(b["block_id"], include_items=True)
    assert loaded2 and isinstance(loaded2.get("items"), list)
    assert loaded2["items"][0]["op"] == "update"


def test_list_change_blocks_filters(load_app_module):
    mod = load_app_module()

    b1 = _mk_block(mod)
    b1["operation_source"] = "raw_edit"
    b1["series_summary"] = {"measurement": "m", "field": "f", "entity_id": "sensor.x", "friendly_name": "X"}
    mod.save_change_block(b1, items=[_mk_update_item(mod, block_id=b1["block_id"], ts=mod._utc_now_iso_ms())])

    b2 = _mk_block(mod)
    b2["operation_source"] = "combine"
    b2["series_summary"] = {"measurement": "m2", "field": "f2", "entity_id": "sensor.y", "friendly_name": "Y"}
    mod.save_change_block(b2, items=[_mk_update_item(mod, block_id=b2["block_id"], ts=mod._utc_now_iso_ms())])

    xs = mod.list_change_blocks({"operation_source": "raw_edit"}, limit=50)
    assert any(x.get("block_id") == b1["block_id"] for x in xs)
    assert not any(x.get("block_id") == b2["block_id"] for x in xs)

    ys = mod.list_change_blocks({"measurement": "m2"}, limit=50)
    assert any(x.get("block_id") == b2["block_id"] for x in ys)


def test_invalid_item_rejected(load_app_module):
    mod = load_app_module()
    bid = uuid.uuid4().hex
    ts = mod._utc_now_iso_ms()

    bad = {
        "schema_version": 1,
        "item_id": uuid.uuid4().hex,
        "block_id": bid,
        "op": "update",
        "point_identity": {
            # bucket missing
            "org": "o",
            "measurement": "m",
            "field": "f",
            "timestamp": ts,
            "tag_set": {},
        },
        "old_point": {"_time": ts, "_measurement": "m", "_field": "f", "_value": 1},
        "new_point": {"_time": ts, "_measurement": "m", "_field": "f", "_value": 2},
        "expected_current_point": {"_time": ts, "_measurement": "m", "_field": "f", "_value": 2},
        "conflict_policy": "strict",
    }

    try:
        mod.validate_change_item_schema(bad)
        assert False, "expected ValueError"
    except ValueError:
        pass
