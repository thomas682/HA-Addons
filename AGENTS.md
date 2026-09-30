# AGENTS.md — HA-Addons by Thomas

Diese Datei ist die Regelquelle dieses Repositories. opencode liest sie direkt,
Claude Code ueber den Import in `CLAUDE.md`. Was hier steht, gilt fuer beide.

| Werkzeug | liest automatisch | zusaetzlich |
|---|---|---|
| opencode | `AGENTS.md` (Projektroot, aufwaerts traversiert) | `instructions` in `opencode.json` |
| Claude Code | `CLAUDE.md` | `@AGENTS.md` als Import darin |

## Harte Regeln

Diese vier gelten in jeder Sitzung, ohne Rueckfrage und ohne fachliche Ausnahme.
Sie stehen vollstaendig hier, damit sie nicht erst in einer anderen Datei
nachgelesen werden muessen.

1. **Issue vor Umsetzung.** Jede umsetzbare Aufgabe aus dem Chat wird vor der
   ersten Dateiaenderung als GitHub-Issue in diesem Repository erfasst, mit dem
   vollstaendigen Aufgabentext unter `## Vorgaben Chat` in Originalsprache und
   chronologischer Reihenfolge. Eine reine Auskunft ohne Dateiaenderung braucht
   kein Issue. Der Abschlusskommentar endet mit der ausgelieferten Version.
2. **VERSION erhoehen.** Jede Aenderung an Quellcode, Skripten,
   Laufzeitkonfiguration oder produktiver Logik erhoeht im selben Arbeitsblock
   die Datei `VERSION` nach dem Schema `YYYY.MM.NNN`. Ausnahmslos.
3. **Keine Secrets im Repository.** Keine Passwoerter, Tokens, privaten
   Schluessel, Exporte oder produktiven Konfigurationen committen. Benoetigte
   Werte kommen ausschliesslich ueber den freigegebenen Reader
   `/Users/thomasschatz/git/global/scripts/secrets-get.sh`, der keinen Modus
   hat, der etwas auf die Ausgabe schreibt. Beim Beschreiben von Ablaeufen nur
   die Art des Secrets nennen, nie den Wert.
4. **Vor jedem Commit pruefen.** `./scripts/run-local-checks.sh` ausfuehren und
   gruen sehen. Ein fehlendes Werkzeug ist ein Abbruch, kein uebersprungener
   Schritt.

## Projekt

- Name: HA-Addons by Thomas
- Zweck: Home-Assistant-Add-on-Repository (HA-Supervisor-Store-Format). Aktuell
  ein Add-on: InfluxBro, eine Flask-Anwendung zur Verwaltung/Analyse einer
  InfluxDB-Instanz unter `influxbro/`.
- Repository: https://github.com/thomas682/HA-Addons
- Root: `/Users/thomasschatz/git/ha-addons`
- Status: Produktiv, HA-Add-on mit lokalem QA-, Playwright- und
  Live-Update-Workflow gegen eine laufende Home-Assistant-Instanz.
- Verantwortlich: Thomas Schatz
- Sprache fuer Nutzerkommunikation: Deutsch, sofern der Nutzer nichts anderes verlangt.

## Befehle

```sh
./scripts/run-local-checks.sh
python3 -m compileall influxbro/app/app.py
python3 -m py_compile influxbro/app/app.py
pytest tests/test_api_yaml_flow.py -q
HA_URL=http://127.0.0.1:8099 npx playwright test tests/e2e/*.spec.js
./scripts/backup-agents.sh
```

- `scripts/run-local-checks.sh` ist das verbindliche Pre-Commit-Gate: prueft
  `scripts/validate_function_docs.py` und `tests/test_function_docs_validator.py`.
  Es ersetzt nicht die weiteren Pflicht-QA-Schritte unten.
- `scripts/backup-agents.sh` erzeugt bei Bedarf eine rein lokale
  Vergleichssicherung, wenn `AGENTS.md` geaendert wurde; sie wird nicht
  automatisch committet.
- Welche der App-, Docker-, UI- und Live-Pruefungen zusaetzlich Pflicht sind,
  regelt "Pflicht-QA" unten.
- Fehlt ein Befehl, zuerst in `docs/local-checks.md`, `package.json` oder
  `influxbro/README.md` nachsehen.
- Reine Dokumentations- oder Regelaenderungen brauchen mindestens
  Plausibilitaetspruefung, Diff-Review und Secret-Check.
- Eine nicht moegliche oder nicht sinnvolle Pruefung im Abschluss benennen und
  begruenden, statt sie stillschweigend zu lassen.

## Struktur

- `AGENTS.md`: diese Datei, von opencode direkt gelesen.
- `CLAUDE.md`: Startpunkt fuer Claude Code, importiert diese Datei.
- `repository.yaml`: HA-Add-on-Store-Metadaten (Name, URL, Maintainer). Muss im
  Repository-Root bleiben.
- `VERSION`: kanonische Root-Versionsquelle (`YYYY.MM.NNN`), unabhaengig vom
  `version:`-Feld in `influxbro/config.yaml`.
- `influxbro/`: das Add-on selbst — `config.yaml` (Add-on-Metadaten, Slug,
  Versionierung, Ingress), `Dockerfile`, `run.sh`, `app/app.py`,
  `app/templates/*.html`, `requirements.txt`, `CHANGELOG.md`, `MANUAL.md`,
  `TECHNICAL.md`, `README.md`, `UI_ELEMENT_DOCS.md`, `caching.md`,
  `projekt-template*.md` (UI-Spezialregeln).
- `docs/`: `functions.yaml`, `function-reviews.json`, `handbuch.md`,
  `local-checks.md`, `audit-evidence.json`, `ui-id-map.json`,
  `rules/global-rule-baseline.json`.
- `scripts/`: `run-local-checks.sh` (Pflicht-Gate), `backup-agents.sh`,
  `validate_function_docs.py`.
- `.githooks/pre-commit`, `.githooks/pre-push`: erzwingen lokal einen
  Versionsbump in `influxbro/config.yaml` bei Code-Aenderungen. Aktivierung:
  `git config core.hooksPath .githooks`.
- `.pre-commit-config.yaml`: Pre-Commit-Framework-Konfiguration fuer denselben
  Versionsbump-Hook.
- `.tombstones.yml`: Protokoll fuer entfernte/ersetzte UI- und API-Elemente.
- `tests/`: pytest-Suite (`tests/test_api_*.py`, `tests/test_changeblock_*.py`,
  `tests/conftest.py`, ...) und Playwright-E2E unter `tests/e2e/*.spec.js`.
- `playwright.config.js`, `tui.json`: Playwright- und lokale
  Tooling-Konfiguration.
- `.opencode/plugins/opencode-local-todos-sidebar/`: lokales opencode-Plugin.
- `GO_*.md`: operative Kommandodateien, siehe "Issue-Workflow".
- `saveFiles/`, `savefiles/`: lokale Snapshots frueherer `AGENTS.md`-Vergleiche
  (aus `scripts/backup-agents.sh`); keine Regelquelle.
- `.agents.md`: historische, eigenstaendige Datei mit der
  API-Dokumentationspflicht (Issue #324). Ihr Inhalt ist jetzt vollstaendig
  unter "Projektregeln > API-Dokumentationspflicht" uebernommen; die Datei
  selbst bleibt unveraendert bestehen (siehe Abschlussbericht).
- `.local-config/`, `.local-data/`: lokale, nicht versionsrelevante
  Laufzeitdaten fuer Add-on-Tests, git-ignoriert bis auf Beispieldateien.

## Projektregeln

Diese Regeln sind aus der Arbeit an diesem Projekt entstanden und gelten
weiterhin. Sie verschaerfen die globalen Regeln, schwaechen sie nicht ab.

### Repository-Pruefung

- Vor der ersten Umsetzung pruefen, ob der Repository-Root `influxbro/`,
  `AGENTS.md` und `repository.yaml` enthaelt; bei falschem Root stoppen und
  melden.
- `repository.yaml` muss im Repo-Root bleiben.
- `influxbro/` darf nicht umbenannt werden und der `slug` in
  `influxbro/config.yaml` darf nicht geaendert werden.

### Add-on-Invarianten

- Home Assistant erkennt Updates ueber das `version:`-Feld in
  `influxbro/config.yaml`.
- Container erwartet HA-Mounts: `/data` beschreibbar/persistent, `/config` nur
  lesbar in diesem Add-on.
- Loeschfunktionen muessen Opt-in bleiben: durch `ALLOW_DELETE` abgesichert und
  mit exakter Bestaetigungsphrase.
- InfluxDB-v2-Clients kontextverwaltet und geschlossen verwenden
  (`with v2_client(cfg): ...`).
- Timeouts und SSL-Verifikation bei v1-Client konfigurierbar halten.
- Abfragegroesse begrenzt halten; UI downsampled auf etwa 5000 Punkte.
- Keine Geheimnisse, Token, Passwoerter oder internen URLs loggen,
  zurueckgeben oder in UI/API ausgeben.

### API-Dokumentationspflicht

- Jeder neue oder geaenderte API-Endpunkt muss sofort und vollstaendig
  dokumentiert werden (Herkunft: `.agents.md`, Issue #324). Das gilt bei neuen
  Endpunkten, geaenderten Request-/Response-Formen oder Fehlern, entfernten
  Endpunkten (Doku-Eintrag entfernen oder als deprecated markieren) sowie
  Aenderungen an URL, HTTP-Methode, Fehlercodes, Timeouts oder
  Performance-Eigenschaften.
- Zu aktualisieren ist die `API_DOCS`-Datenstruktur, die die UI nutzt, mit den
  Pflichtfeldern: `id`, `method`, `path`, `summary`, `description`, `group`,
  `tags`, `role`/`roleLabel`/`roleColor`, `authRequired`, `request`
  (Content-Type, Schema/Keys, Beispiel), `response` (Content-Type, Schema,
  Beispiel, Statuscodes), `timing` (`typicalMs`/`p95Ms`/`timeoutMs`/
  `bottleneck`), `correlations` (`dependsOn`/`triggers`/`parallelWith`/
  `usedIn`/`criticalPath`/`phase`), `errors` (Symptom/Ursache/Fix, oder
  Abschnitt weglassen falls keine), `examples` (curl/JavaScript/Python,
  copy-paste-fertig) und `notes`.
- Keine Platzhalter (`TODO`, `...`, `TBD`). Beispiele nutzen die echte
  Server-Basis-URL und reale Home-Assistant-`entity_id`s. `summary` muss fuer
  Nicht-Programmierer verstaendlich sein, `description` technisch praezise.
- Endpunkt-Aenderungen und ihre Dokumentation gehoeren in denselben
  Commit/PR. Ein ohne vollstaendige Dokumentation gemergter Endpunkt gilt als
  Bug und ist sofort zu beheben.

### Issue- und Abschlussworkflow

- `rememberme`-Issues sind bei jeder Pruefung, Triage oder Sammelumsetzung
  strikt zu ueberspringen, sofern der Nutzer nicht genau dieses Issue nennt.
- Neue GitHub-Issues duerfen fuer jede neue umsetzbare Chat-Aufgabe angelegt
  werden; bestehende aktive Issues bleiben bis zum Abschluss oder Blocker im
  Arbeitskontext.
- Genau ein Status-Label pro Issue ist aktiv: `status/open`,
  `status/in_progress`, `status/done` oder `status/cancelled`; vorherige
  Status-Labels entfernen.
- Ein aktives Issue gilt erst als erledigt, wenn Umsetzung, relevante QA,
  Sicherheitspruefung falls erforderlich, Version/Changelog/Manual falls
  erforderlich, Commit, Push, Live-Update falls erforderlich,
  Issue-Kommentar, `status/done`, Issue-Schluss und Abschlussbericht erledigt
  oder explizit blockiert sind.
- Fuer GitHub-Issue-Kommentare mit Backticks, Dollarzeichen, URLs,
  Dateipfaden oder Befehlen immer eine Body-Datei oder heredoc-artige
  Eingabe verwenden, keine fragile Inline-Quote.

### Versionierung und Release

- Jede Aenderung an app-relevanter Laufzeit-, UI-, API- oder Verhaltenslogik
  erzwingt zusaetzlich zur Root-`VERSION` (harte Regel 2) eine neue Version in
  `influxbro/config.yaml`.
- App-relevante Dateitypen sind insbesondere `*.py`, `*.html`, `*.js`, `*.css`,
  `Dockerfile`, Shell-/Startskripte und Laufzeit-Konfigurationen.
- Bei Versionsbump `influxbro/CHANGELOG.md` aktualisieren, neueste Version
  oben.
- Bei UI- oder Verhaltensaenderungen `influxbro/MANUAL.md` aktualisieren.
- Pro veroeffentlichter Add-on-Version die getestete Home-Assistant-
  Core-Version in `influxbro/CHANGELOG.md` dokumentieren, wenn sie ermittelt
  werden kann.
- Nach freigegebenen app-relevanten Aenderungen gehoeren Commit und Push nach
  `main` zum Abschluss, sofern QA und Sicherheitsregeln nicht blockieren.
  Force-Push ist verboten.

### Home Assistant Live-Update

- Wenn `influxbro/config.yaml` eine neue Add-on-Version erhalten hat, nach
  erfolgreichem Push nach `main` Home Assistant auf diese Version
  aktualisieren oder den Blocker klar melden.
- Erwartete Version aus `influxbro/config.yaml` bestimmen und Live-Version
  ueber `GET http://192.168.2.200:8099/api/info` pruefen.
- Bevorzugter Updatepfad ist die Home-Assistant-Core-API:
  `homeassistant/update_entity` fuer `update.influxbro_update`, danach
  `update/install` und Polling bis `/api/info` die erwartete Version liefert.
- Nur wenn der HA-Core-API-Updatepfad technisch nicht nutzbar ist, darf der
  bestehende Playwright-Fallback `tests/e2e/ha-live-update-influxbro.spec.js`
  verwendet werden.
- Die Live-Version muss exakt der erwarteten Version entsprechen; Abweichung
  ist ein Blocker.

### Pflicht-Sicherheitspruefung

- Bei jeder Aenderung an diesem Home-Assistant-Add-on vor Fertigstellung
  delta-orientiert eine Sicherheitspruefung durchfuehren.
- Mindestbereich je nach Relevanz: `influxbro/config.yaml`,
  `influxbro/Dockerfile`, `influxbro/run.sh`, Backend-API-Routen,
  Request-Handler, HTML/Templates/Frontend-JavaScript, Dateioperationen,
  Logging und Abhaengigkeitsdateien.
- Pruefen auf hartcodierte Geheimnisse, Secret-Leaks in Logs/API/UI, fehlende
  Eingabevalidierung, Command Injection, Path Traversal, XSS/DOM-Injection,
  CSRF-relevante Schreib-/Loeschaktionen, SSRF, unsichere
  Import-/Export-/Backup-/Restore-Pfade, fehlende Auth/Autorisierung,
  gefaehrliche Defaults, zu weitreichende Container-Rechte und
  Informationslecks.
- Add-on-Rechte nach Least Privilege pruefen: `host_network`, `privileged`,
  `full_access`, `homeassistant_api`, `ingress`, `ports`, Host-Mounts,
  Docker-Socket und Geraetezugriffe.
- Befunde konkret dokumentieren: Schweregrad, Datei/Bereich, Risiko,
  realistisches Szenario, konkrete Behebung.
- Sicher und eindeutig behebbare Sicherheitsprobleme minimal und
  nachvollziehbar direkt beheben.

### Pflicht-QA

- Wenn ausschliesslich nicht app-relevante Regel- oder Dokumentationsdateien
  geaendert werden, entfallen App-QA, Syntaxpruefung, Docker-Verifikation,
  UI-Verifikation und Live-Tests; Plausibilitaetspruefung genuegt und ist im
  Abschluss zu nennen.
- Laufzeit-/API-Smoke-Tests sind Pflicht, wenn Backend-Routen,
  Request-Handling, Config-Loading oder UI-ausgeloeste API-Aktionen
  betroffen sind.
- Docker-Verifikation ist Pflicht, wenn Laufzeitverhalten, Abhaengigkeiten,
  Container-Verhalten, Startskripte, Add-on-Paketierung oder
  Konfigurationsverarbeitung betroffen sind.
- UI-Verifikation ist Pflicht, wenn Templates, JavaScript oder
  Browser-Interaktionen betroffen sind.
- Fehlgeschlagene Pflichtpruefungen blockieren den Abschluss, bis sie
  behoben oder als nicht zusammenhaengender Altfehler begruendet sind.

### Live- und Playwright-Tests

- Standard-Testhost fuer HA-gestuetzte Live-Integrationstests ist
  `http://192.168.2.200:8099`.
- Fuer Live-UI- und Playwright-Tests darf der Browser das Live-Add-on nicht
  direkt ueber `192.168.2.200:8099` ansteuern; stattdessen lokalen
  HTTP-Proxy `127.0.0.1:8099 -> http://192.168.2.200:8099` verwenden.
- Playwright-Konfiguration: `playwright.config.js`, Tests unter
  `tests/e2e/*.spec.js`, mit `HA_URL=http://127.0.0.1:8099 npx playwright
  test ...`.
- Live-Tests nur gegen die erwartete Version ausfuehren; wenn `/api/info`
  nicht zur erwarteten Version passt, zuerst aktualisieren oder Blocker
  melden.
- Ein Dienst gilt erst als bereit, wenn ein Health-/API-Endpunkt erfolgreich
  antwortet und gueltiges JSON liefert; Port-Listening allein reicht nicht.

### Lokale Starts und Smokes

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

### UI- und Template-Regeln

- Allgemeine Template-, Ingress- und JavaScript-Grundregeln fuer
  Handbuch-/Dokumentationsspruenge stehen in
  `influxbro/projekt-template-handbuch-rules.md` und sind vor entsprechenden
  Aenderungen zu lesen.
- Vor dem Hinzufuegen oder Aendern von GUI-Elementen
  `influxbro/projekt-template.md` lesen und beachten.
- Je nach GUI-Umbau zusaetzlich passende Spezialregeln lesen:
  `influxbro/projekt-template-dialog-rules.md`,
  `influxbro/projekt-template-tooltips-rules.md`,
  `influxbro/projekt-template-measurement-select-rules.md`,
  `influxbro/projekt-template-section-rules.md`,
  `influxbro/projekt-template-picker-rules.md`,
  `influxbro/projekt-template-tables-rules.md`,
  `influxbro/projekt-template-handbuch-rules.md`.
- Konsistente Layout-Muster, Spacing, Card-/Layout-Struktur, Klassen und IDs
  ueber alle UI-Komponenten hinweg einhalten.
- UI-Komponenten auf Container-Ebene und fuer alle Kind-Elemente validieren.
- Jedes sichtbare, support-relevante UI-Element muss eine stabile `data-ui`-
  Kennung und eine eindeutige `data-ib-pickkey`-Kennung besitzen.
- Funktionaler globaler Zustand und profilbasierter UI-Zustand muessen
  technisch getrennt bleiben; Browser-lokaler UI-Zustand darf serverseitigen
  funktionalen Zustand nicht ueberschreiben.
- Beim Entfernen, Ersetzen oder Stilllegen von UI-Elementen, Templates,
  Buttons, Tabellen, Dialogen, Frontend-Aktionen, API-gebundenen
  UI-Funktionen oder Routen den Tombstone-Prozess anwenden: Abhaengigkeiten
  pruefen, `.tombstones.yml` ergaenzen, Migrations-/Ersatzpfad dokumentieren
  und Abschlussbericht erweitern.

### Code-Stil

- Python: 4 Leerzeichen, F-Strings fuer Formatierung, moeglichst kurze
  Zeilen, Imports gruppieren in Standardbibliothek, Drittanbieter, lokale
  Imports; ein Import pro Zeile.
- Type-Hints fuer neue oder geaenderte Funktionen hinzufuegen.
- Fuer JSON-aehnliche Payloads `dict[str, Any]` verwenden und an Grenzen
  validieren/normalisieren.
- Flask-Routen als Vertrauensgrenzen behandeln: Parameter validieren, Typen
  normalisieren, klare Fehler mit passenden HTTP-Status-Codes zurueckgeben.
- Einheitliches JSON-Envelope verwenden: Erfolg `{"ok": true, ...}`, Fehler
  `{"ok": false, "error": "..."}`.
- Keine breiten `except Exception` in reinen Hilfsfunktionen; an
  HTTP-Grenzen nur bewusst und mit nuetzlichen Fehlermeldungen.
- Werden Python-Abhaengigkeiten geaendert, `influxbro/requirements.txt` in
  derselben Aenderung aktualisieren.

## Arbeitsweise

- Vor einer Aenderung die betroffenen Dateien frisch lesen; Index- und
  Memory-Daten sind Orientierung, keine aktuelle Dateiquelle.
- Kleine, nachvollziehbare Aenderungen. Bestehende Muster und Namen beibehalten.
- Keine unangeforderten Umbauten, Formatierungen oder Umbenennungen. Fremde
  lokale Aenderungen nicht zuruecksetzen und nicht mitcommitten.
- Neue oder geaenderte Funktionen, Eingaben und GUI-Elemente im selben
  Arbeitsblock in `docs/functions.yaml` und `docs/handbuch.md` nachziehen.
- `.github/workflows/` bleibt leer: Remote-CI ist ohne ausdrueckliche
  Nutzerfreigabe untersagt, Pruefungen laufen lokal.

## Globale Regeln nachschlagen

Die verbindlichen projektuebergreifenden Regeln liegen unter
`/Users/thomasschatz/git/global/`. Die vier harten Regeln oben sind daraus
bereits hier vollstaendig wiedergegeben. Die uebrigen Dateien werden gelesen,
wenn die Aufgabe das jeweilige Thema beruehrt -- nicht vorsorglich alle:

| Thema der Aufgabe | Datei |
|---|---|
| Arbeitsweise, Scope, Abschluss, Git-Hygiene | `global-workflow-rules.md` |
| Grundregeln fuer Agenten, Freigaben, Prioritaet | `global-agents.md` |
| Version, Linter je Sprache, Pruefskripte, lokale Workflows | `global-project-rules.md` |
| Secrets, Maskierung, Vorfaelle | `global-secrets-rules.md` |
| Security-Baseline, destruktive Aktionen | `global-security-rules.md` |
| Funktionskatalog, Handbuch, Kurzbeschreibungen | `global-documentation-rules.md` |
| Installation, Setup-Scripts, Distribution, Releases | `global-installation-rules.md` |
| Web- und GUI-Verhalten, Ladezustaende, Sichtposition | `global-gui-rules.md` |
| MCP- und Werkzeugnutzung | `global-mcp-rules.md` |
| Logs und Protokolle | `global-log-rules.md` |
| DNS, Netzwerk, UDM | `global-dns-rules.md`, `global-udm-rules.md` |
| Docker, Registry, Portainer, Deployment | `global-registry-workflow.md` |

`global-registry-workflow.md` ist fuer Docker-/Registry-/Portainer-/
Deployment-Arbeiten an diesem Add-on zwingend vorher zu lesen.

Der zuletzt gepruefte Stand steht in `docs/rules/global-rule-baseline.json`.
Vor nicht-trivialen Arbeiten den Drift pruefen:

```sh
python3 /Users/thomasschatz/git/global/scripts/check-global-rule-drift.py /Users/thomasschatz/git/ha-addons
```

Meldet der Check Drift oder fehlt der Marker, zuerst einen Global-Rule-Audit
anbieten; die Baseline erst nach abgeschlossenem Audit mit `--write-baseline`
erneuern.

## Abschluss

Eine Aufgabe ist erst fertig, wenn die Aenderung umgesetzt ist, die Pruefungen
gruen sind oder ihr Ausfall begruendet ist, Funktionskatalog und Handbuch den
neuen Stand zeigen, `VERSION` (und bei App-Aenderungen `influxbro/config.yaml`)
erhoeht ist, keine Secret- oder Security-Risiken offen sind und Commit, Push
sowie der Issue-Abschluss erledigt oder konkret als blockiert gemeldet sind.
Der Abschlussbericht nennt offene Restpunkte und Risiken; Pruefungen, die nur
der Nutzer an seiner Hardware ausfuehren kann, stehen dort unter
`Offene Benutzerpruefungen`.
