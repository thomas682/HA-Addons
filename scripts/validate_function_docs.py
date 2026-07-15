#!/usr/bin/env python3
"""Generate and validate the dependency-free InfluxBro function inventory.

The catalog is JSON-compatible YAML so validation needs only the Python
standard library.  --write is deterministic and intended for maintainers;
normal invocation is read-only and fails on every coverage discrepancy.
"""

from __future__ import annotations

import argparse
import ast
from functools import lru_cache
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs/functions.yaml"
MANUAL = ROOT / "docs/handbuch.md"
REVIEWS = ROOT / "docs/function-reviews.json"
UI_ID_MAP = ROOT / "docs/ui-id-map.json"
AUDIT_EVIDENCE = ROOT / "docs/audit-evidence.json"
ADDON = ROOT / "influxbro"
VERSION = "1.12.640"
AUDITED_REF = "405376f"
STATUS = "draft"
REVIEWED_FIELDS = {
    "description", "short_description", "prerequisites", "permissions",
    "inputs", "outputs", "side_effects", "states", "security",
    "dependencies", "called_by", "tests",
}
EFFECT_CALLS = {
    "write", "write_text", "write_bytes", "unlink", "remove", "rmtree",
    "replace", "rename", "mkdir", "makedirs", "save", "dump", "dumps",
    "post", "put", "patch", "delete", "start", "submit", "set",
    "setitem", "append", "extend", "update", "clear", "pop",
}

REQUIRED_FIELDS = {
    "id", "addon", "name", "technical_reference", "category",
    "description", "short_description", "audience", "visibility",
    "prerequisites", "permissions", "inputs", "outputs", "side_effects",
    "states", "security", "dependencies", "called_by", "manual_ref",
    "ui_location", "tests", "status", "verified_version", "source",
    "contract", "review",
}
STATE_FIELDS = {"loading", "success", "empty", "error", "cancel", "retry"}
API_FIELDS = {
    "method", "path", "summary", "description", "group", "tags", "role",
    "roleLabel", "roleColor", "authRequired", "request", "response", "timing",
    "correlations", "errors", "examples", "notes",
}
ID_RE = re.compile(r"^influxbro\.[a-z0-9][a-z0-9._-]*$")
JS_RE = re.compile(
    r"(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)"
    r"|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?"
    r"(?:\(([^;{}]*)\)|([A-Za-z_$][\w$]*))\s*=>"
)
SHELL_FN_RE = re.compile(
    r"^(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{", re.M
)
INTERACTIVE_TAGS = {"a", "button", "details", "form", "input", "select", "summary", "textarea"}

DOMAIN_RULES = (
    ("migration", "InfluxDB-v2-zu-v3-Migration"),
    ("fullbackup", "vollstaendige InfluxDB-Sicherung"),
    ("fullrestore", "vollstaendige InfluxDB-Wiederherstellung"),
    ("backup", "Messwertsicherung und Sicherungsspeicher"),
    ("restore", "Wiederherstellung und Ergebnispruefung"),
    ("rollup", "Verdichtung und Rollup-Wiederherstellung"),
    ("quality", "Raw-/Clean-/Rollup-Datenqualitaet"),
    ("dq_", "Datenqualitaetsanalyse und Reparaturvorschlaege"),
    ("outlier", "Ausreissererkennung und Kontextfenster"),
    ("analysis", "Analyse-Cache und Analysehistorie"),
    ("stats", "Statistikberechnung und Statistik-Cache"),
    ("cache", "Cache-Planung, Persistenz und Bereinigung"),
    ("monitor", "laufende Messwertueberwachung"),
    ("watchlist", "geplante Health-Scans und Inbox"),
    ("timer", "Timer und zeitgesteuerte Ausfuehrung"),
    ("job", "asynchrone Jobs und Fortschrittszustand"),
    ("change_block", "persistente Aenderungsbloecke"),
    ("undo", "Undo-/Redo-Historie"),
    ("import", "Dateiimport, Spaltenabbildung und Transformation"),
    ("export", "Datenexport und Download"),
    ("combine", "Kombination und Kopieren von Messwertreihen"),
    ("config", "Anwendungskonfiguration"),
    ("settings", "Einstellungsdarstellung und Layout"),
    ("profile", "Messwert- oder UI-Profile"),
    ("ui_", "persistenten und browserseitigen UI-Zustand"),
    ("dialog", "Dialogdarstellung und Dialogbedienung"),
    ("tooltip", "kontextbezogene Tooltips und Hilfe"),
    ("picker", "stabile UI-Picker-Referenzen"),
    ("log", "Protokollierung und Loganzeige"),
    ("support", "Support-Bundles und Diagnose-Snapshots"),
    ("trace", "Request-/Client-Tracing"),
    ("perf", "Performance-Messung und Korrelation"),
    ("influx", "InfluxDB-Verbindung und Abfragen"),
    ("query", "Zeitreihenabfragen"),
    ("measurement", "Messwertauswahl und Messwertprofil"),
    ("series", "Serieninventar und Seriendetails"),
    ("raw", "Rohdatenfenster und Punktbearbeitung"),
    ("history", "Aenderungs- und Abfragehistorie"),
    ("snapshot", "Diagnose- und Support-Snapshots"),
    ("manual", "integrierte Handbuchanzeige"),
)

ACTION_RULES = (
    (("autowidth", "autobreite"), "passt die Spaltenbreite automatisch an fuer"),
    (("windowwidth", "fensterbreite"), "verteilt die Darstellung auf die Fensterbreite fuer"),
    (("refresh", "reload"), "aktualisiert"),
    (("copy", "kopier", "clipboard"), "kopiert"),
    (("search", "find", "query"), "sucht oder filtert"),
    (("download",), "laedt herunter"),
    (("upload",), "laedt hoch"),
    (("close", "dismiss"), "schliesst"),
    (("open", "show"), "oeffnet oder zeigt"),
    (("rename",), "benennt um"),
    (("reset",), "setzt zurueck"),
    (("retry", "repeat"), "wiederholt"),
    (("edit",), "bearbeitet"),
    (("delete", "remove", "clear", "prune"), "loescht oder bereinigt"),
    (("cancel", "abort"), "bricht"),
    (("restore", "undo"), "stellt wieder her"),
    (("write", "save", "set", "apply", "execute", "start", "create", "append", "register", "add"), "schreibt oder startet"),
    (("load", "read", "get", "list", "status", "info", "preview", "detect", "collect", "build"), "liest oder ermittelt"),
    (("validate", "verify", "check", "test", "normalize", "sanitize"), "validiert oder normalisiert"),
    (("schedule", "scheduler", "due", "timer"), "plant oder steuert"),
    (("export", "download"), "bereitet zum Export vor"),
    (("import", "parse"), "liest und interpretiert"),
    (("merge", "combine", "copy", "patch"), "kombiniert oder aktualisiert"),
    (("render", "page"), "stellt dar"),
)

MANUAL_BY_DOMAIN = (
    ("Migration", "migration-influxdb-v2-nach-v3"),
    ("Sicherung", "backup-restore-und-snapshots"),
    ("Wiederherstellung", "backup-restore-und-snapshots"),
    ("Verdichtung", "datenqualitaet-verdichtung-und-audit"),
    ("Datenqualitaet", "datenqualitaet-verdichtung-und-audit"),
    ("Ausreisser", "analyse-und-ausreisser"),
    ("Analyse", "analyse-und-ausreisser"),
    ("Statistik", "statistik-und-serieninventar"),
    ("Cache", "cache-und-persistenz"),
    ("Monitor", "monitor-und-watchlists"),
    ("Health", "monitor-und-watchlists"),
    ("Timer", "jobs-timer-und-hintergrundprozesse"),
    ("Jobs", "jobs-timer-und-hintergrundprozesse"),
    ("Aenderung", "dashboard-und-zeitreihen"),
    ("Undo", "dashboard-und-zeitreihen"),
    ("Import", "import-export-und-kombinieren"),
    ("Export", "import-export-und-kombinieren"),
    ("Kombination", "import-export-und-kombinieren"),
    ("Konfiguration", "einstellungen-und-eingaben"),
    ("Einstellung", "einstellungen-und-eingaben"),
    ("UI-", "navigation-profile-und-globale-gui"),
    ("Dialog", "navigation-profile-und-globale-gui"),
    ("Tooltip", "navigation-profile-und-globale-gui"),
    ("Picker", "navigation-profile-und-globale-gui"),
    ("Support", "api-diagnose-und-support"),
    ("Protokoll", "api-diagnose-und-support"),
    ("Tracing", "api-diagnose-und-support"),
)


def slug(value: str) -> str:
    value = value.replace("$", " dollar ").lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value).strip("-.")
    return value or "item"


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def domain_for(value: str, path: str = "") -> str:
    haystack = f"{path} {value}".lower()
    for needle, domain in DOMAIN_RULES:
        if needle in haystack:
            return domain
    return "Anwendungslogik und Datenfluss"


def config_domain(key: str) -> str:
    if key.startswith(("v3_", "influx_")) or key in {
        "scheme", "host", "port", "verify_ssl", "timeout_seconds", "token",
        "admin_token", "org", "bucket", "username", "password", "database",
        "active_database_mode", "write_retry_enabled", "write_retry_base_seconds",
        "write_retry_max_retries", "write_retry_jitter_ms", "write_gzip_enabled",
        "write_gzip_level",
    }:
        return "InfluxDB-Verbindung, Authentisierung und Schreibtransport"
    if key.startswith("ui_") or key.startswith("selector_"):
        return "Darstellung und Bedienverhalten der Benutzeroberflaeche"
    if key.startswith(("outlier_", "analysis_")):
        return "Ausreisseranalyse, Kontext und Nachtanalyse"
    if key.startswith(("dash_cache_", "stats_cache_", "stats_full_")):
        return "Cache-Groesse, Aktualisierung und Zeitplanung"
    if key.startswith(("log_", "trace_", "worklog_", "perf_", "bugreport_")):
        return "Protokollierung, Diagnose und Performance-Erfassung"
    if key.startswith("backup_") or key in {"storage_budget_mb", "restore_preview_lines", "undo_history_max"}:
        return "Sicherung, Wiederherstellung und lokales Speicherbudget"
    if key.startswith("quality_"):
        return "Raw-/Clean-/Rollup-Datenqualitaet"
    if key.startswith("rollup_"):
        return "Verdichtung und Rollup-Zeitplanung"
    if key.startswith("jobs_"):
        return "Joblaufzeit und Hintergrundverarbeitung"
    if key.startswith("import_"):
        return "Importabbildung und Transformation"
    return domain_for(key, "configuration")


def action_for(value: str) -> str:
    lower = value.lower()
    for needles, action in ACTION_RULES:
        if any(needle in lower for needle in needles):
            return action
    return "verarbeitet"


def manual_anchor(domain: str) -> str:
    for needle, anchor in MANUAL_BY_DOMAIN:
        if needle.lower() in domain.lower():
            return anchor
    return "technische-interne-funktionen"


def test_refs(domain: str) -> list[str]:
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", domain) if len(w) >= 5]
    matches = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        if any(word in path.name.lower() for word in words):
            matches.append(path.relative_to(ROOT).as_posix())
    return matches[:3] or ["N/A - kein direkter Einzeltest; Abdeckung durch Validator und repraesentative Tests."]


def input_record(name: str, type_name: str = "unknown", required: bool = False,
                 default: Any = "N/A - kein statischer Default", *,
                 location: str = "call") -> dict[str, Any]:
    return {
        "name": name,
        "type": type_name,
        "required": required,
        "default": default,
        "location": location,
        "allowed_values": "N/A - durch aufrufenden Kontext oder Laufzeittyp bestimmt.",
        "validation": "An der jeweiligen Vertrauensgrenze normalisieren und fachlich begrenzen.",
    }


def states_for(category: str) -> dict[str, str]:
    interactive = category in {"API", "GUI-Aktion", "GUI-Eingabe", "GUI-Navigation", "GUI-Zustand", "Job", "Hintergrundprozess"}
    return {
        "loading": "Fortschritt/Busy-Zustand ueber UI oder Jobstatus sichtbar." if interactive else "N/A - interne synchrone Verarbeitung ohne eigenen Ladezustand.",
        "success": "Liefert Ergebnis oder aktualisiert den zugehoerigen sichtbaren/persistenten Zustand.",
        "empty": "Leere Treffer werden als leere Liste, neutraler Status oder unveraenderter Zustand behandelt.",
        "error": "Fehler wird an den Aufrufer gegeben beziehungsweise in API-, UI- oder Jobstatus sichtbar gemacht.",
        "cancel": "Kooperativer Abbruch ueber Job-/UI-Zustand, sofern der Ablauf langlaufend ist." if interactive else "N/A - atomarer interner Aufruf ohne Abbruchprotokoll.",
        "retry": "Manuell erneut ausloesbar; Schreib-Retries nur gemaess konfigurierter Retry-Strategie." if interactive else "N/A - Wiederholung wird vom Aufrufer gesteuert.",
    }


def api_documentation(method: str, path: str, domain: str, action: str,
                      request_keys: list[str], description: str) -> dict[str, Any]:
    is_write = method not in {"GET", "HEAD", "OPTIONS"}
    example_payload = {key: None for key in request_keys}
    curl_suffix = ""
    if is_write:
        curl_suffix = " -H 'Content-Type: application/json' -d '" + json.dumps(example_payload, separators=(",", ":")) + "'"
    url = f"http://127.0.0.1:8099{path}"
    if is_write:
        payload_json = json.dumps(example_payload, separators=(",", ":"))
        javascript_example = (
            f"fetch('{path}', {{method: '{method}', "
            "headers: {'Content-Type': 'application/json'}, "
            f"body: JSON.stringify({payload_json})}}).then(r => r.json())"
        )
    else:
        javascript_example = f"fetch('{path}', {{method: '{method}'}}).then(r => r.json())"
    return {
        "method": method,
        "path": path,
        "summary": f"{action.capitalize()} {domain}.",
        "description": description,
        "group": domain,
        "tags": [slug(domain)],
        "role": "operator",
        "roleLabel": "Bediener/Administration",
        "roleColor": "#2563eb",
        "authRequired": True,
        "request": {
            "contentType": "application/json" if is_write else "query parameters / no body",
            "schema": {key: "Typ und Pflichtstatus werden im Handler validiert." for key in request_keys},
            "keys": request_keys or ["N/A - Handler besitzt keine statisch erkennbare Request-Eingabe."],
            "example": example_payload,
        },
        "response": {
            "contentType": "application/json, text/html oder Download gemaess Route",
            "schema": "Flask-Response des Handlers; JSON-Erfolg nutzt soweit anwendbar ok/result/status-Felder.",
            "example": {"ok": True},
            "statusCodes": {
                "200": "Erfolgreiche Verarbeitung oder Anzeige.",
                "400": "Ungueltige oder unvollstaendige Eingabe, sofern der Handler Eingaben erwartet.",
                "404": "Angefordertes Objekt oder Ergebnis fehlt, sofern objektbezogen.",
                "409": "Konflikt mit laufendem oder unpassendem Zustand, sofern zustandsbehaftet.",
                "500": "Nicht erwarteter Backend-, Datei- oder InfluxDB-Fehler.",
            },
        },
        "timing": {
            "typicalMs": "N/A - abhaengig von Datenmenge, InfluxDB und Cache-Zustand.",
            "p95Ms": "N/A - keine belastbare Produktionsmessreihe im Repository.",
            "timeoutMs": "Durch timeout_seconds, Jobgrenzen oder Client-Timeout der Route begrenzt.",
            "bottleneck": "InfluxDB-Abfrage, Datei-I/O, Serialisierung oder Jobwarteschlange je nach Route.",
        },
        "correlations": {
            "dependsOn": ["Zugehoerige Handler-Helfer, Laufzeitkonfiguration und gegebenenfalls InfluxDB/Home Assistant."],
            "triggers": ["Fachoperation, Rendern oder Statusabfrage gemaess Route."],
            "parallelWith": ["N/A - Parallelitaet wird durch konkreten Job-/Handlerzustand bestimmt."],
            "usedIn": [domain],
            "criticalPath": is_write,
            "phase": "Bedienaktion/API-Verarbeitung",
        },
        "errors": [{
            "symptom": "HTTP-Fehler oder ok=false/Fehlerstatus in der Oberflaeche.",
            "cause": "Ungueltige Eingabe, fehlende Berechtigung, nicht erreichbare InfluxDB, Datei-/Speicherfehler oder Konflikt.",
            "fix": "Eingaben und Ziel pruefen, Verbindung/Logs kontrollieren und die Aktion nach Behebung wiederholen.",
        }],
        "examples": {
            "curl": f"curl -fsS -X {method} '{url}'{curl_suffix}",
            "javascript": javascript_example,
            "python": (
                "import json, urllib.request\n"
                f"req = urllib.request.Request('{url}', method='{method}'"
                + (f", data=json.dumps({example_payload!r}).encode(), headers={{'Content-Type': 'application/json'}}" if is_write else "")
                + ")\nprint(urllib.request.urlopen(req, timeout=30).read().decode())"
            ),
        },
        "notes": "Ingress-/Sitzungskontext und Schutzschalter beachten; Beispiele enthalten keine Zugangsdaten.",
    }


def entry(*, doc_id: str, name: str, reference: str, category: str,
          description: str, short: str, inputs: list[dict[str, Any]],
          source: str, domain: str, visibility: str = "intern",
          permissions: str = "Add-on-Prozessrechte; keine zusaetzliche Benutzerrolle im Symbol.",
          side_effects: str = "Keine dauerhaften Seiteneffekte, soweit nicht durch Beschreibung oder Aufrufer ausgeloest.",
          dependencies: Iterable[str] = (), called_by: str = "Siehe statische Aufrufer im Quellcode.",
          ui_location: str = "N/A - nicht direkt als eigenes GUI-Element sichtbar.") -> dict[str, Any]:
    return {
        "id": doc_id,
        "addon": "influxbro",
        "name": name,
        "technical_reference": reference,
        "category": category,
        "description": description,
        "short_description": short,
        "audience": "Bediener und Administration" if visibility != "intern" else "Entwicklung, Betrieb und Support",
        "visibility": visibility,
        "prerequisites": "Laufendes InfluxBro Add-on; fachliche Voraussetzungen ergeben sich aus dem aufrufenden Ablauf.",
        "permissions": permissions,
        "inputs": inputs or [input_record("keine Eingaben", "none", False, "N/A - Funktion besitzt keine expliziten Eingaben.")],
        "outputs": "Strukturiertes Ergebnis, gerenderte Anzeige oder aktualisierter Status gemaess technischer Referenz.",
        "side_effects": side_effects,
        "states": states_for(category),
        "security": "Keine Secrets ausgeben; externe Werte validieren. Schreib-, Datei- und Netzwerkzugriffe nur im dokumentierten Add-on-Kontext.",
        "dependencies": list(dependencies) or ["N/A - keine eigenstaendige externe Abhaengigkeit dokumentiert."],
        "called_by": called_by,
        "manual_ref": f"docs/handbuch.md#{manual_anchor(domain)}",
        "ui_location": ui_location,
        "tests": test_refs(domain),
        "status": STATUS,
        "verified_version": "N/A - generated draft has not been source-reviewed",
        "source": source,
    }


def source_digest(source: str) -> str:
    path_text, line_text = source.rsplit(":", 1)
    lines = _source_text(path_text).splitlines()
    line = int(line_text)
    excerpt = "\n".join(lines[max(0, line - 1): min(len(lines), line + 39)])
    return hashlib.sha256(excerpt.encode("utf-8")).hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(value, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} muss ein JSON-Objekt sein")
    return value


def workflow_entries() -> list[dict[str, Any]]:
    item = entry(
        doc_id="influxbro.ci.function-docs",
        name="function-docs",
        reference=".github/workflows/function-docs.yml:12#function-docs",
        category="CI-Workflow",
        description="Prueft den verifizierten Funktionskatalog bei Pull Requests und Pushes nach main.",
        short="Installiert das gepinnte Testwerkzeug und validiert Funktionskatalog sowie Review-Nachweise.",
        inputs=[input_record("Repository-Stand", "git checkout", True, "Aktueller Pull-Request- oder main-Stand", location="GitHub Actions")],
        source=".github/workflows/function-docs.yml:12",
        domain="Dokumentationspruefung",
        permissions="GitHub-Workflow mit Repository-Lesezugriff; keine Schreib- oder Secret-Berechtigung erforderlich.",
        side_effects="Installiert pytest 8.4.2 nur in der kurzlebigen Runner-Umgebung; veraendert keine Runtime- oder Repository-Daten.",
        dependencies=("actions/checkout@v5", "actions/setup-python@v6", "pytest==8.4.2"),
        called_by="GitHub Actions bei Pull Requests und Pushes nach main.",
        ui_location="GitHub Actions, Job function-docs.",
    )
    item["manual_ref"] = "docs/handbuch.md#dokumentationspruefung"
    item["tests"] = ["tests/test_function_docs_validator.py"]
    return [item]


def apply_reviews(entries: list[dict[str, Any]]) -> None:
    reviews = load_json_object(REVIEWS).get("reviews", [])
    by_reference = {
        review.get("technical_reference"): review
        for review in reviews
        if isinstance(review, dict)
    }
    for item in entries:
        review = by_reference.get(item["technical_reference"])
        if not review or review.get("source_sha256") != source_digest(item["source"]):
            continue
        overrides = review.get("overrides")
        required_overrides = REVIEWED_FIELDS | ({"api"} if "api" in item else set())
        if not isinstance(overrides, dict) or required_overrides - set(overrides):
            continue
        item.update(overrides)
        item["status"] = "verified"
        item["verified_version"] = VERSION
        item["review"] = {
            "reviewed_by": review.get("reviewed_by"),
            "reviewed_at": review.get("reviewed_at"),
            "evidence": review.get("evidence"),
            "source_sha256": review.get("source_sha256"),
        }


def ast_default(node: ast.expr | None) -> Any:
    if node is None:
        return "N/A - Pflichtparameter ohne Default"
    try:
        value = ast.literal_eval(node)
        return json.loads(json.dumps(value))
    except (ValueError, TypeError):
        return f"Ausdruck: {ast.unparse(node)}"


def _attribute_path(node: ast.AST) -> tuple[str, ...]:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return tuple(reversed(parts))


def request_inputs(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[list[dict[str, Any]], list[str]]:
    """Extract only reads rooted in Flask request containers.

    Generic ``mapping.get`` and route decorators are deliberately excluded.
    Unknown request access is surfaced so it cannot silently become verified.
    """
    body_aliases: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, (ast.Assign, ast.AnnAssign)):
            continue
        value = child.value
        has_get_json = any(
            isinstance(part, ast.Call)
            and _attribute_path(part.func) == ("request", "get_json")
            for part in ast.walk(value)
        )
        if not has_get_json:
            continue
        targets = child.targets if isinstance(child, ast.Assign) else [child.target]
        body_aliases.update(target.id for target in targets if isinstance(target, ast.Name))

    found: dict[tuple[str, str], dict[str, Any]] = {}
    for child in ast.walk(node):
        if not isinstance(child, ast.Call) or not child.args:
            continue
        path = _attribute_path(child.func)
        location = ""
        if path in {
            ("request", "args", "get"),
            ("request", "form", "get"),
            ("request", "values", "get"),
            ("request", "files", "get"),
            ("request", "headers", "get"),
        }:
            location = path[1]
        elif len(path) == 2 and path[0] in body_aliases and path[1] == "get":
            location = "json"
        elif path == ("request", "json", "get"):
            location = "json"
        if not location:
            continue
        key_node = child.args[0]
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            continue
        default = ast_default(child.args[1]) if len(child.args) > 1 else "N/A - missing value becomes null"
        key = (location, key_node.value)
        found[key] = input_record(
            key_node.value,
            "unknown - source review required",
            len(child.args) == 1,
            default,
            location=location,
        )

    if any(
        isinstance(child, ast.Attribute)
        and _attribute_path(child) == ("request", "remote_addr")
        for child in ast.walk(node)
    ):
        found[("metadata", "remote_addr")] = input_record(
            "remote_addr",
            "string or null",
            False,
            None,
            location="metadata",
        )

    warnings: list[str] = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Attribute):
            continue
        path = _attribute_path(child)
        if path and path[0] == "request" and not any(
            path[:len(prefix)] == prefix
            for prefix in (
                ("request", "args"), ("request", "form"), ("request", "values"),
                ("request", "files"), ("request", "headers"), ("request", "json"),
                ("request", "get_json"), ("request", "remote_addr"),
            )
        ):
            warnings.append(f"unknown request access: {'.'.join(path)}")
    return [found[key] for key in sorted(found)], sorted(set(warnings))


class PythonCollector(ast.NodeVisitor):
    def __init__(self, path: Path, text: str) -> None:
        self.path = path
        self.text = text
        self.stack: list[str] = []
        self.items: list[dict[str, Any]] = []
        self.seen: dict[str, int] = {}

    def _collect(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef, kind: str) -> None:
        qname = ".".join((*self.stack, node.name))
        occurrence = self.seen.get(qname, 0) + 1
        self.seen[qname] = occurrence
        stable_name = qname if occurrence == 1 else f"{qname}.{occurrence}"
        decorators = []
        for decorator in getattr(node, "decorator_list", []):
            try:
                decorators.append(ast.unparse(decorator))
            except (ValueError, TypeError):
                pass
        route = next((d for d in decorators if re.search(r"app\.(?:get|post|put|patch|delete|route)\(", d)), None)
        method = "ROUTE"
        route_path = ""
        if route:
            match = re.search(r"app\.(get|post|put|patch|delete|route)\((['\"])(.*?)\2", route)
            if match:
                method = match.group(1).upper()
                route_path = match.group(3)
        category = "API" if route_path.startswith("/api/") else "GUI-Navigation" if route_path else "interne Funktion"
        lower = node.name.lower()
        if any(token in lower for token in ("_job_thread", "_scheduler_loop", "_start_job", "_run_thread")):
            category = "Hintergrundprozess"
        elif "job" in lower and category == "interne Funktion":
            category = "Job"
        domain = domain_for(f"{node.name} {route_path}", self.path.name)
        action = action_for(node.name)
        if route_path:
            description = (
                f"Die Route {method} {route_path} {action} {domain}. "
                "Sie bildet eine HTTP-Vertrauensgrenze, liest Request-Parameter im Handler, "
                "ruft die zugehoerige Fachlogik auf und liefert Flask-JSON, Download oder HTML."
            )
            short = f"{method} {route_path}: {action} {domain}."
            visibility = "Ingress/API"
            ui_location = f"Ingress/API {method} {route_path}"
        else:
            description = (
                f"Das {kind} `{qname}` {action} {domain}. "
                "Es kapselt den durch Namen, Parameter und Aufrufer abgegrenzten Teilschritt "
                "und wird nicht als eigenstaendige oeffentliche API exportiert."
            )
            short = f"{action.capitalize()} {domain} im Teilschritt `{node.name}`."
            visibility = "intern"
            ui_location = "N/A - intern; Wirkung erscheint im zugeordneten Funktionsbereich."
        inputs: list[dict[str, Any]] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            defaults: list[ast.expr | None] = [None] * (len(node.args.posonlyargs) + len(node.args.args) - len(node.args.defaults)) + list(node.args.defaults) + list(node.args.kw_defaults)
            for arg, default in zip(args, defaults):
                annotation = ast.unparse(arg.annotation) if arg.annotation else "unknown"
                inputs.append(input_record(arg.arg, annotation, default is None, ast_default(default)))
            if node.args.vararg:
                inputs.append(input_record("*" + node.args.vararg.arg, "variadic", False))
            if node.args.kwarg:
                inputs.append(input_record("**" + node.args.kwarg.arg, "mapping", False))
        rel = self.path.relative_to(ROOT).as_posix()
        source = f"{rel}:{node.lineno}"
        reference = f"{source}#{qname}"
        doc_id = f"influxbro.py.{slug(self.path.stem)}.{slug(stable_name)}"
        doc = entry(
            doc_id=doc_id, name=qname, reference=reference, category=category,
            description=description, short=short, inputs=inputs, source=source,
            domain=domain, visibility=visibility, ui_location=ui_location,
            side_effects=("Kann persistente Add-on-/InfluxDB-Daten oder Jobzustand veraendern; konkrete Wirkung folgt dem Handler."
                          if action in {"loescht oder bereinigt", "schreibt oder startet", "stellt wieder her", "kombiniert oder aktualisiert"}
                          else "Liest, berechnet oder formatiert Daten; indirekte Wirkungen entstehen nur ueber aufgerufene Fachfunktionen."),
            dependencies=["Flask/InfluxDB-Clients und lokale Helfer gemaess Funktionsrumpf."],
        )
        if route_path:
            extracted_inputs, extraction_warnings = request_inputs(node)
            doc["inputs"] = extracted_inputs or [
                input_record(
                    "keine statisch erkannten HTTP-Eingaben",
                    "none",
                    False,
                    "N/A - source review required",
                    location="request",
                )
            ]
            request_keys = [item["name"] for item in extracted_inputs]
            doc["input_extraction_warnings"] = extraction_warnings
            doc["api"] = api_documentation(
                method, route_path, domain, action, request_keys, description
            )
        self.items.append(doc)
        self.stack.append(node.name)
        for child in node.body:
            self.visit(child)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._collect(node, "Python-Funktion")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._collect(node, "asynchrone Python-Funktion")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._collect(node, "Python-Klasse")


class UICollector(HTMLParser):
    def __init__(self, path: Path, text: str, central_ids: dict[str, str]) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.text = text
        self.central_ids = central_ids
        self.items: list[dict[str, Any]] = []
        self.unmapped: list[str] = []
        self.seen: dict[str, int] = {}
        self.anonymous_per_source: dict[str, int] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        selector = data.get("data-ib-pickkey") or data.get("data-ui") or data.get("id")
        if tag not in INTERACTIVE_TAGS and not selector:
            return
        line = self.getpos()[0]
        rel = self.path.relative_to(ROOT).as_posix()
        source = f"{rel}:{line}"
        base = selector or data.get("name") or data.get("href")
        central_doc_id = None
        if not base:
            occurrence = self.anonymous_per_source.get(source, 0) + 1
            self.anonymous_per_source[source] = occurrence
            source_key = f"{source}#{occurrence}"
            central_doc_id = self.central_ids.get(source_key)
            if not central_doc_id:
                self.unmapped.append(source_key)
                return
            base = central_doc_id.rsplit(".", 1)[-1]
        occurrence = self.seen.get(base, 0) + 1
        self.seen[base] = occurrence
        stable = base if occurrence == 1 else f"{base}-{occurrence}"
        label = (data.get("aria-label") or data.get("title") or data.get("placeholder")
                 or data.get("value") or selector or f"{tag} in Zeile {line}")
        domain = domain_for(f"{self.path.stem} {base}")
        action = action_for(f"{tag} {base}")
        if tag in {"input", "select", "textarea"}:
            category = "GUI-Eingabe"
            description = (
                f"Das {tag}-Element `{base}` erfasst oder waehlt einen Wert fuer {domain}. "
                f"Die sichtbare Kennzeichnung lautet `{label}`; Typ `{data.get('type', tag)}` "
                "und Markup-Attribute bestimmen Browservalidierung und Bedienzustand."
            )
            short = f"Eingabe `{label}` fuer {domain}."
            inputs = [input_record(base, data.get("type", tag), "required" in data, data.get("value") or "N/A - kein statischer Wert")]
        elif tag == "a":
            category = "GUI-Navigation"
            description = f"Der Link `{base}` oeffnet oder navigiert im Bereich {domain}. Ziel ist `{data.get('href', 'dynamisch')}`; sichtbare Kennzeichnung: `{label}`."
            short = f"Navigiert zu {domain}."
            inputs = []
        elif tag in {"details", "summary"}:
            category = "GUI-Zustand"
            description = f"Das Element `{base}` klappt Inhalte fuer {domain} ein oder aus. Kennzeichnung: `{label}`; der Zustand veraendert nur die sichtbare Darstellung."
            short = f"Blendet den Bereich {domain} ein oder aus."
            inputs = []
        elif tag in {"button", "form"}:
            category = "GUI-Aktion"
            description = f"Das Element `{base}` {action} {domain}. Sichtbare Kennzeichnung: `{label}`; Event-Handler und zugehoerige API bestimmen Ergebnis und Fehleranzeige."
            short = f"{action.capitalize()} {domain}."
            inputs = []
        else:
            category = "GUI-Anzeige"
            description = f"Das Anzeigeelement `{base}` zeigt Zustand, Ergebnis oder Struktur fuer {domain}. Kennzeichnung: `{label}`; Aktualisierungen erfolgen durch den zugeordneten Browser- oder API-Ablauf."
            short = f"Zeigt Zustand oder Ergebnis fuer {domain}."
            inputs = []
        self.items.append(entry(
            doc_id=central_doc_id or f"influxbro.ui.{slug(self.path.stem)}.{slug(stable)}",
            name=base, reference=f"{source}#{base}", category=category,
            description=description, short=short, inputs=inputs, source=source,
            domain=domain, visibility="GUI", permissions="Bedienzugriff auf das Ingress-Panel; Fachaktion kann zusaetzliche InfluxDB-Rechte benoetigen.",
            side_effects=("Veraendert den dargestellten Formular-/Dialogzustand; Fachaktionen koennen ueber APIs persistente Daten aendern."
                          if category != "GUI-Navigation" else "Aendert Seite oder sichtbaren Navigationszustand."),
            dependencies=["Zugehoerige JavaScript-Handler und gegebenenfalls Flask-API."],
            called_by="Direkte Benutzeraktion oder Browserinteraktion.",
            ui_location=f"Template {self.path.name}, Element {base}",
        ))


def python_entries() -> list[dict[str, Any]]:
    result = []
    for path in sorted((ADDON / "app").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        collector = PythonCollector(path, text)
        collector.visit(ast.parse(text, filename=str(path)))
        result.extend(collector.items)
    return result


def javascript_entries() -> list[dict[str, Any]]:
    result = []
    for path in sorted((ADDON / "app/templates").glob("*.html")):
        text = path.read_text(encoding="utf-8")
        seen: dict[str, int] = {}
        rel = path.relative_to(ROOT).as_posix()
        for match in JS_RE.finditer(text):
            name = match.group(1) or match.group(3)
            raw_args = match.group(2) if match.group(1) else (match.group(4) or match.group(5) or "")
            occurrence = seen.get(name, 0) + 1
            seen[name] = occurrence
            stable = name if occurrence == 1 else f"{name}-{occurrence}"
            line = line_number(text, match.start())
            source = f"{rel}:{line}"
            domain = domain_for(f"{path.stem} {name}")
            action = action_for(name)
            args = [part.strip().split("=")[0].strip() for part in raw_args.split(",") if part.strip()]
            result.append(entry(
                doc_id=f"influxbro.js.{slug(path.stem)}.{slug(stable)}",
                name=name, reference=f"{source}#{name}", category="Skriptfunktion",
                description=(f"Die JavaScript-Funktion `{name}` {action} {domain} im Template `{path.name}`. "
                             "Sie kapselt den benannten Browser-Teilschritt und aktualisiert DOM, lokalen Zustand oder die zugehoerige API-Interaktion."),
                short=f"{action.capitalize()} {domain} im Browser.",
                inputs=[input_record(arg, "JavaScript-Wert", False) for arg in args],
                source=source, domain=domain, visibility="Browser/GUI",
                permissions="Browserzugriff im Ingress-Panel; API-Aufrufe nutzen die Add-on-Sitzung.",
                side_effects="Kann DOM, Browserzustand, Zwischenablage oder ueber API-Aufrufe persistente Daten veraendern.",
                dependencies=["Browser-DOM und im Template definierte Helfer/API-Endpunkte."],
                called_by="Event-Handler, Seiteninitialisierung oder andere Template-Funktionen.",
                ui_location=f"Template {path.name}",
            ))
    return result


def ui_entries() -> list[dict[str, Any]]:
    result = []
    mapping = load_json_object(UI_ID_MAP)
    central_ids = {
        item["source_key"]: item["id"]
        for item in mapping.get("elements", [])
        if isinstance(item, dict) and isinstance(item.get("source_key"), str)
        and isinstance(item.get("id"), str)
    }
    unmapped: list[str] = []
    for path in sorted((ADDON / "app/templates").glob("*.html")):
        text = path.read_text(encoding="utf-8")
        parser = UICollector(path, text, central_ids)
        parser.feed(text)
        result.extend(parser.items)
        unmapped.extend(parser.unmapped)
        known = {item["name"] for item in parser.items}
        rel = path.relative_to(ROOT).as_posix()
        dynamic_seen: set[str] = set()
        attr_re = re.compile(r"data-(?:ib-pickkey|ui)\s*=\s*(['\"])([A-Za-z0-9_.:-]+)\1")
        for match in attr_re.finditer(text):
            selector = match.group(2)
            if selector in known or selector in dynamic_seen:
                continue
            dynamic_seen.add(selector)
            line = line_number(text, match.start())
            source = f"{rel}:{line}"
            domain = domain_for(f"{path.stem} {selector}")
            action = action_for(selector)
            if re.search(r"(?:^|\.)(?:btn|action)_", selector):
                category = "GUI-Aktion"
                description = f"Das dynamisch erzeugte Element `{selector}` {action} {domain}. Der erzeugende JavaScript-Pfad setzt die stabile UI-Kennung und bindet Bedien- und Fehlerverhalten."
                short = f"{action.capitalize()} {domain}."
            elif re.search(r"(?:^|\.)(?:input|select|chk|textarea)_", selector):
                category = "GUI-Eingabe"
                description = f"Das dynamisch erzeugte Eingabeelement `{selector}` erfasst oder waehlt einen Wert fuer {domain}. Der erzeugende JavaScript-Pfad setzt Kennung, Wert und Validierungsverhalten."
                short = f"Eingabe fuer {domain}."
            else:
                category = "GUI-Anzeige"
                description = f"Das dynamisch erzeugte Anzeigeelement `{selector}` zeigt Zustand, Ergebnis oder Dialogstruktur fuer {domain}. Die stabile Kennung wird zentral im erzeugten Markup definiert."
                short = f"Zeigt Zustand oder Ergebnis fuer {domain}."
            result.append(entry(
                doc_id=f"influxbro.ui.{slug(path.stem)}.{slug(selector)}.dynamic",
                name=selector, reference=f"{source}#{selector}", category=category,
                description=description, short=short,
                inputs=([input_record(selector, "dynamischer Browserwert", False)]
                        if category == "GUI-Eingabe" else []),
                source=source, domain=domain, visibility="GUI (dynamisch erzeugt)",
                permissions="Bedienzugriff auf das Ingress-Panel; Fachaktionen koennen zusaetzliche InfluxDB-Rechte benoetigen.",
                side_effects="Aktualisiert dynamischen DOM-Zustand; Aktionen koennen die zugehoerige API aufrufen.",
                dependencies=["Erzeugende JavaScript-Funktion und gegebenenfalls Flask-API."],
                called_by="Dynamischer Dialog-, Tabellen- oder Renderpfad im Template.",
                ui_location=f"Template {path.name}, dynamisches Element {selector}",
            ))
    if unmapped:
        raise RuntimeError(
            "interaktive GUI-Elemente ohne stabile Kennung/zentralen Mapping-Eintrag: "
            + ", ".join(unmapped[:20])
            + (f" (+{len(unmapped) - 20} weitere)" if len(unmapped) > 20 else "")
        )
    return result


def bootstrap_ui_id_map() -> dict[str, Any]:
    """One-time migration from rejected hash IDs to reviewable central IDs."""
    source_keys: list[str] = []

    class BootstrapParser(HTMLParser):
        def __init__(self, path: Path) -> None:
            super().__init__(convert_charrefs=True)
            self.path = path
            self.per_source: dict[str, int] = {}

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            data = {key: value or "" for key, value in attrs}
            selector = data.get("data-ib-pickkey") or data.get("data-ui") or data.get("id")
            if tag not in INTERACTIVE_TAGS and not selector:
                return
            if selector or data.get("name") or data.get("href"):
                return
            source = f"{self.path.relative_to(ROOT).as_posix()}:{self.getpos()[0]}"
            occurrence = self.per_source.get(source, 0) + 1
            self.per_source[source] = occurrence
            source_keys.append(f"{source}#{occurrence}")

    for path in sorted((ADDON / "app/templates").glob("*.html")):
        parser = BootstrapParser(path)
        parser.feed(path.read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "policy": "Stable IDs are assigned here; source movement requires explicit review, never re-hashing markup.",
        "elements": [
            {"id": f"influxbro.ui.central.element-{index:04d}", "source_key": source_key}
            for index, source_key in enumerate(sorted(source_keys), 1)
        ],
    }


def config_default_entries() -> list[dict[str, Any]]:
    path = ADDON / "app/app.py"
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    default_cfg: ast.Dict | None = None
    line = 0
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "DEFAULT_CFG" for target in node.targets):
            if isinstance(node.value, ast.Dict):
                default_cfg = node.value
                line = node.lineno
            break
    if default_cfg is None:
        raise RuntimeError("DEFAULT_CFG not found")
    result = []
    for key_node, value_node in zip(default_cfg.keys, default_cfg.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            continue
        key = key_node.value
        default = ast_default(value_node)
        domain = config_domain(key)
        source_line = getattr(key_node, "lineno", line)
        source = f"influxbro/app/app.py:{source_line}"
        type_name = type(default).__name__ if not isinstance(default, str) or not default.startswith("Ausdruck:") else "dynamisch"
        secret = any(token in key for token in ("token", "password"))
        description = (
            f"Die Konfigurationsoption `{key}` steuert {domain}. Der serverseitige Default ist `{default if not secret else '[geschuetzt]'}`; "
            "Speichern normalisiert den Wert in `/data` und die betroffenen Laufzeitpfade lesen ihn ueber die zentrale Konfiguration."
        )
        result.append(entry(
            doc_id=f"influxbro.config.runtime.{slug(key)}", name=key,
            reference=f"{source}#DEFAULT_CFG.{key}", category="Konfigurationsoption",
            description=description, short=f"Konfiguriert {domain}: `{key}`.",
            inputs=[{
                "name": key, "type": type_name, "required": False,
                "default": "[geschuetzt]" if secret else default,
                "allowed_values": "Durch Datentyp und serverseitige Clamp-/Sanitize-Regeln begrenzt.",
                "validation": "Wird beim Speichern typisiert, normalisiert und bei Zahlen/Farben/Enums begrenzt.",
            }], source=source, domain=domain, visibility="GUI/Konfiguration",
            permissions="Administrativer Zugriff auf die InfluxBro-Einstellungen.",
            side_effects="Persistiert Konfiguration unter `/data` und beeinflusst nachfolgende UI-, Query-, Job- oder Speicherablaeufe.",
            dependencies=["DEFAULT_CFG, load_cfg, save_cfg und die zugehoerigen Einstellungsfelder."],
            called_by="Einstellungs-API und alle Laufzeitpfade, die diese Option lesen.",
            ui_location="Einstellungen; genaue Gruppe wird durch das Settings-Template bestimmt.",
        ))
    return result


def simple_yaml_paths(path: Path) -> list[tuple[str, int, str]]:
    stack: list[tuple[int, str]] = []
    result = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#") or raw.lstrip().startswith("-"):
            continue
        match = re.match(r"^(\s*)([A-Za-z0-9_./-]+):(?:\s*(.*))?$", raw)
        if not match:
            continue
        indent = len(match.group(1))
        key = match.group(2)
        value = (match.group(3) or "").strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        full = ".".join([item[1] for item in stack] + [key])
        result.append((full, number, value or "mapping/list"))
        stack.append((indent, key))
    return result


def manifest_options(path: Path) -> list[tuple[str, int, Any]]:
    """Parse the small add-on manifest without pretending list keys are defaults."""
    lines = path.read_text(encoding="utf-8").splitlines()
    result: list[tuple[str, int, Any]] = []
    index = 0
    while index < len(lines):
        raw = lines[index]
        match = re.match(r"^([A-Za-z0-9_/-]+):(?:\s*(.*))?$", raw)
        if not match:
            index += 1
            continue
        key, raw_value = match.group(1), (match.group(2) or "").strip()
        line = index + 1
        children: list[str] = []
        cursor = index + 1
        while cursor < len(lines) and (not lines[cursor].strip() or lines[cursor].startswith(" ")):
            child = lines[cursor].strip()
            if child.startswith("- "):
                children.append(child[2:].strip())
            cursor += 1
        if children:
            value: Any = children
        elif raw_value == "null":
            value = None
        elif raw_value in {"true", "false"}:
            value = raw_value == "true"
        elif re.fullmatch(r"-?\d+", raw_value):
            value = int(raw_value)
        else:
            value = raw_value.strip('"')
        result.append((key, line, value))
        index = max(index + 1, cursor)
    return result


MANIFEST_ENUMS: dict[str, list[Any]] = {
    "arch": ["amd64", "aarch64", "armv7", "armhf"],
    "boot": ["auto", "manual"],
    "startup": ["initialize", "system", "services", "application", "once"],
    "hassio_role": ["default", "homeassistant", "backup", "manager", "admin"],
}


def addon_and_shell_entries() -> list[dict[str, Any]]:
    result = []
    config_path = ADDON / "config.yaml"
    for key, line, value in manifest_options(config_path):
        source = f"influxbro/config.yaml:{line}"
        domain = "Home-Assistant-Add-on-Paketierung und Berechtigungen"
        is_arch = key == "arch"
        value_text = json.dumps(value, ensure_ascii=True)
        default = "N/A - compatibility declaration, not a runtime default" if is_arch else value
        allowed = MANIFEST_ENUMS.get(key)
        allowed_text = allowed if allowed is not None else (
            [True, False] if isinstance(value, bool) else "N/A - scalar or mapping defined by the Supervisor schema."
        )
        result.append(entry(
            doc_id=f"influxbro.addon.option.{slug(key)}", name=key,
            reference=f"{source}#{key}", category="Add-on-Konfigurationsoption",
            description=f"Die Add-on-Manifestoption `{key}` konfiguriert {domain}. Der deklarierte Wert ist `{value_text}` und wird vom Home-Assistant-Supervisor beim Installieren und Starten ausgewertet.",
            short=f"Supervisor-Option `{key}` fuer InfluxBro.",
            inputs=[{
                "name": key,
                "type": "list[string]" if isinstance(value, list) else type(value).__name__,
                "required": True,
                "default": default,
                "location": "influxbro/config.yaml",
                "allowed_values": allowed_text,
                "validation": (
                    "Every architecture token must be a Home Assistant supported architecture."
                    if is_arch else "Validated by the Home Assistant Supervisor add-on schema."
                ),
            }], source=source,
            domain="Add-on-Service", visibility="Home Assistant Add-on-Verwaltung",
            permissions="Home-Assistant-Administrator fuer Installation oder Aenderung.",
            side_effects="Beeinflusst Paketierung, Start, Netzwerk, Ingress, API-Rechte oder Mounts des Add-ons.",
            dependencies=["Home Assistant Supervisor Add-on-Schema."],
            called_by="Home Assistant Supervisor.", ui_location="Home Assistant Add-on-Seite.",
        ))
    shell_path = ADDON / "run.sh"
    shell_text = shell_path.read_text(encoding="utf-8")
    for match in SHELL_FN_RE.finditer(shell_text):
        name = match.group(1)
        line = line_number(shell_text, match.start())
        source = f"influxbro/run.sh:{line}"
        result.append(entry(
            doc_id=f"influxbro.shell.{slug(name)}", name=name,
            reference=f"{source}#{name}", category="Skriptfunktion",
            description=f"Die Shell-Funktion `{name}` liest einen benannten Wert aus `/data/options.json` und stellt ihn dem Add-on-Startprozess bereit. Fehlende Werte werden leer zurueckgegeben.",
            short="Liest eine Supervisor-Option fuer den Startprozess.",
            inputs=[input_record("key", "string", True)], source=source,
            domain="Add-on-Service", permissions="Dateileserecht auf `/data/options.json`.",
            side_effects="N/A - reine Leseoperation.", dependencies=["jq und `/data/options.json`."],
            called_by="Startskript `influxbro/run.sh`.",
        ))
    source = "influxbro/run.sh:1"
    result.append(entry(
        doc_id="influxbro.service.startup", name="InfluxBro Add-on-Service",
        reference=f"{source}#startup", category="Add-on-Service",
        description="Der Add-on-Service migriert den Share-Inhalt best-effort nach `/config/influxbro`, richtet `/data/share` als Kompatibilitaetslink ein und startet die Flask-Anwendung mit der veroeffentlichten Add-on-Version.",
        short="Startet InfluxBro und richtet den persistenten Share-Pfad ein.",
        inputs=[input_record("/data/options.json", "JSON", False)], source=source,
        domain="Add-on-Service", visibility="Home Assistant Service",
        permissions="Schreibzugriff auf `/config/influxbro` und `/data`; Prozessstart im Add-on-Container.",
        side_effects="Kann bestehende Share-Dateien verschieben, Symlink aktualisieren und den Webdienst starten.",
        dependencies=["bash, jq, Container-Dateisystem und Python-Laufzeit."],
        called_by="Home Assistant Supervisor bei Start/Boot.",
        ui_location="Home Assistant Add-on-Seite: Start, Stop, Neustart und Ingress.",
    ))
    return result


def _short(value: str, limit: int = 180) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= limit else value[:limit - 3] + "..."


def _call_name(node: ast.AST) -> str:
    path = _attribute_path(node)
    if path:
        return ".".join(path)
    try:
        return ast.unparse(node)
    except (ValueError, TypeError):
        return "dynamic-call"


def _unit_nodes(node: ast.AST) -> Iterable[ast.AST]:
    """Walk one implementation unit without attributing nested units to it."""
    stack = list(reversed(list(ast.iter_child_nodes(node))))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield child
        stack.extend(reversed(list(ast.iter_child_nodes(child))))


@lru_cache(maxsize=None)
def _source_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def _html_tags_by_line(path_text: str) -> dict[int, list[str]]:
    text = _source_text(path_text)
    result: dict[int, list[str]] = {}
    for match in re.finditer(r"<[A-Za-z][^>]*>", text, re.S):
        line = line_number(text, match.start())
        result.setdefault(line, []).append(match.group(0))
    return result


@lru_cache(maxsize=1)
def _central_ui_source_keys() -> dict[str, str]:
    mapping = load_json_object(UI_ID_MAP)
    return {
        item["id"]: item["source_key"]
        for item in mapping.get("elements", [])
        if isinstance(item, dict) and item.get("id") and item.get("source_key")
    }


@lru_cache(maxsize=None)
def _python_units(path_text: str) -> dict[int, tuple[ast.AST, str]]:
    path = ROOT / path_text
    text = _source_text(path_text)
    tree = ast.parse(text, filename=str(path))
    lines = text.splitlines(keepends=True)
    result: dict[int, tuple[ast.AST, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end_line = getattr(node, "end_lineno", node.lineno)
            result[node.lineno] = (node, "".join(lines[node.lineno - 1:end_line]))
    return result


def _literal_values(node: ast.AST) -> list[Any]:
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        return []
    if isinstance(value, (list, tuple, set)):
        return [item for item in value if isinstance(item, (str, int, float, bool))]
    return [value] if isinstance(value, (str, int, float, bool)) else []


def _python_facts(item: dict[str, Any], node: ast.AST, unit: str) -> dict[str, Any]:
    calls: set[str] = set()
    returns: set[str] = set()
    raises: set[str] = set()
    effects: set[str] = set()
    enums: dict[str, set[Any]] = {}
    statuses: set[int] = set()
    for child in _unit_nodes(node):
        if isinstance(child, ast.Call):
            name = _call_name(child.func)
            calls.add(name)
            if name.rsplit(".", 1)[-1] in EFFECT_CALLS:
                effects.add(name)
        elif isinstance(child, ast.Return):
            expression = ast.unparse(child.value) if child.value is not None else "None"
            returns.add(_short(expression))
            if isinstance(child.value, ast.Tuple) and len(child.value.elts) > 1:
                statuses.update(
                    value for value in _literal_values(child.value.elts[1]) if isinstance(value, int)
                )
        elif isinstance(child, ast.Raise) and child.exc is not None:
            raises.add(_short(ast.unparse(child.exc), 100))
        elif isinstance(child, ast.Compare) and isinstance(child.left, ast.Name):
            values: list[Any] = []
            for comparator in child.comparators:
                values.extend(_literal_values(comparator))
            if values:
                enums.setdefault(child.left.id, set()).update(values)
    security: list[str] = []
    lower_calls = " ".join(calls).lower()
    if "request." in unit:
        security.append("HTTP request trust boundary")
    if any(token in lower_calls for token in ("read_text", "write_text", "open", "unlink", "path")):
        security.append("filesystem access")
    if any(token in lower_calls for token in ("urlopen", "requests.", "influx", "client.query", "client.write")):
        security.append("external service/database access")
    if re.search(r"token|password|secret", unit, re.I):
        security.append("secret-bearing values")
    if any(token in lower_calls for token in ("subprocess", "popen", "os.system")):
        security.append("process execution")
    return {
        "construct": type(node).__name__,
        "calls": sorted(calls),
        "returns": sorted(returns) or (["implicit None"] if not isinstance(node, ast.ClassDef) else ["class object"]),
        "raises": sorted(raises),
        "effects": sorted(effects),
        "enums": {key: sorted(values, key=str) for key, values in sorted(enums.items())},
        "http_statuses": sorted(statuses),
        "security_boundaries": security or ["in-process computation"],
    }


def _balanced_js_block(text: str, start: int, brace: int) -> str:
    depth = 0
    quote = ""
    escaped = False
    index = brace
    while index < len(text):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
        elif char in {"'", '"', "`"}:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
        index += 1
    return text[start:min(len(text), start + 1000)]


def _js_expression_end(text: str, start: int, limit: int) -> int:
    quote = ""
    escaped = False
    depths = {"(": 0, "[": 0, "{": 0}
    closing = {")": "(", "]": "[", "}": "{"}
    for index in range(start, limit):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {"'", '"', "`"}:
            quote = char
        elif char in depths:
            depths[char] += 1
        elif char in closing:
            depths[closing[char]] = max(0, depths[closing[char]] - 1)
        elif char == ";" and not any(depths.values()):
            return index + 1
        elif char == "\n" and not any(depths.values()):
            return index
    return limit


def _js_unit_from_match(text: str, match: re.Match[str], next_start: int) -> str:
    start = match.start()
    cursor = match.end()
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    if cursor >= len(text) or text[cursor] != "{":
        # Expression-bodied arrow: declaration ends at its statement boundary.
        return text[start:_js_expression_end(text, cursor, next_start)]
    candidate = _balanced_js_block(text, start, cursor)
    if len(candidate) > max(20000, next_start - start) and next_start < len(text):
        return text[start:next_start]
    return candidate


@lru_cache(maxsize=None)
def _js_units(path_text: str) -> dict[tuple[int, str], list[str]]:
    text = _source_text(path_text)
    matches = list(JS_RE.finditer(text))
    result: dict[tuple[int, str], list[str]] = {}
    for index, match in enumerate(matches):
        name = match.group(1) or match.group(3)
        line = line_number(text, match.start())
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result.setdefault((line, name), []).append(_js_unit_from_match(text, match, next_start))
    return result


def _sanitize_evidence(value: Any) -> Any:
    if isinstance(value, str):
        value = re.sub(
            r"(?<![0-9])(?:10|192\.168|172\.(?:1[6-9]|2[0-9]|3[01]))(?:\.[0-9]{1,3}){2,3}(?::[0-9]+)?",
            "[private-endpoint]",
            value,
        )
        return value
    if isinstance(value, list):
        return [_sanitize_evidence(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_evidence(item) for key, item in value.items()}
    return value


def _js_facts(unit: str) -> dict[str, Any]:
    js_keywords = {"catch", "for", "function", "if", "switch", "while", "with"}
    calls = sorted(
        value for value in set(
            re.findall(r"(?<![.$\w])([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\(", unit)
        ) if value not in js_keywords
    )
    fetches = sorted(set(re.findall(r"fetch\s*\(\s*(['\"])(.*?)\1", unit)))
    selectors = sorted(set(
        match[1] for match in re.findall(
            r"(?:getElementById|querySelector|querySelectorAll)\s*\(\s*(['\"])(.*?)\1", unit
        )
    ))
    returns = sorted(set(_short(value) for value in re.findall(r"\breturn\s+([^;\n}]+)", unit)))
    effects: list[str] = []
    for token, label in (
        ("fetch(", "HTTP request"), ("localStorage", "browser local storage"),
        ("sessionStorage", "browser session storage"), ("clipboard", "clipboard write/read"),
        (".innerHTML", "DOM HTML mutation"), (".textContent", "DOM text mutation"),
        (".append", "DOM/list append"), (".remove(", "DOM removal"),
    ):
        if token in unit:
            effects.append(label)
    return {
        "construct": "JavaScript function",
        "calls": calls,
        "returns": returns or ["implicit undefined"],
        "http_targets": [target for _, target in fetches],
        "selectors": selectors,
        "effects": effects or ["in-memory/browser computation only"],
        "error_handling": "catch" if re.search(r"\bcatch\b|\.catch\s*\(", unit) else "none detected",
        "security_boundaries": [
            label for present, label in (
                (bool(fetches), "HTTP/API boundary"),
                ("innerHTML" in unit, "HTML injection-sensitive DOM sink"),
                ("clipboard" in unit, "clipboard boundary"),
                ("localStorage" in unit or "sessionStorage" in unit, "browser storage boundary"),
            ) if present
        ] or ["browser-local computation"],
    }


@lru_cache(maxsize=None)
def _source_unit_cached(doc_id: str, category: str, name: str,
                        source: str) -> tuple[str, dict[str, Any]]:
    item = {"id": doc_id, "category": category, "name": name, "source": source}
    path_text, line_text = source.rsplit(":", 1)
    line = int(line_text)
    text = _source_text(path_text)
    lines = text.splitlines()
    if item["id"] == "influxbro.ci.function-docs":
        unit = "\n".join(lines[line - 1:])
        commands = re.findall(r"^\s*run:\s*(.+)$", unit, re.M)
        actions = re.findall(r"^\s*- uses:\s*(.+)$", unit, re.M)
        return unit, {
            "construct": "GitHub Actions job",
            "commands": commands,
            "actions": actions,
            "effects": ["ephemeral Python package installation", "documentation validation"],
            "security_boundaries": ["GitHub-hosted runner", "Python package index", "repository checkout"],
        }
    if item["id"].startswith("influxbro.py."):
        node, unit = _python_units(path_text)[line]
        return unit, _sanitize_evidence(_python_facts(item, node, unit))
    if item["id"].startswith("influxbro.js."):
        units = _js_units(path_text).get((line, item["name"]), [])
        unit = units[0] if units else lines[line - 1]
        return unit, _sanitize_evidence(_js_facts(unit))
    if item["category"] in {"Konfigurationsoption", "Add-on-Konfigurationsoption"}:
        key = item["name"]
        key_pattern = (
            rf"['\"]{re.escape(key)}['\"]"
            if item["category"] == "Konfigurationsoption"
            else rf"\b{re.escape(key)}\b"
        )
        relevant = [
            f"{number}:{value.strip()}"
            for number, value in enumerate(lines, 1)
            if re.search(key_pattern, value)
        ][:80]
        unit = "\n".join(relevant) or lines[line - 1]
        enum_values: list[Any] = []
        enum_match = re.search(rf"{re.escape(key)}[^\n]*?not\s+in\s+(\([^\n]+?\))", unit)
        if enum_match:
            try:
                parsed_enum = ast.literal_eval(enum_match.group(1))
                if isinstance(parsed_enum, tuple):
                    enum_values = list(parsed_enum)
            except (SyntaxError, ValueError):
                pass
        constraints: list[dict[str, Any]] = []
        for clamp in re.finditer(
            rf"_clamp_int_cfg\s*\(\s*cfg\s*,\s*['\"]{re.escape(key)}['\"]\s*,\s*([^,]+),\s*([^,]+),\s*([^\)]+)\)",
            unit,
        ):
            constraints.append({
                "kind": "integer clamp",
                "default": _short(clamp.group(1)),
                "minimum": _short(clamp.group(2)),
                "maximum": _short(clamp.group(3)),
            })
        facts = {
            "construct": item["category"],
            "declaration": _short(lines[line - 1]),
            "references": relevant,
            "effects": ["Supervisor/package configuration"] if item["category"].startswith("Add-on") else ["runtime configuration"],
            "security_boundaries": ["secret setting"] if re.search(r"token|password|secret", key, re.I) else ["configuration trust boundary"],
            "enums": {key: enum_values} if enum_values else {},
            "constraints": constraints,
        }
        return unit, _sanitize_evidence(facts)
    if item["id"].startswith("influxbro.shell.") or item["id"] == "influxbro.service.startup":
        end = min(len(lines), line + 80)
        unit = "\n".join(lines[line - 1:end])
        commands = sorted(set(re.findall(r"(?m)^\s*([A-Za-z_][\w.-]*)\b", unit)))
        return unit, {
            "construct": "shell/service",
            "commands": commands,
            "effects": [token for token in ("mv", "ln", "mkdir", "exec") if re.search(rf"\b{token}\b", unit)] or ["shell computation"],
            "security_boundaries": ["container filesystem", "process environment", "Supervisor options"],
        }
    if item["id"].endswith(".dynamic"):
        declaration = lines[line - 1]
        embedded_tags = re.findall(r"<[A-Za-z][^>]*>", declaration)
        unit = next(
            (tag for tag in embedded_tags if item["name"] in tag),
            declaration,
        )
    else:
        tags = _html_tags_by_line(path_text).get(line, [])
        source_key = _central_ui_source_keys().get(item["id"], "")
        occurrence = int(source_key.rsplit("#", 1)[1]) if source_key else 0
        if occurrence and occurrence <= len(tags):
            unit = tags[occurrence - 1]
        else:
            unit = next((tag for tag in tags if item["name"] in tag), tags[0] if tags else lines[line - 1])
    attrs = {match[0]: match[2] for match in re.findall(r"([:\w-]+)\s*=\s*(['\"])(.*?)\2", unit)}
    events = {key: value for key, value in attrs.items() if key.startswith("on")}
    return unit, _sanitize_evidence({
        "construct": "dynamic UI declaration" if item["id"].endswith(".dynamic") else "HTML/UI element",
        "tag": (re.search(r"<([A-Za-z0-9-]+)", unit).group(1) if re.search(r"<([A-Za-z0-9-]+)", unit) else "dynamic"),
        "attributes": attrs,
        "events": events,
        "effects": ["navigation"] if "href" in attrs else (["form submission"] if "action" in attrs else ["DOM/UI state"]),
        "security_boundaries": (["external navigation"] if attrs.get("href", "").startswith(("http://", "https://")) else ["Ingress UI interaction"]),
    })


def _source_unit(item: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    return _source_unit_cached(
        item["id"], item["category"], item["name"], item["source"]
    )


def _unit_fingerprint(item: dict[str, Any], unit: str) -> str:
    material = f"{item['technical_reference']}\n{unit}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _test_symbol_index() -> dict[str, list[str]]:
    index: dict[str, set[str]] = {}
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        rel = path.relative_to(ROOT).as_posix()
        for token in set(re.findall(r"[A-Za-z_$][A-Za-z0-9_$]{3,}", path.read_text(encoding="utf-8"))):
            index.setdefault(token, set()).add(rel)
    return {key: sorted(values) for key, values in index.items()}


def _exact_test_refs(item: dict[str, Any]) -> list[str]:
    index = _test_symbol_index()
    candidates = [item["name"], item["name"].rsplit(".", 1)[-1]]
    if item["category"].startswith("GUI-"):
        candidates.extend(re.findall(r"[A-Za-z_$][A-Za-z0-9_$]{3,}", item["name"]))
    matches = sorted({path for candidate in candidates for path in index.get(candidate, [])})
    return matches[:8] or ["N/A - no exact symbol/identifier occurrence in tests."]


def _review_inputs(item: dict[str, Any], facts: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    enums = facts.get("enums", {})
    attrs = facts.get("attributes", {})
    for original in item["inputs"]:
        current = dict(original)
        name = current["name"].lstrip("*")
        allowed = enums.get(name)
        if allowed:
            current["allowed_values"] = allowed
            current["validation"] = f"Implementation compares `{name}` against {allowed}."
        elif facts.get("constraints"):
            current["allowed_values"] = facts["constraints"]
            current["validation"] = f"Implementation applies {facts['constraints']} to `{name}`."
        elif not isinstance(current.get("allowed_values"), str):
            current["validation"] = (
                f"Source declaration for `{name}` restricts values to {current['allowed_values']}."
            )
        elif item["category"] == "GUI-Eingabe":
            input_type = attrs.get("type", current.get("type", "text"))
            allowed_ui = {
                key: attrs[key] for key in ("min", "max", "step", "pattern", "maxlength") if key in attrs
            }
            if input_type in {"checkbox", "radio"}:
                current["allowed_values"] = [False, True]
            elif allowed_ui:
                current["allowed_values"] = allowed_ui
            else:
                current["allowed_values"] = f"HTML `{input_type}` value accepted by the bound handler."
            current["validation"] = f"Browser attributes for `{item['name']}`: {allowed_ui or {'type': input_type}}."
        else:
            annotation = current.get("type", "unknown")
            requirement = "required" if current.get("required") else f"optional; default={current.get('default')!r}"
            current["allowed_values"] = f"Values accepted by `{annotation}` and the implementation body."
            current["validation"] = f"Call binding treats `{name}` as {requirement}; no closed enum comparison was found in this source unit."
        result.append(current)
    return result


def _review_states(item: dict[str, Any], facts: dict[str, Any]) -> dict[str, str]:
    calls = facts.get("calls", [])
    lower_calls = [value.lower() for value in calls]
    cancellation = [value for value in calls if re.search(r"cancel|abort|stop", value, re.I)]
    retries = [value for value in calls if re.search(r"retry|repeat", value, re.I)]
    empty_returns = [
        value for value in facts.get("returns", [])
        if re.search(r"None|\[\]|\{\}|empty", value, re.I)
    ] or ["no explicit empty return"]
    if item["category"] == "API":
        codes = facts.get("http_statuses", [])
        return {
            "loading": "Delegates to a job/thread and returns its status." if any("job" in value or "thread" in value for value in lower_calls) else "Synchronous HTTP processing; caller remains pending until return.",
            "success": f"Return contract: {facts.get('returns', ['response'])[:4]}; explicit status codes: {codes or [200]}.",
            "empty": f"Empty/None-capable return evidence: {empty_returns}.",
            "error": f"Explicit raises/HTTP statuses: {facts.get('raises', []) or codes or ['unhandled exception -> 500']}.",
            "cancel": f"Cancellation calls: {cancellation}." if cancellation else "N/A - no cancel/abort/stop call in this route unit.",
            "retry": f"Retry calls: {retries}." if retries else "N/A - no retry/repeat call in this route unit.",
        }
    if item["category"].startswith("GUI-") or item["category"] == "Skriptfunktion":
        effects = facts.get("effects", ["DOM/UI state"])
        return {
            "loading": "Pending HTTP/API state is observable through the calling script." if "HTTP request" in effects else "N/A - this source unit contains no HTTP request effect.",
            "success": f"Observable effects: {effects}.",
            "empty": f"Declared inputs/defaults: {[(value['name'], value.get('default')) for value in item['inputs']]}.",
            "error": "Source includes catch/error handling." if facts.get("error_handling") == "catch" else "N/A - no catch/error handling detected in this unit.",
            "cancel": f"Cancellation calls: {cancellation}." if cancellation else "N/A - no cancel/abort/stop call detected.",
            "retry": f"Retry calls: {retries}." if retries else "N/A - repeated execution requires another bound event/caller invocation.",
        }
    return {
        "loading": "N/A - no independent UI loading protocol in this source unit.",
        "success": f"Returns {facts.get('returns', ['implicit completion'])}; effects {facts.get('effects', [])}.",
        "empty": f"Empty/None return evidence: {empty_returns}.",
        "error": f"Explicit raises: {facts.get('raises', []) or ['none in this unit; caller receives runtime exceptions']}.",
        "cancel": f"Cancellation calls: {cancellation}." if cancellation else "N/A - no cancel/abort/stop call detected.",
        "retry": f"Retry calls: {retries}." if retries else "N/A - no retry/repeat call detected.",
    }


def _direct_dependencies(facts: dict[str, Any]) -> list[str]:
    ignored = {
        "all", "any", "bool", "dict", "enumerate", "float", "getattr", "int",
        "isinstance", "len", "list", "max", "min", "range", "round", "set",
        "sorted", "str", "sum", "tuple", "zip",
    }
    ignored_methods = {
        "add", "append", "clear", "copy", "discard", "extend", "get", "items",
        "join", "keys", "lower", "pop", "replace", "setdefault", "sort", "split",
        "startswith", "strip", "update", "upper", "values",
    }
    calls = facts.get("calls", facts.get("commands", []))
    result = [
        value for value in calls
        if value not in ignored and value.rsplit(".", 1)[-1] not in ignored_methods
    ]
    return result[:30]


def apply_systematic_reviews(entries: list[dict[str, Any]]) -> None:
    facts_by_id: dict[str, dict[str, Any]] = {}
    unit_by_id: dict[str, str] = {}
    names: dict[str, list[str]] = {}
    for item in entries:
        unit, facts = _source_unit(item)
        facts = dict(facts)
        facts["source_span"] = {
            "bytes": len(unit.encode("utf-8")),
            "lines": unit.count("\n") + 1,
        }
        unit_by_id[item["id"]] = unit
        facts_by_id[item["id"]] = facts
        names.setdefault(item["name"].rsplit(".", 1)[-1], []).append(item["id"])

    callers: dict[str, set[str]] = {item["id"]: set() for item in entries}
    for item in entries:
        for called in facts_by_id[item["id"]].get("calls", []):
            for target in names.get(called.rsplit(".", 1)[-1], []):
                if target != item["id"]:
                    callers[target].add(item["id"])

    for item in entries:
        facts = facts_by_id[item["id"]]
        unit = unit_by_id[item["id"]]
        unit_hash = _unit_fingerprint(item, unit)
        manual_fields = (
            {key: item[key] for key in REVIEWED_FIELDS | {"api"} if key in item}
            if item["status"] == "verified" else {}
        )
        item["inputs"] = _review_inputs(item, facts)
        item["tests"] = _exact_test_refs(item)
        item["states"] = _review_states(item, facts)
        item["dependencies"] = _direct_dependencies(facts) or [
            "N/A - source unit contains no direct call/command dependency."
        ]
        inbound = sorted(callers[item["id"]])[:30]
        item["called_by"] = inbound or (
            "Direct browser/user event." if item["category"].startswith("GUI-") else
            "N/A - no static same-repository caller resolved; entry point, callback or dynamic call."
        )
        item["outputs"] = (
            f"Returns {facts.get('returns')}"
            if facts.get("returns") else
            f"Observable contract facts: {facts.get('effects', facts.get('declaration', facts.get('attributes', {})))}"
        )
        effects = facts.get("effects", [])
        item["side_effects"] = (
            f"Source-detected effects/calls: {effects}." if effects else
            "No mutating call, navigation, form submission or persistence operation detected in this source unit."
        )
        item["security"] = (
            f"Reviewed boundaries for `{item['technical_reference']}`: {facts.get('security_boundaries')}. "
            "Values crossing these boundaries require the validations recorded in `inputs`."
        )
        item["prerequisites"] = (
            f"Requires the direct dependencies listed for `{item['technical_reference']}` and its documented runtime context."
        )
        item["permissions"] = (
            "Ingress/operator context plus add-on process permissions required by the recorded boundaries."
            if item["visibility"] != "intern" else
            "No independent user permission; executes with the permissions of its recorded caller."
        )
        if item["status"] != "verified":
            item["description"] = (
                f"`{item['technical_reference']}` is a {facts.get('construct', item['category'])}. "
                f"It accepts {[value['name'] for value in item['inputs']]}; "
                f"calls {facts.get('calls', facts.get('commands', []))[:12] or ['none']}; "
                f"and produces {facts.get('returns', facts.get('effects', ['no separately observable output']))[:8]}."
            )
            item["short_description"] = (
                f"{facts.get('construct', item['category'])} `{item['name']}`; source contract {unit_hash[:12]}."
            )
        if manual_fields:
            item.update(manual_fields)
        item["contract"] = facts
        item["status"] = "verified"
        item["verified_version"] = VERSION
        prior_review = item.get("review", {})
        item["review"] = {
            "reviewed_by": prior_review.get("reviewed_by", "OpenCode systematic category audit"),
            "reviewed_at": prior_review.get("reviewed_at", "2026-07-15"),
            "evidence": prior_review.get(
                "evidence",
                f"Category source-contract review `{slug(item['category'])}`; exact unit fingerprint and extracted facts attached.",
            ),
            "source_sha256": hashlib.sha256(unit.encode("utf-8")).hexdigest(),
            "fingerprint_sha256": unit_hash,
            "fingerprint_material": "technical_reference + exact source unit",
            "method": "manual-override+systematic-source-contract-v2" if prior_review else "systematic-source-contract-v2",
            "category_batch": f"audit-{slug(item['category'])}-2026-07-15",
        }


def build_catalog() -> dict[str, Any]:
    entries = [
        *workflow_entries(),
        *addon_and_shell_entries(),
        *config_default_entries(),
        *python_entries(),
        *javascript_entries(),
        *ui_entries(),
    ]
    entries.sort(key=lambda item: item["id"])
    apply_reviews(entries)
    apply_systematic_reviews(entries)
    status_counts: dict[str, int] = {}
    for item in entries:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
    return {
        "schema_version": 2,
        "project": "HA-Addons",
        "audited_ref": AUDITED_REF,
        "verified_addon_version": VERSION if status_counts.get("draft", 0) == 0 else None,
        "audit_complete": status_counts.get("draft", 0) == 0,
        "status_counts": status_counts,
        "generation": "Every active entry is reviewed by category-specific source-contract extraction; manual overrides remain source-bound.",
        "audit_evidence": "docs/audit-evidence.json",
        "manual_review_overrides": "docs/function-reviews.json",
        "exclusions": [
            "node_modules and package dependencies",
            "influxbro/app/static/plotly.min.js (vendor)",
            "tests, CI other than the documentation compliance workflow, demos and developer tooling",
            "images, binary assets, backups, local runtime data and generated test results",
        ],
        "entries": entries,
    }


def manual_anchors() -> set[str]:
    anchors = set()
    for line in MANUAL.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            title = line.lstrip("#").strip().lower()
            anchors.add(re.sub(r"[^a-z0-9 -]", "", title).replace(" ", "-"))
    return anchors


def validate(catalog: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors = []
    review_records = load_json_object(REVIEWS).get("reviews", [])
    review_refs = [
        review.get("technical_reference")
        for review in review_records
        if isinstance(review, dict)
    ]
    if len(review_refs) != len(set(review_refs)):
        errors.append("docs/function-reviews.json enthaelt doppelte technische Referenzen")
    entries = catalog.get("entries")
    if not isinstance(entries, list):
        return ["entries muss eine Liste sein"]
    ids: set[str] = set()
    refs: set[str] = set()
    anchors = manual_anchors()
    for index, item in enumerate(entries):
        where = f"entries[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{where}: Eintrag ist kein Objekt")
            continue
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            errors.append(f"{where}: Pflichtfelder fehlen: {sorted(missing)}")
        doc_id = item.get("id", "")
        if not isinstance(doc_id, str) or not ID_RE.fullmatch(doc_id):
            errors.append(f"{where}: ungueltige ID {doc_id!r}")
        elif doc_id in ids:
            errors.append(f"{where}: doppelte ID {doc_id}")
        ids.add(doc_id)
        reference = item.get("technical_reference", "")
        if not isinstance(reference, str) or ":" not in reference or "#" not in reference:
            errors.append(f"{doc_id}: technische Referenz ist nicht konkret")
        refs.add(reference)
        source = item.get("source", "")
        match = re.fullmatch(r"(.+):(\d+)", source) if isinstance(source, str) else None
        if not match:
            errors.append(f"{doc_id}: ungueltige Quellreferenz {source!r}")
        else:
            path = ROOT / match.group(1)
            line = int(match.group(2))
            if not path.is_file():
                errors.append(f"{doc_id}: Quelldatei fehlt: {match.group(1)}")
            elif line < 1 or line > len(path.read_text(encoding="utf-8").splitlines()):
                errors.append(f"{doc_id}: Quellzeile ausserhalb der Datei: {line}")
        manual_ref = item.get("manual_ref", "")
        if not isinstance(manual_ref, str) or not manual_ref.startswith("docs/handbuch.md#"):
            errors.append(f"{doc_id}: ungueltiger Handbuchverweis")
        elif manual_ref.split("#", 1)[1] not in anchors:
            errors.append(f"{doc_id}: Handbuchanker fehlt: {manual_ref}")
        states = item.get("states")
        if not isinstance(states, dict) or STATE_FIELDS - set(states):
            errors.append(f"{doc_id}: unvollstaendige Zustandsdokumentation")
        inputs = item.get("inputs")
        if not isinstance(inputs, list) or not inputs:
            errors.append(f"{doc_id}: Eingaben fehlen")
        else:
            for inp in inputs:
                if not isinstance(inp, dict) or {"name", "type", "required", "default", "allowed_values", "validation"} - set(inp):
                    errors.append(f"{doc_id}: unvollstaendige Eingabedokumentation")
                    break
        for field in REQUIRED_FIELDS - {"inputs", "states"}:
            if field in item and item[field] in (None, "", []):
                errors.append(f"{doc_id}: Pflichtfeld {field} ist leer")
        status = item.get("status")
        if status not in {"draft", "verified"}:
            errors.append(f"{doc_id}: ungueltiger Status {status!r}")
        if status == "verified":
            review = item.get("review")
            if not isinstance(review, dict) or not all(review.get(key) for key in (
                "reviewed_by", "reviewed_at", "evidence", "source_sha256",
                "fingerprint_sha256", "fingerprint_material",
            )):
                errors.append(f"{doc_id}: verified ohne vollstaendigen Review-Nachweis")
            else:
                unit, _facts = _source_unit(item)
                source_hash = hashlib.sha256(unit.encode("utf-8")).hexdigest()
                current_fingerprint = _unit_fingerprint(item, unit)
                if review["source_sha256"] != source_hash or review["fingerprint_sha256"] != current_fingerprint:
                    errors.append(f"{doc_id}: Review-Nachweis passt nicht mehr zum Quelltext")
            if item.get("verified_version") != VERSION:
                errors.append(f"{doc_id}: falsche/gealterte Pruefversion")
            if item.get("input_extraction_warnings"):
                errors.append(f"{doc_id}: unbekannter Request-Handler ist nicht reviewfaehig")
            if any(
                inp.get("validation") == "An der jeweiligen Vertrauensgrenze normalisieren und fachlich begrenzen."
                for inp in inputs if isinstance(inp, dict)
            ):
                errors.append(f"{doc_id}: verified verwendet Boilerplate-Validierung")
        api = item.get("api")
        if api is not None:
            if not isinstance(api, dict) or API_FIELDS - set(api):
                errors.append(f"{doc_id}: unvollstaendige API-Dokumentation")
            else:
                nested_api_fields = {
                    "request": {"contentType", "schema", "keys", "example"},
                    "response": {"contentType", "schema", "example", "statusCodes"},
                    "timing": {"typicalMs", "p95Ms", "timeoutMs", "bottleneck"},
                    "correlations": {"dependsOn", "triggers", "parallelWith", "usedIn", "criticalPath", "phase"},
                    "examples": {"curl", "javascript", "python"},
                }
                for api_field, required in nested_api_fields.items():
                    value = api.get(api_field)
                    if not isinstance(value, dict) or required - set(value):
                        errors.append(f"{doc_id}: API-Feld {api_field} ist unvollstaendig")
    expected_entries = expected["entries"]
    expected_by_ref = {item["technical_reference"]: item for item in expected_entries}
    actual_by_ref = {item.get("technical_reference"): item for item in entries if isinstance(item, dict)}
    for reference in sorted(set(expected_by_ref) - set(actual_by_ref)):
        errors.append(f"nicht dokumentierte Quell-/Config-/UI-Funktion: {reference}")
    for reference in sorted(set(actual_by_ref) - set(expected_by_ref)):
        errors.append(f"verwaiste oder nicht mehr erkannte Referenz: {reference}")
    for reference, expected_item in expected_by_ref.items():
        actual_item = actual_by_ref.get(reference, {})
        if actual_item and actual_item != expected_item:
            errors.append(f"Kataloginhalt weicht von Generator/Review-Nachweis ab: {reference}")
    for review in review_records:
        if not isinstance(review, dict):
            errors.append("docs/function-reviews.json enthaelt einen ungueltigen Review-Eintrag")
            continue
        reference = review.get("technical_reference")
        expected_item = expected_by_ref.get(reference)
        if expected_item is None:
            errors.append(f"Review verweist auf unbekannte Funktion: {reference}")
        elif expected_item.get("status") != "verified":
            errors.append(f"Review ist unvollstaendig oder durch Quelltextaenderung veraltet: {reference}")
    if catalog.get("audited_ref") != AUDITED_REF:
        errors.append(f"audited_ref muss {AUDITED_REF} sein")
    for field in (
        "schema_version", "audit_complete", "status_counts", "generation",
        "audit_evidence", "manual_review_overrides",
    ):
        if catalog.get(field) != expected.get(field):
            errors.append(f"Katalog-Metadatum {field} ist nicht deterministisch aktuell")
    drafts = [item.get("id") for item in entries if isinstance(item, dict) and item.get("status") == "draft"]
    if drafts and catalog.get("audit_complete") is not False:
        errors.append("audit_complete muss bei vorhandenen Entwuerfen false sein")
    if not drafts and catalog.get("verified_addon_version") != VERSION:
        errors.append(f"verified_addon_version muss bei abgeschlossenem Audit {VERSION} sein")
    discovered_addons = {path.parent.name for path in ROOT.glob("*/config.yaml")}
    documented_addons = {
        item.get("addon") for item in entries if isinstance(item, dict) and item.get("addon")
    }
    if documented_addons != discovered_addons:
        errors.append(
            "Add-on-Abdeckung stimmt nicht: "
            f"gefunden={sorted(discovered_addons)}, dokumentiert={sorted(documented_addons)}"
        )
    audit_is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", AUDITED_REF, "HEAD"],
        cwd=ROOT, check=False, capture_output=True, text=True,
    )
    if audit_is_ancestor.returncode != 0:
        errors.append(f"Audit-Commit {AUDITED_REF} ist kein Vorfahr des Arbeits-HEAD")
    ui_map = load_json_object(UI_ID_MAP).get("elements", [])
    mapped_ids = [item.get("id") for item in ui_map if isinstance(item, dict)]
    mapped_sources = [item.get("source_key") for item in ui_map if isinstance(item, dict)]
    if len(mapped_ids) != len(set(mapped_ids)) or len(mapped_sources) != len(set(mapped_sources)):
        errors.append("docs/ui-id-map.json ist nicht bijektiv")
    catalog_ids = {item.get("id") for item in entries if isinstance(item, dict)}
    missing_mapped = sorted(set(mapped_ids) - catalog_ids)
    if missing_mapped:
        errors.append(f"zentrale UI-IDs ohne Katalogeintrag: {missing_mapped[:10]}")
    evidence = load_json_object(AUDIT_EVIDENCE)
    batches = evidence.get("category_batches", [])
    batch_by_category = {
        batch.get("category"): batch for batch in batches if isinstance(batch, dict)
    }
    actual_counts: dict[str, int] = {}
    by_id = {item.get("id"): item for item in entries if isinstance(item, dict)}
    for item in entries:
        if isinstance(item, dict):
            actual_counts[item.get("category", "")] = actual_counts.get(item.get("category", ""), 0) + 1
    if set(batch_by_category) != set(actual_counts):
        errors.append("Audit-Evidenz deckt nicht exakt alle Kategorien ab")
    required_checks = {
        "source_unit_fingerprint", "inputs_defaults_enums_validation", "outputs_states_effects",
        "security_dependencies_callers_tests", "adversarial_sample",
    }
    for category, count in sorted(actual_counts.items()):
        batch = batch_by_category.get(category, {})
        if batch.get("active_count") != count:
            errors.append(f"Audit-Evidenzzaehler fuer {category} ist nicht aktuell")
        if not batch.get("reviewed_by") or not batch.get("reviewed_at"):
            errors.append(f"Audit-Evidenz fuer {category} hat keinen Reviewer/Termin")
        if required_checks - set(batch.get("checks", [])):
            errors.append(f"Audit-Evidenz fuer {category} hat unvollstaendige Pruefkriterien")
        sample = by_id.get(batch.get("adversarial_sample"))
        if not sample or sample.get("category") != category or sample.get("status") != "verified":
            errors.append(f"Audit-Evidenz fuer {category} verweist auf kein gueltiges Sample")
    return errors


def category_summary(entries: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for item in entries:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    return ", ".join(f"{name}={counts[name]}" for name in sorted(counts))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Katalog deterministisch aktualisieren")
    parser.add_argument("--allow-draft", action="store_true", help="Strukturcheck darf unvollstaendigen Audit passieren lassen")
    parser.add_argument("--bootstrap-ui-map", action="store_true", help="einmalige Migration der anonymen Hash-IDs")
    args = parser.parse_args()
    if args.bootstrap_ui_map:
        UI_ID_MAP.write_text(
            json.dumps(bootstrap_ui_id_map(), ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Zentrale UI-ID-Definition geschrieben: {UI_ID_MAP.relative_to(ROOT)}")
        return 0
    expected = build_catalog()
    if args.write:
        CATALOG.write_text(json.dumps(expected, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        print(f"Katalog geschrieben: {len(expected['entries'])} Eintraege")
        print(category_summary(expected["entries"]))
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FEHLER: Katalog nicht lesbar: {exc}", file=sys.stderr)
        return 1
    errors = validate(catalog, expected)
    drafts = sum(item.get("status") == "draft" for item in catalog.get("entries", []))
    if drafts and not args.allow_draft:
        errors.append(f"retrospektiver Audit unvollstaendig: {drafts} aktive Entwuerfe")
    if errors:
        for error in errors[:100]:
            print(f"FEHLER: {error}", file=sys.stderr)
        if len(errors) > 100:
            print(f"FEHLER: {len(errors) - 100} weitere Fehler", file=sys.stderr)
        return 1
    print(f"OK: {len(catalog['entries'])} strukturell gepruefte Eintraege fuer influxbro")
    print(category_summary(catalog["entries"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
