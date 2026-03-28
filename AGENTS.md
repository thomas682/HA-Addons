# 🧠 AI Efficiency, Model Strategy & Cost Optimization (CRITICAL)

## Model Strategy

### Chat Queue Handling

- Anweisungen, die im Chat erteilt werden, werden solange nicht bearbeitet, bis die laufenden Umsetzungen oder Issues beendet sind.
- Neue Eingaben werden daher zunächst in eine Queue bzw. ToDo-Liste aufgenommen.
- Wenn bereits eine Abarbeitung laeuft, unterbrechen spaetere Benutzeranweisungen diese laufende Abarbeitung NICHT automatisch.
- Jede neue Benutzeranweisung wird stattdessen in die Queue bzw. ToDo-Liste einsortiert und erst nach Abschluss der aktuell laufenden Abarbeitung der Reihe nach bearbeitet.
- Das gilt ausdruecklich auch dann, wenn:
  - waehrend einer laufenden `build`-Abarbeitung eine weitere `build`-Anweisung kommt
  - waehrend einer laufenden `build`-Abarbeitung eine neue `plan`-Anfrage kommt
  - waehrend einer laufenden `plan`-Analyse eine weitere `plan`-Anfrage kommt
  - waehrend einer laufenden `plan`-Analyse eine neue `build`-Anweisung kommt
- Eine neue `build`-Anweisung unterbricht also weder eine laufende `build`-Abarbeitung noch eine laufende `plan`-Analyse.
- Eine neue `plan`-Anfrage unterbricht also ebenfalls keine bereits laufende `build`- oder `plan`-Abarbeitung.
- Ausnahme:
  - Antworten des Benutzers auf konkrete Rueckfragen des Agenten gehoeren zur aktuell laufenden Abarbeitung und wirken sofort auf diese laufende Aufgabe.
  - Solche Rueckantworten werden NICHT als neuer Queue-Eintrag behandelt.

- 2026-03-27: Betriebsmodus `build` per Chat-Befehl `GO` aktiv. Der Agent darf Aenderungen am Arbeitsbaum vornehmen, Tests ausfuehren sowie Commits/Pushes nach `main` erstellen.

### Build-Mode Completion Rule (HARD)

- Wenn Betriebsmodus `build` aktiv ist, ist `rules/WORKFLOW.md` fuer den Abschluss jeder Umsetzung verbindlich.
- `build` bedeutet nicht nur Erlaubnis, sondern Abschluss-Pflicht.
- Eine Umsetzung darf NICHT als abgeschlossen gemeldet werden, wenn `rules/WORKFLOW.md` fuer diesen Fall verlangt, dass noch:
  - `influxbro/config.yaml` version erhoeht werden muss
  - ein Commit erstellt werden muss
  - nach `main` gepusht werden muss
- Bei Aenderungen an Runtime, UI, API oder Verhalten sind Version-Bump, Commit und Push nach `main` obligatorischer Teil des Abschlusses, sofern `rules/WORKFLOW.md` nichts Engeres vorgibt.
- Wenn QA themenfremde Altfehler zeigt, darf der Agent die verpflichtende Abschlusssequenz nicht stillschweigend auslassen.
  - Der Agent muss klar zwischen neuen fixbezogenen Fehlern und bereits bestehenden, themenfremden Fehlern unterscheiden.
  - Nur fixbezogene/blockierende Fehler duerfen Version-Bump, Commit und Push verhindern.

## Mandatory Rule Files (HARD REQUIREMENT)

- Die folgenden Regeldateien sind IMMER verpflichtend und duerfen niemals als optional behandelt werden:
  - `rules/TESTING.md`
  - `rules/ISSUES.md`
  - `rules/WORKFLOW.md`
  - `rules/CODESTYLE.md`
- Diese vier Dateien sind verbindliche Repo-Policy und muessen bei jeder Aufgabe beachtet werden.
- Es ist VERBOTEN, eine dieser Dateien als nur situative Empfehlung oder als nachrangige Zusatzinfo zu behandeln.
- Auch wenn eine Aufgabe primaer nur Analyse, Recherche, Planung, Text, QA, Commit, Push, Styling, UI, Refactoring oder Issue-Arbeit betrifft, bleiben diese vier Regeldateien verpflichtend.

### Enforcement

- Vor Analyse, Umsetzung, Test, Issue-Bearbeitung, Commit, Push oder Abschlussmeldung muessen diese vier Regeldateien als verbindlicher Regelrahmen gelten.
- Wenn eine Anweisung aus einer dieser Dateien fuer die aktuelle Aufgabe relevant ist, MUSS sie angewendet werden.
- Wenn mehrere dieser Dateien gleichzeitig Anforderungen an dieselbe Aufgabe stellen, muessen alle zusammen eingehalten werden.
- Bei Konflikten zwischen allgemeinem Standardverhalten und diesen Repo-Regeln haben diese vier Regeldateien Vorrang.
- Eine Aufgabe darf NICHT als abgeschlossen gemeldet werden, wenn eine relevante Anforderung aus diesen Regeldateien nicht eingehalten wurde.

### Default Model Strategy

- API:
  - PRIMARY: gpt-4o
  - SECONDARY: gpt-4o-mini

- Web/Auth:
  - PRIMARY: gpt-5.4
  - SECONDARY: gpt-4o

### Provider Awareness Rule

- The agent MUST always respect the active provider:

  - openai_api → use API model mapping
  - openai     → use Web/Auth model mapping

- It is FORBIDDEN to mix provider strategies.

- Model selection MUST always follow:
  1. active provider
  2. task classification

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

## Model Usage Policy (STRICT – HARD ENFORCED)

### API Models

#### gpt-4o (PRIMARY – REQUIRED for ALL technical work)

Use for:

- ANY code-related task
- reading code
- debugging
- searching files
- repository navigation
- UI/backend interaction
- test execution or validation
- reasoning about behavior
- architecture or logic decisions
- ANY task with uncertainty

→ Default model for ALL non-trivial work

#### gpt-4o-mini (SECONDARY – EXTREMELY RESTRICTED)

Use ONLY for:

- documentation text
- changelog entries

STRICT CONDITIONS:

- MUST NOT read code
- MUST NOT search files
- MUST NOT analyze logic
- MUST NOT interpret code behavior
- MUST NOT generate or modify code
- MUST NOT run or evaluate tests
- MUST NOT perform reasoning about system behavior

→ ONLY allowed for pure text output without ANY technical context

### Secondary Model Gate

- Before using a SECONDARY model, the agent MUST verify:

  - task contains NO code
  - task requires NO analysis
  - task involves NO files
  - task output is purely textual

- If ANY condition is not met:
  → MUST use PRIMARY model

### Web/Auth Models

#### gpt-5.4 (PRIMARY – REQUIRED for ALL tasks)

Use for:

- ALL tasks (technical + non-technical)
- code analysis
- debugging
- repository search
- implementation
- documentation
- reasoning

→ Default model for ALL Web/Auth usage

#### gpt-4o (SECONDARY – EXTREMELY RESTRICTED)

Use ONLY for:

- documentation text
- changelog entries

STRICT CONDITIONS:

- MUST NOT read code
- MUST NOT search files
- MUST NOT analyze logic
- MUST NOT interpret system behavior
- MUST NOT generate or modify code
- MUST NOT run or evaluate tests
- MUST NOT perform reasoning about implementation

→ ONLY allowed for pure text output without ANY technical context

## Automatic Model Switching

### Provider-aware selection

#### If provider = API:

- Technical tasks → MUST use gpt-4o
- Documentation / changelog ONLY → MAY use gpt-4o-mini

#### If provider = Web/Auth:

- ALL tasks → MUST use gpt-5.4
- ONLY if task is strictly documentation/changelog → MAY use gpt-4o

### HARD CONDITION

- If ANY code, file, logic, or uncertainty is involved:
  → MUST use PRIMARY model

### Escalation rules

Escalate ONLY if:

- multi-file architecture changes
- repeated failures (>2 attempts)
- complex debugging (concurrency, SQL, parsing, security)
- unclear solution space
- insufficient exploration detected (too few files searched or early termination)

### De-escalation

After a successful solution:

- API:
  - gpt-4o-mini ONLY for documentation/changelog
  - otherwise ALWAYS gpt-4o

- Web/Auth:
  - gpt-4o ONLY for documentation/changelog
  - otherwise ALWAYS gpt-5.4

## Token Efficiency Guard

- Prefer fewer high-quality requests over many small ones
- Avoid repeated retries with the same model
- If 2 attempts fail → escalate model immediately

## Automatic Escalation (ERROR-DRIVEN)

### Purpose

Ensure robust behavior in API mode by automatically escalating the model when weak or incomplete results are detected.

### Escalation triggers

Escalate to the PRIMARY model of the current provider:

- API: gpt-4o
- Web/Auth: gpt-5.4

if ANY of the following occurs:

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

1. Immediately switch to the PRIMARY model of the current provider:
   - API: gpt-4o
   - Web/Auth: gpt-5.4
2. Restart analysis with:
   - broader search scope
   - multiple search passes
   - inclusion of all file types
3. Do NOT reuse previous incomplete conclusions
4. Re-evaluate the problem from scratch if necessary

### De-escalation

- After a successful solution:
  - return to task-based model selection

- Secondary models may ONLY be used if the next task is strictly:
  - documentation
  - changelog

- Otherwise:
  → MUST remain on PRIMARY model

### HARD RULE (NON-NEGOTIABLE)

- Secondary models (gpt-4o-mini, gpt-4o) are STRICTLY limited to documentation and changelog.

- It is FORBIDDEN to use secondary models if:
  - code is visible
  - files are accessed
  - system behavior is analyzed
  - correctness depends on logic

- If ANY technical context is present:
  → MUST use PRIMARY model

- If there is ANY doubt:
  → ALWAYS use PRIMARY model

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
