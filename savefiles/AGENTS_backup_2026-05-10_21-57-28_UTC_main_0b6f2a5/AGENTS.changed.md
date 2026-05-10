
# AGENTS v3.1 – Stand: 2026-05-07

Sprache: Deutsch · Repository: influxbro · Typ: Home Assistant Add-on

## PRIORITÄTSREIHENFOLGE (ABSOLUT VERBINDLICH)

Bei Konflikten gilt immer diese Rangfolge:

1. Systemanweisungen der Plattform
2. Developer-Anweisungen
3. Modussperre (`Plan Mode` / `READ-ONLY`)
4. Regeln dieser Datei
5. Nutzerwunsch

Nutzerwünsche und Arbeitsregeln dürfen niemals eine höhere Priorität erhalten als eine aktive Modussperre.

## ABSCHNITT 1 – PFLICHT-AUSFÜHRUNGSFLUSS

### 1.1 Repository-Verzeichnisprüfung (KRITISCH, gecacht)

**PFLICHT:** Vor der ersten Tool-Aktion der OpenCode-Session MUSS der Agent prüfen, ob das Arbeitsverzeichnis folgende Einträge enthält:

- `influxbro/`
- `AGENTS.md`
- `repository.yaml`

Fehlt einer dieser Einträge: **SOFORT STOPPEN** und melden:
> „Falsches Arbeitsverzeichnis – Repository-Root erforderlich."

Nach erfolgreicher Prüfung gilt das Arbeitsverzeichnis für die gesamte laufende OpenCode-Session als verifiziert.

Die Prüfung wird danach NICHT erneut ausgeführt, solange dieselbe OpenCode-Session läuft.

Die Prüfung MUSS erst wieder erfolgen:

- nach einem Neustart von OpenCode
- beim Beginn einer neuen Session, in der noch keine erfolgreiche Prüfung erfolgt ist

### 1.2 Pflichtablauf vor jeder Umsetzung (KRITISCH)

1.2.0 Schritt 0 - Plan-Zustand muss leer sein

Solange offenen Aufgaben in der aktuellen ToDo-Liste und `./.opencode/plan_state.md` vorhanden sind, dürfen KEINE neuen Issues oder Aufgaben die nicht darin beinhaltet sind - ohne Ausnahme - gestartet werden. Der Agent meldet in diesem Fall den blockierten Zustand und listet die offenen Punkte auf.

1.2.1 Schritt 1 – GitHub-Issues (NUR AUF EXPLIZITEN BEFEHL)

- GitHub-Issues werden NICHT automatisch geprüft, geladen oder gestartet.
- Issues werden ausschließlich geprüft und abgearbeitet, wenn der Nutzer dies explizit anweist (z. B. „offene Issues abarbeiten", „prüfe Issues").
- Solange ToDo-Einträge mit Status `in_progress` oder `ausstehend` existieren oder `./.opencode/plan_state.md` offene Punkte enthält, dürfen KEINE neuen Issues gestartet werden – auch nicht auf explizite Anfrage. Der Agent meldet in diesem Fall den blockierten Zustand und listet die offenen Punkte auf.
- `rememberme`-Issues sind bei jeder Prüfung strikt zu überspringen, auch wenn der Nutzer nach „allen Issues" fragt.

1.2.2 Schritt 2 – Issue erstellen bei neuer Anfrage

- Ist die Anfrage NEU, MUSS ein GitHub-Issue erstellt werden, BEVOR mit der Umsetzung begonnen wird.
- Titel: kurze Zusammenfassung
- Body: vollständige Beschreibung
- Der Issue-Body MUSS zusätzlich einen eigenen Abschnitt `## Ursprüngliche Nutzeranweisung` enthalten.
- In diesem Abschnitt MUSS die ursprüngliche Chat-Anweisung des Nutzers möglichst wortgetreu übernommen werden.
- Die ursprüngliche Nutzeranweisung darf nicht sinngemäß ersetzt, gekürzt oder stillschweigend geglättet werden.
- Falls die Anforderung aus mehreren zusammengehörigen Chat-Nachrichten besteht, MÜSSEN alle relevanten Nachrichten chronologisch in diesem Abschnitt dokumentiert werden.
- Technische Interpretationen, Ableitungen und Akzeptanzkriterien gehören NICHT in diesen Abschnitt, sondern in die normale Issue-Beschreibung.
- Enthält die ursprüngliche Nutzeranweisung sensible Daten, Zugangsdaten, Tokens, Passwörter oder private personenbezogene Daten, MÜSSEN diese vor dem Einfügen entfernt oder maskiert werden.
- Label: `type/enhancement` oder `type/bug`
- Status: `status/in_progress` wenn sofort umgesetzt wird, sonst `status/open`

1.2.3 Schritt 3 – ToDo-Liste anlegen oder aktualisieren**

- Für jeden Auftrag MUSS eine ToDo-Liste angelegt und sichtbar gehalten werden.
- Genau ein Eintrag trägt zu jedem Zeitpunkt den Status `in_progress`.
- Abgeschlossene Einträge werden sofort als `erledigt` markiert.
- Die aktive ToDo-Liste wird gemeinsam mit dem aktuellen Arbeitsstand im Chat angezeigt.

1.2.4 Schritt 4 – Plan-Zustand persistieren**

- Den aktuellen Arbeitsstand nach jeder bedeutsamen Änderung in `./.opencode/plan_state.md` spiegeln.
- Inhalt: aktuelle ToDo-Liste (mit Status), offene Entscheidungen, vereinbarte Planänderungen.
- Diese Datei ist lokal zu halten und NICHT zu committen.
- Beim Start einer neuen Sitzung MUSS `./.opencode/plan_state.md` zuerst geladen werden, sofern sie existiert. Einträge mit Status `ausstehend` oder `in_progress` sind aktiv weiterzuführen. Erledigte Einträge werden ignoriert.

### 1.3 Pflichtablauf während der Umsetzung

- Alle Schreiboperationen **MÜSSEN** strikt sequenziell ausgeführt werden.
- Änderungen minimal halten und konsistent mit bestehenden Repository-Mustern halten.
- Genau ein ToDo-Eintrag trägt den Status `in_progress`.
- Dateiinhalte vor jeder Änderung neu lesen – niemals auf erwartete oder frühere Versionen verlassen.
- Schlägt ein `apply_patch` fehl, MUSS:
  1. die betroffene Datei neu gelesen werden
  2. die Zielstelle auf Basis des echten Inhalts neu identifiziert werden
  3. der Patch mit robusten Ankern neu erstellt werden
- Schlägt ein identischer Befehl zweimal mit demselben Fehlerbild fehl, darf er NICHT weiter unverändert wiederholt werden. Der Agent MUSS zuerst die Fehlerausgabe oder ein vorhandenes Log auswerten, die Ursache klassifizieren und den Befehl korrigieren oder auf ein alternatives Tool wechseln. Ausnahme: klar transiente Netzwerk-, Lock- oder Timeout-Fehler mit plausibler Erfolgschance.

### 1.4 Pflichtablauf nach der Umsetzung

Die folgenden Schritte sind in dieser Reihenfolge auszuführen und dürfen nicht übersprungen werden.

#### Schritt A – Pflicht-Sicherheitsüberprüfung (HA Add-on)

Bei jeder Änderung an einem Home Assistant Add-on MUSS vor der Fertigstellung eine Sicherheitsprüfung durchgeführt werden.

**Mindest-Prüfumfang:**

- `influxbro/config.yaml`
- `influxbro/Dockerfile`
- `influxbro/run.sh` und weitere Startskripte
- Backend-API-Routen und Request-Handler
- HTML/Templates/Frontend-JavaScript
- Dateioperationen
- Logging
- Abhängigkeitsdateien (`requirements.txt`, `pyproject.toml`, `package.json`)

Die Sicherheitsprüfung ist delta-orientiert auszuführen, ohne den Mindest-Prüfumfang aufzuweichen:

- Geänderte Dateien und betroffene Trust-Boundaries vollständig prüfen.
- Unveränderte Pflichtdateien auf sicherheitsrelevante Konfigurations-, Berechtigungs- oder Abhängigkeitsauswirkungen prüfen.
- Bereits im selben Auftrag geprüfte unveränderte Dateien müssen nicht erneut vollständig gelesen werden, sofern sich ihr Inhalt nicht geändert hat.
- Der Abschlussbericht MUSS klar trennen, welche Dateien vollständig geprüft wurden und welche unverändert/konfigurationsbezogen geprüft wurden.

**Pflichtprüfungen:**

- Hartcodierte Geheimnisse, Tokens, Passwörter, API-Keys oder interne URLs
- Geheimnisse oder sensible Werte in Logs
- Fehlende Eingabevalidierung für alle externen Eingaben
- Command-Injection-Risiken (subprocess/shell)
- Path-Traversal und unsicherer Dateizugriff
- XSS und unsichere DOM-Injection in Frontend/Templates
- CSRF-relevante Schreib-/Löschaktionen ohne Absicherung
- SSRF über nutzerkontrollierte URLs/Hosts
- Unsichere Upload-/Download-/Backup-/Restore-/Import-/Export-Pfade
- Fehlende Authentifizierungs-/Autorisierungsprüfungen
- Gefährliche Standardeinstellungen
- Zu weitreichende Container-Privilegien, Host-Mounts, Gerätezugriffe, offene Ports
- Informationslecks in Fehlermeldungen
- Unsichere dynamische Code-Ausführung (`eval`, `exec` oder Äquivalente)
- Veraltete oder offensichtlich risikobehaftete Abhängigkeiten

**HA-spezifische Prüfung (Least Privilege):**

Folgende Add-on-Konfigurationen MÜSSEN auf Notwendigkeit geprüft werden. Jede nicht eindeutig benötigte Berechtigung MUSS gemeldet und eine Reduzierung vorgeschlagen werden:

- `host_network`, `privileged`, `full_access`, `homeassistant_api`, `ingress`, `ports`
- gemountete Host-Pfade, Docker-Socket-Zugriff, angebundene Geräte

**Externe-Eingabe-Regel:**

Alle externen Eingaben sind standardmäßig als nicht vertrauenswürdig zu behandeln:
Query-Parameter, JSON-Bodies, Formularfelder, Dateinamen, Pfade, Sortier-/Filterwerte, Umgebungsvariablen, HA-Optionswerte, URLs, Hosts, IDs, Tokens.

**Befunde-Pflicht:**

- Keine generischen Sicherheitsaussagen ohne Code-Belege.
- Jeder Befund MUSS enthalten: Schweregrad (kritisch/hoch/mittel/niedrig), betroffene Datei + Funktion/Bereich, Risikoerklärung, realistisches Angriffsszenario, konkrete Behebung, Patch-Vorschlag (wenn machbar).

**Behebungs-Pflicht:**

- Ist ein Sicherheitsproblem sicher und eindeutig behebbar, MUSS die Behebung direkt implementiert werden.
- Behebungen minimal, risikoarm und nachvollziehbar halten.

**Abschlussgate:**

Als erledigt gilt die Aufgabe erst, wenn: Sicherheitsprüfung durchgeführt, Befunde dokumentiert, sichere Fixes angewendet, verbleibende Risiken explizit aufgelistet.

**Pflichtausgabe der Sicherheitsprüfung:**

- Befunde nach Schweregrad
- Umgesetzte Fixes
- Verbleibende Risiken
- Empfohlene Folgeprüfungen

#### Schritt B – Pflicht-QA

Reihenfolge einhalten:

1. Syntaxprüfung (immer Pflicht): `python -m py_compile influxbro/app/app.py`
2. Gezielte Tests (Pflicht wenn vorhanden): einzelner Test, einzelne Testdatei oder Keyword-gefilterter Pytest-Lauf
3. Laufzeit-/API-Smoke-Tests (Pflicht wenn relevant für Backend-Routen, Request-Handling, Config-Loading oder UI-ausgelöste API-Aktionen)
4. Docker-Verifikation (Pflicht nur wenn relevant für Laufzeitverhalten, Abhängigkeiten, Container-Verhalten, Startskripte, Add-on-Paketierung oder Konfigurationsverarbeitung)
5. UI-Verifikation (Pflicht wenn relevant für Templates, JavaScript oder Browser-Interaktionen)

Fehlverhalten:**

- Schlägt eine Pflichtprüfung fehl: Arbeit NICHT als abgeschlossen erklären.
- Fehler beheben, kleinste relevante Validierung erneut ausführen.
- Bereits vorhandene, nicht zusammenhängende Fehler blockieren den Flow NICHT automatisch – der Agent MUSS explizit begründen, warum sie nicht zusammenhängen.

Abschlussbericht QA:**

- Welche Prüfungen wurden ausgeführt?
- Welche wurden übersprungen und warum?
- Endergebnis jeder ausgeführten Prüfung

#### Schritt C – Versionierung (PFLICHT FÜR HA)

**Jede Änderung an app-relevanter Laufzeit-, UI-, API- oder Verhaltenslogik erzwingt zwingend eine neue Version. Es gibt keine Ausnahmen für app-relevante Änderungen.**

Betroffene Dateitypen: `*.py`, `*.html`, `*.js`, `*.css`, Dockerfile, Shell-/Startskripte, Laufzeit-Konfigurationen.

Nicht app-relevante Dateien erzwingen KEINEN Add-on-Versionsbump, sofern sie das ausgelieferte Add-on, dessen Laufzeitverhalten, UI, API, Container, Startverhalten, Konfiguration oder Abhaengigkeiten nicht beeinflussen. Dazu zaehlen insbesondere reine Agent-/Repository-Regeln, lokale Plan-/Arbeitsdateien, nicht ausgelieferte Hilfsdateien und Dokumentation ausserhalb des Add-ons. Wenn keine Add-on-Version erhoeht wird, entfallen Changelog-Eintrag zur Add-on-Version und Home-Assistant-Live-Update.

Pflichtschritte:

- Version in `influxbro/config.yaml` inkrementieren (letztes Segment: z. B. `1.12.44 → 1.12.45`)
- Eintrag in `influxbro/CHANGELOG.md` ergänzen (neueste Version oben)
  - Bei GitHub-Issue: Changelog-Bullet MUSS einen klickbaren Issue-Link enthalten: `([#123](https://github.com/<owner>/<repo>/issues/123))`
- `influxbro/MANUAL.md` aktualisieren, wenn sich Verhalten oder UI geändert haben
- Vor dem Changelog-Eintrag: installierte HA-Core-Version ermitteln:

  ```bash
  curl -s -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://192.168.2.200:8123/api/config | jq -r '.version'

  ```

  Den ermittelten Wert unter `Tested with Home Assistant Core: <wert>` eintragen. `unknown` ist nur als Fallback erlaubt, wenn die Abfrage nicht erfolgreich ausgeführt werden kann.

Ohne erforderlichen Versionsbump bei app-relevanten Änderungen erkennt Home Assistant kein Update. Eine app-relevante Änderung gilt dann als unvollständig.

#### Schritt D – Git-Flow (HA Main-First, PFLICHT)

Standard:** Alle Änderungen werden direkt nach `main` gepusht, damit Home Assistant das Update erkennen kann.

Bevorzugter Pflichtweg ist der HA-Core-API-Updatepfad. Er vermeidet Playwright-Login,
HA-UI-Abhaengigkeiten und bekannte Node/Playwright-Netzwerkfehler. Der Ablauf ist in
`tools/ha-live-update-influxbro.md` dauerhaft dokumentiert.

Pflichtsequenz:

1. Erforderliche QA ausführen
2. Fehler klassifizieren: fix-bezogen/blockierend vs. bereits vorhandene/nicht zusammenhängende Fehler
3. Bei ausschließlich vorhandenen/nicht zusammenhängenden Fehlern: Pflichtfluss fortsetzen
4. `influxbro/config.yaml` Version erhöhen (wenn Laufzeit/UI/API/Verhalten geändert)
5. Änderungen stagen
6. Commit erstellen
7. Nach `main` pushen
8. Wenn eine Add-on-Version erhöht wurde: Home Assistant Live-Update gemäß Schritt D2 ausführen
9. Ergebnis klar im Chat melden

VERBOTEN:** Nach Codeänderungen oder nach QA stoppen, wenn diese Policy Version-Bump, Commit und Push fordert.

VERBOTEN:** `build`-Modus als bloße Erlaubnis behandeln, während Pflicht-Abschlussschritte übersprungen werden.

Abschluss-Verifikation (PFLICHT VOR FERTIGMELDUNG):**

- [ ] Umsetzung abgeschlossen
- [ ] Erforderliche QA ausgeführt
- [ ] QA-Ergebnis klassifiziert
- [ ] `influxbro/config.yaml` Version erhöht (wenn erforderlich)
- [ ] Änderungen gestagt
- [ ] Commit erstellt
- [ ] Push nach `main` abgeschlossen

Fehlt ein Punkt: Aufgabe ist NICHT abgeschlossen.

Hochrisikoausnahme:
Bei sicherheitsrelevanter Logik, Löschlogik, größeren Architekturänderungen oder unklaren Seiteneffekten: Weiterhin nach `main` pushen, jedoch:

- strengere QA vor Push
- Commit-Message mit `⚠ HOHES RISIKO` kennzeichnen

Optionale Branches:
Branches dürfen NUR verwendet werden, wenn die Änderung lokal ohne Home Assistant testbar ist ODER der Nutzer ausdrücklich einen PR-Workflow verlangt.

**Commit-Konventionen:**

| Präfix | Verwendung |

|---|---|
| `feat:` | Neue Funktionen |
| `fix:` | Fehlerbehebungen |
| `refactor:` | Umstrukturierungen |
| `chore:` | Wartungsarbeiten |
| `⚠ HOHES RISIKO` | Risikobehaftete Änderungen |

Jeder Commit enthält: kurze Zusammenfassung + wichtigste Änderungen.

VERBOTEN:** Force Push.

VERBOTEN:** Push wenn Syntaxprüfung fehlgeschlagen, erforderliche QA nicht ausgeführt oder blockierende Fehler vorhanden.

#### Schritt D2 – Home Assistant Live-Update nach Push (PFLICHT BEI VERSION-BUMP)

Wenn `influxbro/config.yaml` in diesem Auftrag eine neue Add-on-Version erhalten hat, MUSS nach erfolgreichem Push nach `main` Home Assistant angewiesen werden, das InfluxBro-Add-on auf diese Version zu aktualisieren.

Pflichtsequenz:

1. Erwartete Version aus `influxbro/config.yaml` bestimmen.
2. Aktuelle Live-Version vor dem Update erfassen:

   ```bash
   curl -fsS http://192.168.2.200:8099/api/info | python3 -c "import json,sys; print(json.load(sys.stdin).get('version','unknown'))"
   ```

3. HA-Core-API-Updatepfad ausfuehren:

   - `SUPERVISOR_TOKEN` als Bearer-Token gegen `http://192.168.2.200:8123/api/*` verwenden.
   - `POST /api/services/homeassistant/update_entity` mit `{"entity_id":"update.influxbro_update"}` ausfuehren.
   - `GET /api/states/update.influxbro_update` pollen, bis `latest_version` der erwarteten Version entspricht und `state` `on` ist.
   - `POST /api/services/update/install` mit `{"entity_id":"update.influxbro_update","backup":false}` ausfuehren.
   - `/api/info` des Add-ons pollen, bis die Live-Version exakt der erwarteten Version entspricht.

4. Nur wenn der HA-Core-API-Updatepfad technisch nicht nutzbar ist, darf als Fallback der bestehende Playwright-Test ausgeführt werden:

   ```bash
   INFLUXBRO_EXPECT_VERSION=<version> HA_URL=http://192.168.2.200:8123 npx playwright test tests/e2e/ha-live-update-influxbro.spec.js
   ```

5. Live-Version über das Add-on verifizieren:

   ```bash
   curl -fsS http://192.168.2.200:8099/api/info | python3 -c "import json,sys; print(json.load(sys.stdin).get('version','unknown'))"
   ```

6. Die Live-Version MUSS exakt der erwarteten Version entsprechen.
7. Wenn sich die Live-Version tatsächlich geändert hat, MUSS zusätzlich diese Sprachausgabe erfolgen:

   ```bash
   say -v Anna "Homeassistant wurde erfolgreich von version <alte_version> auf version <neue_version> aktualisiert"
   ```

8. GitHub-Issue-Abschluss, Abschlusssignal und Versionsansage dürfen erst danach erfolgen.

Fehlverhalten:

- Schlägt der Home-Assistant-Update-Flow fehl, ist das ein Blocker.
- Weicht die Live-Version von der erwarteten Version ab, ist das ein Blocker.
- Bei Blocker: Fehler im Chat melden, diese Sprachausgabe ausführen, Issue NICHT schließen, keine Abschlussmeldung erzeugen, offenen Rest in ToDo-Liste und `./.opencode/plan_state.md` dokumentieren.

  ```bash
  say "Homeassistant konnte nicht erfolgreich aktualisiert werden"
  ```

#### Schritt E – GitHub-Issue abschließen

Ein Issue gilt erst als umgesetzt, wenn:

1. Die angeforderte Code-/Konfig-/Dokumentationsänderung tatsächlich angewendet wurde
2. Alle relevanten Pflicht-QA-Prüfungen ohne Fehler für dieses Issue ausgeführt wurden
3. Keine blockierenden Fehler für dieses Issue verbleiben
4. Die Änderung committed wurde
5. Die Änderung nach `main` gepusht wurde (gemäß Repository-Policy)

Pflichtschritte nach Umsetzung:

1. Issue-Statuslabel auf `status/done` setzen (vorheriges Label entfernen)
2. Issue-Kommentar hinzufügen mit: Ursache des Problems, gewählte Lösung, Commit-Hash und/oder PR-Link
3. Issue schließen

PFLICHT: GitHub-Kommentar IMMER via HEREDOC erstellen:

```bash
cat > /tmp/opencode_issue_comment.md <<'EOF'
<vollständiger Kommentartext inkl. Backticks, $, URLs usw.>
EOF
gh issue comment <ISSUE_NUMMER> --repo <OWNER>/<REPO> --body-file /tmp/opencode_issue_comment.md
```

VERBOTEN: `gh issue comment -b "..."` wenn der Inhalt Backticks, Dollarzeichen, shell-ähnliche Ausdrücke, URLs mit Query-Parametern, Dateipfade oder Befehle enthält.

##### Pflichtbindung an das aktive Issue (ABSOLUT)

Sobald der Agent ein konkretes Issue aktiv begonnen hat, gilt ausschließlich dieses Issue als aktiver Arbeitskontext.
Ein Issue gilt als aktiv begonnen, sobald mindestens eine der folgenden Bedingungen erfüllt ist:

- das Issue wurde ausdrücklich als aktuelles Issue genannt
- das Issue wurde lokal in ToDo/plan_state als `in_progress` geführt
- das Issue wurde auf GitHub auf `status/in_progress` gesetzt
- der Agent hat nach Erstellung oder Auswahl des Issues mit der inhaltlichen Abarbeitung begonnen
Ab diesem Zeitpunkt gilt:
- Der Agent darf bis zum vollständigen Abschluss dieses aktiven Issues NICHT auf ein anderes Issue umschalten.
- Der Agent darf bis zum vollständigen Abschluss dieses aktiven Issues NICHT auf einen früheren Abschlusszustand oder eine frühere Abschlussmeldung zurückspringen.
- Der Agent darf bis zum vollständigen Abschluss dieses aktiven Issues KEINE Abschlussmeldung für ein anderes Issue oder für einen globalen Gesamtzustand erzeugen.
- Der Agent darf bis zum vollständigen Abschluss dieses aktiven Issues KEINE Prüfung anderer offener Issues priorisieren oder berichten, außer ein echter Blocker macht die Weiterarbeit am aktiven Issue unmöglich.

##### Vollständiger Abschluss eines aktiven Issues (PFLICHT)

Ein aktives Issue darf erst dann als abgeschlossen behandelt oder gemeldet werden, wenn ALLE folgenden Punkte für genau dieses aktive Issue erfüllt sind:

1. Angeforderte Änderung umgesetzt (Schritt A – Pflicht-Sicherheitsüberprüfung (HA Add-on))
2. Relevante Pflicht-QA ausgeführt (Schritt B – Pflicht-QA)
3. Keine blockierenden issue-bezogenen Fehler verbleiben
4. Sicherheitsprüfung durchgeführt, falls erforderlich
5. Versionsbump durchgeführt, falls erforderlich (Schritt C – Versionierung (PFLICHT FÜR HA))
6. CHANGELOG aktualisiert, falls erforderlich
7. MANUAL aktualisiert, falls erforderlich
8. Commit erstellt
9. Nach `main` gepusht (Schritt D – Git-Flow (HA Main-First, PFLICHT))
10. Home Assistant Live-Update abgeschlossen, falls eine Add-on-Version erhöht wurde (Schritt D2)
11. GitHub-Issue auf `status/done` gesetzt und geschlossen (Schritt E – GitHub-Issue abschließen)
12. Abschlusssignal ausgeführt (Schritt F – Abschlusssignal (PFLICHT, IMMER AUSFÜHREN))
13. Erst DANACH `./.opencode/plan_state.md` geprüft und Nutzer über verbleibende Restpunkte informiert

##### Verbotene Umschaltung vor Punkt 12 und 13

Insbesondere ist VERBOTEN:

- nach Punkt 11 (GitHub-Issue geschlossen) bereits auf andere offene Issues umzuschalten
- vor Punkt 12 (Abschlusssignal) eine Abschlussmeldung zu erzeugen
- vor Punkt 13 (Restprüfung) einen globalen Fertigzustand zu behaupten
- einen früheren Issue-Abschluss als Antwort auf ein später aktiv gewordenes Issue zu verwenden

##### Pflichtangabe in Status- und Abschlussmeldungen

Solange ein aktives Issue existiert, MUSS jede substanzielle Status- oder Abschlussmeldung die aktive Issue-Nummer eindeutig referenzieren.
Vor jeder Abschlussmeldung MUSS der Agent intern prüfen:

- Ist dies noch dasselbe aktive Issue?
- Wurden Punkt 1 bis 13 für genau dieses Issue erfüllt?
- Wird keine frühere Abschlussmeldung wiederverwendet?
- Erfolgt die Restprüfung erst nach dem issue-lokalen Abschluss?

Wenn eine dieser Prüfungen negativ ist, ist eine Abschlussmeldung VERBOTEN.

#### Schritt F – Signale und Abschluss (PFLICHT, IMMER AUSFÜHREN)

Es gibt vier unterschiedliche Signalarten:

1. Abschlusssignal
2. Versionsansage
3. Blockersignal
4. Entscheidungssignal

Die Home-Assistant-Live-Update-Sprachausgabe aus Schritt D2 ist zusätzlich zur Versionsansage auszuführen, aber nur nach erfolgreichem Live-Update und nur wenn sich die Live-Version tatsächlich geändert hat.

Das Abschlusssignal darf AUSSCHLIESSLICH ganz am Ende des vollständigen Abschlussflusses erfolgen.
Pflichtreihenfolge vor jedem Abschlusssignal:

1. Umsetzung abgeschlossen
2. Erforderliche QA abgeschlossen
3. Versionsbump / Changelog / Manual abgeschlossen (falls erforderlich)
4. Commit erstellt
5. Push nach `main` erfolgreich abgeschlossen
6. GitHub-Issue auf `status/done` gesetzt und geschlossen (falls vorhanden)
7. Erst DANACH Abschlusssignal ausführen
8. Eine Versionsansage darf nur zusätzlich und erst nach erfolgreichem Push ausgeführt werden

VERBOTEN:

- Abschlusssignal vor erfolgreichem Commit
- Abschlusssignal vor erfolgreichem Push
- Versionsansage vor erfolgreichem Push
- Home-Assistant-Live-Update-Sprachausgabe ohne erfolgreiche D2-Verifikation oder ohne tatsächliche Versionsänderung
- Abschlusssignal oder Versionsansage, wenn Commit oder Push fehlgeschlagen ist

Nach erfolgreicher Fertigstellung wird das Abschlusssignal ausgeführt:

```bash
afplay /System/Library/Sounds/Glass.aiff
say "Fertig mit der Umsetzung"
```

Wenn eine neue Add-on-Version erstellt wurde (Version in influxbro/config.yaml erhöht), wird zusätzlich und erst nach erfolgreichem Push die Versionsansage ausgeführt:

```bash
say -v Anna "Generierung erfolgt, Version X Punkt Y Punkt Z wurde erzeugt"
```

Bei blockierenden Fehlern oder offenen Fragen wird das Blockersignal ausgeführt:

```bash
afplay /System/Library/Sounds/Basso.aiff
say "Einige Punkte muessten noch beantwortet werden"
```

Wenn der Agent auf eine Entscheidung des Nutzers wartet, wird das Entscheidungssignal ausgeführt:

```bash
say "Entscheidung erforderlich"
```

Hinweis: Audio-Signale sind Best-Effort. Ein fehlendes Signal macht eine abgeschlossene Aufgabe NICHT ungültig.
Abgeschlossen ist eine Aufgabe AUSSCHLIESSLICH, wenn alle Pflichtschritte A bis F ausgeführt wurden.

## ABSCHNITT 2 – INPUT-LOGIK UND ABARBEITUNGSKONTEXT

### 2.1 Grundregel: Keine Unterbrechung aktiver Abarbeitung

Solange eine Abarbeitung aktiv ist und noch nicht vollständig abgeschlossen wurde (inkl. Abschlusssignal, ohne offene Restarbeiten und ohne offene Rückfragen), gilt:

- **Neue Eingaben des Nutzers werden NICHT sofort ausgeführt.**
- **Neue Eingaben werden als offene Folgepunkte im aktiven Arbeitskontext dokumentiert.**
- **Der aktive Prozess läuft bis zum vollständigen Abschluss weiter.**

Diese Regel gilt NICHT kontextübergreifend: Beginnt ein neuer Auftrag mit anderem Scope oder unter aktiver Modussperre, verfallen frühere GO-/Issue-Freigaben gemäß Abschnitt 2.1.1 und 4.1 automatisch.

### 2.1.1 Verfall früherer GO-/Issue-Freigaben (PFLICHT)

- Eine frühere `GO`-, Build- oder Issue-Freigabe gilt ausschließlich für den damals aktiven Auftrag.
- Kommt später eine neue Nutzeranweisung mit anderem Ziel, anderem Scope, anderen Verboten oder anderen Deliverables, verfällt die frühere Freigabe automatisch.
- `GO` darf NIEMALS als globaler Dauerzustand interpretiert werden.
- `GO` darf NUR an den unmittelbar davor aktiven, thematisch passenden Auftrag gebunden werden.
- Frühere `GO`-/Issue-Freigaben dürfen NICHT auf neue Analyse-, Plan-, Read-Only- oder anders gelagerte Aufträge übertragen werden.

### 2.2 Sichtbarkeit und Folgeeingaben

Neue Folgeeingaben, Restpunkte und offene Entscheidungen werden nicht in getrennten Arbeitslisten geführt, sondern ausschließlich:

- in der aktiven ToDo-Liste
- im aktuellen Arbeitsstand in `./.opencode/plan_state.md`
- und, solange eine Modussperre aktiv ist, zusätzlich sichtbar im Chat

Die aktive ToDo-Liste MUSS im Chat sichtbar gehalten werden.
Genau eine sichtbare ToDo-Darstellung reicht aus. Wenn das verwendete Tool die ToDo-Liste bereits sichtbar anzeigt, DARF der zusaetzliche manuelle Chat-ToDo-Block entfallen. Wenn kein sichtbares ToDo-Tool verfuegbar ist oder ein Blocker/Abschlussstatus gemeldet wird, zeigt der Agent die ToDo-Liste kompakt als Block an:

```text
📋 ToDo – Aktiv
  ✅ <erledigter Schritt>
  🔄 <aktueller Schritt> (in_progress)
  ⬜ <ausstehender Schritt>
```

ToDo- und `plan_state.md`-Updates sind bei echten Statuswechseln Pflicht, insbesondere wenn ein Task startet, abgeschlossen wird, ein Blocker entsteht, sich der Plan ändert, vor Commit/Push und nach erfolgreichem Abschluss. Reine Lese- oder Such-Zwischenschritte ohne neue Entscheidung oder Statusänderung sollen nicht zusätzlich als eigener ToDo-/Plan-State-Update ausgegeben werden. `plan_state.md` wird nicht routinemaessig im Chat ausgegeben; im Chat reicht der Hinweis `Plan-State aktualisiert.` oder bei Blockern eine kurze Liste der offenen Punkte.

### 2.2.1 Kompakte Chat-Ausgaben (PFLICHT)

- Standard-Statusmeldungen nutzen eine einfache Checkliste mit maximal einer Zeile, z. B. `Checkliste: Kontext ✅ | Umsetzung 🔄 | QA ⬜ | Sicherheit ⬜ | Abschluss ⬜`.
- Im Build-Modus ist diese Checkliste die Standardausgabe. Erfolgreiche Einzelaktionen wie Issue-Erstellung, ToDo-/Plan-State-Update, Dateiaenderung, Diff-Pruefung, QA-Start, Commit, Rebase, Push, Live-Update, Issue-Kommentar, Issue-Schluss und Signale werden nicht separat beschrieben.
- Sichtbar bleiben im Build-Modus nur Phasenwechsel in der Checkliste, Fehler, Sicherheitsbefunde, Blocker, Entscheidungen/Rueckfragen, explizit angeforderte Details und der kompakte Abschlussbericht.
- `plan_state.md`-Aktualisierungen werden im Chat nicht mehr einzeln gemeldet, ausser ein Blocker oder eine Abschluss-/Restpunktmeldung macht sie relevant. Auch Tool-Erfolgsausgaben wie `Created plan_state.md`, `Updated plan_state.md` oder vergleichbare Schreibbestaetigungen werden nicht wiedergegeben.
- Patch-/Apply-Patch-Erfolgsausgaben werden im Chat NICHT angezeigt. Dazu zaehlen Meldungen wie `Patched ...`, `Success. Updated files`, `Created ...`, `Deleted ...` oder Datei-/Zeilenzusammenfassungen erfolgreicher Patchvorgaenge. Sichtbar bleiben nur Patch-Fehler, Konflikte oder explizit angeforderte Patchdetails.
- Diffs, Diff-Stats, `git diff`-Ausgaben, Patch-Inhalte, Plus/Minus-Darstellungen und Codeauszuege werden im Chat NICHT angezeigt. Der Agent wertet sie intern aus und meldet nur den Status, ausser ein Fehler, Sicherheitsbefund, Blocker oder eine explizite Nutzeranforderung erfordert Details.
- Code-Stellenlisten, Dateinamenlisten, Zeilenreferenzen und Dateiinhalte werden NICHT angezeigt, ausser sie sind fuer eine Entscheidung, einen Blocker, einen Sicherheitsbefund, einen Fehlerfix oder eine explizite Nutzeranforderung erforderlich.
- Datei-Lesevorgaenge, `Grep`-/Suchtreffer, Suchergebnislisten und Inhalte aus `Read`/Suchwerkzeugen werden im Chat nicht wiedergegeben; sichtbar genannt werden nur die daraus abgeleiteten Erkenntnisse, wenn sie fuer Bedienung, Entscheidungen, Blocker, Sicherheitsbefunde oder Abschluss relevant sind oder vom Nutzer explizit verlangt wurden.
- Vollstaendige Tool-Ausgaben, Testlogs, Polling-Schleifen, Playwright-Details, Build-Logs und API-Rohantworten werden nicht in den Chat uebernommen, solange der Schritt erfolgreich ist.
- Tests, QA, `rtk`-Tests, Smoke-Tests, Live-Tests und UI-Pruefungen erscheinen in der Checkliste nur als `passed`, `failed` oder `skipped`. Vor Testlaeufen reicht eine einzelne Startzeile wie `Test laeuft...`; erfolgreiche Testausgaben bleiben vollstaendig ausgeblendet.
- Bei fehlgeschlagenen Pruefungen werden immer der relevante Fehlerkern, die Ursache/Klassifikation und der naechste Fix-Schritt ausgegeben.
- Rebase-, Push-, Commit-, Home-Assistant-Update-, Live-Update- und Polling-Details werden nicht angezeigt, solange sie erfolgreich sind; sichtbar bleibt nur der Checklistenstatus und im Abschluss Commit, Version und Live-Version. Bei Fehlern werden Fehlerkern, Ursache/Klassifikation und naechster Fix-Schritt angezeigt.
- Compaction- oder Kontextpflege-Vorgaenge werden nur als kurzer Hinweis gemeldet, z. B. `Kontext wird kompaktiert; Arbeitsstand bleibt erhalten.`
- Abschlussberichte bleiben kompakt: Issue, Version, Commit, Push, Live-Version, QA, Sicherheit und offene Restpunkte. Keine Rohlogs, Diffs, Patches, Codeauszuege, Grep-Treffer, Tooldetails oder vollstaendigen Dateiauszuege ohne Nachfrage.

### 2.3 Behandlung neuer Eingaben

Neue Plan- oder Build-Anforderungen werden nicht in getrennten Queues geführt, sondern als offene Folgepunkte im aktiven Arbeitskontext dokumentiert.

### 2.4 Explizite Abbruchsignale (EINZIGE Ausnahme)

Nur folgende Formulierungen gelten als echte Unterbrechung:

- `abbrechen`
- `stop`
- `halt`
- `lass das`
- `nicht weiter damit`
- `stattdessen mache jetzt X`
- `verwirf den aktuellen Ablauf`

Fehlt ein solches Signal, ist jede neue Nachricht als Ergänzung des aktiven Arbeitskontexts zu behandeln.

### 2.5 Verhalten nach Abschluss der aktiven Aufgabe

Wenn die aktive Aufgabe vollständig abgeschlossen ist (alle Pflichtschritte A–F ausgeführt, kein offener Restpunkt, kein offenes Abschlusssignal), MUSS der Agent:

1. Die aktive ToDo-Liste und `./.opencode/plan_state.md` prüfen
2. Den Nutzer informieren, welche offenen Restpunkte ausstehen
3. Explizit fragen, ob diese Restpunkte als nächstes abgearbeitet werden sollen

VERBOTEN: Ausstehende Todos automatisch und ohne Rückfrage ausführen.

Pflichtausgabe nach Abschluss:**

```text
Aktive Aufgabe abgeschlossen.

Offene Restpunkte:
- <Eintrag 1>
- <Eintrag 2>

Soll ich mit der Abarbeitung der offenen Restpunkte beginnen?
1. Ja
2. Nein, ich gebe neue Anweisungen
```

### 2.6 Pflichtverhalten bei Fehlern während der Abarbeitung

Schlägt ein Schritt fehl, MUSS der Agent:

1. Den Fehler klar benennen
2. Den bereits erfolgreich erledigten Teil vom offenen Rest trennen
3. Den offenen Rest in der aktiven ToDo-Liste und in `./.opencode/plan_state.md` dokumentieren
4. Erst danach neue Nutzeranweisungen in diesen aktiven Arbeitskontext einarbeiten

### 2.7 Pflichtverhalten bei Scope-Erweiterungen

Fügt der Nutzer während der Ausführung neue Anforderungen hinzu:

1. Die laufende Arbeit bleibt aktiv
2. Neue Anforderungen werden als offene Folgepunkte in der aktiven ToDo-Liste und in `./.opencode/plan_state.md` ergänzt
3. Der Agent benennt kurz, was in Arbeit war und wie die neue Anweisung im aktiven Arbeitskontext ergänzt wurde
4. Nur bei explizitem Abbruchsignal darf die bisherige Arbeit fallengelassen werden

### 2.8 Kontextbruch-Erkennung (PFLICHT)

- Vor jeder Fortsetzung einer früher freigegebenen Abarbeitung MUSS der Agent prüfen, ob inzwischen ein neuer Auftrag mit anderem Scope aktiv ist.
- Ein Kontextbruch liegt insbesondere vor, wenn:
  - das Ziel fachlich wechselt
  - Analyse/Planung statt Umsetzung verlangt wird
  - neue Verbote oder Modussperren formuliert wurden
  - andere Deliverables oder andere Abnahmekriterien gelten
- Faustregel:
  - neues Ziel
  - neuer Scope
  - neue Verbote
  - neue Deliverables
  = neuer Kontext
- Bei erkanntem Kontextbruch MUSS der Agent:
  1. den alten Ausführungsmodus schließen
  2. alte `GO`-/Issue-Freigaben verwerfen
  3. den neuen Auftrag ausschließlich nach dessen aktuellen Regeln behandeln

---

## ABSCHNITT 3 – MODUSSPERRE

### 3.1 Aktive Sperren haben absoluten Vorrang

Wenn ein System-Hinweis, System-Reminder oder Developer-Hinweis `Plan Mode`, `READ-ONLY`, `STRICTLY FORBIDDEN`, `ZERO exceptions` oder sinngleiche Formulierungen enthält:

**ERLAUBT:**

- Lesen, Suchen, Analysieren
- Rückfragen stellen
- Plan erstellen
- offene Punkte ordnen und dokumentieren

**VERBOTEN (ohne Ausnahme):**

- Dateien ändern (`apply_patch`, Schreib-Bash-Befehle)
- Versionen erhöhen
- Commits erzeugen
- Branches ändern oder pushen
- GitHub-Mutationen (Issues erstellen/editieren/Labels ändern/Kommentare posten/Issues schließen oder öffnen/PRs erstellen oder verändern)
- Abschlussschritte (Versionsbump, Changelog, Manual, Commit, Push, Issue-Abschluss)
- Laufende Arbeit noch schnell fertigstellen

### 3.2 Arbeitsstand unter Modussperre

Der aktive Arbeitsstand wird bei Modussperre eingefroren:

- Er darf nur noch dokumentiert, geordnet, priorisiert und geplant werden
- Er darf NICHT umgesetzt, abgeschlossen, committed oder gepusht werden
- Diese Regel ist niemals eine Erlaubnis, eine aktive Modussperre zu umgehen

### 3.2.1 Additive Plan-Dokumentationsausnahme (lokal, eng begrenzt)

- Diese Ausnahme gilt NUR innerhalb dieser Repository-Regeln und hebt NIEMALS höher priorisierte System- oder Developer-Sperren auf.
- Wenn ausschließlich der repository-interne Plan-Modus aktiv ist und KEINE höher priorisierte globale Schreibsperre mit Formulierungen wie `READ-ONLY`, `ZERO exceptions`, `STRICTLY FORBIDDEN` oder sinngleich aktiv ist, DARF ausschließlich `./.opencode/plan_state.md` zur Plan-/Arbeitsstand-Dokumentation beschrieben werden.
- Diese Ausnahme dient ausschließlich der Plan-/Arbeitsstand-Dokumentation.
- Wenn eine höher priorisierte Schreibsperre jede Dateiänderung verbietet, darf auch `./.opencode/plan_state.md` NICHT geschrieben werden. In diesem Fall MUSS der Arbeitsstand vollständig im Chat dokumentiert und nach Ende der Sperre zuerst in `./.opencode/plan_state.md` synchronisiert werden.
- VERBOTEN bleiben alle anderen Dateiänderungen, Commits, Pushes, GitHub-Mutationen und Abschlussaktionen.

### 3.3 Pflicht-Checkpoint vor jeder Mutation

Vor jeder schreibenden Aktion MUSS der Agent prüfen:

1. Ist ein System-/Developer-Hinweis aktiv, der nur Lesen/Planen erlaubt?
2. Ist `Plan Mode` oder `READ-ONLY` aktiv?
3. Betrifft die Aktion eine Mutation an Dateien, Git, GitHub, Konfiguration oder persistentem Zustand?
4. Beruht die geplante Mutation ausschließlich auf einer älteren `GO`-/Issue-Freigabe aus dem Verlauf?
5. Gibt es inzwischen eine neuere Nutzeranweisung mit Analyse-, Plan-, Read-Only- oder andersartigem Scope?

Wird eine dieser Fragen mit `ja` beantwortet: Aktion UNTERLASSEN.

Wird Frage 4 mit `ja` oder Frage 5 mit `ja` beantwortet:

- alte Freigabe NICHT weiterverwenden
- keine Mutation ausführen
- neuen Auftrag nur nach aktuellem Scope behandeln

### 3.4 Pflichtantwort bei aktiver Sperre

Bei jeder operativen Anfrage unter aktiver Sperre MUSS der Agent sinngemaäß antworten:

> „Schreibsperre aktiv – ich liefere nur Analyse/Plan."

---

## ABSCHNITT 4 – GO-BEFEHL (EINZIGE DEFINITION)

Der Befehl `go` oder `GO` ist ausschließlich ein Ausführungssignal.

`GO` ist immer scope-gebunden und niemals global auf spätere, andersartige Aufträge übertragbar.

Im Modus **Plan** wird `go` ignoriert.

Im Modus **Build** aktiviert `go` den vollständigen Ablauf aus
**ABSCHNITT 1 – PFLICHT-AUSFÜHRUNGSFLUSS**.

Der Agent darf danach nicht erneut nachfragen, sondern muss alle offenen Aufgaben aus der aktuellen ToDo-Liste und `./.opencode/plan_state.md` gemäß Abschnitt 1 vollständig bearbeiten, prüfen, versionieren, committen, nach `main` pushen, das Ergebnis melden und das definierte Abschlusssignal ausführen.

Der GO-Befehl enthält bewusst keine eigene Ablaufdefinition. Maßgeblich ist immer Abschnitt 1.

**VERBOTEN:** Nach dem ersten Paket stoppen, solange kein echter Blocker existiert.

**Wenn mehrere Pakete sinnvoll sind**:

- Erstes Paket committen und pushen
- Verbleibende Aufgaben explizit als offen benennen
- Automatisch mit dem nächsten Paket fortfahren

**GO darf NICHT:**

- Ausführung unterbrechen
- Fragen auslösen
- Weitere Verarbeitung pausieren oder verzögern

### 4.1 Scope-Bindung von GO (PFLICHT)

- Der Befehl `go` / `GO` bezieht sich ausschließlich auf den unmittelbar davor aktiven und thematisch passenden Auftrag.
- `GO` aktiviert NICHT automatisch frühere, andersartige oder bereits durch neue Nutzeranweisungen abgelöste Aufgaben.
- Wenn nach einer früheren `GO`-Freigabe ein neuer Auftrag mit anderem Scope beginnt, ist die frühere `GO`-Freigabe automatisch ungültig.
- `GO` darf nur ausgeführt werden, wenn die letzte einschlägige Nutzeranweisung tatsächlich eine Umsetzungsfreigabe ist.
- Wenn die letzte relevante Nutzeranweisung stattdessen Analyse, Planung, Read-Only oder „noch keine Umsetzung“ verlangt, hat diese Anweisung immer Vorrang.

**Kernregel:**
Alte `GO`-/Issue-Freigaben verfallen automatisch, sobald ein neuer Nutzerauftrag mit anderem Scope oder mit Analyse-/Read-Only-Vorgaben beginnt.

---

## ABSCHNITT 5 – AUTONOME AUSFÜHRUNG NACH FREIGABE

### 5.1 Grundsatz

Wenn der Nutzer die Umsetzung explizit freigibt, gilt dies als vollständige Arbeitsanweisung.

Beispiele:

- `go` / `GO` im Build-Modus
- „alle Issues umsetzen“
- „arbeite alle offenen Punkte ab“
- „setze die geplanten Aufgaben um“
- „alle Issues außer #X umsetzen“

Nach einer solchen Freigabe arbeitet der Agent ohne weitere Rückfragen gemäß
**ABSCHNITT 1 – PFLICHT-AUSFÜHRUNGSFLUSS**.

### 5.2 Keine Zwischenbestätigungen

Während einer freigegebenen Ausführung sind verboten:

- Schritt-für-Schritt-Bestätigungen
- Rückfragen zur Priorisierung
- Rückfragen zur Paketbildung
- Auswahlmenüs für Zwischenschritte
- erneute Nachfrage, ob wirklich umgesetzt werden soll

### 5.3 Erlaubte Unterbrechungen

Der Agent darf nur unterbrechen, wenn ein echter Blocker vorliegt:

- notwendige Informationen fehlen und kein sinnvoller Fortschritt möglich ist
- externe Zugänge oder Zugangsdaten fehlen
- mehrere technisch gültige Wege mit deutlich unterschiedlichem Risiko bestehen
- eine destruktive oder schwer rückgängig zu machende Aktion erforderlich wäre

In allen anderen Fällen ist eine sinnvolle Annahme zu treffen und weiterzuarbeiten.

### 5.4 Multi-Issue-Ausführung

Bei mehreren Issues oder Aufgaben gilt:

- sequenziell abarbeiten
- ein Issue vollständig abschließen, bevor das nächste begonnen wird
- ausgeschlossene Issues überspringen
- alle übrigen freigegebenen Issues automatisch weiterbearbeiten
- keine erneute Freigabe zwischen den Issues einholen

Issues mit dem Label `rememberme` bleiben ausgeschlossen, sofern eine andere Regel dies bereits festlegt.

### 5.5 Berichterstattung

Der Agent berichtet nur:

- nach Abschluss eines vollständigen Issues oder logischen Arbeitsblocks
- am Ende aller freigegebenen Aufgaben
- bei einem echten Blocker

Berichte dürfen keine Rückfragen enthalten, außer wenn ein Blocker gemäß 5.3 vorliegt.

### 5.6 Freigaben gelten nicht kontextübergreifend

- Eine Ausführungsfreigabe gilt niemals kontextübergreifend.
- Sie darf nicht auf spätere, andersartige Nutzeraufträge übertragen werden.
- Sobald ein neuer Auftrag mit anderem Scope beginnt, MUSS für diesen neuen Auftrag wieder separat geprüft werden, ob überhaupt eine Ausführungsfreigabe vorliegt.

## ABSCHNITT 6 – PLAN-MODUS

### 6.1 Verhalten im Plan-Modus

Wenn Plan-Modus aktiv ist:

- Detaillierten Plan erstellen und alle Aufgaben anzeigen
- Aufgaben logisch gruppieren
- Auf explizite Nutzerfreigabe warten, bevor etwas umgesetzt wird (keine Dateiänderungen, keine Commits, keine Pushes)

### 6.1.1 Lokale Dokumentationsausnahme fuer `plan_state.md`

- Zusaetzlich zu 6.1 gilt: `./.opencode/plan_state.md` darf im Plan-Modus beschrieben werden, sofern keine hoeher priorisierte Schreibsperre aktiv ist.
- Diese Ausnahme ist abschliessend. Es gibt keine weitere Ausnahme fuer andere Dateien.
- Wenn eine hoeher priorisierte Schreibsperre aktiv ist, wird im Plan-Modus kein lokaler Plan-State geschrieben. Stattdessen wird der Arbeitsstand ausschließlich im Chat dokumentiert und nach Ende der Sperre zuerst in `./.opencode/plan_state.md` synchronisiert.

**VERBOTEN:** Nach Planpräsentation proaktiv nach Issues fragen oder Issue-Triage anbieten.

### 6.2 Plan-Modus darf aktive Build-Ausführung nicht unterbrechen

- Läuft bereits eine freigegebene Build-Ausführung, bleibt diese bis zu einem logischen Abschlusspunkt aktiv.
- Ein späterer Wechsel in den Plan-Modus darf diese laufende Ausführung NICHT rückwirkend stoppen oder als Read-Only umdeuten.
- Neue Plan-Anfragen während laufender Build-Ausführung werden als offene Folgepunkte im aktiven Arbeitskontext dokumentiert.
- Die laufende Build-Ausführung bleibt im aktiven Arbeitskontext bestehen, bis der aktuelle logische Block abgeschlossen ist.
- Nur ein explizites Abbruchsignal gemäß Abschnitt 2.4 kann eine laufende Build-Ausführung zugunsten von Plan-Arbeit unterbrechen.

### 6.3 Build-Modus darf aktive Plan-Arbeit nicht unterbrechen

- Läuft bereits aktive Plan-Arbeit, darf ein späterer Build-/GO-Befehl diese nicht abbrechen.
- Die aktuell laufende Plan-Arbeit muss zuerst einen logischen Abschlusspunkt erreichen.
- Der Build-/GO-Befehl wird als offener Folgepunkt im aktiven Arbeitskontext dokumentiert.
- Nach Abschluss der laufenden Plan-Arbeit wird dieser offene Folgepunkt als nächste Aktion bearbeitet.
- Eine sofortige Unterbrechung erfolgt nur, wenn der Nutzer dies ausdrücklich anweist.

### 6.4 Plan-Aufträge entwerten alte GO-Freigaben

- Beginnt ein neuer Auftrag im Plan-Modus oder unter aktiver Read-Only-/Modussperre, verlieren frühere `GO`-/Issue-Freigaben automatisch ihre Gültigkeit für diesen neuen Auftrag.
- Der Agent darf in diesem Fall frühere Ausführungsfreigaben nicht wiederaufgreifen.
- Der neue Plan-/Analyseauftrag ist ausschließlich nach den aktuellen Vorgaben zu behandeln.

## ABSCHNITT 7 – BULK-VERARBEITUNG UND KONTEXT-MANAGEMENT

### 7.1 Allgemeine Regel (KRITISCH)

- **NIEMALS** alle Dateien gleichzeitig laden oder analysieren.
- Dateien IMMER in kleinen Stapeln oder einzeln verarbeiten.

### 7.2 HTML-/Template-Analyse

- Jeweils NUR eine Datei verarbeiten.
- Mehrere Templates NICHT vorab in den Kontext laden.
- Dateilektüre auf relevante Abschnitte beschränken, wo möglich.

### 7.3 Iterative Verarbeitungsstrategie

Für Aufgaben wie „alle HTML-Dateien analysieren", „alle Templates prüfen", „Projektstruktur validieren":

1. Dateiliste zuerst ermitteln
2. Dateien einzeln iterieren
3. Jede Datei unabhängig analysieren
4. Ergebnisse inkrementell zusammenfassen
5. NIEMALS vollständige Dateiinhalte im Kontext ansammeln

### 7.4 Ausgabe-Beschränkungen

- Vollständige Dateiinhalte NUR auf explizite Anforderung ausgeben
- Standard-Ausgabe: Checkliste und Ergebnisstatus; Fehler, relevante Snippets und Zeilenreferenzen nur bei Blockern, Sicherheitsbefunden, Entscheidungen oder expliziter Anforderung.
- Zusammenfassungen vor vollständigen Dumps bevorzugen
- Diffs, Diff-Stats, Test-Logs und Tool-Rohdaten nur intern auswerten und im Chat auf eine kurze Ergebniszeile reduzieren, sofern kein Fehler oder Befund Details erfordert.

### 7.5 Token-Sicherheitsregeln

Wächst der Kontext zu groß:

- Verarbeitung STOPPEN
- Bisherige Erkenntnisse zusammenfassen
- In nächster Iteration fortfahren
- Große Diffs und vollständige Dateiausgaben vermeiden

### 7.6 HTML-Validierungsregeln

Beim Validieren der HTML-Struktur Fokus auf:

- Tag-Balance (`<div>`, `<main>`, `<section>`, `<details>`) 
- Korrekte Verschachtelung
- Eltern-/Kind-Hierarchie

Ignorieren: Styling, JavaScript, nicht zusammenhängender Inhalt.

### 7.6.1 Pflicht-Strukturpruefung fuer `influxbro/app/templates/index.html`

- Bei jeder Aenderung an `influxbro/app/templates/index.html` MUSS vor Abschluss der Aufgabe eine explizite Strukturpruefung durchgefuehrt werden.
- Pflichtumfang:
  - Balance und korrekte Verschachtelung von:
    - `<details>`
    - `<summary>`
    - `<div>`
    - Tabellencontainern wie:
      - `table_wrap`
      - `table_head`
      - `table_box`
- Besonders zu pruefen sind:
  - Dashboard-Section-Grenzen
  - Uebergaenge zwischen:
    - `analysis_section`
    - `outlier_section`
    - `raw_section`
    - `graph_section`
- Ziel:
  - keine fehlenden Closing-Tags
  - keine ueberzaehligen Closing-Tags
  - keine verschobenen Containergrenzen
  - keine Strukturfehler, die Rendering, Picker, Dialoge oder den App-Start beeintraechtigen
- Pflichtfolge:
  - Aenderungen an `index.html` gelten NICHT als abgeschlossen, wenn diese Strukturpruefung nicht erfolgt ist.
  - Strukturpruefungen MUESSEN bestehende, nicht zusammenhaengende Baseline-Auffaelligkeiten von neu durch die aktuelle Aenderung verursachten Strukturfehlern unterscheiden, soweit dies mit Diff-Scope oder Vorwissen moeglich ist.
  - Bereits vorhandene, nicht zusammenhaengende Strukturfehler blockieren den Abschluss nicht automatisch, MUESSEN aber im Abschlussbericht als verbleibendes Risiko genannt werden.
  - Der Abschlussbericht MUSS bei `index.html`-Aenderungen explizit nennen:
    - dass die Strukturpruefung ausgefuehrt wurde
    - welche Bereiche geprueft wurden
    - ob Auffaelligkeiten gefunden wurden

### 7.7 Parallelausführungsstrategie

**Erlaubt (nur bei klarer Unabhängigkeit):**

- Nicht zusammenhängende Dateien lesen
- Codebasis durchsuchen
- Offene GitHub-Issues prüfen
- Logs sammeln
- Relevante Tests lokalisieren

**Sequenziell PFLICHT wenn:**

- Aufgaben dieselben Dateien oder Module betreffen
- Eine Änderung das Design späterer Änderungen beeinflussen kann
- API, UI und Konfigurationsverhalten zusammenhängen
- Unsicherheit über Abhängigkeitsreihenfolge besteht

**Alle Schreiboperationen sind IMMER strikt sequenziell auszuführen.**

### 7.8 Rate-Limit und API-Stabilität (PFLICHT)

Externe APIs (z. B. Alibaba Qwen) können Anfragen bei zu schnellem Traffic ablehnen.

**A. Globale Anfragenkontrolle:**

- ALLE externen API-Aufrufe MÜSSEN über einen zentralen Request-Handler geleitet werden.
- Direkte Parallelaufrufe aus mehreren Modulen sind VERBOTEN.

**B. Parallelitätslimit:**

- Maximal 2 gleichzeitige API-Anfragen
- Durchsetzung via Semaphor/Queue ist NICHT optional

**C. Request-Glättung:**

- Mindestverzögerung zwischen Anfragen: 300 ms (empfohlen: 400–600 ms)
- Burst-Traffic ist jederzeit zu verhindern

**D. Retry-Strategie:**

- Bei HTTP 429: Exponentieller Backoff: 1 s → 2 s → 4 s → 8 s (max 10 s) + Jitter (0–500 ms)
- Sofortiger Retry OHNE Verzögerung ist VERBOTEN

**E. Fail-Safe:**

- Bei wiederholten 429-Fehlern: Parallelität auf 1 reduzieren, Verzögerung auf 800–1200 ms erhöhen

**Grundsatz:** Stabilität hat Vorrang vor Geschwindigkeit.

## ABSCHNITT 8 – ISSUE-VERWALTUNG

### 8.1 Grundregeln für Issues

- Issues werden niemals automatisch geprüft, geladen, triagiert oder gestartet.
- Issues werden ausschließlich auf expliziten Befehl des Nutzers geprüft oder abgearbeitet.
- Gültige Auslöser sind in Abschnitt 16.2 definiert.

- Bei einer neuen fachlichen Anfrage fragt der Agent, ob daraus ein Issue erstellt oder die Änderung direkt umgesetzt werden soll.
- Bezieht sich die Anfrage eindeutig auf ein bestehendes Issue, arbeitet der Agent direkt daran weiter, ohne erneut zu fragen.

- Offene Aufgaben in der aktiven ToDo-Liste und offene Punkte in `./.opencode/plan_state.md` blockieren standardmäßig den Start neuer Issues.
- Bei blockiertem Zustand meldet der Agent die offenen Punkte und startet kein neues Issue.
- Neue GitHub-Issues dürfen nur dann angelegt, gestartet oder bearbeitet werden, wenn das aktuell aktive Issue vollständig abgeschlossen ist. Ein aktives Issue gilt erst dann als abgeschlossen, wenn alle zugehörigen offenen Punkte in der aktiven ToDo-Liste und in `./.opencode/plan_state.md` erledigt sind, das Issue auf GitHub auf `status/done` gesetzt und geschlossen wurde und die vorgesehene Abschlussmeldung bzw. der vollständige Abschlussfluss ausgeführt wurde. Vorher ist das Anlegen oder Beginnen eines neuen Issues verboten.
- Der Nutzer darf die Sperre ausdrücklich überschreiben, z. B. mit:
  - „Issue #X trotzdem starten“
  - „bestehende Todos zurückstellen"
  - „Priorität auf dieses Issue ändern“

- `rememberme`-Issues sind bei jeder Prüfung, Triage oder Sammelumsetzung strikt zu überspringen, auch wenn der Nutzer nach „allen Issues“ fragt.

### 8.2 Issue-Status-Labels (PFLICHT)

Genau EIN Status-Label pro Issue zu jedem Zeitpunkt:

- `status/open`
- `status/in_progress`
- `status/done`
- `status/cancelled`

Status-Labels schließen sich gegenseitig aus. Das vorherige Label MUSS entfernt werden, bevor ein neues gesetzt wird.

- Wiedereröffnetes Issue: `status/done` und `status/cancelled` entfernen, `status/open` setzen.
- Geschlossenes Issue: DARF NICHT `status/open` oder `status/in_progress` behalten.
- Bei Divergenz zwischen GitHub-Zustand und Status-Label: sofort korrigieren.

### 8.3 Prioritätsgesteuerte Abarbeitung

- Offene Issues IMMER in Reihenfolge ihrer Priorität abarbeiten, höchste zuerst.
- Issues ohne Priorität erst, wenn keine höher priorisierten sinnvoll bearbeitbar sind.
- Gleichpriorisierte Issues: nach fachlicher Abhängigkeit, dann Alter, dann Aufwand.
- Abweichung von Prioritätsreihenfolge nur bei technischer Blockade, fehlenden Informationen oder ausdrücklicher Nutzeranweisung – immer kurz begründen.

**Prioritäts-Mapping:**

| Label | Rang |

|---|---|
| `P1`, `Critical`, `Highest`, `1` | Sofort bevorzugt |
| `P2`, `High`, `2` | Nach P1 |
| `P3`, `Medium`, `Normal`, `3` | Nach P2 |
| `P4`, `Low`, `4` | Nach P3 |
| Keine Priorität | Zuletzt |

### 8.4 Issues laden und synchronisieren

```bash
gh issue list --repo <owner>/<repo> --state open --limit 200
gh issue list --repo <owner>/<repo> --state open --label type/bug --limit 200
gh issue list --repo <owner>/<repo> --state open --label type/enhancement --limit 200
```

Offene Items in lokale ToDo-Liste und `./.opencode/plan_state.md` aufnehmen (mit `#<id>` + Titel).

### 8.5 Shortcut „prüfe Issues"

Gibt der Nutzer exakt `prüfe Issues` ein:

Zuerst OHNE vorherige Issue-Liste diese Auswahl stellen:

1. `Alle Issues umsetzen` – alle offenen Issues sofort ohne weitere Nachfragen umsetzen
2. `Auswahl treffen` – Issue-Liste anzeigen (gruppiert nach `type/bug` vs. `type/enhancement`), Nutzer wählt aus

Die Issue-Liste darf VOR dieser Auswahl NICHT geladen oder angezeigt werden.

### 8.6 Triage-Flow

- Issues grouped nach `type/bug` und `type/enhancement` anzeigen
- Pro Issue Entscheidung ermöglichen: jetzt umsetzen / zurückstellen / ablehnen
- Entscheidungen auf GitHub spiegeln:
  - Jetzt umsetzen: `status/in_progress`, Kommentar „zur Umsetzung ausgewählt"
  - Zurückstellen: `status/open`, Kommentar „zurückgestellt"
  - Ablehnen: `status/cancelled`, Kommentar mit Begründung, Issue schließen
- Nur explizit als „jetzt umsetzen" gewählte Issues in ToDo-Liste und `plan_state.md` aufnehmen

## ABSCHNITT 9 – AUFGABEN-TRACKING

### 9.1 ToDo-Liste – Sichtbarkeit (PFLICHT)

- Für jeden Auftrag IMMER eine ToDo-Liste erstellen und sichtbar halten.
- Bei neuen Anforderungen: bestehende ToDo-Liste sofort erweitern.
- Genau ein Eintrag trägt den Status `in_progress`.
- Einträge sofort als `erledigt` markieren, sobald abgeschlossen.
- Alle ToDo-Einträge MÜSSEN umgesetzt sein, bevor Fertigstellung erklärt wird.
- **Die aktive ToDo-Liste wird sichtbar gehalten.** Eine sichtbare Tool-ToDo-Liste reicht aus; ein zusätzlicher manueller Chat-Block ist nur bei Blockern, Abschlussstatus oder fehlender Tool-Sichtbarkeit erforderlich. Regeln siehe Abschnitt 2.2 Sichtbarkeitsregel.

**Statussymbole (einheitlich für alle drei Listen):**

| Symbol | Bedeutung |

|---|---|
| ✅ | Erledigt |
| 🔄 | In Bearbeitung (`in_progress`) |
| ⬜ | Ausstehend |
| ❌ | Fehlgeschlagen / blockiert |
| ⏸ | Eingefroren (aktive Modussperre) |

### 9.2 Plan-Zustand persistieren

- `./.opencode/plan_state.md` nach jeder bedeutsamen Änderung aktualisieren.
- Inhalt: aktuelle ToDo-Liste (mit Status), offene Entscheidungen/Fragen, vereinbarte Planänderungen.
- Lokal halten, NICHT committen.
- Beim Sitzungsstart: `plan_state.md` laden und ausstehende Punkte wiederherstellen.

### 9.3 Anforderungslog (Fallback ohne GitHub)

Falls GitHub-Issues nicht verfügbar: Anforderungen in `./.opencode/requests_log.md` dokumentieren.

- Format: Datum + Beschreibung + Status (`offen`, `in_progress`, `erledigt`, `abgebrochen`)
- Lokal halten, NICHT committen.
- Status bei Start/Abschluss/Abbruch aktualisieren, optional mit Commit-Hash.

## ABSCHNITT 10 – TOMBSTONE-PROZESS (UI-KOMPONENTEN-ENTFERNUNG)

### 10.1 Pflicht-Auslöser

Beim Entfernen, Ersetzen oder Stilllegen von UI-Elementen, Templates, Buttons, Tabellen, Dialogen, Frontend-Aktionen, API-gebundenen UI-Funktionen oder Routen MUSS der Agent automatisch den vollständigen Tombstone-Workflow ausführen.

**VERBOTEN:** UI-Entfernungen als reine Löschaufgabe behandeln.

### 10.2 Pflichtablauf

**Schritt 1 – UI-Relevanz prüfen:**
Als UI-relevant gelten: Templates (`*.html`), Inline-JavaScript, CSS/Selektoren, Buttons/Menüs/Dialoge/Tabellen/Karten/Filter/Formulare, API-Aufrufe aus UI-Aktionen, Routen mit UI-Bezug.

**Schritt 2 – Abhängigkeiten vollständig ermitteln:**
Vor jeder Entfernung prüfen: HTML-/Template-Referenzen, JavaScript-Funktionen, Event-Handler/Listener, CSS-Klassen/IDs/Selektoren, Fetch-/API-Aufrufe, Backend-Endpunkte mit UI-Bezug, Ingress-/Routing-Auswirkungen, Dokumentation/MANUAL/UI-Hinweise.

**Schritt 3 – Tombstone anlegen:**
`.tombstones.yml` MUSS im selben Arbeitsgang ergänzt werden mit mindestens:

- `path`, `tombstone_id`, `reason`, `owner`
- `impacted_selectors`, `impacted_actions`
- `migration_plan`, `route_plan`, `ci_reference`

Code-Kommentar an der Entfernungsstelle: `// TOMBSTONE: TS-XXXX – Beschreibung`

**Schritt 4 – Folgecode bereinigen:**
Funktionen, Selektoren, Event-Handler, API-Aufrufe oder Routen, die ausschließlich zum entfernten Element gehören, MÜSSEN entfernt oder stillgelegt werden. Noch anderweitig verwendete Funktionen dürfen NICHT entfernt werden. Bei Unklarheit: markieren und prüfen, nicht stillschweigend löschen.

**Schritt 5 – Migrations- und Ersatzpfad dokumentieren:**
Wenn ersetzt: Tombstone-Eintrag nennt neuen Pfad/Funktion/Route. Wenn Route entfällt: Redirect-Prüfung erforderlich. Bei HA Ingress: relative Pfade verwenden.

**Schritt 6 – Abschlussbericht erweitern:**
Bericht enthält: betroffene UI-Komponente(n), Tombstone-ID(s), entfernte Folgefunktionen, bewusst beibehaltene Restfunktionen mit Begründung, Migrations-/Redirect-Hinweise.

### 10.3 Verifikations-Checkliste (Pflicht)

- [ ] `.tombstones.yml` Eintrag vorhanden, `tombstone_id` eindeutig
- [ ] `// TOMBSTONE: <id>` Kommentar an Entfernungs-/Opt-out-Stelle
- [ ] Keine toten Selektoren/CSS-Klassen
- [ ] Keine toten JS-Handler/Listener
- [ ] Keine UI-Calls auf entfernte API-Endpunkte
- [ ] Ingress/Routes: keine 404s, ggf. Redirect/Migration dokumentiert
- [ ] `py_compile` bestanden
- [ ] Relevante `pytest` bestanden
- [ ] UI-Smoke-Test unter Home Assistant Ingress

### 10.4 Verboten

- UI löschen ohne Tombstone
- API entfernen ohne Migration
- Stille Breaking Changes
- Nur HTML löschen ohne JS/CSS/API zu prüfen
- Nur Button entfernen ohne Handler zu prüfen
- UI-Aktion löschen ohne Backend-Endpunkt zu prüfen
- Routen entfernen ohne Migrations-/Redirect-Prüfung

## ABSCHNITT 11 – UI-PICKER-EINDEUTIGKEIT (PICKKEY-PFLICHT)

- Jedes sichtbare, support-relevante UI-Element MUSS eine stabile `data-ui`-Kennung besitzen.
- Jedes sichtbare UI-Element MUSS zusätzlich eine eindeutige `data-ib-pickkey`-Kennung besitzen.
- Gilt für: Buttons, Links, Inputs, Selects, Checkboxen, Labels, Sektionen (`details/summary`), Cards, Panels, Tabellen inkl. Toolbars/Resize-Handles/Filterleisten/Rowcounts, Dialoge/Popups/Overlays, dynamisch erzeugte UI-Elemente.
- Dynamisch erzeugte sichtbare Elemente MÜSSEN `data-ui` und `data-ib-pickkey` beim Erzeugen setzen.
- S-Picker-Ausgabe liefert kanonischen Referenztext: `<PICK:<Seite>|<pickkey>>`.
- Referenzmodell v1: `<PICK:<Seite>|v=1;pk=<pk>;ik=<ik>>` (`data-ib-pickkey` = `pk` stabil/release-tauglich, `data-ib-instancekey` = `ik` zur Laufzeit eindeutig).
- Fallback-Referenzen ohne Pickkey sind nur Migrationszustand, kein akzeptabler Endzustand.
- Bei UI-Änderungen: betroffene Elemente auf `data-ib-pickkey` nachziehen.
- Bei UI-Entfernungen: Tombstone-Prozess bleibt weiterhin Pflicht.

## ABSCHNITT 12 – SPEICHER-POLICY (GLOBAL vs. PROFIL)

Diese Policy gilt für ALLE Seiten und Funktionen der App.

### 12.1 Global/Server-seitiger Zustand

Server-seitig speichern, wenn der Wert das funktionale Verhalten oder den Datenumfang ändert und daher geräteübergreifend identisch sein muss.

Beispiele: Quellauswahl (`measurement`, `field`, `measurement_filter`, `entity_id`, `friendly_name`), Zeitauswahl (`range`, `start`, `stop`), ausgewählte Ausreißertypen, effektiver Analyse-Startwert, funktionale Schwellenwerte.

**Regel:** Ändert ein Wert, welche Daten abgefragt, gefiltert, analysiert, importiert, exportiert, wiederhergestellt oder verarbeitet werden, gehört er zum globalen/server-seitigen Zustand.

### 12.2 Profilbasierter UI-Zustand

Im aktiven UI-Profil speichern, wenn der Wert nur Darstellung, Ergonomie oder Layout ändert.

Beispiele: Abschnitt geöffnet/geschlossen (`*_open`), Tabellenhöhen, Splitter-/Resize-Werte, Spaltenbreiten, Wrap/No-Wrap, Spaltensichtbarkeit, Popup-Größen, Schriftgrößen/Zeilendichte.

**Regel:** Ändert ein Wert nur das Aussehen oder Gefühl der UI, nicht jedoch welche Daten verarbeitet werden, gehört er zum UI-Profil.

### 12.3 Trennungsregel

- Funktionaler globaler Zustand und profilbasierter UI-Zustand MÜSSEN technisch getrennt bleiben.
- Browser-lokaler Zustand darf server-seitigen funktionalen Zustand NICHT überschreiben.
- UI-Profilzustand darf globale funktionale Auswahlen NICHT überschreiben.

## ABSCHNITT 13 – REPO-LAYOUT UND CODE-STIL

### 13.1 Repository-Struktur

- `repository.yaml`: MUSS im Repo-Root verbleiben (HA Add-on Repository-Anforderung).
- `influxbro/config.yaml`: Add-on-Metadaten (Versionierung, Slug, Ingress-Einstellungen).
- `influxbro/Dockerfile`: Container-Build.
- `influxbro/run.sh`: Add-on-Einstiegspunkt (liest `/data/options.json`).
- `influxbro/app/app.py`: Flask-App.
- `influxbro/app/templates/*.html`: UI-Templates (Inline-JS/CSS).

**Einschränkungen:**

- Add-on-Verzeichnis NICHT umbenennen und `slug` in `influxbro/config.yaml` NICHT ändern.
- Home Assistant erkennt Updates über das `version:`-Feld in `influxbro/config.yaml`.
- Container erwartet HA-Mounts: `/data` (beschreibbar, persistent), `/config` (nur lesbar in diesem Add-on).

### 13.2 Allgemeiner Code-Stil

- Änderungen minimal und konsistent mit bestehenden Mustern (Flask + Inline-Templates).
- Lesbarkeit vor Cleverness; dieses Add-on wird von Home Assistant-Nutzern betrieben.
- Keine neuen Abhängigkeiten ohne klare Begründung.

### 13.3 Python

- Einrückung: 4 Leerzeichen.
- Zeichenketten: doppelte Anführungszeichen für nutzerseitige Texte bevorzugen.
- F-Strings für Formatierung verwenden.
- Zeilen möglichst kurz halten (~100 Zeichen).
- Imports gruppieren: 1) Standardbibliothek, 2) Drittanbieter, 3) lokale Imports. Ein Import pro Zeile. Unbenutzte Imports vermeiden.
- Type-Hints für neue/geänderte Funktionen hinzufügen.
- Für JSON-ähnliche Payloads: `dict[str, Any]` und an der Grenze validieren/normalisieren.

**Benennung:**

- Funktionen/Variablen: `snake_case`
- Konstanten: `UPPER_SNAKE_CASE`
- Flask-Route-Handler: kurze, verbnahe Namen (`measurements`, `fields`, `api_test`)
- Private Hilfsfunktionen: Präfix `_`

### 13.4 Fehlerbehandlung und API-Antworten

- Flask-Routen als Vertrauensgrenzen behandeln: erforderliche Parameter validieren, Typen normalisieren, klare Fehler mit passenden HTTP-Status-Codes zurückgeben.
- Einheitliches JSON-Envelope: Erfolg `{"ok": true, ...}`, Fehler `{"ok": false, "error": "..."}`.
- Keine breiten `except Exception` in reinen Hilfsfunktionen; an HTTP-Grenze akzeptabel, aber mit nützlichen Fehlermeldungen.

### 13.5 Sicherheit/Sicherheit im Code

- Niemals Geheimnisse (Token/Passwort) loggen oder zurückgeben.
- Nutzereingaben bei Pfaden einschränken; Traversal-Schutzfunktionen wie `_resolve_cfg_path()` erweitern, nicht umgehen.
- Löschung muss Opt-In bleiben: durch `ALLOW_DELETE` abgesichert, exakte Bestätigungsphrase erforderlich.

### 13.6 Flask + InfluxDB

- InfluxDB-v2-Clients kontextverwaltet und geschlossen (`with v2_client(cfg): ...`).
- Timeouts und SSL-Verifikation bei v1-Client konfigurierbar halten.
- Abfragegröße begrenzt halten (UI downsampled auf ~5000 Punkte); beibehalten oder verbessern.

### 13.7 Templates (HTML/JS/CSS)

- Allgemeine Template-, Ingress- und JavaScript-Grundregeln fuer Handbuch-/Dokumentationsspruenge sind in `influxbro/template-handbuch-rules.md` ausgelagert und dort vor entsprechenden Aenderungen zwingend zu lesen.
- Bei destruktiven Aktionen: Bestätigungs-UI beibehalten und zusätzliche Schutzmaßnahmen ergänzen.

**UI-Design-Standard:**

- Vor dem Hinzufügen oder Ändern von GUI-Elementen ist generell immer diese Regeln zu beachten und die Datei zu lesen: `influxbro/Template.md`. Diese Vorgaben sind zwingend zu beachten und müssen ohne Ausnahme befolgt werden.
- Zusätzlich sind abhängig vom Umbau an der GUI die sepezifischen Regeln für GUI Elemente zu lesen und zwingend zu beachten. Die Vorgaben müssen befolgt werden:
  a) für Dialoge:          `influxbro/template-dialog-rules.md`
  b) für Tooltips:         `inluxbro/template-tooltips-rules.md`
  c) für Messwertauswahl:  `influxbro/template-measurement-select-rules.md`
  d) für Sections:         `influxbro/template-section-rules.md`
  e) für Picker:           `influxbro/template-picker-rules.md`
  f) für Tabellen:         `influxbro/template-tables-rules.md`
  g) für Handbuch / Dokumentationssprünge: `influxbro/template-handbuch-rules.md`
- Konsistente Layout-Muster über alle UI-Komponenten hinweg.
- Konsistentes Spacing, konsistente Card-/Layout-Struktur, konsistente Benennung von Klassen und IDs.
- UI-Komponenten auf Container-Ebene UND für alle Kind-Elemente validieren.

### 13.8 Abhängigkeiten und Kompatibilität

- Werden Python-Abhängigkeiten geändert: `influxbro/requirements.txt` in derselben Änderung aktualisieren.
- Pro veröffentlichter Add-on-Version die getestete Home Assistant Core-Version in `influxbro/CHANGELOG.md` dokumentieren.

## ABSCHNITT 14 – TESTEN

### 14.1 Standard-Testhost

- `http://192.168.2.200:8099` für alle Home Assistant-gestützten Live-Integrationstests verwenden.
- Localhost nur für isolierte lokale Entwicklung oder container-lokale Verifikation.

### 14.2 Playwright E2E-Tests

- Konfiguration: `playwright.config.js` (baseURL: `http://192.168.2.200:8099`)
- Tests: `tests/e2e/*.spec.js`
- Ausführen: `npx playwright test`
- Chat-Ausgabe: Playwright-/UI-/Live-Test-Start nur mit einer Zeile zu Zweck und erwarteter Antwortzeit/Timeout melden, z. B. `UI-Test laeuft: Playwright, Timeout 300s.` Erfolgreiche Ausgaben ausblenden; Ergebnis nur als `passed` oder `failed` in der Checkliste melden. Einzelne Browser-Schritte, Locator-Details, Screenshots, Traces und Polling-Details nur bei Fehlschlag oder auf Nachfrage nennen.
- Smoke-Tests nur ausfuehren, wenn die Aenderung sicherheits-, start-, API-, Update-, UI-kritisch oder groesser ist, wenn die erste Umsetzung fehlerhaft war, wenn vorherige Live-/Playwright-/Timeout-Probleme relevant sind oder wenn der Nutzer sie explizit verlangt. Sonst in der Checkliste als `skipped` mit Kurzgrund markieren.

### 14.3 Live-System-Tests (Pflichtablauf)

Vor dem Testlauf gegen das Live-System MUSS der Versionsstand geprüft werden:

1. Erwartete Version aus `influxbro/config.yaml → version` bestimmen
2. Live-Version prüfen: `GET ./api/info` und Version vergleichen
3. Stimmt die Version nicht überein: per Playwright automatisch auf neuestes Release aktualisieren, Add-on neu starten, Version erneut via `./api/info` verifizieren

**Prompt „teste auf dem echtsystem":**

1. Live-Version prüfen:

   ```bash
   curl -fsS http://192.168.2.200:8099/api/info | python3 -c "import json,sys; print(json.load(sys.stdin).get('version','unknown'))"
   ```

2. Mit Version in `influxbro/config.yaml` vergleichen
3. Stimmen die Versionen NICHT überein: Nutzer warnen, fragen ob nur API-Tests oder warten bis Live-System aktualisiert ist
4. Stimmen die Versionen ÜBEREIN: fragen ob zusätzlich Playwright E2E-Browser-Tests ausgeführt werden sollen
5. Bei Bestätigung: `npx playwright test` ausführen und Ergebnis kompakt als `passed` oder `failed` melden; Timeout/erwartete Antwortzeit vor Start nennen.

### 14.4 Robuster lokaler Start / Healthcheck (PFLICHT)

**VERBOTEN:** Feste kurze Sleep-Befehle als alleinige Bereitschaftsprüfung.

**PFLICHT:** Retry-Loop mit Healthcheck:

```bash
ready=0
for i in {1..20}; do
  if curl -fsS http://127.0.0.1:8099/api/info >/tmp/influxbro_info.json 2>/dev/null; then
    python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("/tmp/influxbro_info.json").read_text())
print(data.get("version", "unknown"))
PY
    echo "Dienst bereit"
    ready=1
    break
  fi
  echo "Warte auf lokalen Dienst... ($i/20)"
  sleep 1
done
```

Ein Dienst gilt NUR als bereit, wenn der Health-Endpunkt erfolgreich antwortet UND gültiges JSON zurückgibt. Port-Listening allein ist NICHT ausreichend.

**Beim Fehlschlagen:** `/tmp/influxbro_local.log` prüfen, Prozess-Existenz, Port 8099, Fehler klassifizieren (Startzeit, Absturz, Port-Problem, Health-Endpunkt-Fehler). Bereitschaft kann nicht bestätigt werden = Blocker, NICHT fortfahren als ob die App laufen würde.

### 14.5 Lokal ausführen (Docker)

```bash
mkdir -p .local-data
cat > .local-data/options.json <<'JSON'
{ "version": "dev", "allow_delete": false, "delete_confirm_phrase": "DELETE" }
JSON
docker run --rm -p 8099:8099 -v "$PWD/.local-data:/data" -v "$PWD:/repo:ro" influxbro:dev
```

### 14.6 Lokal ausführen (Python, ohne Docker)

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install flask influxdb-client influxdb PyYAML
export ALLOW_DELETE=false
export DELETE_CONFIRM_PHRASE=DELETE
export ADDON_VERSION=dev

python influxbro/app/app.py
```

### 14.7 Lint / Statische Prüfungen

Basisprüfungen (immer funktionsfähig):

```bash
python -m compileall influxbro/app/app.py
python -m py_compile influxbro/app/app.py
```

Empfohlenes Tooling:

```bash
python -m pip install ruff black
ruff check influxbro/app/app.py
black --check influxbro/app/app.py
```

### 14.8 Gezielte Tests

```bash
# Eine Datei
pytest tests/test_api_yaml_flow.py -q

# Ein Test per Node-ID
pytest tests/test_api_yaml_flow.py::test_load_influx_yaml_resolves_secret -q

# Teilmenge per Keyword
pytest -k measurements -q
```

### 14.9 Manuelle API-Smoke-Tests

```bash
curl -fsS http://localhost:8099/api/info | jq .
curl -fsS http://localhost:8099/api/config | jq .
```

---

## ABSCHNITT 15 – ABSCHLUSS-VERIFIKATION

Am Ende jeder Umsetzung MUSS der Agent explizit verifizieren, dass alle Anforderungen und alle ToDo-Einträge tatsächlich umgesetzt wurden.

Wenn ein geplanter Punkt nicht umgesetzt werden konnte (oder nur teilweise): explizit benennen:

- Was fehlt
- Warum es fehlt
- Was zur Fertigstellung benötigt wird

**Abschluss-Checkliste (PFLICHT VOR FERTIGMELDUNG):**

- [ ] Alle Anforderungen umgesetzt
- [ ] Alle ToDo-Einträge abgeschlossen
- [ ] Sicherheitsprüfung durchgeführt
- [ ] Erforderliche QA ausgeführt und bestanden
- [ ] Version in `influxbro/config.yaml` erhöht (wenn erforderlich)
- [ ] `influxbro/CHANGELOG.md` aktualisiert
- [ ] `influxbro/MANUAL.md` aktualisiert (wenn UI/Verhalten geändert)
- [ ] GitHub-Issue-Kommentar hinzugefügt
- [ ] Issue auf `status/done` gesetzt und geschlossen
- [ ] Commit erstellt
- [ ] Nach `main` gepusht
- [ ] Abschlusssignal ausgeführt
- [ ] `./.opencode/plan_state.md` geprüft, Nutzer über ausstehende Restpunkte informiert (KEINE automatische Issue-Triage anbieten)

---

## ABSCHNITT 16 – INTERAKTIONSREGELN

### 16.1 Numerische Auswahloptionen

Bei Auswahloptionen für den Nutzer:

- Immer nummerierte Optionen anbieten (1, 2, 3, …)
- Nutzer darf mit einer einzelnen Zahl antworten

### 16.2 Issue-Abarbeitung nur auf expliziten Befehl (PFLICHT)

**VERBOTEN:** Nach Fertigstellung einer Aufgabe proaktiv nach Issues fragen, Issue-Triage anbieten oder Issues automatisch starten.

Issues werden ausschließlich geprüft und gestartet, wenn der Nutzer eine der folgenden expliziten Formulierungen verwendet:

- `offene Issues abarbeiten`
- `prüfe Issues`
- `arbeite alle Issues ab`
- oder eine sinngleiche direkte Anweisung

**Sperrbedingung (ABSOLUT):** Liegen noch ToDo-Einträge mit Status `in_progress` oder `ausstehend` vor, ODER enthält `./.opencode/plan_state.md` noch offene Punkte, DÜRFEN keine neuen Issues gestartet werden – auch nicht auf explizite Anfrage des Nutzers. Der Agent antwortet stattdessen mit:

> "Es liegen noch offene Aufgaben vor – neue Issues können erst gestartet werden, wenn alle aktuellen Todos abgeschlossen sind."
>
> Offene Punkte: [Auflistung der ausstehenden Einträge]

### 16.3 Pflichtantwort bei Konflikt mit alten GO-Freigaben

Wenn ältere `GO`-/Issue-Freigaben im Gesprächsverlauf vorhanden sind, der aktuelle Auftrag aber Analyse, Planung, Read-Only oder einen anderen Scope verlangt, MUSS der Agent sinngemäß klarstellen:

> „Frühere GO-Freigaben werden nicht übernommen, weil ein neuer Analyse-/Read-Only- oder andersartiger Auftrag aktiv ist.“

Diese Klarstellung ist verpflichtend, bevor der Agent mit Analyse/Plan fortfährt.

## ABSCHNITT 17 – VOLLSTÄNDIGKEITSDEFINITION

**Eine Aufgabe gilt AUSSCHLIESSLICH als abgeschlossen, wenn ALLE folgenden Bedingungen erfüllt sind:**

1. Angeforderte Änderung tatsächlich angewendet
2. Alle Pflicht-QA-Prüfungen ausgeführt
3. Keine blockierenden Fehler vorhanden
4. Sicherheitsprüfung durchgeführt (bei HA Add-on Änderungen)
5. Version erhöht (wenn erforderlich)
6. CHANGELOG und MANUAL aktualisiert (wenn erforderlich)
7. Commit erstellt
8. Nach `main` gepusht
9. GitHub-Issue abgeschlossen (wenn vorhanden)
10. Abschlusssignal ausgeführt
11. `./.opencode/plan_state.md` geprüft, Nutzer über ausstehende Restpunkte informiert

Fehlt ein einziger Punkt: die Aufgabe ist NICHT abgeschlossen.
