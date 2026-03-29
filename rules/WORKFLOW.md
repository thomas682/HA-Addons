
# Workflow Regeln

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

### Completion Gate (NO SILENT STOP)

- The agent MUST treat the following sequence as mandatory end-of-task behavior for implementation work in build/GO mode:
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

### Final Checklist (REQUIRED BEFORE REPORTING DONE)

- Before declaring implementation complete, explicitly verify:
  - implementation finished
  - required QA executed
  - QA result classified
  - `influxbro/config.yaml` version bumped if required
  - changes staged
  - commit created
  - push to `main` completed
- If any item is missing, the task is NOT complete.

### Version Bump (CRITICAL FOR HA)

- Every change that affects runtime, UI, API, or behavior MUST:
  - increment `version` in `influxbro/config.yaml`

- Without version bump:
  - Home Assistant will NOT detect an update

- Version format:
  - increment last digit (e.g. 1.12.44 → 1.12.45)

### Live Verification Gate (CRITICAL FOR HA)

- Before any live verification against Home Assistant / the running add-on instance, the required code changes MUST already be available as an add-on version on `main`.
- Therefore, before a live check against the HA instance, the agent MUST first:
  - stage changes
  - create commit
  - bump `influxbro/config.yaml` version if runtime/UI/API/behavior changed
  - push to `main`
- The agent MUST NOT rely on local-only uncommitted changes for HA live verification.
- If the live instance still runs an older version, the agent must explicitly state that the requested live verification cannot validate the new code until the updated add-on version is installed in Home Assistant.

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

- Pre-existing or unrelated failing tests do NOT automatically count as blocking errors.
  - The agent MUST explicitly state why they are unrelated.
  - If the implemented change passed its relevant QA, the mandatory version-bump/commit/push flow still applies.

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
