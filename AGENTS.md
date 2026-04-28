# AGENTS v2

## EXECUTION BLOCK (CRITICAL – ALWAYS FIRST)

### Mandatory Execution Flow (Hard Requirements)

1 Before ANY implementation:

1.1 Verify repository root:

- `influxbro/`
- `AGENTS.md`
- `repository.yaml`
- If any are missing: STOP immediately.

1.2 Check open GitHub issues unless the user explicitly points to a specific issue.

1.3 If the user request is NEW:

- MUST create a GitHub issue BEFORE implementation.

1.4 Create or update the ToDo list.

1.5 Mirror the current ToDo/plan state to `./.opencode/plan_state.md`.

2 During implementation:

2.1 Execute all write operations strictly sequentially.

2.2 Keep changes minimal and consistent with the repository patterns.

2.3 Maintain exactly ONE ToDo item as `in_progress`.

3 After implementation (Mandatory Completion Flow):

3.0 Mandatory Security Review (Home Assistant Add-ons)

For every change in a Home Assistant add-on, perform a mandatory security review BEFORE marking the task as complete.

Scope (minimum):

- `influxbro/config.yaml`
- `influxbro/Dockerfile`
- `influxbro/run.sh` and other startup scripts
- backend API routes and request handlers
- HTML/templates/frontend JavaScript
- file operations
- logging
- dependency files such as `requirements.txt`, `pyproject.toml`, or `package.json`

Required checks:

- hardcoded secrets, tokens, passwords, API keys, or internal URLs
- secrets or sensitive values written to logs
- missing input validation for all external inputs
- command injection risks (subprocess/shell)
- path traversal and unsafe file access
- XSS and unsafe DOM injection in frontend/templates
- CSRF-relevant write/delete actions exposed unsafely
- SSRF via user-controlled URLs/hosts/remote fetch
- unsafe uploads/downloads/backup/restore/import/export
- missing authentication/authorization checks
- dangerous default settings
- overly broad container privileges/host mounts/devices/exposed ports
- information leakage in error messages
- unsafe dynamic code execution (`eval`, `exec`, or equivalent)
- outdated or obviously risky dependencies

Home Assistant add-on specific review (least privilege):

- verify whether the add-on configuration grants more permissions than necessary: `host_network`, `privileged`, `full_access`, `homeassistant_api`, `ingress`, `ports`, `map`, mounted host paths, docker socket access, attached devices
- if a permission is not clearly required, flag it and propose a reduction

External input rule:

- treat ALL external input as untrusted by default: query params, JSON bodies, form fields, filenames, paths, sorting/filter values, env vars, HA option values, URLs/hosts/IDs/tokens

Findings policy:

- no generic security statements without code evidence
- every finding MUST include: severity (critical/high/medium/low), affected file + function/area, risk explanation, realistic attack scenario, concrete remediation, patch suggestion (if feasible)

Remediation policy:

- if a security issue can be fixed safely and unambiguously, implement the fix directly
- keep fixes minimal, low-risk, and traceable

Completion gate:

- do NOT mark complete until: security review performed, findings documented, safe fixes applied where appropriate, remaining risks listed explicitly

Required final output:

- security findings by severity
- implemented fixes
- remaining risks
- recommended follow-up checks

3.1 Run REQUIRED QA:

- syntax check (mandatory)
- targeted tests where relevant/available
- runtime/API/UI checks when relevant

3.2 If ANY required QA fails:

- DO NOT declare the work complete.

3.3 Versioning (MANDATORY when required by repo rules):

- bump `influxbro/config.yaml`
- update `influxbro/CHANGELOG.md`
- update `influxbro/MANUAL.md` when behavior/UI changed

3.4 Git flow (HA main-first unless user explicitly overrides):

- stage changes
- commit
- push to `main`

3.5 GitHub issue completion flow (when an issue was implemented):

- set status to `status/done`
- add issue comment with root cause, solution, and commit hash / PR link
- close the issue

3.6 Completion Signal (MANDATORY – MUST ALWAYS EXECUTE)

4 After successful completion:

- `afplay /System/Library/Sounds/Glass.aiff`
- `say "Fertig mit der Umsetzung"`

If a new version was produced:

- `say -v Anna "Generierung erfolgt, Version X Punkt Y Punkt Z wurde erzeugt"`

If blockers or failures remain:

- `afplay /System/Library/Sounds/Basso.aiff`
- `say "Einige Punkte müssten noch beantwortet werden"`

### Completion Definition

Completion is ONLY valid if ALL mandatory steps above, including the audio/speech completion signal, were executed.
The agent MUST NOT return control before the completion signal was executed.

## Workspace Requirement (CRITICAL)

- The agent MUST operate from the repository root.
- Before any search, read, write, git, or test operation, verify that the working directory contains:
  - influxbro/
  - AGENTS.md
  - repository.yaml

- If these are not present:
  - STOP immediately
  - report: "Wrong working directory – repository root required"

## 📦 Bulk File Processing & Large Context Handling (CRITICAL)

### General Rule

- NEVER load or analyze all files at once.
- ALWAYS process files in small batches or individually.

### HTML / Template Analysis

When analyzing HTML, Jinja2 templates, or UI files:

- Process ONE file at a time.
- Do NOT preload multiple templates into context.
- Limit file reads to only the relevant sections when possible.

### Iterative Processing Strategy

For tasks like:

- "analyze all HTML files"
- "check all templates"
- "validate project structure"

The agent MUST:

1. Discover file list first
2. Iterate over files one-by-one
3. Analyze each file independently
4. Summarize results incrementally
5. NEVER accumulate full file contents in memory

### Output Constraints

- Do NOT output full file contents unless explicitly requested
- Only output:
  - errors
  - relevant snippets
  - line references
- Prefer summaries over full dumps

### Token Safety Rules

- If context grows too large:
  - STOP processing
  - summarize current findings
  - continue in next iteration

- Avoid large diffs and full-file outputs

### HTML Validation Rules

When validating HTML structure:

- Focus on:
  - tag balance (<div>, <main>, <section>, <details>)
  - nesting correctness
  - parent/child hierarchy
- Ignore:
  - styling
  - JavaScript
  - unrelated content

### Preferred Workflow

1. Identify target files
2. Loop:
   - read file
   - analyze structure
   - report issues
3. Final summary

### Hard Constraint

The agent MUST NOT:

- load entire project into context
- analyze more than 1–2 files simultaneously
- produce large unstructured outputs

### Parallel Execution Strategy (CONTROLLED)

### Rate Limit & API Stability (MANDATORY)

#### Problem

External APIs (e.g. Alibaba Qwen) may reject requests if traffic increases too quickly:
"Request rate increased too quickly"

#### Root Cause

Burst traffic caused by:

- too many parallel requests
- missing throttling
- immediate retries

#### Mandatory Rules

A. Global Request Control

- ALL external API calls MUST be routed through a single central request handler
- Direct parallel calls from multiple modules are FORBIDDEN

B. Parallelism Limit

- Maximum 2 concurrent API requests
- MUST be enforced via semaphore / queue
- This is NOT optional

C. Request Smoothing

- Introduce delay between requests:
  - minimum 300ms
  - recommended 400–600ms
- Prevent burst traffic at all times

D. Retry Strategy

- On HTTP 429:
  - exponential backoff: 1s → 2s → 4s → 8s (max 10s)
  - add jitter (0–500ms)
- Immediate retry WITHOUT delay is FORBIDDEN

E. Queue System

- Requests exceeding concurrency MUST be queued
- Process sequentially or controlled parallel

F. Fail-safe Behavior

- On repeated 429 errors:
  - reduce concurrency to 1
  - increase delay to 800–1200ms

#### Execution Policy

- When in doubt, ALWAYS prefer sequential execution over parallel execution
- Stability has priority over speed

### General Rule plus

- Parallel execution is allowed ONLY for clearly independent read, search, and validation tasks.
- If one task can affect the assumptions, design, or implementation of another task, analysis MUST be sequential.

### Allowed Parallel Tasks

The following may run in parallel ONLY if they are independent:

- reading unrelated files
- searching the codebase
- reviewing open GitHub issues
- collecting logs
- locating relevant tests

### Sequential Analysis Required

Analysis MUST remain sequential if:

- tasks affect the same files or modules
- one change can alter the design of later changes
- API, UI, and config behavior are connected
- there is any uncertainty about dependency order

### Write Operations

- All code changes MUST remain strictly sequential.
- Version bump, changelog, manual updates, commit, and push MUST remain strictly sequential.

### Safety Rule

- When in doubt, prefer sequential analysis over parallel analysis.

### Plan Mode Workflow

When plan mode is active:

- Create a detailed plan first.
- Show all tasks that need to be done.
- Group tasks logically.
- Wait for explicit user approval before implementing anything (no file edits, no commits, no pushes).

### Plan Mode Must Not Interrupt Active Build Execution

- If a build/GO execution was already explicitly approved and implementation has already started, that execution remains active until a logical completion point is reached.
- A later switch into plan mode MUST NOT retroactively stop, block, or reinterpret that already running build execution as read-only work.
- New requests that arrive while such an active build execution is still running may be acknowledged internally, but they MUST be answered or handled only after the running build execution is completed, unless the user explicitly asks to stop or abort the build.
- In this situation, plan mode applies only to new, not-yet-started work items and MUST be deferred until the active build execution is finished.
- If additional build/GO-style execution requests arrive while a build execution is already active, they MUST NOT interrupt the running build. They are to be placed into a sequential execution queue and handled one after another after the current build reaches a logical completion point.
- If additional plan-mode requests arrive while a deferred plan queue already exists behind an active build, those plan requests are also to be queued and answered sequentially after the active build and after any earlier queued plan items.
- Only an explicit user interruption such as `stop`, `abbrechen`, or an equivalent direct cancellation instruction may interrupt a running build execution in favor of plan work.

### Build Mode Must Not Interrupt Active Plan Work

- If plan mode work was already explicitly requested and the agent is actively producing that plan, analysis, or decision-preparation output, a later build/GO instruction MUST NOT retroactively abort or skip that ongoing plan work mid-response.
- The active plan work must first reach a logical completion point for the current answer before any newly requested build execution starts.
- In this situation, the later build/GO request is to be deferred and executed immediately after the running plan response is completed, unless the user explicitly instructs the agent to stop planning and switch immediately.
- This rule applies only to already active plan work; once the current planning response is finished, the deferred build/GO execution becomes the next required action.
- If additional plan-mode requests arrive while plan work is already active, they MUST NOT interrupt the running plan response. They are to be placed into a sequential plan queue and answered one after another after the current plan item reaches a logical completion point.
- If additional build/GO requests are already queued behind active plan work, those build requests must also be handled sequentially in queue order after the active plan response and after any earlier queued items.
- Only an explicit user interruption such as `stop`, `abbrechen`, or an equivalent direct cancellation instruction may interrupt a running plan response in favor of immediate build execution.


## Laufende Abarbeitung und Queue-Regel

Wenn waehrend einer laufenden Abarbeitung eine neue Nutzernachricht eingeht, gilt grundsaetzlich:

- Eine bereits begonnene Abarbeitung wird nicht stillschweigend unterbrochen.
- Offene Arbeit ist als aktive Queue zu behandeln und zuerst sauber zu ordnen und abzuarbeiten.
- Neue Nutzernachrichten sind standardmaessig Queue-Eintraege, keine Interrupts.
- Neue Nutzernachrichten werden standardmaessig als Erweiterung, Praezisierung oder Scope-Aenderung der bestehenden Queue behandelt, nicht als Abbruch des laufenden Vorgangs.
- Vor einem Themenwechsel MUSS der Agent den aktuellen Stand explizit ordnen:
  - erfolgreich abgeschlossene Teilschritte benennen
  - fehlgeschlagene oder offene Teilschritte benennen
  - daraus eine aktualisierte Reihenfolge fuer die weitere Abarbeitung bilden
- Ein neuer Befehl darf die laufende Abarbeitung nur dann sofort ersetzen, wenn der Nutzer dies explizit als Abbruch formuliert.

### Explizite Abbruchsignale

Nur Formulierungen mit klarer Abbruchabsicht gelten als echte Unterbrechung, zum Beispiel:

- `abbrechen`
- `stop`
- `halt`
- `lass das`
- `nicht weiter damit`
- `stattdessen mache jetzt X`
- `verwirf den aktuellen Ablauf`

Fehlt ein solches Signal, ist die neue Nachricht als Zusatz, Praezisierung oder Scope-Erweiterung zur bestehenden Queue zu behandeln.

### Pflichtverhalten bei Fehlern

Wenn ein Schritt fehlschlaegt, darf der Agent nicht still auf einen neuen Ablauf umschalten. Stattdessen MUSS er:

1. den Fehler klar benennen
2. den bereits erfolgreich erledigten Teil vom offenen Rest trennen
3. den offenen Rest in die Queue einsortieren
4. erst danach neue Nutzeranweisungen in diese Queue einarbeiten

### Pflichtverhalten bei Scope-Erweiterungen

Wenn der Nutzer waehrend der Ausfuehrung neue Anforderungen hinzufuegt, gilt:

1. die laufende Arbeit bleibt aktiv
2. neue Anforderungen werden hinten an die Queue angehaengt oder sinnvoll einsortiert
3. der Agent soll kurz benennen, was bereits in Arbeit war und wie die neue Anweisung eingeordnet wird
4. nur bei ausdruecklichem Abbruch darf der Agent die bisherige Arbeit fallenlassen

### Ziel

- Keine stillen Kontextwechsel
- Keine halb abgebrochenen Arbeitsstraenge
- Keine implizite Verdraengung laufender Aufgaben durch nachfolgende Nachrichten



## Modus-Prioritaet und Ausfuehrungssperre

Wenn eine Systemanweisung, ein System-Reminder oder eine Developer-Anweisung einen eingeschraenkten Modus vorgibt, gilt diese Anweisung immer vorrangig vor allen Regeln in dieser Datei.

Dazu gehoeren insbesondere:

- `Plan Mode`
- `READ-ONLY`
- Verbote fuer Edits, Commits, Pushes oder sonstige Systemaenderungen
- sonstige ausdrueckliche Ausfuehrungssperren

### Harte Regel

Wenn `Plan Mode` oder `READ-ONLY` aktiv ist, darf der Agent:

- lesen
- suchen
- analysieren
- Rueckfragen stellen
- einen Plan erstellen
- offene Queue-Punkte ordnen

Der Agent darf in diesem Modus NICHT:

- Dateien aendern
- `apply_patch` verwenden
- schreibende Bash-Befehle ausfuehren
- Versionen erhoehen
- Commits erzeugen
- Branches aendern
- sonstige Systemaenderungen vornehmen

Diese Sperre gilt auch dann, wenn:

- der Nutzer direkt eine Aenderung verlangt
- noch offene Queue-Punkte existieren
- die laufende Abarbeitung noch nicht abgeschlossen ist
- die Regeln zur Queue-Fortsetzung sonst fuer weiteres Arbeiten sprechen wuerden

### Queue-Verhalten unter Modussperre

Wenn eine Queue aktiv ist und gleichzeitig `Plan Mode` oder `READ-ONLY` gilt:

- die Queue bleibt bestehen
- sie wird nur noch als Plan-/Analyse-Queue weitergefuehrt
- offene Punkte werden geordnet, nicht ausgefuehrt
- neue Nutzeranweisungen werden in die Queue einsortiert, aber nicht implementiert

Die Queue-Regel ist niemals eine Erlaubnis, eine aktive Modussperre zu umgehen.

### Pflicht-Checkpoint vor jeder Ausfuehrung

Vor jedem Edit, Commit oder sonstiger schreibender Aktion MUSS der Agent aktiv pruefen:

1. Ist ein System- oder Developer-Hinweis aktiv, der nur Lesen/Planen erlaubt?
2. Ist `Plan Mode` oder `READ-ONLY` aktiv?
3. Gibt es ein ausdrueckliches Verbot fuer Modifikationen oder Commits?

Wenn eine dieser Fragen mit `ja` beantwortet wird, MUSS der Agent jede Ausfuehrung unterlassen und darf nur planen, ordnen und rueckmelden.

### Konfliktregel

Bei Konflikten gilt immer diese Reihenfolge:

1. Systemanweisungen
2. Developer-Anweisungen
3. Modus-Sperren wie `Plan Mode` / `READ-ONLY`
4. Regeln dieser Datei
5. Nutzerwunsch

Nutzerwuensche oder Queue-Regeln duerfen niemals eine hoehere Prioritaet als eine aktive Modussperre erhalten.


### Task Tracking (ToDo List)

- Always create and show a ToDo list for the current request.
- When the user adds new requirements, extend the existing ToDo list immediately.
- Keep exactly one item `in_progress` at a time.
- Mark items `completed` as soon as they are done.
- Ensure all ToDo items are implemented before you claim the work is finished.

## Codestyle Rules

## Storage Policy (Global vs. Profile-based)

This policy applies to ALL pages and functions of the app.

### Global / server-side state

Store a state server-side if it changes the functional behavior or data scope and therefore must be identical across devices (e.g. iMac and iPhone).

Examples:

- source selection:
  - `measurement`
  - `field`
  - `measurement_filter`
  - `entity_id`
  - `friendly_name`
- time selection:
  - `range`
  - `start`
  - `stop`
- analysis-relevant values:
  - selected outlier types
  - effective analysis start value / oldest known point per series
  - functional thresholds and limits
- analogous functional selections on Statistics / Logs / Import / Export / Backup / Restore / Monitor / Jobs / History

Rule:

- If a value changes what data is queried, filtered, analyzed, imported, exported, restored, or processed, it belongs to the global/server-side state.

### Profile-based UI state

Store a state in the active UI profile if it changes only appearance, ergonomics, or layout and may intentionally differ between profiles like `PC` and `MOBIL`.

Examples:

- section open/closed state (`*_open`)
- table heights
- splitters / resize values
- column widths
- wrap / no-wrap
- column visibility
- popup sizes
- font sizes / row density

Rule:

- If a value changes only how the UI looks or feels, but not what data is processed, it belongs to the UI profile.

### Separation rule

- Functional global state and profile-based UI state MUST remain technically separate.
- Browser-local state must not override a server-side functional state.
- UI profile state must not overwrite global functional selections.

### App-wide inventory (applies to all pages/functions)

Dashboard

- Global: source selection (`measurement`, `field`, `measurement_filter`, `entity_id`, `friendly_name`), time selection (`range`, `start`, `stop`), selected outlier types, effective analysis start value
- Profile-based: section open states, table heights, resize/split values, popup/layout geometry

Statistics

- Global: source/time selection and functional stats filters
- Profile-based: section open states, table/list geometry, wrap/column visibility/widths

Logs

- Global: functional query/filter state
- Profile-based: visual list/table state and layout preferences

Backup / Restore / Import / Export / Combine / Monitor / Jobs / History

- Global: all functional selections and operation-relevant parameters
- Profile-based: purely visual/open/layout state only

### Repo Layout (important for HA)

- `repository.yaml`: must stay in repo root for Home Assistant add-on repositories.
- `influxbro/config.yaml`: add-on metadata (versioning, slug, ingress settings).
- `influxbro/Dockerfile`: container build.
- `influxbro/run.sh`: add-on entrypoint (reads `/data/options.json`).
- `influxbro/app/app.py`: Flask app.
- `influxbro/app/templates/*.html`: UI templates (inline JS/CSS).

Constraints:

- Do not rename the add-on directory or change `slug` in `influxbro/config.yaml`.
- Home Assistant detects updates via the `version:` field in `influxbro/config.yaml`.
- The container expects HA mounts:
  - `/data` (writable, persistent)
  - `/config` (read-only in this add-on)

### Code Style Guidelines

### General

- Keep changes minimal and consistent with existing patterns (Flask + inline templates).
- Prefer readability over cleverness; this add-on is operated by Home Assistant users.
- Do not introduce new dependencies unless they are clearly justified.

### Python formatting

- Indentation: 4 spaces.
- Strings: prefer double quotes for user-facing text consistency in this codebase.
- Use f-strings for formatting.
- Keep lines reasonably short (~100 chars) unless it harms clarity.

### Imports

- Group and order imports:
  1) standard library
  2) third-party
  3) local imports
- One import per line when practical.
- Avoid unused imports.

Example:

```py
import json
from pathlib import Path

from flask import Flask, jsonify, request
```

### Types

- Add type hints for new/changed functions.
- Prefer built-in generics: `dict[str, object]`, `list[str]`.
- For JSON-like payloads, use `dict[str, Any]` and validate/normalize at the boundary.

### Naming

- Functions/vars: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Flask route handlers: short verb-ish names (`measurements`, `fields`, `api_test`).
- Private helpers: prefix with `_`.

### Error handling and API responses

- Treat Flask routes as trust boundaries:
  - validate required params
  - normalize types (`int(...)`, `bool(...)`)
  - return clear errors with appropriate HTTP status codes.
- Prefer a consistent JSON envelope for API endpoints:
  - success: `{"ok": true, ...}`
  - error: `{"ok": false, "error": "..."}`
- Avoid broad `except Exception` in pure helpers; it is acceptable at the HTTP boundary to
  prevent crashes, but include useful error messages and status codes.

### Security / Safety

- Never log or return secrets (token/password). Keep the existing redaction behavior.
- Any path coming from users must be constrained; keep traversal protections like
  `_resolve_cfg_path()` and extend them rather than bypassing.
- Deletion must remain opt-in:
  - gated by `ALLOW_DELETE`
  - requires exact confirmation phrase

### Flask + InfluxDB conventions

- InfluxDB v2 clients should be context-managed and closed (`with v2_client(cfg): ...`).
- For v1 client usage, keep timeouts and SSL verification configurable.
- Keep query size bounded (the UI downsamples to ~5000 points); preserve or improve this.

### Templates (HTML/JS/CSS)

- Keep templates self-contained; no build step exists.
- Use relative URLs (`./api/...`) to work under HA Ingress.
- Keep JS simple (no framework). Prefer small functions and explicit DOM lookups.
- For destructive actions, preserve confirmation UI and add additional guardrails if needed.

#### UI Design Standard

- Before adding or modifying any GUI element:
  - consult influxbro/Template.md
- Maintain consistent layout patterns across all UI components
- Ensure:
  - consistent spacing
  - consistent card/layout structure
  - consistent naming of classes and IDs
- UI components must be validated not only on container level but also for all child elements
  
## Release and Versioning

### Versioning / Releases (Home Assistant add-on)

- Jede Codeaenderung erfordert zwingend eine neue Version.
  - Wenn Dateien mit Code oder Laufzeitlogik geaendert werden (z. B. `*.py`, `*.html`, `*.js`, `*.css`, Docker-/Start-/Shell-Logik, Laufzeit-Configs), MUSS immer eine neue Add-on-Version erzeugt werden.
  - Dies gilt auch fuer kleine Korrekturen, Umstrukturierungen und rein technische Anpassungen.

- Bump `version:` in `influxbro/config.yaml` for any user-visible change.
- Do not change `slug:`.
- Keep `repository.yaml` in the repo root.

### Release Workflow

- If you change add-on behavior (Python/HTML/JS/CSS, Dockerfile, run scripts, configs that affect runtime), also:
  - bump `influxbro/config.yaml:version` (so Home Assistant detects the update)
  - add an entry to `influxbro/CHANGELOG.md` for that version
  - update the user handbook `influxbro/MANUAL.md` so it reflects the current UI/behavior for that version
  - when the change implements a GitHub Issue, the corresponding changelog bullets MUST include a clickable issue link in the form `([#123](https://github.com/<owner>/<repo>/issues/123))`
  - verify `influxbro/CHANGELOG.md` completeness/order (the file MUST list version entries in descending order, newest version at the top)
    - The CHANGELOG.md must present versions in strict descending order (most recent first). When adding a new entry, insert it at the top under the new version heading.

## Dependency / Compatibility Rules

- If you change Python dependencies (new imports, add/remove packages, or behavior that requires a new library version), update `influxbro/requirements.txt` in the same change.
- For each released add-on version, record the Home Assistant Core version the add-on was tested with.
  - Preferred place: the corresponding entry in `influxbro/CHANGELOG.md` (e.g. a Maintenance bullet: `Tested with Home Assistant Core: 2026.3.0`).
  - **Ermittlung der HA Core Version:** Vor dem Schreiben des Changelog-Eintrags MUSS die installierte Home Assistant Core Version auf dem Echtsystem ermittelt werden:
  
    ```bash
    curl -s -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://192.168.2.200:8123/api/config | jq -r '.version'
    ```
  
  Der ermittelte Wert MUSS im Changelog-Eintrag unter `Tested with Home Assistant Core: <wert>` eingetragen werden.
  - `unknown` ist nur als Fallback erlaubt, wenn genau diese Abfrage im aktuellen Umfeld nicht erfolgreich ausgefuehrt werden kann oder keinen verwertbaren Versionswert liefert.

## Support & Logging

- Ensure user-visible UI errors are also written to the add-on log file.
  - In particular: client-side/network errors like "Failed to fetch" must be reported from the browser to the backend and logged.
  - When adding new UI error messages, verify they show up in `Logs` (logfile) during failure scenarios.


## UI-Komponenten-Entfernung (Tombstones Pflichtprozess)

Beim Entfernen von UI-Komponenten (HTML, JS, CSS, Backend-Funktionen) muss zwingend ein nachvollziehbarer "Tombstone" hinterlassen werden.

### Pflichtregeln

- Keine stille Entfernung
- Jede entfernte UI-Komponente MUSS in `.tombstones.yml` dokumentiert werden
- Tombstone-Kommentar im Code ist Pflicht
- Abhängigkeiten prüfen (JS, API, CSS, Templates, Ingress)

### Tombstone Datei

- Zentrale Datei: `.tombstones.yml`
- Jeder Eintrag benötigt eindeutige `tombstone_id`

### Code-Kommentar

```js
// TOMBSTONE: TS-XXXX – Beschreibung
```

### Pflichtprüfungen nach Entfernung

- Keine JS Errors
- Keine 404 durch alte API/UI Calls
- HA Ingress funktioniert weiterhin
- API-Endpunkte korrekt entfernt

### CI / QA Pflicht

- Syntax Check
- API Smoke Tests
- UI Test im HA System

### Version / Docs Pflicht

- Wenn sich Laufzeit- oder UI-Verhalten aendert (auch durch Entfernen/Stilllegen):
  - Version bump
  - `CHANGELOG.md` aktualisieren
  - `MANUAL.md` aktualisieren (falls Benutzerfuehrung/Workflows betroffen)
- Wenn eine neue Release-Version fertiggestellt wurde (Version bump + zugehoerige Release-Aenderungen abgeschlossen), MUSS der Agent diese Release anschliessend pushen, sofern keine hoeher priorisierte System-/Developer-Sperre oder ausdrueckliche Nutzeranweisung dagegen spricht.

### GitHub Integration

- Issue muss Tombstone-ID referenzieren
- Label Empfehlung: `type/ui-removal`, `requires-tombstone`

### Automatische Tombstone-Ausführung bei UI-Entfernungen

Wenn ein Auftrag das Entfernen, Ersetzen oder Stilllegen von UI-Elementen, Templates, Buttons, Tabellen, Dialogen, frontendbezogenen Aktionen, API-gebundenen UI-Funktionen oder Routen umfasst, MUSS der Agent automatisch einen vollständigen Tombstone-Workflow ausführen.

#### Pflichtablauf

1. UI-Relevanz prüfen

- Prüfen, ob die Änderung direkt oder indirekt UI-relevant ist.
- Als UI-relevant gelten insbesondere:
  - Templates (`*.html`)
  - Inline-JavaScript
  - CSS/Selektoren
  - Buttons, Menüs, Dialoge, Tabellen, Karten, Filter, Formulare
  - API-Aufrufe, die von UI-Aktionen ausgelöst werden
  - Routen oder Views mit UI-Bezug

2. Abhängigkeiten vollständig ermitteln

- Vor jeder Entfernung zwingend prüfen:
  - HTML-/Template-Referenzen
  - JavaScript-Funktionen
  - Event-Handler / Listener
  - CSS-Klassen, IDs, Selektoren
  - Fetch-/API-Aufrufe
  - Backend-Endpunkte mit Bezug zur UI
  - Ingress-/Routing-Auswirkungen
  - Dokumentation / MANUAL / Hinweise im UI

3. Tombstone automatisch anlegen

- `.tombstones.yml` MUSS im selben Arbeitsgang ergänzt werden.
- Der Eintrag MUSS mindestens enthalten:
  - `path`
  - `tombstone_id`
  - `reason`
  - `owner`
  - `impacted_selectors`
  - `impacted_actions`
  - `migration_plan`
  - `route_plan`
  - `ci_reference`

4. Folgecode bereinigen

- Funktionen, Selektoren, Event-Handler, API-Aufrufe oder Routen, die ausschließlich zu dem entfernten UI-Element gehören, MÜSSEN ebenfalls entfernt oder stillgelegt werden.
- Funktionen dürfen NICHT entfernt werden, wenn sie an anderer Stelle noch verwendet werden.
- Wenn unklar ist, ob ein Element noch verwendet wird, ist es zu markieren und zu prüfen statt es stillschweigend zu löschen.

5. Migrations- und Ersatzpfad dokumentieren

- Wenn das entfernte UI-Element ersetzt wurde, MUSS der Tombstone-Eintrag den neuen Pfad / die neue Funktion / Route nennen.
- Wenn eine Route entfällt, MUSS geprüft werden, ob ein Redirect oder eine kompatible Ersatzbehandlung erforderlich ist.
- Bei Home Assistant Ingress sind relative Pfade zu verwenden.

6. Abschlussbericht erweitern

- Der Abschlussbericht MUSS enthalten:
  - betroffene UI-Komponente(n)
  - Tombstone-ID(s)
  - entfernte Folgefunktionen
  - bewusst beibehaltene Restfunktionen mit kurzer Begründung
  - Migrations- oder Redirect-Hinweise

### Verification Checklist (Pflicht)

- Repo: `.tombstones.yml` Eintrag vorhanden, `tombstone_id` eindeutig
- Code: `// TOMBSTONE: <id>` Kommentar an der Entfernungs-/Opt-out-Stelle
- Abhaengigkeiten:
  - keine toten Selektoren/CSS-Klassen
  - keine toten JS-Handler/Listener
  - keine UI-Calls auf entfernte API-Endpunkte
  - Ingress/Routes: keine 404s, ggf. Redirect/Migration dokumentiert
- QA:
  - `py_compile`
  - relevante `pytest`
  - UI Smoke Test unter Home Assistant Ingress
- Workflow: HA main-first (rebase auf `origin/main` vor Push, keine stillen Breaking Changes)
- Workflow: Eine fertiggestellte neue Release darf nicht nur lokal verbleiben; nach Abschluss der Release-Arbeit ist der Push verpflichtend, sofern kein ausdrueckliches Push-Verbot aktiv ist.

#### Automatik-Regel für OpenCode

- Der Agent darf UI-Entfernungen NICHT als reine Löschaufgabe behandeln.
- Jede UI-Entfernung ist automatisch als kombinierte Aufgabe zu behandeln aus:
  - UI-Entfernung
  - Abhängigkeitsanalyse
  - Folgecode-Bereinigung
  - Tombstone-Dokumentation
  - QA-/Ingress-Prüfung

#### Verbotene Verkürzung

- Verboten ist insbesondere:
  - nur HTML zu löschen, ohne JS/CSS/API zu prüfen
  - nur einen Button zu entfernen, ohne den Handler zu prüfen
  - eine UI-Aktion zu löschen, ohne den Backend-Endpunkt zu prüfen
  - Routen zu entfernen, ohne Migrations- oder Redirect-Prüfung

### Verboten

- UI löschen ohne Tombstone
- API entfernen ohne Migration
- Silent Breaking Changes



## UI Picker Eindeutigkeit (Pickkey Pflicht)

Damit UI-Elemente in Issues/Chat immer 100% eindeutig referenzierbar sind, gilt ab jetzt:

- Jedes sichtbare, support-relevante UI-Element MUSS eine stabile `data-ui` Kennung besitzen.
- Jedes sichtbare UI-Element MUSS zusaetzlich eine eindeutige `data-ib-pickkey` Kennung besitzen.
- Das gilt fuer alle Typen:
  - Buttons, Links, Inputs, Selects, Checkboxen, Labels
  - Sektionen (`details/summary`), Cards, Panels
  - Tabellen inkl. Toolbars, Resize-Handles, Filterleisten, Rowcounts
  - Dialoge/Popups/Overlays
  - dynamisch erzeugte UI (per JS/`innerHTML`/DOM APIs)
- Dynamisch erzeugte sichtbare Elemente MUESSEN `data-ui` und `data-ib-pickkey` beim Erzeugen setzen.
- S-Picker Ausgabe muss den kanonischen Referenztext liefern: `<PICK:<Page>|<pickkey>>`.
- Neu (v1): Support-Referenzen verwenden das 2-stufige Modell `pk` (Produkt-Key) + `ik` (Instanz-Key): `<PICK:<Page>|v=1;pk=<pk>;ik=<ik>>`.
- `data-ib-pickkey` entspricht `pk` (stabil/release-tauglich), `data-ib-instancekey` entspricht `ik` (zur Laufzeit eindeutig).
- Fallback-Referenzen ohne Pickkey sind nur Migrationszustand und nicht akzeptabel als Endzustand.
- `unknown` ist nur als Fallback erlaubt.

Pflicht bei UI-Aenderungen:

- Wenn du sichtbare UI-Elemente anfasst, musst du bestehende betroffene Elemente mit auf `data-ib-pickkey` nachziehen.
- Wenn du UI-Elemente entfernst: Tombstone-Prozess bleibt weiterhin Pflicht.


## Issue Rules

### Handling Rule

- Only ask whether a request should be recorded as an issue or implemented immediately if it is a NEW request
- If the request relates to an existing issue or context:
  - continue implementation without asking

### Requirements Tracking (preferred: GitHub Issues)

- Track requirements primarily as GitHub Issues so others can create/report items externally.
- **AUTOMATISCHE ISSUE-ERSTELLUNG:** Wenn der Benutzer eine neue Aufgabe/Anforderung im Chat stellt, MUSS der Agent automatisch ein GitHub Issue erstellen, BEVOR mit der Umsetzung begonnen wird.
  - Issue-Titel: Kurze Zusammenfassung der Anforderung
  - Issue-Body: Vollstaendige Beschreibung der Anforderung (wie vom Benutzer formuliert)
  - Label: `type/enhancement` fuer neue Features, `type/bug` fuer Fehler
  - Status: `status/in_progress` wenn sofort umgesetzt wird, sonst `status/open`
  - Nach Umsetzung: Status auf `status/done` setzen, Kommentar mit Commit-Hash/PR-Link hinzufuegen
- Use the issue templates to distinguish between:
  - Bug reports (not working): label with `type/bug`
  - Enhancements (feature requests): label with `type/enhancement`
- Use exactly one status label per issue: `status/open`, `status/in_progress`, `status/done`, `status/cancelled`.
- Ensure the label set exists in GitHub (create once in the GitHub UI); the issue templates assume these labels are available.
- When implementing, link PRs to issues and close them via `Fixes #<id>`.

### GitHub Issue Status Label Consistency (MANDATORY)

- Exactly ONE status label may exist on an issue at any time:
  - `status/open`
  - `status/in_progress`
  - `status/done`
  - `status/cancelled`
- Status labels are mutually exclusive. The agent MUST remove any previous status label before setting a new one.
- A reopened issue MUST NEVER keep `status/done` or `status/cancelled`.
- When an issue is reopened:
  - remove `status/done`
  - remove `status/cancelled`
  - set `status/open` by default
  - set `status/in_progress` only if work is actively resumed immediately
- A closed issue MUST NOT remain with `status/open` or `status/in_progress`.
- When closing an issue:
  - use `status/done` if the work is completed
  - use `status/cancelled` only if the issue is intentionally not implemented / declined
- If GitHub state and status label ever diverge, the agent MUST treat that as an inconsistency and correct the label state immediately.
- Repository automation should enforce this label consistency, but the agent MUST NOT rely on automation alone and must still set the correct status explicitly.

### Prioritätsgesteuerte Issue-Abarbeitung

Falls GitHub-Issues eine Priorität besitzen, ist diese bei der Auswahl und Reihenfolge der Bearbeitung verbindlich zu beachten.

#### Pflichtregeln

- Bearbeite offene Issues immer in Reihenfolge ihrer Priorität, höchster zuerst.
- Issues ohne Priorität dürfen erst bearbeitet werden, wenn keine höher priorisierten offenen Issues mehr sinnvoll bearbeitbar sind.
- Gleichpriorisierte Issues sind nach fachlicher Abhängigkeit, danach Alter, danach Umsetzungsaufwand sinnvoll zu ordnen.
- Eine Abweichung von der Prioritätsreihenfolge ist nur zulässig bei technischer Blockade, fehlenden Informationen oder ausdrücklicher Nutzeranweisung.
- Jede Abweichung ist kurz zu begründen.

#### Standard-Mapping

- `P1`, `Critical`, `Highest`, `1` → sofort bevorzugt
- `P2`, `High`, `2` → nach P1
- `P3`, `Medium`, `Normal`, `3` → nach P2
- `P4`, `Low`, `4` → nach P3
- keine Priorität → zuletzt

#### Umsetzungspflicht

- Vor Start einer Sammelbearbeitung ist die offene Issue-Liste auf Prioritätsangaben zu prüfen und entsprechend zu sortieren.
- Die Bearbeitung darf nicht unsortiert oder zufällig begonnen werden, wenn Prioritäten vorhanden sind.

### GitHub Issues: Check, Select, Sync

- Always check for open GitHub Issues when starting work on new items (unless the user explicitly points to a specific issue).
  - Commands:
    - `gh issue list --repo <owner>/<repo> --state open --limit 200`
    - `gh issue list --repo <owner>/<repo> --state open --label type/bug --limit 200`
    - `gh issue list --repo <owner>/<repo> --state open --label type/enhancement --limit 200`
- Issues mit dem Label `rememberme` duerfen bei Issue-Pruefung, Triage oder Sammelumsetzung NICHT bearbeitet, umgesetzt, veraendert, kommentiert, geschlossen oder in Auswahl-/Umsetzungspakete aufgenommen werden.
- `rememberme`-Issues sind bei jeder Bearbeitung offener Issues strikt zu ueberspringen, auch wenn der Benutzer allgemein nach offenen Issues oder nach "allen Issues" fragt.
- Present open items grouped by **Bugs** (`type/bug`) vs **Enhancements** (`type/enhancement`).
- The user must be able to decide per issue:
  - implement now
  - defer (backlog)
  - decline
- This per-issue decision flow applies only during explicit triage mode.
- If the user explicitly requests implementation of all open issues or a defined subset of open issues, do NOT require per-issue decisions and process the selected issues immediately.

- Reflect the user's decision back to GitHub:
  - implement now: set `status/in_progress` and add a short comment "picked for implementation"
  - defer: keep `status/open` and add a short comment "deferred"
  - decline: set `status/cancelled`, add a short comment with reason (if provided), and close the issue

### Issue Completion (STRICT)

- An issue counts as implemented only when:
  1. the requested code/config/documentation change is actually applied
  2. all REQUIRED relevant QA checks for that issue have been executed
  3. blocking failures for that issue do not remain
  4. the change has been committed
  5. if repository policy requires it, the change has also been pushed

- Once an issue is implemented by the above definition, the agent MUST immediately do all of the following:
  1. set the issue status label to `status/done`
  2. add an issue comment containing at least:
     - root cause
     - implemented solution
     - commit hash and/or PR link
  3. set the issue to 'close'

- This completion flow is MANDATORY and MUST NOT be skipped.
- The issue MUST be closed even if no PR exists; in that case the commit hash is sufficient.
- Do NOT wait for extra user confirmation to perform the close step if the issue was selected for implementation.

- Wenn du angewiesen wirst, offene Issues zu bearbeiten oder abzuarbeiten, musst du vor jeder Umsetzung den gesamten Issue-Text, alle Kommentare und insbesondere die neuesten Kommentare/Fehlermeldungen lesen und beruecksichtigen.
- Die neueste Information im Issue hat Vorrang vor aelteren Annahmen; keine Umsetzung auf Basis veralteter Informationen.
- Vor jeder Aenderung muss der aktuelle Ist-Zustand der betroffenen Datei(en) gelesen werden; nicht auf erwartete oder fruehere Versionen verlassen.
- Bei `apply_patch verification failed` ist verpflichtend:
  1. betroffene Datei erneut lesen
  2. Zielstelle auf Basis des echten Inhalts neu identifizieren
  3. Patch robust mit Ankern/Kontext statt unveraenderten Erwartungszeilen neu erstellen
- Nach jeder Issue-Umsetzung muss der Issue-Kommentar mindestens enthalten:
  - Ursache des Problems
  - gewaehlte Loesung
  - Commit-Hash und/oder PR-Link
- Nach jeder erfolgreich abgeschlossenen Issue-Umsetzung ist das Issue im selben Arbeitsgang zwingend auf `status/done` zu setzen und zu schliessen.
- Ein Issue darf nach erfolgreicher Umsetzung nicht offen bleiben, nur weil kein PR existiert oder kein weiterer Benutzerhinweis vorliegt.
- Sync selected issues into the local open-points list:
  - add chosen "implement now" issues to the in-chat ToDo list and to `./.opencode/plan_state.md` (with `#<id>` + title)
  - when the issue is completed/declined/deferred, update `./.opencode/plan_state.md` accordingly
- Before declaring an implemented issue complete, verify all of the following:
  - [ ] requested change implemented
  - [ ] relevant QA completed
  - [ ] issue comment added
  - [ ] status set to `status/done`
  - [ ] issue closed
- The issue close step MUST happen only after the required repository completion flow for that issue is finished.
- If the repository policy requires push to `main`, the issue must not be closed before that push succeeded.

### GitHub Comment Execution Safety (CRITICAL)

#### Core Rule

When creating GitHub issue comments via CLI, the agent MUST ensure that the comment text is NOT interpreted by the shell.

#### Mandatory Method (ALWAYS USE)

The agent MUST:

A. Write the full comment text into a temporary Markdown file using a HEREDOC with single-quoted EOF:

```bash
cat > /tmp/opencode_issue_comment.md <<'EOF'
<full comment text including backticks, $, URLs, etc.>
EOF
```

B. Post the comment using:

```bash
gh issue comment <ISSUE_NUMBER> --repo <OWNER>/<REPO> --body-file /tmp/opencode_issue_comment.md
```

#### Forbidden Patterns (STRICT)

The agent MUST NOT use:

```bash
gh issue comment -b "..."
```

if the content contains any of:

- backticks (`...`)
- dollar signs ($...)
- shell-like expressions
- URLs with query parameters
- file paths or commands

Reason:

- Backticks trigger command substitution in the shell
- This leads to unintended command execution (e.g. "command not found")
- Comment content becomes corrupted or partially executed

#### Rationale

Backticks inside double quotes are interpreted by the shell as commands:

```bash
`GET /api/app_state`
```

→ becomes command execution instead of literal text

This MUST be prevented by using HEREDOC with <<'EOF'.

#### Optional Post-Processing

After posting the comment, the agent MAY:

```bash
gh issue edit <ISSUE_NUMBER> --repo <OWNER>/<REPO> --remove-label "status/in_progress" --add-label "status/done"
gh issue close <ISSUE_NUMBER> --repo <OWNER>/<REPO>
```

### Completion Rule

A GitHub issue comment is considered successfully created ONLY if:

- the comment content is fully intact
- no shell errors occurred during execution
- no unintended commands were executed

### GitHub Issues: Proactive Prompting

- In plan mode, after presenting the plan for the user's request, ALWAYS ask whether the user wants to triage GitHub Issues now.
- After finishing implementation of the user's selected points (i.e. when the ToDo list is completed), ALSO ask whether the user wants to triage GitHub Issues next.

Triage flow:

- List open issues grouped by Bugs (`type/bug`) vs Enhancements (`type/enhancement`).
- Let the user pick issues to:
  - implement now
  - defer
  - decline
- Before implementation, allow the user to add/clarify requirements per selected issue (short additions to title/body/acceptance criteria).
  Apply these clarifications to the GitHub issue as a comment (or by editing the issue body) so the context is preserved.
- Only issues explicitly chosen as "implement now" are synced into the in-chat ToDo list and mirrored into `./.opencode/plan_state.md`.

### Shortcut: "prüfe Issues" Verhalten

- Wenn der Benutzer genau die Phrase `prüfe Issues` eingibt, zeige zuerst eine kurze Auswahlfrage (ohne Issues vorab zu laden):
  1) `Alle Issues umsetzen` — alle offenen Issues sofort und ohne weitere Nachfragen umsetzen.
  2) `Auswahl treffen` — zuerst die Liste der offenen Issues anzeigen (gruppiert nach `type/bug` vs `type/enhancement`) und dem Benutzer erlauben, auszuwählen, welche umgesetzt werden sollen.
- WICHTIG: Die Issue‑Liste darf vor der Auswahl nicht geladen oder angezeigt werden — die erste Frage ist ausschließlich dazu da, den Flow zu bestimmen.
- Verhalten bei Auswahl:
  - Wahl 1: Sofort mit der Implementierung aller Issues fortfahren (Änderungen anwenden, Tests/QAs ausführen, `influxbro/config.yaml` version bump, commit und push), ohne weitere per‑Issue Rückfragen.
  - Wahl 2: Normale Triage: Issues auflisten, Auswahl ermöglichen, dann die ausgewählten Issues implementieren.
- Diese Verhaltensregel ist eine Agenten‑Policy und wird in dieser Datei dokumentiert, damit sie persistent ist.

### Requirements Log (local, fallback)

- If GitHub Issues are not available, record user requirements/requests (as written) in `./.opencode/requests_log.md` with date + status.
- Status values: `open`, `in_progress`, `done`, `cancelled`.
- Keep this file local (do not commit); it is not synced to GitHub.
- Update the status when work starts/completes/cancels; optionally include the commit hash/PR link in the entry.

### Persist Plan Changes (VSCode/code-server restarts)

- Mirror the current ToDo/plan state to a workspace file on every meaningful change so it survives editor/server restarts.
  - File: `./.opencode/plan_state.md`
  - Contents: current ToDo list (incl. status), open decisions/questions, and any agreed plan changes.
- At the start of a new session, if `./.opencode/plan_state.md` exists, load it first and restore the pending items before proceeding.
- Keep this file local (do not commit); it is session state, not project source.

## Testing Rules

### Default Test Host

- Use <http://192.168.2.200:8099> for all Home Assistant-backed live integration tests.
- Use this host for:
  - API smoke tests
  - UI validation
  - integration checks
- Localhost remains valid only for isolated local development or container-local verification.

### Playwright E2E Tests

Playwright is configured for browser-based UI testing against the live HA instance.

- Config: `playwright.config.js` (baseURL: `http://192.168.2.200:8099`)
- Tests: `tests/e2e/*.spec.js`
- Run: `npx playwright test` (all tests) or `npx playwright test tests/e2e/dashboard.spec.js` (single file)


### Live-System Tests (Version Check + Update via Playwright)

Wenn Tests gegen das Live-System (Home Assistant Ingress) ausgefuehrt werden, MUSS vor dem Testlauf der Versionsstand von InfluxBro geprueft werden.

Pflichtablauf:

1. Erwartete Version bestimmen

- Quelle: `influxbro/config.yaml` -> `version` (Repo-Stand).

2. Live-Version pruefen

- InfluxBro Web UI oeffnen (Ingress).
- `GET ./api/info` (same-origin) ausfuehren und `version` vergleichen.

3. Wenn Version nicht korrekt ist: Update automatisieren

- Falls Live-Version != erwartete Version, MUSS per Playwright die Aktualisierung auf das neueste InfluxBro Release/Update im Home Assistant UI ausgefuehrt werden.
- Danach Add-on neu starten (falls HA UI das nicht automatisch macht) und Version erneut via `./api/info` verifizieren.

#### Playwright Anweisung (Beispiel)

Voraussetzungen (als Env-Variablen):

- `HA_URL` (z.B. `http://192.168.2.200:8123`)
- `HA_USERNAME`
- `HA_PASSWORD`
- `INFLUXBRO_EXPECT_VERSION` (z.B. `1.12.456`)

Playwright Test-Skript (Snippet, best-effort):

```ts
// playwright/influxbro-update.spec.ts
import { test, expect } from '@playwright/test'

test('update InfluxBro if version mismatches', async ({ page }) => {
  const HA_URL = process.env.HA_URL!
  const USER = process.env.HA_USERNAME!
  const PASS = process.env.HA_PASSWORD!
  const EXPECT = process.env.INFLUXBRO_EXPECT_VERSION!

  await page.goto(HA_URL, { waitUntil: 'domcontentloaded' })

  // Login (works for fresh sessions; already-logged-in is fine)
  if (await page.getByLabel('Username').isVisible().catch(() => false)) {
    await page.getByLabel('Username').fill(USER)
    await page.getByLabel('Password').fill(PASS)
    await page.getByRole('button', { name: /log in/i }).click()
  }

  // Open Add-ons
  await page.goto(`${HA_URL}/hassio/dashboard`, { waitUntil: 'domcontentloaded' })
  await page.getByRole('link', { name: /add-ons/i }).click().catch(() => {})
  await page.getByText('InfluxBro', { exact: false }).click()

  // If an Update button is present, click it
  const updateBtn = page.getByRole('button', { name: /^update$/i })
  if (await updateBtn.isVisible().catch(() => false)) {
    await updateBtn.click()
    // Wait for update to finish (best-effort: wait until Update disappears)
    await expect(updateBtn).toBeHidden({ timeout: 10 * 60 * 1000 })
  }

  // Start/Restart add-on (best-effort)
  const startBtn = page.getByRole('button', { name: /^start$/i })
  if (await startBtn.isVisible().catch(() => false)) {
    await startBtn.click()
  }

  // Open Web UI and verify version via /api/info
  await page.getByRole('button', { name: /open web ui/i }).click()
  const popup = await page.waitForEvent('popup')
  await popup.waitForLoadState('domcontentloaded')

  const liveVer = await popup.evaluate(async () => {
    const r = await fetch('./api/info')
    const j = await r.json().catch(() => ({}))
    return String((j && j.version) || '')
  })
  expect(liveVer).toBe(EXPECT)
})
```

Hinweis:

- Selektoren in HA koennen je nach Version variieren. Wenn die Automation scheitert, Testlauf abbrechen und manuell updaten (oder Selektoren anpassen), bevor Live-Tests fortgesetzt werden.


**"teste auf dem echtsystem" Prompt:**

- When the user says "teste auf dem echtsystem" (or equivalent), the agent MUST:
  1. First check if the live system version matches the latest git version:

     ```bash
     curl -fsS http://192.168.2.200:8099/api/info | python3 -c "import json,sys; print(json.load(sys.stdin).get('version','unknown'))"
     ```

  2. Compare with the latest version in `influxbro/config.yaml`.
  3. If versions DO NOT match: warn the user that the live system is outdated and ask whether to proceed with API tests only, or skip testing until the live system is updated.
  4. If versions MATCH: ask the user whether to also run Playwright E2E browser tests in addition to API smoke tests.
  5. If the user confirms Playwright tests: run `npx playwright test` and report results.

### Mandatory Testing & Cost-Aware Execution (REQUIRED)

After every implementation, testing is REQUIRED, but execution must remain cost-efficient.

### Required QA Flow

Run validation in this order:

1. Syntax / static sanity check first
2. Targeted tests second
3. Runtime / API smoke checks only if relevant
4. Docker/build verification only if relevant
5. Broader validation only if earlier checks fail, the user explicitly requests it, or the change is high-risk

Minimum requirements:

- Syntax check is ALWAYS required:
  - `python -m py_compile influxbro/app/app.py`
- Targeted tests are required WHEN AVAILABLE for the changed functionality:
  - single test by node id
  - single test file
  - keyword-filtered pytest run
- Runtime / API smoke tests are required WHEN RELEVANT for backend routes, request handling, config loading, or UI-triggered API actions.
- Docker verification is required ONLY WHEN RELEVANT for runtime behavior, dependencies, container behavior, startup scripts, add-on packaging, or config handling.
- UI verification is required WHEN RELEVANT for templates, JavaScript, or browser interactions:
  - verify the affected page loads
  - verify the changed interaction path only
  - avoid broad manual retesting of unrelated pages

Execution constraints:

- Prefer targeted reads over full-file rereads.
- Prefer targeted tests over full test suites.
- Do not rerun the same failing test repeatedly without making a change.
- Do not perform Docker/runtime validation if the change is clearly documentation-only or non-runtime-only.
- Use minimal sufficient QA by default; do not automatically expand to full end-to-end or heavy integration tests unless needed.

Failure handling and completion:

- If any required check fails:
  - do NOT declare the work complete
  - fix the issue first
  - rerun the smallest relevant validation set
  - escalate validation scope only if needed
- If a user-reported or agent-reproduced UI/browser-visible error remains present after at least one concrete fix attempt, explicitly offer a Playwright-based browser test to validate the real interaction path.
- Implementation is ONLY complete if all relevant required checks passed.
- After completing all REQUIRED tests, DO NOT ask the user whether additional testing should be performed unless:
  - the user explicitly requested it
  - critical functionality could not be tested
  - the test environment is incomplete

Reporting:

- At the end of the task, explicitly report:
  - which checks were executed
  - which were skipped
  - why they were skipped
  - final result of each executed check

## Build / Run / Lint / Test

### Test Rules

#### Robust Local Start / Healthcheck (REQUIRED)

When starting a local server (Flask or similar), the agent MUST:

- NOT rely on fixed short sleep (e.g. `sleep 2` / `sleep 4`)
- ALWAYS verify readiness via API endpoint

##### Readiness Rule

A service is considered READY only if:

- the health endpoint responds successfully
- AND returns valid JSON

Port listening alone is NOT sufficient.

##### Required Health Endpoint

- <http://127.0.0.1:8099/api/info>

##### Mandatory Readiness Loop

The agent MUST use a retry loop:

```bash
ready=0
for i in {1..20}; do
  if curl -fsS http://127.0.0.1:8099/api/info >/tmp/influxbro_info.json 2>/dev/null; then
    python3 - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("/tmp/influxbro_info.json").read_text())
print(data.get("version", "unknown"))
PY
    echo "Service ready"
    ready=1
    break
  fi
  echo "Waiting for local service... ($i/20)"
  sleep 1
done
```

##### Failure Handling

If the service is NOT ready after retries, the agent MUST:

- inspect `/tmp/influxbro_local.log`
- check whether the process still exists
- check whether port `8099` is listening
- classify the failure as one of:
  - startup delay
  - app crash
  - bind/port problem
  - health endpoint failure

If readiness cannot be confirmed, the agent MUST treat this as a blocker and MUST NOT continue as if the app were running.

##### Forbidden Pattern

The agent MUST NOT use a fixed short sleep as the sole readiness check, for example:

```bash
nohup python influxbro/app/app.py >/tmp/influxbro_local.log 2>&1 & sleep 4 && curl -fsS http://127.0.0.1:8099/api/info
```

Reason:

- fixed sleep is unreliable
- the app may still be starting
- a single early failed curl can incorrectly stop the workflow

##### Completion Rule

The local start step is only complete if:

- the app process was started
- the health endpoint responded successfully
- the response was validated as JSON
- the agent explicitly reports readiness before continuing

### Run locally (Docker)

Minimum (no HA supervisor; you must provide `/data/options.json` yourself):

```bash
mkdir -p .local-data
cat > .local-data/options.json <<'JSON'
{ "version": "dev", "allow_delete": false, "delete_confirm_phrase": "DELETE" }
JSON

docker run --rm -p 8099:8099   -v "$PWD/.local-data:/data"   -v "$PWD:/repo:ro"   influxbro:dev
```

Notes:

- The UI is served on `http://127.0.0.1:8099/`.
- In real HA, Ingress changes the base path; keep relative URLs (current templates do).

#### Run locally (Python, outside Docker)

This repo does not ship a lockfile/pyproject; for quick iteration:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install flask influxdb-client influxdb PyYAML

# emulate add-on env
export ALLOW_DELETE=false
export DELETE_CONFIRM_PHRASE=DELETE
export ADDON_VERSION=dev

python influxbro/app/app.py
```

#### Lint / Static checks

There is no enforced linter in CI today, but ruff/black + pre-commit config exist.

Baseline checks that should always work:

```bash
python -m compileall influxbro/app/app.py
python -m py_compile influxbro/app/app.py
```

Recommended (optional) tooling for agents:

```bash
python -m pip install ruff black
ruff check influxbro/app/app.py
black --check influxbro/app/app.py

# or run via pre-commit
python -m pip install pre-commit
pre-commit run --all-files
```

#### Tests

Pytest is available (see `tests/` + `pytest.ini`). Prefer patterns that make running a single test easy:

```bash
# run one file
pytest tests/test_api_yaml_flow.py -q

# run one test by node id
pytest tests/test_api_yaml_flow.py::test_load_influx_yaml_resolves_secret -q

# run a subset by keyword
pytest -k measurements -q
```

#### Manual “single test” (API smoke)

After starting the app, these are useful targeted checks:

```bash
curl -fsS http://localhost:8099/api/info | jq .
curl -fsS http://localhost:8099/api/config | jq .

# connectivity test uses the posted form values
curl -fsS -X POST http://localhost:8099/api/test   -H 'Content-Type: application/json'   -d '{"influx_version":2,"scheme":"http","host":"localhost","port":8086,"verify_ssl":true,"timeout_seconds":10,"org":"...","bucket":"...","token":"..."}' | jq .
```

## End-of-Implementation Verification (Required)

- At the end of every implementation, explicitly verify that all requirements and all ToDo items were actually implemented.
- If any planned item could not be implemented (or remains only partially implemented), explicitly call it out with:
  - what is missing
  - why it is missing
  - what would be needed to complete it
- Perform a final checklist-style confirmation before declaring the work finished.

## Interaction Rules

### Questions: Numeric Choices

- When asking the user to choose between options:
  - always provide numbered options (1, 2, 3, …)
  - allow the user to respond with just the number
- Example:
  1. Merge
  2. Rebase
  3. Fast-forward only

## Execution Policies

### Autonomous Execution Policy (NO INTERMEDIATE QUESTIONS)

#### Core Rule

- If the user explicitly approves implementation (e.g. "implement all issues", "go", or equivalent),
  the agent MUST execute all tasks end-to-end WITHOUT asking intermediate questions.

#### No-Interruption Rule

- DO NOT ask for:
  - step-by-step confirmation
  - prioritization choices
  - “how should I proceed?” questions
  - numbered selection prompts (1/2/3)

- Once execution is approved:
  - proceed through ALL ToDo items automatically
  - only stop if a real blocker exists

#### Allowed Interruptions (ONLY THESE)

The agent MAY interrupt execution ONLY if:

- critical information is missing (cannot proceed)
- external dependency is required (e.g. credentials, API access)
- multiple valid implementations exist with significant impact
- a destructive or irreversible action is required

#### Default Behavior

- Assume: user wants FULL execution of approved tasks
- Execute tasks sequentially until:
  - all ToDo items are completed OR
  - a real blocker is encountered

#### Handling Multi-Issue Execution

If multiple issues are selected:

- process issues sequentially
- complete one issue fully before starting the next
- DO NOT ask between issues
- DO NOT re-confirm execution
- Wenn der Benutzer verlangt, dass offene Issues abgearbeitet werden, dann gilt dies fuer ALLE von ihm ausgewaehlten Issues, bis diese vollstaendig umgesetzt sind.
- Formulierungen wie `arbeite alle Issues ab` oder `arbeite alle Issues ausser #134 ab` sind als vollstaendige Arbeitsanweisung zu verstehen; sie benoetigen keine zusaetzliche Bestaetigung, kein weiteres `GO` und keine Rueckfrage zur Paketbildung.
- Wenn der Benutzer einzelne Issues explizit ausschliesst, dann sind alle uebrigen offenen Issues automatisch zur Umsetzung ausgewaehlt.
- Wenn mehrere kleinere Umsetzungspakete sinnvoll sind, duerfen diese Pakete nacheinander erstellt werden, aber:
  - die restlichen vom Benutzer angeforderten Issues bleiben verpflichtend offen im Plan
  - sie muessen danach automatisch weiter bearbeitet werden
  - es darf nicht nach dem ersten Paket stehen geblieben werden, solange kein echter Blocker existiert
- Offene Issues, die laut Benutzer umgesetzt werden sollen, muessen selbststaendig automatisch weiter bearbeitet und abgeschlossen werden, bis keine solcher Issues mehr offen sind.

#### Reporting

- Only report:
  - after a logical block is completed (e.g. one issue fully implemented), OR
  - at the very end

- Reporting must NOT include questions unless a blocker exists
- Reporting after one completed issue is allowed, but reporting must NOT pause or block continued execution when the user explicitly requested that multiple issues be processed automatically.
- After reporting one completed issue, immediately continue with the next selected issue unless a real blocker exists.

### Agent Command Convention

#### GO

- If the user writes `go` (or `GO`), treat that as: stage relevant changes, create a git commit with an appropriate message, and push to the tracked remote branch.

- Showing current open GitHub issues (grouped by Bugs vs Enhancements) after an implementation package is OPTIONAL and informational only.

- It MUST NOT:
  - interrupt execution
  - trigger questions
  - pause or delay further processing

- During active multi-issue execution:
  - this step MUST be skipped entirely unless explicitly requested by the user
  
### Auto Push & PR Policy (ENFORCED – HA MAIN-FIRST MODE)

#### Core Principle

- Home Assistant ONLY detects updates from the `main` branch.
- Therefore ALL changes MUST be pushed to `main` to enable testing inside Home Assistant.
- Feature branches and PR-only workflows are NOT the default in this repository.

#### Mandatory Completion Flow (NO SILENT STOP)

After successful implementation AND completed QA:

- DO NOT ask for confirmation.
- ALWAYS complete this sequence for build/GO execution when applicable:
  1. run required QA
  2. classify any failures as either:
     - fix-related/blocking
     - pre-existing/unrelated
  3. if failures are only pre-existing/unrelated, continue mandatory completion flow
  4. bump `influxbro/config.yaml` version when runtime, UI, API, or behavior changed
  5. stage changes
  6. create commit
  7. push to `main`
  8. report result clearly in chat
- It is FORBIDDEN to stop after code changes or after QA only, if the policy in this file requires version bump, commit, and push.
- It is FORBIDDEN to treat `build` mode as mere permission while skipping mandatory completion steps.
- Before declaring implementation complete, explicitly verify:
  - implementation finished
  - required QA executed
  - QA result classified
  - `influxbro/config.yaml` version bumped if required
  - changes staged
  - commit created
  - push to `main` completed
- If any item is missing, the task is NOT complete.

#### Version Bump (CRITICAL FOR HA)

- Jede Aenderung am Code erzwingt eine neue Version.
  - Sobald Python, HTML, JavaScript, CSS, Docker-, Shell- oder sonstige Laufzeit-/Build-Logik geaendert wird, MUSS zwingend eine neue Add-on-Version erzeugt werden.
  - Es gibt keine Ausnahmen fuer kleine Fixes, Refactorings oder rein strukturelle Codeaenderungen.

- Every change that affects runtime, UI, API, or behavior MUST:
  - increment `version` in `influxbro/config.yaml`

- Without version bump:
  - Home Assistant will NOT detect an update
  - die Aenderung gilt in diesem Repository als unvollstaendig

- Version format:
  - increment last digit (e.g. 1.12.44 → 1.12.45)

#### Live Verification Gate (CRITICAL FOR HA)

- Before any live verification against Home Assistant / the running add-on instance, the required code changes MUST already be available as an add-on version on `main`.
- Therefore, before a live check against the HA instance, the agent MUST first:
  - stage changes
  - create commit
  - bump `influxbro/config.yaml` version if runtime/UI/API/behavior changed
  - push to `main`
- The agent MUST NOT rely on local-only uncommitted changes for HA live verification.
- If the live instance still runs an older version, the agent must explicitly state that the requested live verification cannot validate the new code until the updated add-on version is installed in Home Assistant.

#### Decision Logic (SIMPLIFIED FOR HA)

Default rule:

- If a change affects runtime, UI, API, or behavior, use the HA main-first flow:
  - commit
  - bump version
  - push directly to `main`

High-risk exception handling:

- If the change involves security-related logic, deletion logic, major architecture changes, or unclear side effects:
  - STILL push to `main` for HA testing
  - BUT:
    - ensure stricter QA before push
    - clearly label the commit message with `⚠ HIGH-RISK`

#### Optional Branch Usage (LIMITED)

Branches MAY be used ONLY if:

- change can be tested locally WITHOUT Home Assistant
- OR user explicitly requests PR workflow

Otherwise:

- ALWAYS use `main`

#### Commit Rules

- Use structured commit messages:
  - feat: for new features
  - fix: for bug fixes
  - refactor: for restructuring
  - chore: for maintenance

- Include short summary + key changes

- For risky changes:
  - prefix with: `⚠ HIGH-RISK`

#### Issue-, Commit- und Pull-Request-Workflow

- Vor jeder Umsetzung muss die Aenderung eingeordnet werden:
  - klein, eindeutig, risikoarm -> direkter Commit
  - komplex, mehrdeutig, mehrere Dateien oder potenziell riskant -> strengere Analyse, erweiterte QA und nur bei ausdruecklichem Benutzerwunsch Branch/PR-Workflow
- In diesem Repository gilt weiterhin die HA-Main-First-Regel:
  - Standard ist direkter Commit nach `main`
  - PR/Branch nur wenn der Benutzer dies ausdruecklich verlangt oder wenn die bestehende Repo-Policy explizit dafuer geaendert wird
- Auch wenn eine Issue existiert, ist nicht automatisch ein PR erforderlich; entscheidend sind Komplexitaet, Risiko und Repo-Policy.
- Vor jeder Umsetzung ist verbindlich zu klaeren:
  - betroffene Dateien/Logikbereiche
  - Ursache des Problems
  - ob die Loesung klein und eindeutig ist oder interpretative/risikoreiche Annahmen enthaelt
- Wenn eine Umsetzung fehlschlaegt:
  - denselben Ansatz nicht blind wiederholen
  - aktuellen Datei-Iststand neu lesen
  - Ursache analysieren
  - Loesung auf Basis des realen Zustands neu ableiten

#### Safeguards (MANDATORY)

- NEVER push if:
  - syntax check failed
  - required QA not executed
  - blocking errors exist

- Pre-existing or unrelated failing tests do NOT automatically count as blocking errors.
  - The agent MUST explicitly state why they are unrelated.
  - If the implemented change passed its relevant QA, the mandatory version-bump/commit/push flow still applies.

- ALWAYS ensure:
  - minimal QA passed
  - version bump applied

- NEVER force push

#### Completion Behavior

After push:

- report:
  - new version number
  - commit summary
  - confirmation that HA update is available

- DO NOT ask for confirmation

#### Override Rule

If user explicitly requests:

- branch workflow
- PR creation
- no push

→ follow user instruction instead of this policy

#### GO Must Complete Planned Work

- When the user start working on issues, you MUST ensure all open/pending planned work is implemented before committing/pushing.
- "Planned work" includes both:
  - the current request's ToDo list (in-chat)
  - any remaining open items recorded in `./.opencode/plan_state.md` (if the file exists)
- If implementing everything in one batch is not sensible (too risky/too large), you MUST:
  - explicitly state you are splitting into multiple smaller packages,
  - commit/push only the first package,
  - and immediately list the remaining planned items still pending.
- Diese verbleibenden geplanten Items muessen danach automatisch weiter umgesetzt werden, bis alle vom Benutzer angeforderten Issues abgearbeitet sind oder ein echter Blocker vorliegt.
- Dasselbe gilt ausdruecklich fuer ausgewaehlte/offene GitHub-Issues: sie muessen selbststaendig automatisch weiter bearbeitet und abgeschlossen werden, bis keine zur Umsetzung vorgesehenen Issues mehr offen sind.
- Auch bei Befehlen wie `arbeite alle Issues ausser #134 ab` muessen die verbleibenden offenen Issues automatisch ohne Rueckfrage bis zum Abschluss abgearbeitet werden.
- After a successful workflow (commit + push), play a macOS completion sound:
  - `afplay /System/Library/Sounds/Glass.aiff`
  - If the workflow fails, play an error sound:
    - `afplay /System/Library/Sounds/Basso.aiff`
- After the completion sound, speak a short status message via macOS `say`:
  - If the workflow produced a new add-on version (i.e., `influxbro/config.yaml` version was bumped as part of the changes), use a female voice and speak the version as a version number (not a date), e.g. `say -v Anna "Generierung erfolgt, Version 1 Punkt 11 Punkt 34 wurde erzeugt"` (version derived from `influxbro/config.yaml`)
  - If the workflow ends with pending questions/blockers: `say "Einige Punkte müssten noch beantwortet werden"`

### Audio Notifications (Environment-specific / macOS)

- After completing any user-requested execution/workflow that runs commands, play a macOS completion sound:
  - success / ready for next input: `afplay /System/Library/Sounds/Glass.aiff`
  - failure / blocker: `afplay /System/Library/Sounds/Basso.aiff`
- If you need any blocking input or decision from the user, also speak a short German prompt via `say`:
  - default for decision needed: `say "Entscheidung erforderlich"`
  - optional confirmation-style prompt: `say "Bitte bestaetigen"`
- If the requested work is fully done and you are ready for the next instruction, speak:
  - `say "Fertig mit der Umsetzung"`
- Only speak the "Generierung erfolgt..." version message when a new add-on version was produced via version bump in `influxbro/config.yaml`.
