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
