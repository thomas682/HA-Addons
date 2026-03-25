# 🧠 AI Efficiency, Model Strategy & Cost Optimization (CRITICAL)

## Model Strategy

- Moduswechsel 2026-03-19: Betriebsmodus `build` aktiv. Der Agent darf Aenderungen am Arbeitsbaum vornehmen, Tests ausfuehren sowie Commits/Pushes nach `main` erstellen.

### Default Model Strategy

- API:
  - PRIMARY: gpt-4o
  - SECONDARY: gpt-4o-mini

- Web:
  - Use the available GPT-5-class model
  - Apply the same task selection principles conceptually

## Workspace Requirement (CRITICAL)

- The agent MUST operate from the repository root.
- Before any search, read, write, git, or test operation, verify that the working directory contains:
  - `influxbro/`
  - `AGENTS.md`
  - `repository.yaml`

- If these are not present:
  - STOP immediately
  - report: `Wrong working directory – repository root required`

- The agent MUST NOT assume project structure or continue analysis if the working directory is incorrect.

## Model Usage Policy (STRICT)

### gpt-4o (PRIMARY – REQUIRED for reasoning)

Use for:

- code analysis
- debugging
- multi-file changes
- repository search
- UI + backend interactions
- unknown problem investigation

### gpt-4o-mini (SECONDARY – LIMITED USE)

Use ONLY for:

- documentation generation
- changelog writing
- commit messages
- simple text transformations
- formatting tasks

### HARD RULES

- It is FORBIDDEN to use gpt-4o-mini for:
  - debugging
  - unknown code analysis
  - repository-wide search
  - multi-file logic changes

## Automatic Model Switching

- If task involves:
  - reading code
  - searching files
  - debugging
  - multiple files
→ MUST use gpt-4o

- If task involves ONLY:
  - writing text
  - formatting
  - summarizing
→ MAY use gpt-4o-mini

### Escalation rules

Escalate ONLY if:

- multi-file architecture changes
- repeated failures (>2 attempts)
- complex debugging (concurrency, SQL, parsing, security)
- unclear solution space
- insufficient exploration detected (too few files searched or early termination)

### De-escalation

- After a successful solution:
  - return to the default model for the current task class
  - use gpt-4o for code/debug/search tasks
  - use gpt-4o-mini only for documentation/text-only tasks

## Token Efficiency Guard

- Prefer fewer high-quality requests over many small ones
- Avoid repeated retries with the same model
- If 2 attempts fail → escalate model immediately

## Automatic Escalation (ERROR-DRIVEN)

### Purpose

Ensure robust behavior in API mode by automatically escalating the model when weak or incomplete results are detected.

### Escalation triggers

Escalate to a stronger model (gpt-4o) if ANY of the following occurs:

#### 1. Search failure

- target symbol/function not found
- only 1–2 files searched
- search limited to a single file type (e.g. only *.js)

#### 2. Early termination

- analysis stops after first attempt
- no follow-up search or refinement
- no expansion of search scope

#### 3. Low-confidence result

- phrases like:
  - "not found"
  - "does not exist"
  - "no results"
  - "probably"
- without exhaustive search

#### 4. Repeated failure

- same issue not solved after 1 attempt
- patch failed or did not apply correctly
- bug persists after change

#### 5. Incomplete code understanding

- missing relationships between components
- ignoring templates, backend, or config
- partial system analysis

### Escalation behavior

When a trigger is detected:

1. Immediately switch to a stronger model (API: gpt-4o)
2. Restart analysis with:
   - broader search scope
   - multiple search passes
   - inclusion of all file types
3. Do NOT reuse previous incomplete conclusions
4. Re-evaluate the problem from scratch if necessary

### De-escalation

- After a successful solution:
  - return to default model (gpt-4o-mini)

### Hard rule

- It is FORBIDDEN to conclude "not found" without:
  - searching the full repository
  - including all relevant file types
  - performing at least 2 search passes
  
## Exploration Depth Requirement (CRITICAL)

- Minimum exploration:
  - at least 2 search passes
  - at least 2 different file types
  - at least 3 relevant files or sections inspected

- If this is not met:
  → trigger escalation

- It is NOT allowed to conclude analysis before minimum exploration is reached.

- DO NOT read large files sequentially in chunks unless absolutely required.

- Prefer:
  - targeted search
  - symbol search
  - relevant sections
  - surrounding context only

- If a file is large:
  - read only the relevant sections
  - avoid full sequential reads

## Context Efficiency

- Read only relevant files
- Never load full repo unless required
- Prefer partial reads (functions/sections)
- Search first, read second
- For large files, inspect only relevant sections unless a full read is unavoidable

## Deep Analysis Override (CRITICAL FOR API MODE)

- For code search and debugging tasks:
  - ALWAYS perform multiple search passes
  - NEVER stop after first unsuccessful result
  - EXPAND search scope if nothing is found

- Ignore cost optimization rules when:
  - searching for functions
  - analyzing bugs
  - investigating missing behavior

- Always include:
  - Python (*.py)
  - HTML templates (*.html)
  - inline JavaScript
  - configuration files

- If a symbol is not found:
  - assume it may exist in another file type
  - re-run search with broader scope

- Prefer completeness over cost in analysis phase.
  
## Output Efficiency

- Prefer diffs over full files
- Do NOT repeat unchanged code
- Keep explanations short unless requested

## Cost Behavior

- Avoid unnecessary iterations, BUT allow multiple iterations for code analysis and debugging
- Prefer small incremental changes
- Use tools (grep/search) instead of reading many files

This repository contains a Home Assistant add-on (Ingress UI) for browsing/cleaning InfluxDB data.

UI design standard

- Before adding/changing any GUI element (tables, buttons, checkboxes, selects, etc.), consult `influxbro/Template.md`.
- Keep pages aligned with the master table template (toolbar above table, column resize, auto-fit/window-fit, wrap toggle, per-column filters, height resize, info icon).

New Requests: Issue or Immediate Implementation

- Only ask whether a request should be recorded as a GitHub Issue or implemented immediately if the user is describing a NEW requirement that is not already tracked in GitHub.
- If the user explicitly instructs the agent to work on existing open GitHub Issues, do NOT ask this question and start implementation immediately according to the selected issue scope.
- The requirement to choose between "record as issue" and "implement immediately" applies only to new, not-yet-tracked requests and must NOT block execution of already existing GitHub Issues selected by the user.

Default Test Host & Operational Mode

- Verwende standardmäßig für externe API‑Smoke/Integrationstests die Add‑on IP `http://192.168.2.200:8099` (sofern vom Benutzer nicht anders angegeben). Tests gegen `127.0.0.1:8099` sind nur für lokale Entwicklungsinstanzen gedacht.
- Benutzerhinweis 2026-03-19: Für Tests gegen die Home-Assistant-Installation ausschließlich `http://192.168.2.200:8099` verwenden.
- Betriebsmodus: Wenn der Benutzer den Betriebsmodus auf "build"/"GO" wechselt, darf der Agent Änderungen am Arbeitsbaum vornehmen, Dateien ändern, Tests ausführen und Commits/pushes nach `main` erstellen, gemäß den sonstigen Repo‑Richtlinien. Notiere solche Moduswechsel in `AGENTS.md` und handle danach entsprechend.

Questions: Numeric Choices

- If you need user input and the answer is a selection (A/B, yes/no, option set), write the question so the user can reply with a single number.
  - Example: "Soll ich (1) das speichern oder (2) nicht speichern? Antworte nur mit 1 oder 2."

GitHub Issues: Language

- When creating GitHub Issues for the user, write the title and body in German.

Kommunikation

- Alle Interaktionen im Chat mit dem Benutzer sollen auf Deutsch erfolgen. Wenn du dem Benutzer eine Frage stellst oder eine Entscheidung einforderst, formuliere diese Frage auf Deutsch.
- Wenn Elemente aus dem Programm geloescht oder entfernt werden, muessen alle damit verbundenen Verweise, Funktionen, UI-Elemente, Listener und Datenpfade geprueft und so umgebaut werden, dass der Code auch ohne dieses Element fehlerfrei funktioniert.
- Wenn der Benutzer sagt "uebernehme die Funktion", muss vor der Umsetzung geklaert werden, ob der Code 1:1 wortgleich uebernommen werden soll oder ob nur funktionale Anpassungen gewuenscht sind. Bei echter Codeuebernahme duerfen alte Elemente nicht weiterverwendet werden; diese sind zu entfernen und der uebernommene Code ist anschliessend nur noch fuer die neue Zielumgebung anzupassen.
- Vergleiche UI-Komponenten niemals nur auf Containerebene. Pruefe immer die vollstaendige Komponentenstruktur einschliesslich: direkter und indirekter Child-Elemente, sichtbarkeits- und zustandsabhaengiger Renderlogik, Properties, Klassen, Styles und Layout-Regeln, Event-Handlern und Interaktionen, Datenquellen, Bindings und Seiteneffekten.
- Zwei Elemente gelten nur dann als gleich, wenn nicht nur der Container, sondern auch alle damit zusammenhaengenden funktionalen und visuellen Unterelemente gleich arbeiten.

No Cursor/Copilot instruction files were found at:

- `.cursor/rules/`
- `.cursorrules`
- `.github/copilot-instructions.md`

## Parallel Execution Strategy (CONTROLLED)

### General Rule

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

## Plan Mode Workflow

When plan mode is active:

- Create a detailed plan first.
- Show all tasks that need to be done.
- Group tasks logically.
- Wait for explicit user approval before implementing anything (no file edits, no commits, no pushes).

## Task Tracking (ToDo List)

- Always create and show a ToDo list for the current request.
- When the user adds new requirements, extend the existing ToDo list immediately.
- Keep exactly one item `in_progress` at a time.
- Mark items `completed` as soon as they are done.
- Ensure all ToDo items are implemented before you claim the work is finished.

## Autonomous Execution Policy (NO INTERMEDIATE QUESTIONS)

### Core Rule

- If the user explicitly approves implementation (e.g. "implement all issues", "go", or equivalent),
  the agent MUST execute all tasks end-to-end WITHOUT asking intermediate questions.

### No-Interruption Rule

- DO NOT ask for:
  - step-by-step confirmation
  - prioritization choices
  - “how should I proceed?” questions
  - numbered selection prompts (1/2/3)

- Once execution is approved:
  - proceed through ALL ToDo items automatically
  - only stop if a real blocker exists

### Allowed Interruptions (ONLY THESE)

The agent MAY interrupt execution ONLY if:

- critical information is missing (cannot proceed)
- external dependency is required (e.g. credentials, API access)
- multiple valid implementations exist with significant impact
- a destructive or irreversible action is required

### Default Behavior

- Assume: user wants FULL execution of approved tasks
- Execute tasks sequentially until:
  - all ToDo items are completed OR
  - a real blocker is encountered

### Handling Multi-Issue Execution

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

### Reporting

- Only report:
  - after a logical block is completed (e.g. one issue fully implemented), OR
  - at the very end

- Reporting must NOT include questions unless a blocker exists
- Reporting after one completed issue is allowed, but reporting must NOT pause or block continued execution when the user explicitly requested that multiple issues be processed automatically.
- After reporting one completed issue, immediately continue with the next selected issue unless a real blocker exists.

## End-of-Implementation Verification (Required)

- At the end of every implementation, explicitly verify that all requirements and all ToDo items were actually implemented.
- If any planned item could not be implemented (or remains only partially implemented), explicitly call it out with:
  - what is missing
  - why it is missing
  - what would be needed to complete it
- Perform a final checklist-style confirmation before declaring the work finished.

## Mandatory Testing & Cost-Aware Execution (REQUIRED)

After every implementation, testing is REQUIRED, but execution must remain cost-efficient.

### Execution Order

Run checks in this order:

1. Syntax / static sanity check first
2. Targeted tests second
3. Runtime / Docker checks only if relevant
4. Full broader validation only if earlier checks fail or the change is high-risk

### Minimum Required Checks

#### 1. Syntax Check (ALWAYS)

Run:

- `python -m py_compile influxbro/app/app.py`

This must pass before declaring the work complete.

#### 2. Targeted Tests (WHEN AVAILABLE)

If existing tests cover the changed functionality, run the smallest relevant subset first, for example:

- single test by node id
- single test file
- keyword-filtered pytest run

Examples:

- `pytest tests/test_api_yaml_flow.py -q`
- `pytest tests/test_api_yaml_flow.py::test_load_influx_yaml_resolves_secret -q`
- `pytest -k measurements -q`

Do NOT start with full test suites unless necessary.

#### 3. Runtime / API Smoke Test (WHEN RELEVANT)

If backend routes, request handling, config loading, or UI-triggered API actions were changed, perform at least one relevant smoke test.

Examples:

- `curl -fsS http://localhost:8099/api/info | jq .`
- `curl -fsS http://localhost:8099/api/config | jq .`

#### 4. Docker Verification (ONLY WHEN RELEVANT)

Build and/or run Docker ONLY if changes affect:

- runtime behavior
- dependencies
- container behavior
- startup scripts
- add-on packaging
- config handling

Example:

- `docker build -t influxbro:dev ./influxbro`

### UI Verification (WHEN RELEVANT)

If templates, JavaScript, or browser interactions were changed:

- verify the affected page loads
- verify the changed interaction path only
- avoid broad manual retesting of unrelated pages

### Cost Optimization Rules

- Prefer the cheapest sufficient model for:
  - syntax-related fixes
  - log interpretation
  - small single-file corrections
  - narrow follow-up adjustments

- Use the stronger model only for:
  - multi-file architecture work
  - repeated failed fixes
  - complex debugging
  - ambiguous root-cause analysis

- Prefer targeted reads over full-file rereads.
- Prefer targeted tests over full test suites.
- Do not rerun the same failing test repeatedly without making a change.
- Do not perform Docker/runtime validation if the change is clearly documentation-only or non-runtime-only.

### Failure Handling

If any required check fails:

- do NOT declare the work complete
- fix the issue first
- rerun the smallest relevant validation set
- escalate validation scope only if needed

### Completion Rule

Implementation is ONLY complete if:

- syntax check passed
- relevant targeted tests passed (if applicable)
- relevant runtime/API checks passed (if applicable)
- relevant Docker/build checks passed (if applicable)

### Reporting Rule

At the end of the task, explicitly report:

- which checks were executed
- which were skipped
- why they were skipped
- final result of each executed check

## QA Depth Strategy

- Perform ONLY minimal sufficient QA by default:
  - syntax
  - API smoke tests
  - basic runtime verification

- Do NOT automatically perform:
  - full end-to-end tests
  - UI interaction simulations
  - heavy integration tests

- Only expand QA depth if:
  - user explicitly requests it
  - previous tests failed
  - change is high-risk

## QA Completion Policy (NO QUESTIONS)

- After completing all REQUIRED tests, DO NOT ask the user whether additional testing should be performed.

- If all required checks passed:
  - declare QA as completed
  - provide a short summary of results
  - proceed to next logical step (e.g. push, PR, or finish)

- Only ask for additional QA if:
  - explicitly requested by the user
  - critical functionality could not be tested
  - test environment is incomplete (e.g. missing InfluxDB)

- Default behavior:
  - minimal sufficient QA
  - no interactive confirmation required

## Auto Push & PR Policy (ENFORCED – HA MAIN-FIRST MODE)

### Core Principle

- Home Assistant ONLY detects updates from the `main` branch.
- Therefore ALL changes MUST be pushed to `main` to enable testing inside Home Assistant.
- Feature branches and PR-only workflows are NOT the default in this repository.

### Default Behavior (MANDATORY)

After successful implementation AND completed QA:

- DO NOT ask for confirmation
- ALWAYS:
  - stage changes
  - create commit
  - bump add-on version
  - push directly to `main`

### Version Bump (CRITICAL FOR HA)

- Every change that affects runtime, UI, API, or behavior MUST:
  - increment `version` in `influxbro/config.yaml`

- Without version bump:
  - Home Assistant will NOT detect an update

- Version format:
  - increment last digit (e.g. 1.12.44 → 1.12.45)

### Decision Logic (SIMPLIFIED FOR HA)

#### Case 1: Small / Medium Changes

If the change is:

- bugfix
- small feature
- UI change
- API adjustment
- limited multi-file change

THEN:

- commit
- bump version
- push directly to `main`

#### Case 2: Larger Changes (HA-Test Required)

If the change involves:

- multiple files
- new features
- refactoring
- logic changes

AND requires testing inside Home Assistant:

THEN:

- commit
- bump version
- push directly to `main`

#### Case 3: High-Risk Changes

If the change involves:

- security-related logic
- deletion logic
- major architecture changes
- unclear side effects

THEN:

- STILL push to `main` (for HA testing)
- BUT:
  - clearly label commit message with:
    - `⚠ HIGH-RISK`
  - ensure stricter QA before push

### Optional Branch Usage (LIMITED)

Branches MAY be used ONLY if:

- change can be tested locally WITHOUT Home Assistant
- OR user explicitly requests PR workflow

Otherwise:

- ALWAYS use `main`

### Commit Rules

- Use structured commit messages:
  - feat: for new features
  - fix: for bug fixes
  - refactor: for restructuring
  - chore: for maintenance

- Include short summary + key changes

- For risky changes:
  - prefix with: `⚠ HIGH-RISK`

### Issue-, Commit- und Pull-Request-Workflow

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

### Safeguards (MANDATORY)

- NEVER push if:
  - syntax check failed
  - required QA not executed
  - blocking errors exist

- ALWAYS ensure:
  - minimal QA passed
  - version bump applied

- NEVER force push

### Completion Behavior

After push:

- report:
  - new version number
  - commit summary
  - confirmation that HA update is available

- DO NOT ask for confirmation

### Override Rule

If user explicitly requests:

- branch workflow
- PR creation
- no push

→ follow user instruction instead of this policy

## Requirements Tracking (preferred: GitHub Issues)

- Track requirements primarily as GitHub Issues so others can create/report items externally.
- Use the issue templates to distinguish between:
  - Bug reports (not working): label with `type/bug`
  - Enhancements (feature requests): label with `type/enhancement`
- Use exactly one status label per issue: `status/open`, `status/in_progress`, `status/done`, `status/cancelled`.
- Ensure the label set exists in GitHub (create once in the GitHub UI); the issue templates assume these labels are available.
- When implementing, link PRs to issues and close them via `Fixes #<id>`.

### GitHub Issues: Check, Select, Sync

- Always check for open GitHub Issues when starting work on new items (unless the user explicitly points to a specific issue).
  - Commands:
    - `gh issue list --repo <owner>/<repo> --state open --limit 200`
    - `gh issue list --repo <owner>/<repo> --state open --label type/bug --limit 200`
    - `gh issue list --repo <owner>/<repo> --state open --label type/enhancement --limit 200`
- Present open items grouped by **Bugs** (`type/bug`) vs **Enhancements** (`type/enhancement`).
- The user must be able to decide per issue:
  - implement now
  - defer (backlog)
  - decline
- This per-issue decision flow applies only during explicit triage mode.
- If the user explicitly requests implementation of all open issues or a defined subset of open issues, do NOT require per-issue decisions and process the selected issues immediately.

- Reflect the user's decision back to GitHub:
  - implement now: set `status/in_progress` and (optionally) add a short comment "picked for implementation"
  - defer: keep `status/open` and add a short comment "deferred"
  - decline: set `status/cancelled`, add a short comment with reason (if provided), and close the issue
- When implementation is finished:
  - set `status/done`
  - add a comment with the PR URL and/or commit hash
  - close the issue
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
- Sync selected issues into the local open-points list:
  - add chosen "implement now" issues to the in-chat ToDo list and to `./.opencode/plan_state.md` (with `#<id>` + title)
  - when the issue is completed/declined/deferred, update `./.opencode/plan_state.md` accordingly

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

## Repo Layout (important for HA)

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

## Build / Run / Lint / Test

### Build the add-on image

From repo root:

```bash
docker build -t influxbro:dev ./influxbro
```

### Run locally (Docker)

Minimum (no HA supervisor; you must provide `/data/options.json` yourself):

```bash
mkdir -p .local-data
cat > .local-data/options.json <<'JSON'
{ "version": "dev", "allow_delete": false, "delete_confirm_phrase": "DELETE" }
JSON

docker run --rm -p 8099:8099 \
  -v "$PWD/.local-data:/data" \
  -v "$PWD:/repo:ro" \
  influxbro:dev
```

Notes:

- The UI is served on `http://localhost:8099/`.
- In real HA, Ingress changes the base path; keep relative URLs (current templates do).

### Run locally (Python, outside Docker)

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

### Lint / Static checks

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

### Tests

Pytest is available (see `tests/` + `pytest.ini`). Prefer patterns that make running a single test easy:

```bash
# run one file
pytest tests/test_api_yaml_flow.py -q

# run one test by node id
pytest tests/test_api_yaml_flow.py::test_load_influx_yaml_resolves_secret -q

# run a subset by keyword
pytest -k measurements -q
```

### Manual “single test” (API smoke)

After starting the app, these are useful targeted checks:

```bash
curl -fsS http://localhost:8099/api/info | jq .
curl -fsS http://localhost:8099/api/config | jq .

# connectivity test uses the posted form values
curl -fsS -X POST http://localhost:8099/api/test \
  -H 'Content-Type: application/json' \
  -d '{"influx_version":2,"scheme":"http","host":"localhost","port":8086,"verify_ssl":true,"timeout_seconds":10,"org":"...","bucket":"...","token":"..."}' | jq .
```

## Code Style Guidelines

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

## Versioning / Releases (Home Assistant add-on)

- Bump `version:` in `influxbro/config.yaml` for any user-visible change.
- Do not change `slug:`.
- Keep `repository.yaml` in the repo root.

## Workflow Rule (Repo Convention)

- If you change add-on behavior (Python/HTML/JS/CSS, Dockerfile, run scripts, configs that affect runtime), also:
  - bump `influxbro/config.yaml:version` (so Home Assistant detects the update)
  - add an entry to `influxbro/CHANGELOG.md` for that version
  - update the user handbook `influxbro/MANUAL.md` so it reflects the current UI/behavior for that version
  - update the user handbook `influxbro/MANUAL.md` so it reflects the current UI/behavior for that version
  - verify `influxbro/CHANGELOG.md` completeness/order (the file MUST list version entries in descending order, newest version at the top)
    - The CHANGELOG.md must present versions in strict descending order (most recent first). When adding a new entry, insert it at the top under the new version heading.

## Dependency / Compatibility Rule

- If you change Python dependencies (new imports, add/remove packages, or behavior that requires a new library version), update `influxbro/requirements.txt` in the same change.
- For each released add-on version, record the Home Assistant Core version the add-on was tested with.
  - Preferred place: the corresponding entry in `influxbro/CHANGELOG.md` (e.g. a Maintenance bullet: `Tested with Home Assistant Core: 2026.3.0`).
  - If the HA version cannot be determined in the current environment, explicitly note it as `unknown` and update once you have the value.

## Logging Rule (Support)

- Ensure user-visible UI errors are also written to the add-on log file.
  - In particular: client-side/network errors like "Failed to fetch" must be reported from the browser to the backend and logged.
  - When adding new UI error messages, verify they show up in `Logs` (logfile) during failure scenarios.

## Agent Command Convention

- If the user writes `go` (or `GO`), treat that as: stage relevant changes, create a git commit with an appropriate message, and push to the tracked remote branch.

- Showing current open GitHub issues (grouped by Bugs vs Enhancements) after an implementation package is OPTIONAL and informational only.

- It MUST NOT:
  - interrupt execution
  - trigger questions
  - pause or delay further processing

- During active multi-issue execution:
  - this step MUST be skipped entirely unless explicitly requested by the user

### GO Must Complete Planned Work

- When the user issues `go`/`GO`, you MUST ensure all open/pending planned work is implemented before committing/pushing.
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
- After a successful `go` workflow (commit + push), play a macOS completion sound:
  - `afplay /System/Library/Sounds/Glass.aiff`
  - If the workflow fails, play an error sound:
    - `afplay /System/Library/Sounds/Basso.aiff`
- After the completion sound, speak a short status message via macOS `say`:
  - If the workflow produced a new add-on version (i.e., `influxbro/config.yaml` version was bumped as part of the changes), use a female voice and speak the version as a version number (not a date), e.g. `say -v Anna "Generierung erfolgt, Version 1 Punkt 11 Punkt 34 wurde erzeugt"` (version derived from `influxbro/config.yaml`)
  - If the workflow ends with pending questions/blockers: `say "Einige Punkte müssten noch beantwortet werden"`

## Completion Notifications

- After completing any user-requested execution/workflow that runs commands (independent of plan/build mode and independent of `go`), play a macOS completion sound:
  - Success: `afplay /System/Library/Sounds/Glass.aiff`
  - Failure/blocker: `afplay /System/Library/Sounds/Basso.aiff`
- After completing a unit of work where you either (a) expect an answer from the user to continue, or (b) you are fully done and ready for a new input, play a macOS completion sound:
  - Ready/awaiting input: `afplay /System/Library/Sounds/Glass.aiff`
  - Blocked/failed: `afplay /System/Library/Sounds/Basso.aiff`
- When you ask the user for confirmation/decision to continue (a blocking question), also:
  - play a completion sound: `afplay /System/Library/Sounds/Glass.aiff`
  - speak a short prompt via macOS `say` (German), e.g. `say "Bitte bestaetigen"`
- Only speak the "Generierung erfolgt..." message when a new add-on version was produced (version bump in `influxbro/config.yaml`).

## Interactive Prompts (Audio)

- If you need any input/decision from the user to continue (any question that blocks progress or requires a choice), you MUST:
  - play a sound: `afplay /System/Library/Sounds/Glass.aiff`
  - speak (German): `say "Entscheidung erforderlich"`
- If you are done implementing the requested work are ready for the next instruction, you MUST:
  - play a sound: `afplay /System/Library/Sounds/Glass.aiff`
  - speak (German): `say "Fertig mit der Umsetzung"`
