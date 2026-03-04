# AGENTS.md

This repository contains a Home Assistant add-on (Ingress UI) for browsing/cleaning InfluxDB data.

No Cursor/Copilot instruction files were found at:
- `.cursor/rules/`
- `.cursorrules`
- `.github/copilot-instructions.md`

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

## Agent Command Convention

- If the user writes `go` (or `GO`), treat that as: stage relevant changes, create a git commit with an appropriate message, and push to the tracked remote branch.
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
- Only speak the "Generierung erfolgt..." message when a new add-on version was produced (version bump in `influxbro/config.yaml`).
