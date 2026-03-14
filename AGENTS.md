# AGENTS.md

This repository contains a Home Assistant add-on (Ingress UI) for browsing/cleaning InfluxDB data.

UI design standard
- Before adding/changing any GUI element (tables, buttons, checkboxes, selects, etc.), consult `influxbro/Template.md`.
- Keep pages aligned with the master table template (toolbar above table, column resize, auto-fit/window-fit, wrap toggle, per-column filters, height resize, info icon).

New Requests: Issue or Immediate Implementation
- When the user asks for new requirements/bugs/changes, ask first whether the item should be recorded as a GitHub Issue (to be implemented later via the issue backlog) or implemented immediately.
- Only start implementation after the user chooses one of these two paths.

Questions: Numeric Choices
- If you need user input and the answer is a selection (A/B, yes/no, option set), write the question so the user can reply with a single number.
  - Example: "Soll ich (1) das speichern oder (2) nicht speichern? Antworte nur mit 1 oder 2." 

GitHub Issues: Language
- When creating GitHub Issues for the user, write the title and body in German.

No Cursor/Copilot instruction files were found at:
- `.cursor/rules/`
- `.cursorrules`
- `.github/copilot-instructions.md`

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

## End-of-Implementation Verification (Required)

- At the end of every implementation, explicitly verify that all requirements and all ToDo items were actually implemented.
- If any planned item could not be implemented (or remains only partially implemented), explicitly call it out with:
  - what is missing
  - why it is missing
  - what would be needed to complete it
- Perform a final checklist-style confirmation before declaring the work finished.

### Requirements Tracking (preferred: GitHub Issues)

- Track requirements primarily as GitHub Issues so others can create/report items externally.
- Use the issue templates to distinguish between:
  - Bug reports (not working): label with `type/bug`
  - Enhancements (feature requests): label with `type/enhancement`
- Use exactly one status label per issue: `status/open`, `status/in_progress`, `status/done`, `status/cancelled`.
- Ensure the label set exists in GitHub (create once in the GitHub UI); the issue templates assume these labels are available.
- When implementing, link PRs to issues and close them via `Fixes #<id>`.

#### GitHub Issues: Check, Select, Sync

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
- Reflect the user's decision back to GitHub:
  - implement now: set `status/in_progress` and (optionally) add a short comment "picked for implementation"
  - defer: keep `status/open` and add a short comment "deferred"
  - decline: set `status/cancelled`, add a short comment with reason (if provided), and close the issue
- When implementation is finished:
  - set `status/done`
  - add a comment with the PR URL and/or commit hash
  - close the issue
- Sync selected issues into the local open-points list:
  - add chosen "implement now" issues to the in-chat ToDo list and to `./.opencode/plan_state.md` (with `#<id>` + title)
  - when the issue is completed/declined/deferred, update `./.opencode/plan_state.md` accordingly

#### GitHub Issues: Proactive Prompting

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
  - verify `influxbro/CHANGELOG.md` completeness/order (new version present at top; headings in descending order)

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

- After each implementation package is committed (and pushed, if applicable), show the user the current open GitHub issues (grouped by Bugs vs Enhancements) so they can immediately see what remains.

### GO Must Complete Planned Work

- When the user issues `go`/`GO`, you MUST ensure all open/pending planned work is implemented before committing/pushing.
- "Planned work" includes both:
  - the current request's ToDo list (in-chat)
  - any remaining open items recorded in `./.opencode/plan_state.md` (if the file exists)
- If implementing everything in one batch is not sensible (too risky/too large), you MUST:
  - explicitly state you are splitting into multiple smaller packages,
  - commit/push only the first package,
  - and immediately list the remaining planned items still pending.
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
- If you are done implementing the requested work and are ready for the next instruction, you MUST:
  - play a sound: `afplay /System/Library/Sounds/Glass.aiff`
  - speak (German): `say "Fertig mit der Umsetzung"`
