# projekt-agents.md

# AGENTS - InfluxBro

Sprache: Deutsch. Repository: `influxbro`. Typ: Home Assistant Add-on.

## Globale Regeln

- Die projektuebergreifenden Agent-Regeln in `/Users/thomasschatz/git/global/global-agents.md` sind verbindlich zu lesen und zu beachten.
- Projektspezifische Regeln in dieser Datei ergaenzen oder verschaerfen die globalen Regeln, duerfen sie aber nicht abschwaechen.
- `/Users/thomasschatz/git/global/global-registry-workflow.md` ist fuer Docker-/Registry-/Portainer-/Deployment-Arbeiten zwingend vorher zu lesen und zu beachten.

## Global Rule Drift

- Der zuletzt gepruefte globale Regelstand wird in `docs/rules/global-rule-baseline.json` dokumentiert.
- Vor nicht-trivialen Arbeiten den Drift-Status mit `python3 /Users/thomasschatz/git/global/scripts/check-global-rule-drift.py /Users/thomasschatz/git/ha-addons` pruefen.
- Wenn der Baseline-Marker fehlt oder Drift meldet, muss ein Global-Rule-Audit angeboten werden, bevor bestehende Projektlogik an neue globale Regeln angepasst wird.
- `docs/rules/global-rule-baseline.json` wird erst nach abgeschlossenem Audit bzw. bewusster Pruefung mit `--write-baseline` aktualisiert.

## Repository-Pruefung

- Vor der ersten Umsetzung pruefen, ob der Repository-Root `influxbro/`, `AGENTS.md` und `repository.yaml` enthaelt; bei falschem Root stoppen und melden.
- `repository.yaml` muss im Repo-Root bleiben.
- `influxbro/` darf nicht umbenannt werden und der `slug` in `influxbro/config.yaml` darf nicht geaendert werden.

## Projektstruktur

- `influxbro/config.yaml`: Add-on-Metadaten, Versionierung, Slug, Ingress-Einstellungen.
- `influxbro/Dockerfile`: Container-Build.
- `influxbro/run.sh`: Add-on-Einstiegspunkt, liest `/data/options.json`.
- `influxbro/app/app.py`: Flask-App.
- `influxbro/app/templates/*.html`: UI-Templates mit Inline-JS/CSS.
- `influxbro/requirements.txt`: Python-Abhaengigkeiten.
- `influxbro/CHANGELOG.md`: Add-on-Changelog.
- `influxbro/MANUAL.md`: Nutzerhandbuch.
- `influxbro/projekt-template.md` und `influxbro/projekt-template-projekt-*-rules.md`: verbindliche UI-/Template-Spezialregeln.

## Add-on-Invarianten

- Home Assistant erkennt Updates ueber das `version:`-Feld in `influxbro/config.yaml`.
- Container erwartet HA-Mounts: `/data` beschreibbar/persistent, `/config` nur lesbar in diesem Add-on.
- Loeschfunktionen muessen Opt-in bleiben: durch `ALLOW_DELETE` abgesichert und mit exakter Bestaetigungsphrase.
- InfluxDB-v2-Clients kontextverwaltet und geschlossen verwenden (`with v2_client(cfg): ...`).
- Timeouts und SSL-Verifikation bei v1-Client konfigurierbar halten.
- Abfragegroesse begrenzt halten; UI downsampled auf etwa 5000 Punkte.
- Keine Geheimnisse, Token, Passwoerter oder internen URLs loggen, zurueckgeben oder in UI/API ausgeben.

## Issue- und Abschlussworkflow

- GitHub-Issues werden nicht automatisch geprueft, geladen oder gestartet; nur auf explizite Nutzeranweisung wie `pruefe Issues` oder `offene Issues abarbeiten`.
- `rememberme`-Issues sind bei jeder Pruefung, Triage oder Sammelumsetzung strikt zu ueberspringen, sofern der Nutzer nicht genau dieses Issue nennt.
- Neue GitHub-Issues duerfen nur angelegt, gestartet oder bearbeitet werden, wenn das aktuell aktive Issue vollstaendig abgeschlossen oder explizit vom Nutzer zurueckgestellt wurde.
- Genau ein Status-Label pro Issue ist aktiv: `status/open`, `status/in_progress`, `status/done` oder `status/cancelled`; vorherige Status-Labels entfernen.
- Ein aktives Issue gilt erst als erledigt, wenn Umsetzung, relevante QA, Sicherheitspruefung falls erforderlich, Version/Changelog/Manual falls erforderlich, Commit, Push, Live-Update falls erforderlich, Issue-Kommentar, `status/done`, Issue-Schluss und Abschlussbericht erledigt oder explizit blockiert sind.
- Fuer GitHub-Issue-Kommentare mit Backticks, Dollarzeichen, URLs, Dateipfaden oder Befehlen immer eine Body-Datei oder heredoc-artige Eingabe verwenden, keine fragile Inline-Quote.

## Versionierung und Release

- Jede Aenderung an app-relevanter Laufzeit-, UI-, API- oder Verhaltenslogik erzwingt eine neue Version in `influxbro/config.yaml`.
- App-relevante Dateitypen sind insbesondere `*.py`, `*.html`, `*.js`, `*.css`, Dockerfile, Shell-/Startskripte und Laufzeit-Konfigurationen.
- Nicht app-relevante Regel-, Plan-, Arbeits- oder reine Doku-Dateien ausserhalb des Add-ons erzwingen keinen Add-on-Versionsbump, sofern sie Laufzeitverhalten, UI, API, Container, Startverhalten, Konfiguration oder Abhaengigkeiten nicht beeinflussen.
- Bei Versionsbump `influxbro/CHANGELOG.md` aktualisieren, neueste Version oben.
- Bei UI- oder Verhaltensaenderungen `influxbro/MANUAL.md` aktualisieren.
- Pro veroeffentlichter Add-on-Version die getestete Home Assistant Core-Version in `influxbro/CHANGELOG.md` dokumentieren, wenn sie ermittelt werden kann.
- Nach freigegebenen app-relevanten Aenderungen gehoeren Commit und Push nach `main` zum Abschluss, sofern QA und Sicherheitsregeln nicht blockieren.
- Force-Push ist verboten.

## Home Assistant Live-Update

- Wenn `influxbro/config.yaml` eine neue Add-on-Version erhalten hat, nach erfolgreichem Push nach `main` Home Assistant auf diese Version aktualisieren oder den Blocker klar melden.
- Erwartete Version aus `influxbro/config.yaml` bestimmen und Live-Version ueber `GET http://192.168.2.200:8099/api/info` pruefen.
- Bevorzugter Updatepfad ist die Home-Assistant-Core-API: `homeassistant/update_entity` fuer `update.influxbro_update`, danach `update/install` und Polling bis `/api/info` die erwartete Version liefert.
- Nur wenn der HA-Core-API-Updatepfad technisch nicht nutzbar ist, darf der bestehende Playwright-Fallback `tests/e2e/ha-live-update-influxbro.spec.js` verwendet werden.
- Die Live-Version muss exakt der erwarteten Version entsprechen; Abweichung ist ein Blocker.
- Lokale Audio-/Sprachausgaben fuer Abschluss, Version, Blocker oder Entscheidungen duerfen nur lokal auf dem Agent-Rechner erfolgen, z. B. `say` oder `afplay`; Home Assistant, Alexa, `notify.*`, `tts.*` oder `browser_mod.notification` sind dafuer verboten.

## Pflicht-Sicherheitspruefung

- Bei jeder Aenderung an einem Home Assistant Add-on vor Fertigstellung delta-orientiert Sicherheitspruefung durchfuehren.
- Mindestbereich je nach Relevanz: `influxbro/config.yaml`, `influxbro/Dockerfile`, `influxbro/run.sh`, Backend-API-Routen, Request-Handler, HTML/Templates/Frontend-JavaScript, Dateioperationen, Logging und Abhaengigkeitsdateien.
- Pruefen auf hartcodierte Geheimnisse, Secret-Leaks in Logs/API/UI, fehlende Eingabevalidierung, Command Injection, Path Traversal, XSS/DOM-Injection, CSRF-relevante Schreib-/Loeschaktionen, SSRF, unsichere Import-/Export-/Backup-/Restore-Pfade, fehlende Auth/Autorisierung, gefaehrliche Defaults, zu weitreichende Container-Rechte und Informationslecks.
- Add-on-Rechte nach Least Privilege pruefen: `host_network`, `privileged`, `full_access`, `homeassistant_api`, `ingress`, `ports`, Host-Mounts, Docker-Socket und Geraetezugriffe.
- Befunde konkret dokumentieren: Schweregrad, Datei/Bereich, Risiko, realistisches Szenario, konkrete Behebung.
- Sicher und eindeutig behebbare Sicherheitsprobleme minimal und nachvollziehbar direkt beheben.

## Pflicht-QA

- Wenn ausschliesslich nicht app-relevante Regel- oder Dokumentationsdateien geaendert werden, entfallen App-QA, Syntaxpruefung, Docker-Verifikation, UI-Verifikation und Live-Tests; Plausibilitaetspruefung genuegt und ist im Abschluss zu nennen.
- Standard-Syntaxpruefung fuer App-Code:

```sh
python -m py_compile influxbro/app/app.py
```

- Basispruefungen:

```sh
python -m compileall influxbro/app/app.py
python -m py_compile influxbro/app/app.py
```

- Gezielte Tests, wenn relevant/vorhanden:

```sh
pytest tests/test_api_yaml_flow.py -q
pytest tests/test_api_yaml_flow.py::test_load_influx_yaml_resolves_secret -q
pytest -k measurements -q
```

- Laufzeit-/API-Smoke-Tests sind Pflicht, wenn Backend-Routen, Request-Handling, Config-Loading oder UI-ausgeloeste API-Aktionen betroffen sind.
- Docker-Verifikation ist Pflicht, wenn Laufzeitverhalten, Abhaengigkeiten, Container-Verhalten, Startskripte, Add-on-Paketierung oder Konfigurationsverarbeitung betroffen sind.
- UI-Verifikation ist Pflicht, wenn Templates, JavaScript oder Browser-Interaktionen betroffen sind.
- Fehlgeschlagene Pflichtpruefungen blockieren den Abschluss, bis sie behoben oder als nicht zusammenhaengender Altfehler begruendet sind.

## Live- und Playwright-Tests

- Standard-Testhost fuer HA-gestuetzte Live-Integrationstests ist `http://192.168.2.200:8099`.
- Fuer Live-UI- und Playwright-Tests darf der Browser das Live-Add-on nicht direkt ueber `192.168.2.200:8099` ansteuern; stattdessen lokalen HTTP-Proxy `127.0.0.1:8099 -> http://192.168.2.200:8099` verwenden.
- Playwright-Konfiguration: `playwright.config.js`, Tests unter `tests/e2e/*.spec.js`, mit `HA_URL=http://127.0.0.1:8099 npx playwright test ...`.
- Live-Tests nur gegen die erwartete Version ausfuehren; wenn `/api/info` nicht zur erwarteten Version passt, zuerst aktualisieren oder Blocker melden.
- Ein Dienst gilt erst als bereit, wenn ein Health-/API-Endpunkt erfolgreich antwortet und gueltiges JSON liefert; Port-Listening allein reicht nicht.

## Lokale Starts und Smokes

- Docker lokal:

```sh
mkdir -p .local-data
docker run --rm -p 8099:8099 -v "$PWD/.local-data:/data" -v "$PWD:/repo:ro" influxbro:dev
```

- Python lokal ohne Docker:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install flask influxdb-client influxdb PyYAML
export ALLOW_DELETE=false
export DELETE_CONFIRM_PHRASE=DELETE
export ADDON_VERSION=dev
python influxbro/app/app.py
```

- Manuelle API-Smokes:

```sh
curl -fsS http://localhost:8099/api/info | jq .
curl -fsS http://localhost:8099/api/config | jq .
```

## UI- und Template-Regeln

- Allgemeine Template-, Ingress- und JavaScript-Grundregeln fuer Handbuch-/Dokumentationsspruenge stehen in `influxbro/projekt-template-handbuch-rules.md` und sind vor entsprechenden Aenderungen zu lesen.
- Vor dem Hinzufuegen oder Aendern von GUI-Elementen `influxbro/projekt-template.md` lesen und beachten.
- Je nach GUI-Umbau zusaetzlich passende Spezialregeln lesen: `influxbro/projekt-template-projekt-dialog-rules.md`, `influxbro/projekt-template-tooltips-rules.md`, `influxbro/projekt-template-measurement-select-rules.md`, `influxbro/projekt-template-section-rules.md`, `influxbro/projekt-template-picker-rules.md`, `influxbro/projekt-template-tables-rules.md`, `influxbro/projekt-template-handbuch-rules.md`.
- Konsistente Layout-Muster, Spacing, Card-/Layout-Struktur, Klassen und IDs ueber alle UI-Komponenten hinweg einhalten.
- UI-Komponenten auf Container-Ebene und fuer alle Kind-Elemente validieren.
- Jedes sichtbare, support-relevante UI-Element muss stabile `data-ui`-Kennung und eindeutige `data-ib-pickkey`-Kennung besitzen.
- Funktionaler globaler Zustand und profilbasierter UI-Zustand muessen technisch getrennt bleiben; Browser-lokaler UI-Zustand darf serverseitigen funktionalen Zustand nicht ueberschreiben.
- Beim Entfernen, Ersetzen oder Stilllegen von UI-Elementen, Templates, Buttons, Tabellen, Dialogen, Frontend-Aktionen, API-gebundenen UI-Funktionen oder Routen den Tombstone-Prozess anwenden: Abhaengigkeiten pruefen, `.tombstones.yml` ergaenzen, Migrations-/Ersatzpfad dokumentieren und Abschlussbericht erweitern.

## Code-Stil

- Python: 4 Leerzeichen, F-Strings fuer Formatierung, moeglichst kurze Zeilen, Imports gruppieren in Standardbibliothek, Drittanbieter, lokale Imports; ein Import pro Zeile.
- Type-Hints fuer neue oder geaenderte Funktionen hinzufuegen.
- Fuer JSON-aehnliche Payloads `dict[str, Any]` verwenden und an Grenzen validieren/normalisieren.
- Flask-Routen als Vertrauensgrenzen behandeln: Parameter validieren, Typen normalisieren, klare Fehler mit passenden HTTP-Status-Codes zurueckgeben.
- Einheitliches JSON-Envelope verwenden: Erfolg `{"ok": true, ...}`, Fehler `{"ok": false, "error": "..."}`.
- Keine breiten `except Exception` in reinen Hilfsfunktionen; an HTTP-Grenzen nur bewusst und mit nuetzlichen Fehlermeldungen.
- Werden Python-Abhaengigkeiten geaendert, `influxbro/requirements.txt` in derselben Aenderung aktualisieren.
