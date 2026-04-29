
# AGENTS v3.1 – Stand: 2026-04-29

Sprache: Deutsch · Repository: influxbro · Typ: Home Assistant Add-on

## PRIORITÄTSREIHENFOLGE (ABSOLUT VERBINDLICH)

Bei Konflikten gilt immer diese Rangfolge:

1. Systemanweisungen der Plattform
2. Developer-Anweisungen
3. Modussperre (`Plan Mode` / `READ-ONLY`)
4. Regeln dieser Datei
5. Nutzerwunsch

Nutzerwünsche und Queue-Regeln dürfen niemals eine höhere Priorität erhalten als eine aktive Modussperre.

## ABSCHNITT 1 – PFLICHT-AUSFÜHRUNGSFLUSS

### 1.1 Repository-Verzeichnisprüfung (KRITISCH)

**PFLICHT:** Vor jeder Aktion MUSS der Agent prüfen, ob das Arbeitsverzeichnis folgende Einträge enthält:

- `influxbro/`
- `AGENTS.md`
- `repository.yaml`

Fehlt einer dieser Einträge: **SOFORT STOPPEN** und melden:
> „Falsches Arbeitsverzeichnis – Repository-Root erforderlich."

Diese Prüfung ist vor jeder Such-, Lese-, Schreib-, Git- oder Testaktion durchzuführen.

### 1.2 Pflichtablauf vor jeder Umsetzung

1.2.1 Schritt 1 – GitHub-Issues (NUR AUF EXPLIZITEN BEFEHL)

- GitHub-Issues werden NICHT automatisch geprüft, geladen oder gestartet.
- Issues werden ausschließlich geprüft und abgearbeitet, wenn der Nutzer dies explizit anweist (z. B. „offene Issues abarbeiten", „prüfe Issues").
- Solange ToDo-Einträge mit Status `in_progress` oder `ausstehend` existieren ODER Einträge in `.opencode/todo_plan.md` bzw. `.opencode/todo_build.md` vorhanden sind, dürfen KEINE neuen Issues gestartet werden – auch nicht auf explizite Anfrage. Der Agent meldet in diesem Fall den blockierten Zustand und listet die offenen Punkte auf.
- `rememberme`-Issues sind bei jeder Prüfung strikt zu überspringen, auch wenn der Nutzer nach „allen Issues" fragt.

1.2.2 Schritt 2 – Issue erstellen bei neuer Anfrage

- Ist die Anfrage NEU, MUSS ein GitHub-Issue erstellt werden, BEVOR mit der Umsetzung begonnen wird.
- Titel: kurze Zusammenfassung
- Body: vollständige Beschreibung
- Label: `type/enhancement` oder `type/bug`
- Status: `status/in_progress` wenn sofort umgesetzt wird, sonst `status/open`

1.2.3 Schritt 3 – ToDo-Liste anlegen oder aktualisieren**

- Für jeden Auftrag MUSS eine ToDo-Liste angelegt und sichtbar gehalten werden.
- Genau ein Eintrag trägt zu jedem Zeitpunkt den Status `in_progress`.
- Abgeschlossene Einträge werden sofort als `erledigt` markiert.
- ToDo Plan und ToDo Build werden gemeinsam mit der aktiven ToDo-Liste als Block im Chat angezeigt (Abschnitt 2.2 Sichtbarkeitsregel).

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

**Jede Änderung an Laufzeit-, UI-, API- oder Verhaltenslogik erzwingt zwingend eine neue Version. Es gibt keine Ausnahmen.**

Betroffene Dateitypen: `*.py`, `*.html`, `*.js`, `*.css`, Dockerfile, Shell-/Startskripte, Laufzeit-Konfigurationen.

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

Ohne Versionsbump: Home Assistant erkennt kein Update. Die Änderung gilt als unvollständig.

#### Schritt D – Git-Flow (HA Main-First, PFLICHT)

Standard:** Alle Änderungen werden direkt nach `main` gepusht, damit Home Assistant das Update erkennen kann.

Pflichtsequenz:

1. Erforderliche QA ausführen
2. Fehler klassifizieren: fix-bezogen/blockierend vs. bereits vorhandene/nicht zusammenhängende Fehler
3. Bei ausschließlich vorhandenen/nicht zusammenhängenden Fehlern: Pflichtfluss fortsetzen
4. `influxbro/config.yaml` Version erhöhen (wenn Laufzeit/UI/API/Verhalten geändert)
5. Änderungen stagen
6. Commit erstellen
7. Nach `main` pushen
8. Ergebnis klar im Chat melden

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

#### Schritt E – GitHub-Issue abschließen

Ein Issue gilt erst als umgesetzt, wenn:

1. Die angeforderte Code-/Konfig-/Dokumentationsänderung tatsächlich angewendet wurde
2. Alle relevanten Pflicht-QA-Prüfungen für dieses Issue ausgeführt wurden
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

---

#### Schritt F – Abschlusssignal (PFLICHT, IMMER AUSFÜHREN)

Nach erfolgreicher Fertigstellung:

```bash
afplay /System/Library/Sounds/Glass.aiff
say "Fertig mit der Umsetzung"
```

Wenn eine neue Add-on-Version erstellt wurde (Version in `influxbro/config.yaml` erhöht):

```bash
say -v Anna "Generierung erfolgt, Version X Punkt Y Punkt Z wurde erzeugt"
```

Bei blockierenden Fehlern oder offenen Fragen:

```bash
afplay /System/Library/Sounds/Basso.aiff
say "Einige Punkte muessten noch beantwortet werden"
```

Wenn der Agent auf eine Entscheidung des Nutzers wartet:

```bash
say "Entscheidung erforderlich"
```

Hinweis: Audio-Signale sind Best-Effort. Ein fehlendes Audio-Signal macht eine abgeschlossene Aufgabe NICHT ungültig.

Abgeschlossen ist eine Aufgabe AUSSCHLIESSLICH, wenn alle Pflichtschritte A bis F ausgeführt wurden.

## ABSCHNITT 2 – INPUT-QUEUE UND ABARBEITUNGSLOGIK

### 2.1 Grundregel: Keine Unterbrechung aktiver Abarbeitung

Solange eine Abarbeitung aktiv ist und noch nicht vollständig abgeschlossen wurde (inkl. Abschlusssignal, ohne offene Restarbeiten und ohne offene Rückfragen), gilt:

- **Neue Eingaben des Nutzers werden NICHT sofort ausgeführt.**
- **Neue Eingaben werden in die entsprechende Queue eingereiht.**
- **Der aktive Prozess läuft bis zum vollständigen Abschluss weiter.**

### 2.2 Zwei Queues

#### ToDo Plan – Planungsanfragen

Wird verwendet für: Analyseanfragen, Plan-Erstellungen, Triage-Anfragen, Fragen, Recherchen.

Speicherort: `./.opencode/todo_plan.md`
Format:

```text
## ToDo Plan – Queue
- [ ] <Kurzbeschreibung> | Eingegangen: <Zeitstempel> | Quelle: Nutzereingabe
```

#### ToDo Build – Umsetzungsaufgaben

Wird verwendet für: Implementierungsaufträge, GO-Befehle, Issue-Umsetzungen, Codeänderungen.

Speicherort: `./.opencode/todo_build.md`
Format:

```text
## ToDo Build – Queue
- [ ] <Kurzbeschreibung> | Eingegangen: <Zeitstempel> | Quelle: Nutzereingabe
```

Beide Dateien sind lokal zu halten und NICHT zu committen.

#### Sichtbarkeitsregel (PFLICHT)

Beide Queues MÜSSEN im Chat sichtbar gehalten werden – genauso wie die aktive ToDo-Liste.
Der Agent zeigt alle drei Listen als Block** nach jedem abgeschlossenen Schritt, nach jeder Statusmeldung und nach jedem neuen Queue-Eintrag:

```text
📋 ToDo – Aktiv
  ✅ <erledigter Schritt>
  🔄 <aktueller Schritt> (in_progress)
  ⬜ <ausstehender Schritt>

📥 ToDo Plan – Queue  (.opencode/todo_plan.md)
  ⬜ <Eintrag> | Eingegangen: <Zeitstempel>
  — leer —

🔨 ToDo Build – Queue  (.opencode/todo_build.md)
  ⬜ <Eintrag> | Eingegangen: <Zeitstempel>
  — leer —
```

Anzeigeregeln:

- Ist eine Queue leer, wird sie trotzdem angezeigt mit dem Eintrag `— leer —`.
- Der Block wird IMMER vollständig dargestellt – nie nur einzelne Listen.
- Nach einem neuen Queue-Eintrag wird der Block sofort aktualisiert ausgegeben.
- Nach Abschluss der aktiven Aufgabe ersetzt der Block den regulären Status (siehe Abschnitt 2.5).

### 2.3 Einreihungsregeln

| Eingabe-Typ | Ziel-Queue |

|---|---|
| Neue Planungs-/Analyseanfrage | ToDo Plan |
| Neuer Implementierungsauftrag oder GO | ToDo Build |
| Präzisierung/Ergänzung zur aktiven Aufgabe | Aktive ToDo-Liste ergänzen |
| Explizites Abbruchsignal | Sofortige Unterbrechung (siehe 2.4) |

### 2.4 Explizite Abbruchsignale (EINZIGE Ausnahme)

Nur folgende Formulierungen gelten als echte Unterbrechung:

- `abbrechen`
- `stop`
- `halt`
- `lass das`
- `nicht weiter damit`
- `stattdessen mache jetzt X`
- `verwirf den aktuellen Ablauf`

Fehlt ein solches Signal, ist jede neue Nachricht als Ergänzung oder Einreihung in die Queue zu behandeln.

### 2.5 Verhalten nach Abschluss der aktiven Aufgabe

Wenn die aktive Aufgabe vollständig abgeschlossen ist (alle Pflichtschritte A–F ausgeführt, kein offener Restpunkt, kein offenes Abschlusssignal), MUSS der Agent:

1. Beide Queue-Dateien prüfen (`./.opencode/todo_plan.md` und `./.opencode/todo_build.md`)
2. Den Nutzer informieren, welche Einträge ausstehen – geordnet nach Plan-Queue und Build-Queue
3. Explizit fragen, ob die ausstehenden Todos abgearbeitet werden sollen

VERBOTEN: Ausstehende Todos automatisch und ohne Rückfrage ausführen.

Pflichtausgabe nach Abschluss:**

```text
Aktive Aufgabe abgeschlossen.

Ausstehende Plan-Queue (.opencode/todo_plan.md):
- <Eintrag 1>
- <Eintrag 2>

Ausstehende Build-Queue (.opencode/todo_build.md):
- <Eintrag 1>
- <Eintrag 2>

Soll ich mit der Abarbeitung der ausstehenden Todos beginnen?
1. Ja, Plan-Queue zuerst
2. Ja, Build-Queue zuerst
3. Ja, beide Queues (Plan zuerst)
4. Nein, ich gebe neue Anweisungen
```

### 2.6 Pflichtverhalten bei Fehlern während der Abarbeitung

Schlägt ein Schritt fehl, MUSS der Agent:

1. Den Fehler klar benennen
2. Den bereits erfolgreich erledigten Teil vom offenen Rest trennen
3. Den offenen Rest in der Queue einsortieren
4. Erst danach neue Nutzeranweisungen in diese Queue einarbeiten

### 2.7 Pflichtverhalten bei Scope-Erweiterungen

Fügt der Nutzer während der Ausführung neue Anforderungen hinzu:

1. Die laufende Arbeit bleibt aktiv
2. Neue Anforderungen werden an die Build-Queue angehängt
3. Der Agent benennt kurz, was in Arbeit war und wie die neue Anweisung eingereiht wurde
4. Nur bei explizitem Abbruchsignal darf die bisherige Arbeit fallengelassen werden

---

## ABSCHNITT 3 – MODUSSPERRE

### 3.1 Aktive Sperren haben absoluten Vorrang

Wenn ein System-Hinweis, System-Reminder oder Developer-Hinweis `Plan Mode`, `READ-ONLY`, `STRICTLY FORBIDDEN`, `ZERO exceptions` oder sinngleiche Formulierungen enthält:

**ERLAUBT:**

- Lesen, Suchen, Analysieren
- Rückfragen stellen
- Plan erstellen
- Queue-Punkte ordnen und dokumentieren

**VERBOTEN (ohne Ausnahme):**

- Dateien ändern (`apply_patch`, Schreib-Bash-Befehle)
- Versionen erhöhen
- Commits erzeugen
- Branches ändern oder pushen
- GitHub-Mutationen (Issues erstellen/editieren/Labels ändern/Kommentare posten/Issues schließen oder öffnen/PRs erstellen oder verändern)
- Abschlussschritte (Versionsbump, Changelog, Manual, Commit, Push, Issue-Abschluss)
- Laufende Arbeit noch schnell fertigstellen

### 3.2 Queue-Einfrieren unter Modussperre

Eine aktive Queue wird bei Modussperre eingefroren:

- Sie darf nur noch dokumentiert, geordnet, priorisiert und geplant werden
- Sie darf NICHT umgesetzt, abgeschlossen, committed oder gepusht werden
- Die Queue-Regel ist niemals eine Erlaubnis, eine aktive Modussperre zu umgehen

### 3.3 Pflicht-Checkpoint vor jeder Mutation

Vor jeder schreibenden Aktion MUSS der Agent prüfen:

1. Ist ein System-/Developer-Hinweis aktiv, der nur Lesen/Planen erlaubt?
2. Ist `Plan Mode` oder `READ-ONLY` aktiv?
3. Betrifft die Aktion eine Mutation an Dateien, Git, GitHub, Konfiguration oder persistentem Zustand?

Wird eine dieser Fragen mit `ja` beantwortet: Aktion UNTERLASSEN.

### 3.4 Pflichtantwort bei aktiver Sperre

Bei jeder operativen Anfrage unter aktiver Sperre MUSS der Agent sinngemaäß antworten:

> „Schreibsperre aktiv – ich liefere nur Analyse/Plan."

---

## ABSCHNITT 4 – GO-BEFEHL (EINZIGE DEFINITION)

Schreibt der Nutzer `go` oder `GO`, führt der Agent folgende Sequenz vollständig und ohne Unterbrechung aus:

1. Alle offenen/ausstehenden geplanten Aufgaben aus ToDo-Liste und `./.opencode/plan_state.md` implementieren
2. Erforderliche QA ausführen (Abschnitt 1.4 Schritt B)
3. Fehler klassifizieren
4. `influxbro/config.yaml` Version erhöhen (wenn Laufzeit/UI/API/Verhalten geändert)
5. Änderungen stagen
6. Commit mit strukturierter Message erstellen
7. Nach `main` pushen
8. Ergebnis im Chat melden
9. Abschlusssignal ausführen (Abschnitt 1.4 Schritt F)

**VERBOTEN:** Nach dem ersten Paket stoppen, solange kein echter Blocker existiert.

**Wenn mehrere Pakete sinnvoll sind**:

- Erstes Paket committen und pushen
- Verbleibende Aufgaben explizit als offen benennen
- Automatisch mit dem nächsten Paket fortfahren

**GO darf NICHT:**

- Ausführung unterbrechen
- Fragen auslösen
- Weitere Verarbeitung pausieren oder verzögern

---

## ABSCHNITT 5 – AUTONOME AUSFÜHRUNGSRICHTLINIE

### 5.1 Kern-Regel

Wenn der Nutzer die Umsetzung explizit freigibt (z. B. „alle Issues umsetzen", `go` oder äquivalente Formulierung), MUSS der Agent alle Aufgaben vollständig und ohne Zwischenfragen ausführen.

### 5.2 Keine-Unterbrechung-Regel

**VERBOTEN während freigegebener Ausführung:**

- Schritt-für-Schritt-Bestätigungen einholen
- Priorisierungsfragen stellen
- „Wie soll ich vorgehen?"-Fragen stellen
- Nummerierte Auswahlmenüs (1/2/3) für Zwischenschritte

### 5.3 Erlaubte Unterbrechungen (AUSSCHLIESSLICH DIESE)

Der Agent DARF die Ausführung nur unterbrechen, wenn:

- Kritische Informationen fehlen und kein Fortschritt möglich ist
- Externe Abhängigkeiten erforderlich sind (z. B. Zugangsdaten, API-Zugang)
- Mehrere gültige Umsetzungen mit erheblichem Einfluss existieren
- Eine destruktive oder nicht umkehrbare Aktion erforderlich ist

### 5.4 Multi-Issue-Ausführung

- Issues sequenziell abarbeiten
- Ein Issue vollständig abschließen, bevor das nächste beginnt
- NICHT zwischen Issues fragen
- NICHT Ausführung neu bestätigen
- „Arbeite alle Issues ab" oder „Arbeite alle Issues außer #X ab" sind vollständige Arbeitsanweisungen – keine zusätzliche Bestätigung, kein weiteres `GO` und keine Rückfrage zur Paketbildung erforderlich
- Schließt der Nutzer einzelne Issues explizit aus, sind alle übrigen automatisch zur Umsetzung ausgewählt
- Offene Issues, die laut Nutzer umgesetzt werden sollen, MÜSSEN selbstständig automatisch weiter bearbeitet werden, bis keine solchen Issues mehr offen sind

### 5.5 Berichterstattung

Berichte NUR:

- Nach Abschluss eines logischen Blocks (z. B. ein Issue vollständig umgesetzt)
- Oder am Ende aller Aufgaben

Berichte dürfen KEINE Fragen enthalten, außer bei einem echten Blocker.

## ABSCHNITT 6 – PLAN-MODUS

### 6.1 Verhalten im Plan-Modus

Wenn Plan-Modus aktiv ist:

- Detaillierten Plan erstellen und alle Aufgaben anzeigen
- Aufgaben logisch gruppieren
- Auf explizite Nutzerfreigabe warten, bevor etwas umgesetzt wird (keine Dateiänderungen, keine Commits, keine Pushes)

**VERBOTEN:** Nach Planpräsentation proaktiv nach Issues fragen oder Issue-Triage anbieten.

### 6.2 Plan-Modus darf aktive Build-Ausführung nicht unterbrechen

- Läuft bereits eine freigegebene Build-Ausführung, bleibt diese bis zu einem logischen Abschlusspunkt aktiv.
- Ein späterer Wechsel in den Plan-Modus darf diese laufende Ausführung NICHT rückwirkend stoppen oder als Read-Only umdeuten.
- Neue Plan-Anfragen während laufender Build-Ausführung werden in die ToDo-Plan-Queue eingereiht.
- Nur ein explizites Abbruchsignal (Abschnitt 2.4) kann eine laufende Build-Ausführung zugunsten von Plan-Arbeit unterbrechen.

### 6.3 Build-Modus darf aktive Plan-Arbeit nicht unterbrechen

- Läuft bereits aktive Plan-Arbeit, DARF ein späterer Build/GO-Befehl diese nicht abbrechen.
- Der aktuelle Plan-Antwort muss zuerst einen logischen Abschlusspunkt erreichen.
- Der Build/GO-Befehl wird danach als nächste Aktion ausgeführt, es sei denn, der Nutzer weist ausdrücklich an sofort zu wechseln.

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
- Standard-Ausgabe: Fehler, relevante Snippets, Zeilenreferenzen
- Zusammenfassungen vor vollständigen Dumps bevorzugen

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

### 8.1 Grundregeln (KRITISCH)

- **Issues werden NIEMALS automatisch geprüft, geladen oder gestartet.**
- Issues werden ausschließlich auf expliziten Befehl des Nutzers geprüft und abgearbeitet (Auslöser: Abschnitt 16.2).
- Nur bei NEUER Anfrage fragen, ob ein Issue erstellt oder sofort umgesetzt werden soll.
- Bezieht sich die Anfrage auf ein bestehendes Issue: direkt weiterarbeiten, keine Rückfrage.
- **Sperrbedingung:** Sind noch Todos offen (ToDo-Liste, `todo_plan.md`, `todo_build.md`), dürfen KEINE neuen Issues gestartet werden – auch nicht auf Anfrage. Der Agent meldet den blockierten Zustand und listet offene Punkte auf.
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

### 9.1 ToDo-Liste und Queues – Sichtbarkeit (PFLICHT)

- Für jeden Auftrag IMMER eine ToDo-Liste erstellen und sichtbar halten.
- Bei neuen Anforderungen: bestehende ToDo-Liste sofort erweitern.
- Genau ein Eintrag trägt den Status `in_progress`.
- Einträge sofort als `erledigt` markieren, sobald abgeschlossen.
- Alle ToDo-Einträge MÜSSEN umgesetzt sein, bevor Fertigstellung erklärt wird.
- **Alle drei Listen werden gemeinsam als Block im Chat sichtbar gehalten** (aktive ToDo + ToDo Plan + ToDo Build). Regeln siehe Abschnitt 2.2 Sichtbarkeitsregel.

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

- Templates selbstständig halten; kein Build-Schritt vorhanden.
- Relative URLs (`./api/...`) verwenden damit HA Ingress funktioniert.
- JS einfach halten (kein Framework). Kleine Funktionen und explizite DOM-Lookups bevorzugen.
- Bei destruktiven Aktionen: Bestätigungs-UI beibehalten und zusätzliche Schutzmaßnahmen ergänzen.

**UI-Design-Standard:**

- Vor dem Hinzufügen oder Ändern von GUI-Elementen: `influxbro/Template.md` konsultieren.
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
5. Bei Bestätigung: `npx playwright test` ausführen und Ergebnisse melden

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
- [ ] Beide Queue-Dateien geprüft, Nutzer über ausstehende Todos informiert (KEINE automatische Issue-Triage anbieten)

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

**Sperrbedingung (ABSOLUT):** Liegen noch ToDo-Einträge mit Status `in_progress` oder `ausstehend` vor, ODER sind Einträge in `.opencode/todo_plan.md` bzw. `.opencode/todo_build.md` vorhanden, DÜRFEN keine neuen Issues gestartet werden – auch nicht auf explizite Anfrage des Nutzers. Der Agent antwortet stattdessen mit:

> "Es liegen noch offene Aufgaben vor – neue Issues können erst gestartet werden, wenn alle aktuellen Todos abgeschlossen sind."
>
> Offene Punkte: [Auflistung der ausstehenden Einträge]

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
11. Queue-Dateien geprüft, Nutzer über ausstehende Todos informiert

Fehlt ein einziger Punkt: die Aufgabe ist NICHT abgeschlossen.
