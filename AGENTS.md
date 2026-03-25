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

## External Rule Files

- Detailed rules are split across:
  - `rules/TESTING.md`
  - `rules/ISSUES.md`
  - `rules/WORKFLOW.md`
  - `rules/CODESTYLE.md`

- Do NOT automatically load all rule files.
- Only load the rule file(s) directly relevant to the current task.
