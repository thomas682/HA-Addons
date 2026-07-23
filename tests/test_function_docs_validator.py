import ast
import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "function_docs_validator", ROOT / "scripts/validate_function_docs.py"
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


@lru_cache(maxsize=1)
def _catalog():
    return validator.build_catalog()


def _function(source: str):
    return ast.parse(source).body[0]


def test_request_extractor_ignores_decorator_and_mapping_get():
    node = _function(
        '''
@app.get("/api/example")
def handler():
    local = {"wrong": 1}
    local.get("wrong")
    return request.args.get("right", "default")
'''
    )
    inputs, warnings = validator.request_inputs(node)
    assert warnings == []
    assert [(item["location"], item["name"], item["default"]) for item in inputs] == [
        ("args", "right", "default")
    ]


def test_request_extractor_distinguishes_json_alias():
    node = _function(
        '''
def handler():
    body = request.get_json(force=True) or {}
    return body.get("payload", 3)
'''
    )
    inputs, warnings = validator.request_inputs(node)
    assert warnings == []
    assert [(item["location"], item["name"], item["default"]) for item in inputs] == [
        ("json", "payload", 3)
    ]


def test_unknown_request_handler_is_reported():
    node = _function(
        '''
def handler():
    return request.cookies.get("session")
'''
    )
    inputs, warnings = validator.request_inputs(node)
    assert inputs == []
    assert warnings == ["unknown request access: request.cookies", "unknown request access: request.cookies.get"]


def test_manifest_arch_is_enum_not_default():
    entries = validator.addon_and_shell_entries()
    arch = next(item for item in entries if item["name"] == "arch")
    documented = arch["inputs"][0]
    assert documented["default"].startswith("N/A - compatibility declaration")
    assert documented["allowed_values"] == ["amd64", "aarch64", "armv7", "armhf"]


def test_catalog_reference_source_inputs_are_exact():
    catalog = _catalog()
    item = next(entry for entry in catalog["entries"] if entry["name"] == "api_reference_source")
    assert item["status"] == "verified"
    assert [(value["location"], value["name"]) for value in item["inputs"]] == [
        ("query", "path"),
        ("query", "line"),
    ]
    assert "/api/reference_source" not in item["api"]["request"]["keys"]


def test_reviewed_active_mode_has_exact_enum_and_default():
    catalog = _catalog()
    item = next(entry for entry in catalog["entries"] if entry["name"] == "active_database_mode")
    documented = item["inputs"][0]
    assert item["status"] == "verified"
    assert documented["default"] == "v2"
    assert documented["allowed_values"] == ["v2", "v3"]


def test_validator_rejects_reviewed_config_default_and_unknown_handler_tamper():
    expected = _catalog()
    actual = copy.deepcopy(expected)
    mode = next(entry for entry in actual["entries"] if entry["name"] == "active_database_mode")
    mode["inputs"][0]["default"] = "v3"
    route = next(entry for entry in actual["entries"] if entry["name"] == "api_reference_source")
    route["input_extraction_warnings"] = ["unknown request access: request.cookies"]
    errors = validator.validate(actual, expected)
    assert any("Kataloginhalt weicht" in error and "active_database_mode" in error for error in errors)
    assert any("unbekannter Request-Handler" in error and "api_reference_source" in error for error in errors)


def test_every_active_unit_has_its_own_source_contract_and_fingerprint():
    catalog = _catalog()
    assert catalog["audit_complete"] is True
    assert catalog["status_counts"] == {"verified": 5741}
    for item in catalog["entries"]:
        unit, facts = validator._source_unit(item)
        assert item["status"] == "verified"
        assert {key: value for key, value in item["contract"].items() if key != "source_span"} == facts
        assert item["contract"]["source_span"] == {
            "bytes": len(unit.encode("utf-8")), "lines": unit.count("\n") + 1
        }
        assert item["review"]["source_sha256"] == hashlib.sha256(unit.encode()).hexdigest()
        assert item["review"]["fingerprint_sha256"] == validator._unit_fingerprint(item, unit)
        assert item["review"]["fingerprint_material"] == "technical_reference + exact source unit"
        assert item["review"]["category_batch"] == f"audit-{validator.slug(item['category'])}-2026-07-15"
        assert all(
            value["validation"] != "An der jeweiligen Vertrauensgrenze normalisieren und fachlich begrenzen."
            for value in item["inputs"]
        )


def test_adversarial_contract_samples_cover_every_category():
    entries = {item["id"]: item for item in _catalog()["entries"]}
    samples = {
        "API": "influxbro.py.app.api_reference_source",
        "Add-on-Konfigurationsoption": "influxbro.addon.option.arch",
        "Add-on-Service": "influxbro.service.startup",
        "Lokale Pruefung": "influxbro.local-checks.function-docs",
        "GUI-Aktion": "influxbro.ui._nav.nav_main.btn_sidebar_toggle",
        "GUI-Anzeige": "influxbro.ui._nav.nav_main.row_sidebar_tools",
        "GUI-Eingabe": "influxbro.ui._dialog.docs_modal.input_search.dynamic",
        "GUI-Navigation": "influxbro.ui._nav.nav_main.panel_audit",
        "GUI-Zustand": "influxbro.ui._measurement_selection.sel_root_ui",
        "Hintergrundprozess": "influxbro.py.app._analysis_nightly_start_job",
        "Job": "influxbro.py.app._active_job_ids",
        "Konfigurationsoption": "influxbro.config.runtime.active_database_mode",
        "Skriptfunktion": "influxbro.js._dialog._clipboardhost",
        "interne Funktion": "influxbro.py.app._active_profile_set",
    }
    assert {item["category"] for item in entries.values()} == set(samples)
    for category, doc_id in samples.items():
        assert entries[doc_id]["category"] == category
        assert entries[doc_id]["contract"]

    assert entries[samples["API"]]["api"]["request"]["keys"] == ["path", "line"]
    assert entries[samples["Add-on-Konfigurationsoption"]]["inputs"][0]["allowed_values"] == [
        "amd64", "aarch64", "armv7", "armhf"
    ]
    assert "mv" in entries[samples["Add-on-Service"]]["contract"]["effects"]
    local_check = entries[samples["Lokale Pruefung"]]
    assert local_check["technical_reference"] == "scripts/run-local-checks.sh:1#function-docs"
    button = entries[samples["GUI-Aktion"]]["contract"]
    assert button["tag"] == "button" and "href" not in button["attributes"]
    assert entries[samples["GUI-Anzeige"]]["contract"]["tag"] == "div"
    dynamic_input = entries[samples["GUI-Eingabe"]]["contract"]
    assert dynamic_input["tag"] == "input"
    assert dynamic_input["attributes"]["type"] == "search"
    assert entries[samples["GUI-Navigation"]]["contract"]["attributes"]["href"] == "./audit"
    assert entries[samples["GUI-Zustand"]]["contract"]["tag"] == "details"
    assert "job_id" in entries[samples["Hintergrundprozess"]]["contract"]["returns"]
    assert entries[samples["Job"]]["contract"]["returns"] == ["active_ids"]
    assert entries[samples["Konfigurationsoption"]]["inputs"][0]["allowed_values"] == ["v2", "v3"]
    assert "clipboard boundary" in entries[samples["Skriptfunktion"]]["contract"]["security_boundaries"]
    assert "UI_PROFILE_ACTIVE_PATH.write_text" in entries[samples["interne Funktion"]]["contract"]["effects"]


def test_contracts_reject_false_config_enums_oversized_js_and_private_endpoints():
    entries = _catalog()["entries"]
    database = next(item for item in entries if item["id"] == "influxbro.config.runtime.database")
    assert database["contract"]["enums"] == {}
    assert max(
        item["contract"]["source_span"]["bytes"]
        for item in entries if item["id"].startswith("influxbro.js.")
    ) < 50000
    serialized = json.dumps(_catalog(), ensure_ascii=True)
    assert "192.168." not in serialized
    assert "[private-endpoint]" in serialized


def test_central_ui_ids_are_bijective_and_not_markup_hashes():
    mapping = json.loads((ROOT / "docs/ui-id-map.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in mapping["elements"]]
    source_keys = [item["source_key"] for item in mapping["elements"]]
    assert len(ids) == len(set(ids)) == len(source_keys) == len(set(source_keys))
    assert all("anon-" not in value for value in ids)


def test_ui_source_drift_is_not_silently_reidentified(tmp_path, monkeypatch):
    template = tmp_path / "influxbro/app/templates/example.html"
    template.parent.mkdir(parents=True)
    template.write_text('<button class="before">Run</button>\n', encoding="utf-8")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    parser = validator.UICollector(
        template,
        template.read_text(encoding="utf-8"),
        {"influxbro/app/templates/example.html:1#1": "influxbro.ui.central.element-0001"},
    )
    parser.feed(template.read_text(encoding="utf-8"))
    assert [item["id"] for item in parser.items] == ["influxbro.ui.central.element-0001"]
    template.write_text('\n<button class="after">Run</button>\n', encoding="utf-8")
    parser = validator.UICollector(
        template,
        template.read_text(encoding="utf-8"),
        {"influxbro/app/templates/example.html:1#1": "influxbro.ui.central.element-0001"},
    )
    parser.feed(template.read_text(encoding="utf-8"))
    assert parser.items == []
    assert parser.unmapped == ["influxbro/app/templates/example.html:2#1"]
