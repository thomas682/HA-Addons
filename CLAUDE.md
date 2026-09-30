# CLAUDE.md

Claude Code liest beim Start ausschliesslich diese Datei, nicht `AGENTS.md`.
Der folgende Import holt die Projektregeln nach; alles Verbindliche steht dort
und gilt fuer Claude Code und opencode gleichermassen.

@AGENTS.md

## Die eine Regel, die vor allem anderen kommt

**Issue vor Umsetzung.** Jede umsetzbare Aufgabe aus dem Chat wird vor der
ersten Dateiaenderung als GitHub-Issue in diesem Repository erfasst, mit dem
vollstaendigen Aufgabentext unter `## Vorgaben Chat` in Originalsprache und
chronologischer Reihenfolge. Eine reine Auskunft ohne Dateiaenderung braucht
kein Issue.

Sie steht hier doppelt, weil sie greifen muss, bevor das erste Werkzeug laeuft.
Die uebrigen harten Regeln -- `VERSION` erhoehen, keine Secrets, vor dem Commit
`./scripts/run-local-checks.sh` -- stehen in `AGENTS.md`.
