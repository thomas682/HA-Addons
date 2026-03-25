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

- If any required check fails:

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

docker run --rm -p 8099:8099   -v "$PWD/.local-data:/data"   -v "$PWD:/repo:ro"   influxbro:dev
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
curl -fsS -X POST http://localhost:8099/api/test   -H 'Content-Type: application/json'   -d '{"influx_version":2,"scheme":"http","host":"localhost","port":8086,"verify_ssl":true,"timeout_seconds":10,"org":"...","bucket":"...","token":"..."}' | jq .
```
