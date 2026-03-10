# Requests Log

This file tracks user-entered requirements/requests as written, with date and implementation status.

Status values: `open`, `in_progress`, `done`, `cancelled`.

| Date | Requirement (as written) | Status | Notes |
| --- | --- | --- | --- |
| 2026-03-10 | "Pruefe ob noch irgendwelche alten Planaenderungen offen sind" | done | Checked git state; no stashes; one old local branch `beta/plotly`; `gh` not installed so PR list not checked. |
| 2026-03-10 | "Ergaenze in der Agents.md: Merke dir die Planaenderungen die anstehen so, dass selbst bei einem Neustart von VSCode oder Codeserver diese noch zur Verfuegungs tehen" | done | Implemented in `AGENTS.md`, plus `.gitignore` ignores `.opencode/` (commit `bfac01f`). |
| 2026-03-10 | "zusaetzlich: erzeuge eine Daten mit den Anforderungen die ich hier eingebe inkl. Datum und der Information ob Du diese umgesetzt hast. auch diese Datei commiten" | done | Implemented by adding committed `REQUESTS_LOG.md`. |
| 2026-03-10 | "Speichere diese Anforderungn auch in Agents.md" | done | Implemented by adding `AGENTS.md` rules to maintain `REQUESTS_LOG.md`. |
