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
