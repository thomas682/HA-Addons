# Changelog

## 1.12.521

### Fix

- Dialoge / Zwischenablage: Der zentrale Popup-Copy-Button bevorzugt jetzt den aktuell sichtbaren oder im Popup markierten Inhalt, bevor auf den gespeicherten Fallbacktext zurueckgegriffen wird. Dadurch kopiert der Button im Dialog `Letzter Fehler` nach `Logs (5min)` wieder den angezeigten Log-/Textinhalt statt leer oder veraltet zu bleiben. ([#482](https://github.com/thomas682/HA-Addons/issues/482))
- Maintenance: Tested with Home Assistant Core: 2026.4.4

## 1.12.520

### Fix

- Dashboard / Messwertinfos: Der Friendly-Name-Historienpfad `friendly_name + entity_id + range=all` baut die Bereichsanalyse fuer `api/tag_combo_ranges` jetzt mit einem gueltigen zweistufigen Flux-Join auf. Dadurch verschwindet der 500er `stream[A] is not Record (argument tables)` beim Dashboard-Start und die historischen Namenszeitrange koennen wieder geladen werden. ([#481](https://github.com/thomas682/HA-Addons/issues/481))
- Maintenance: Tested with Home Assistant Core: 2026.4.4

## 1.12.519

### Fix

- Dashboard / Graph-Start: Fruehe `window_points`-Aufrufe werden jetzt nur noch gestartet, wenn fuer Main-Graph, Zoom-Nachladen und Bearbeitungsgraph wirklich ein gueltiges `start`/`stop`-Zeitfenster vorliegt. Dadurch entfaellt der fruehe Fehlerpfad `POST /api/window_points` ohne Zeitbereich, der die GUI-Startphase stoeren konnte. ([#479](https://github.com/thomas682/HA-Addons/issues/479))
- Maintenance: Tested with Home Assistant Core: 2026.4.4

## 1.12.518

### Fix

- Dashboard / Logging: Interne Performance-Endpunkte (`/api/perf_event`, `/api/perf_stats`, Client-Log/Error und Trace-Span-POSTs) werden nicht mehr selbst als Langlauf-HTTP-Events instrumentiert. Dadurch entfaellt die fehlerhafte `perf_event`-Schleife, die den Start der GUI verlangsamen und die Logs mit Selbsttreffern fuellen konnte. ([#478](https://github.com/thomas682/HA-Addons/issues/478))
- Dashboard / Caching: Die Outlier-Typleiste im Cache-Zeitstrahl spiegelt jetzt nur noch die fuer den aktuellen Messwert effektiv aktiven Strategietypen wider. Typen wie `Counter-Sprung pro Zeit` erscheinen bei Messwerten ohne Counter-Semantik korrekt inaktiv statt nur als lokale Sichtbarkeits-Toggles aktiv zu wirken. ([#478](https://github.com/thomas682/HA-Addons/issues/478))
- Maintenance: Tested with Home Assistant Core: 2026.4.4

## 1.12.517

### Enhancement

- UI / Logging / Analyse: Lange Client- und Server-Wartezeiten werden jetzt zentraler behandelt. User-relevante API-Wartezeiten koennen ab einer konfigurierbaren Schwellzeit global im Statusfeld unter dem Menue erscheinen, und die Section `Messwertinfos von Homeassistant` zeigt fuer die Profilermittlung zusaetzlich einen lokalen Spinner mit Laufzeit direkt unter der Infozeile. ([#477](https://github.com/thomas682/HA-Addons/issues/477))
- Logs / Settings: Neue Settings fuer `Langlauf-Schwelle (ms)` und `Zeitintensive Protokollierung aktiv`. Auf der Logs-Seite gibt es eine neue auf-/zuklappbare Section `Zeitintensive Protokollierung` mit Top-10-Analyse nach Haeufigkeit und maximaler Laufzeit, waehlbarem Zeitbereich (`range`/`start`/`stop`) sowie Direkt-Toggles pro Langlauf-Key. Fehler bleiben immer aktiv und koennen dort nicht deaktiviert werden. ([#477](https://github.com/thomas682/HA-Addons/issues/477))
- Maintenance: Tested with Home Assistant Core: 2026.4.4

## 1.12.516

### Enhancement

- UI / Backup / Restore / Export / Import: Laufende Aktionen zeigen jetzt abschnittsnahe Statusbereiche mit Spinner, Klartext und Laufzeit direkt bei den ausloesenden Buttons. Gleichzeitig werden FullBackup- und FullRestore-Laeufe zusaetzlich in die globale Statusleiste gespiegelt, damit laufende Vordergrund- und Hintergrundaktionen konsistenter sichtbar bleiben. ([#476](https://github.com/thomas682/HA-Addons/issues/476))
- Maintenance: Tested with Home Assistant Core: 2026.4.4

## 1.12.515

### Fix

- Fehler-UI / Statusleiste: Client- und Fetch-Fehler werden jetzt zuverlässiger in den sichtbaren Fehlerpuffer (`InfluxBroErrors`) gespiegelt. Dadurch tauchen relevante `Failed to fetch`-/`api/influx_ping`-Fehler nicht nur im Server-/Client-Log, sondern auch als letzter Fehler in Statusleiste und Fehlerdialog auf. ([#473](https://github.com/thomas682/HA-Addons/issues/473))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.514

### Fix

- Dashboard / Smart Assist: Zwei Nachfixe. Erstens nutzt `tag_combo_ranges` bei `friendly_name` + gesetzter `entity_id` im All-Time-Fall jetzt einen Spezialpfad mit vorgelagerter Namensermittlung per `schema.tagValues(...)`, bevor die Zeitbereiche je Name geladen werden. Das reduziert die Timeout-Anfälligkeit für diesen Fall. Zweitens wurde der Dialog `Fehler melden (Smart Assist)` an die übrigen Dialoge angenähert: kleinere Textarea-Schrift für `Was wurde erwartet?`, `Was ist tatsächlich passiert?` und `Erkannte Schritte` sowie ein Meta-Footer unten rechts (`pk: unknown | tpl: dialog_info_popup`). ([#471](https://github.com/thomas682/HA-Addons/issues/471))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.513

### Enhancement

- Release-Refresh: Neue Add-on-Version erzeugt, damit der aktuelle Frontend-/Backend-Stand sicher als frisches Update ausgeliefert wird. ([#469](https://github.com/thomas682/HA-Addons/issues/469))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.512

### Fix

- UI / Referenzierung / Strategieinfo: Mehrere Nachfixe für den neuen Profil-/Tooltip-Bereich. Der doppelte `hideT`-Syntaxfehler in `_tooltips.html` ist entfernt. Der Super Picker kopiert bei Fallback-Panels jetzt zusätzlich den vollständigen Tooltip-/Infotext statt nur des Fallback-Selectors. Die Kachel `Referenzierung` zeigt die Verwendungen kompakt dedupliziert (eine Zeile pro Automation/Script/Datei) und bietet eine neue `Detailliste` mit Dateiinhalt, Volltextsuche, Vor/Zurück-Sprung und direktem Öffnen derselben Referenzdatei/Zeile im Dialog. Außerdem erläutert die Strategieinfo nun ausdrücklich, dass `fault_cluster`/Störphase nur als Folge zuvor aktiver Primärtypen entstehen kann. ([#467](https://github.com/thomas682/HA-Addons/issues/467))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.511

### Enhancement

- Bugreport / Support: Neuer `Fehler melden (Smart Assist)`-MVP auf Basis des vorhandenen Bugreport- und Snapshot-Systems. Der Assistent fuehrt durch eine strukturierte Fehleraufnahme (Ort, Zeitpunkt, erwartet, tatsächlich), zeigt rekonstruierte UI-/Analyse-Schritte aus vorhandenen Recent-Actions-/Worklog-Daten, kann serverseitig einen Support-Snapshot erzeugen und übergibt das Ergebnis direkt an den bestehenden Issue-Composer. ([#465](https://github.com/thomas682/HA-Addons/issues/465))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.510

### Enhancement

- Backup / Restore: Neuer MVP für `Backup verifizieren` direkt in `backup.html`. Er enthält einen Verify-Dialog für Messwert- und Fullbackup-Prüfungen, jobbasierte Status- und Result-Endpoints, Restore in temporäre Verify-Buckets (v2) sowie einen ersten Vergleich von Punktanzahl, Measurements und Zeitbereichen. Originaldaten werden dabei nicht verändert; der temporäre Prüf-Bucket kann optional automatisch gelöscht werden. ([#464](https://github.com/thomas682/HA-Addons/issues/464))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.509

### Enhancement

- Dashboard / Messwertprofil: Die InfluxDB-Kachel zeigt jetzt bei `Erster Wert`, `Letzter Wert`, `Min` und `Max` den jeweiligen Zeitpunkt direkt neben dem Wert an. Zusätzlich gibt es die neue Kachel `Referenzierung`, die weitere Verwendungen des Messwerts in YAML-/JSON-Dateien auflistet und – wo sinnvoll – einen Direktlink (z. B. zu Dashboards/Automationen) anbietet. Die Strategiekarten im Profilbereich verwenden nun eine Hintergrundfarbe, die sich an der Typ-/Chipfarbe orientiert. ([#462](https://github.com/thomas682/HA-Addons/issues/462))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.508

### Fix

- Analyse / Dashboard: Mehrere Laufzeitfehler rund um `Analyse mit Cache` und das gefilterte Analyse-Logging behoben. Dazu gehören der Frontend-Fehler `typeLabels is not defined`, die markierende Volltextsuche im `analysis_log_modal` (inkl. Prev/Next) und ein zusätzlicher Copy-Button in der Actionleiste. Gleichzeitig nutzt `/api/fields?measurement=...&range=all` bei reinem Measurement-Fall wieder den leichten `schema.measurementFieldKeys(...)`-Pfad, und abgelaufene Statistik-Job-IDs erzeugen im Statistikbereich keinen unnötigen 404-Abbruch mehr. In allen Analyseanzeigen werden jetzt außerdem die tatsächlich geprüften Ausreißertypen aus der aktuellen Typenauswahl ausgewiesen. ([#461](https://github.com/thomas682/HA-Addons/issues/461))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.507

### Enhancement

- UI / Tooltips: Die bisherige gemischte Tooltip-Landschaft wurde um eine zentrale `InfluxBroUnifiedTooltip`-Engine in `_tooltips.html` erweitert. Sie liefert fuer Dashboard-Elemente denselben professionellen Rich-Tooltip-Stil (Header, technische Kennung, Beschreibung, Meta-Grid, Beispiel, Doku-Link) und unterstuetzt Pinning, Tastatur-Shortcuts sowie die Einbindung von Graphwerten/Graphkontext im selben Tooltip-Familienstil. ([#460](https://github.com/thomas682/HA-Addons/issues/460))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.506

### Enhancement

- Dashboard / Ausreißerstrategie: Die Analysetyp-Chips im Strategiebereich besitzen jetzt professionelle Tooltips mit Severity-Farbpunkt, technischer Kennung, Beschreibung, Meta-Grid, Beispielbedingung und Doku-Link. Sie reagieren auf Hover, Fokus, Klick/Touch (Pin-Modus), `Enter`/`Space`, `Esc` und den `?`-Shortcut für die Dokumentation. ([#458](https://github.com/thomas682/HA-Addons/issues/458))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.505

### Enhancement

- Dashboard / Strategieinfo: Im Dialog fuer benutzerdefinierte Strategien gibt es jetzt den Button `JSON Aufbau und Beispiele`. Er oeffnet einen Hilfedialog im Stil der bestehenden Info-Dialoge mit Einleitung, Suchfeld, Copy-Buttons, mindestens 6 direkt nutzbaren JSON-Beispielen und Rueckkehrlogik zum vorher geoeffneten `Strategieinfo`-Dialog. ([#457](https://github.com/thomas682/HA-Addons/issues/457))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.504

### Enhancement

- Analyse / Strategien: Interne Ausreißerregel-Keys wurden auf klarere technische Namen migriert (`counter` -> `rate_jump`, `counterreset` -> `reset_event`, `decrease` -> `negative_jump`, `bounds` -> `range_violation`, `gap` -> `time_gap`, `fault_phase` -> `fault_cluster`, `null` -> `null_value`, `zero` -> `zero_value`). Alte gespeicherte Werte werden weiterhin gelesen und beim Speichern auf die neuen Keys normalisiert. Dadurch bleiben Strategien, Overrides und Dashboard-Zustände kompatibel, waehrend neue Daten nur noch die neuen Schluessel schreiben. ([#455](https://github.com/thomas682/HA-Addons/issues/455))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.503

### Enhancement

- Dashboard / Ausreißerstrategie: Die Strategiesteuerung wurde im Messwertprofil weiter ausgebaut. Neben den Modi `Automatikwahl`, `alle ein` und `alle aus` verarbeitet das Backend jetzt zusätzliche Parametervorgaben und Korrekturreaktionen pro aktivem Typ (`bounds`, `counter`, `counterreset`, `decrease`, `gap`, `fault_phase`, `null`, `zero`). Die UI zeigt diese Felder direkt unter den effektiven Typen an; Änderungen werden messwertspezifisch serverseitig gespeichert. Zusätzlich liefert das Profil jetzt `unit_group`, `type_unit_consistency`, `counter_semantics` und eine mehrzeilige `strategy_explanation` für die Strategieinfo. ([#456](https://github.com/thomas682/HA-Addons/issues/456))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.502

### Enhancement

- Dashboard / Ausreißerstrategie: Die Strategiesteuerung sitzt jetzt direkt im Bereich `Messwertinfos von Homeassistant` statt erst im Ausreißer-Tabellenbereich. Alle Typen werden als bekannte Chip-Auswahl dargestellt; dazu kommen die Modi `Automatikwahl`, `alle ein` und `alle aus`. Pro aktivem Typ erscheinen nun direkt messwertspezifische Parameter- und Korrekturfelder, die serverseitig als Overrides gespeichert werden. ([#454](https://github.com/thomas682/HA-Addons/issues/454))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.501

### Enhancement

- Dashboard / Ausreißerstrategie: Neue serverseitige Strategien auf Basis des Messwertprofils. `derived.internal_type`, HA-Klassifikation und Influx-Metadaten werden jetzt zu einer deterministischen Basisstrategie zusammengeführt. Der Dashboard-Bereich zeigt die effektiven Ausreißertypen automatisch an, manuelle Overrides werden serverseitig gespeichert, und der neue Dialog `Strategiewahl` erlaubt die Sicht auf aktive Strategie, Begründung, effektive Typen sowie benutzerdefinierte Strategien/Overrides. ([#454](https://github.com/thomas682/HA-Addons/issues/454), [#453](https://github.com/thomas682/HA-Addons/issues/453))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.500

### Fix

- Analyse / Dashboard: Das Fenster `analysis_log_modal` nutzt jetzt das bestehende Dialogmuster konsistenter weiter: Copy-Button `In Zwischenablage kopieren`, Template-Meta rechts unten, kein S-Picker, rote Hervorhebung für Fehlereinträge und robustere `dur_ms`-Anzeige aus den Eventdaten. ([#452](https://github.com/thomas682/HA-Addons/issues/452))
- Analyse mit Cache: `_query_payload(...)` bevorzugt v2 weiterhin defensiv und beendet den v2-Dynamic-Pfad jetzt auch im Normalfall korrekt mit `return`, statt bei bestimmten Ergebnismengen in den v1-Fehlerpfad (`InfluxDB v1 requires database`) durchzufallen. ([#452](https://github.com/thomas682/HA-Addons/issues/452))
- Messwertinfos von Homeassistant: Das Profilpanel bleibt sichtbar und wird weiter geladen, auch wenn keine oder nur eine historische `friendly_name`-Variante gefunden wird. Die Timeline zeigt dann einen neutralen Leer-/Einzelzustand, statt die gesamte Section auszublenden. ([#452](https://github.com/thomas682/HA-Addons/issues/452))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.499

### Fix

- Dashboard / Messwertinfos von Homeassistant: Das Messwertprofil bleibt jetzt sichtbar und wird immer geladen, sobald `measurement`, `field` und `entity_id` vorliegen, auch wenn nur ein oder gar kein historischer `friendly_name` gefunden wird. Die Timeline wechselt in diesem Fall auf einen neutralen Einzel-/Leerzustand, statt die gesamte Section per `display:none` auszublenden. ([#451](https://github.com/thomas682/HA-Addons/issues/451))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.498

### Fix

- Dashboard / Messwertinfos von Homeassistant: `/api/measurement_profile` verarbeitet InfluxDB-v2-Ergebnisse jetzt korrekt ueber `FluxTable.records`, statt `query_api().query(...)` wie direkte Records zu behandeln. Dadurch verschwindet der 500er `FluxTable object has no attribute get_time` und das Profilfeld laedt wieder sauber. ([#450](https://github.com/thomas682/HA-Addons/issues/450))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.497

### Enhancement

- Dashboard / Messwertinfos von Homeassistant: Die Section oberhalb der Mehrfachnamen-Ansicht zeigt jetzt ein professionell gegliedertes Messwertprofil aus Home-Assistant-Metadaten, YAML-Fundstellen und InfluxDB-Basisstatistiken. Dazu wurde der zentrale Endpoint `/api/measurement_profile` eingeführt; `#448` (Titel/Infofeld) wurde direkt im selben Paket miterledigt. ([#448](https://github.com/thomas682/HA-Addons/issues/448), [#449](https://github.com/thomas682/HA-Addons/issues/449))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.496

### Fix

- Dashboard / Mehrere Messwertnamen: Dynamisch erzeugte Zeilen der Namensliste verwenden jetzt stabile, pro Variante eindeutige `data-ib-pickkey`-/`data-ib-instancekey`-Werte statt eines gemeinsamen Schluessels. Dadurch verschwindet die Console-Meldung zu Pickkey-Kollisionen beim Oeffnen der Dashboard-Seite. ([#447](https://github.com/thomas682/HA-Addons/issues/447))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.495

### Enhancement

- Dashboard / Mehrere Messwertnamen: Die Section wurde aus der Messwertauswahl herausgezogen und steht jetzt als eigenstaendiger, auf-/zuklappbarer Block zwischen `Messwertauswahl` und `Caching`. Das Innenlayout wurde auf die Vorlage `demo/messwertnamen-professional.html` umgestellt: Panel-Header mit Aktion, Summary-Bar, obere Vergleichsachse und 1:1-Listenlayout mit Index, Name, Zeitraum, Punkte und Status. ([#439](https://github.com/thomas682/HA-Addons/issues/439))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.494

### Enhancement

- Dashboard / Mehrere Messwertnamen: Die Namens-Zeitleiste ist jetzt als echte auf-/zuklappbare Section innerhalb der Messwertauswahl umgesetzt. Sobald mehrere historische `friendly_name`-Varianten gefunden werden, blendet sich die Section ein und klappt automatisch auf; danach kann sie vom Nutzer manuell wieder geschlossen werden. Die vorhandene Merge-/Undo-Logik bleibt unveraendert erhalten. ([#439](https://github.com/thomas682/HA-Addons/issues/439))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.493

### Enhancement

- Dashboard / Mehrere Messwertnamen: Die bereits vorhandene Namens-Zeitleiste wurde stilistisch auf eine kompakte Balkenansicht umgebaut. Unterhalb der Messwertauswahl erscheint jetzt die Section `Mehrere Messwertnamen` mit Uebersichts-Badges, Statuschips (`aktuell` / `historisch`) und einem horizontalen Zeitbalken pro historischem `friendly_name`. Die bestehende Merge-/Undo-Logik bleibt unveraendert erhalten. ([#439](https://github.com/thomas682/HA-Addons/issues/439))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.492

### Fix

- Dashboard-Start: Gespeicherte Selector-Werte (`measurement`, `field`, `entity_id`, `friendly_name`) werden jetzt vor dem ersten `loadMeasurements()`-Aufruf ins UI zurueckgeschrieben. Dadurch kann die initiale Measurement-Abfrage vorhandene Filter direkt beruecksichtigen, statt zuerst unnoetig breit zu laden und erst danach den gespeicherten Zustand zu restaurieren. ([#446](https://github.com/thomas682/HA-Addons/issues/446))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.491

### Fix

- Query-Test-Dialog / Dashboard-Selector: Der Query-Test-Dialog faellt nicht mehr an einem lokal gescopten `applyMiniCheckboxStyle`-Helfer aus. Gleichzeitig nutzt `/api/measurements?range=all` ohne weitere Filter wieder den leichten `schema.measurements(...)`-Pfad statt die teure Distinct-All-Time-Abfrage, wodurch unnoetige Timeouts und 500er bei der Messwertliste vermieden werden. ([#445](https://github.com/thomas682/HA-Addons/issues/445))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.490

### Enhancement

- Query-Test-Dialog: Unterhalb von `influxbro_querytest_input` gibt es jetzt die Checkbox `Query History`. Sie blendet ein Panel mit bisherigen Queries aus dem serverseitigen Trace-Store ein (neueste oben). Eintraege lassen sich direkt kopieren oder ganz/teilweise in das obere Query-Feld einfuegen. ([#443](https://github.com/thomas682/HA-Addons/issues/443))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.489

### Fix

- Dashboard / Messwertauswahl: Der `friendly_name`-Selector verwendet bei gesetzter `entity_id` jetzt einen enger gefilterten Direktquery-Pfad inklusive `_field`, statt fuer All-Time-Abfragen auf den breiteren `schema.tagValues(...)`-Pfad zu gehen. Dadurch bleiben alle historischen Namen auffindbar, waehrend die Query weniger unnoetig scannt und bei grossen Buckets deutlich robuster laeuft. ([#444](https://github.com/thomas682/HA-Addons/issues/444))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.488

### Fix

- Dashboard / Messwertauswahl: `/api/tag_combo_ranges` erzeugt fuer historische `friendly_name`-Bereiche jetzt wieder gueltige Flux-Queries. Die Auswahl ueber `entity_id` laeuft damit auch bei `range=all` ohne Reduce-Parsefehler weiter. ([#442](https://github.com/thomas682/HA-Addons/issues/442))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.487

### Enhancement

- Verdichtung / Audit: Neue Audit-Seite mit KPI-Uebersicht fuer Raw- vs. Rollup-Punkte, Aggregationsfaktor, Einsparung, Backup-/Restore-Status und Detailtabelle pro Tag-Key. Die Seite nutzt vorhandene Rollup-Profile und Rollup-Run-Backups als Datenbasis und erlaubt JSON-/CSV-Export direkt im Browser. ([#421](https://github.com/thomas682/HA-Addons/issues/421))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.486

### Enhancement

- Repository-Tooling: Neue lokale Versionsbump-Guards fuer Commit und Push. Ein gemeinsames Checkscript prueft jetzt Code-Aenderungen gegen `influxbro/config.yaml`, ist als `pre-commit`-Hook eingebunden und kann ueber `.githooks/pre-push` via `core.hooksPath` aktiviert werden. ([#437](https://github.com/thomas682/HA-Addons/issues/437))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.485

### Enhancement

- Dashboard / Messwertauswahl: Unterhalb der Auswahl erscheint jetzt ein Panel `Analyse Messwertname`, sobald fuer die aktuelle `entity_id` im gewaehlten Zeitraum mehrere historische `friendly_name`-Werte existieren. Der neueste Name wird erkannt, fruehere Namensbereiche werden mit Zeitfenster angezeigt und koennen per Button direkt auf den letzten Namen vereinigt werden. Die Aenderung laeuft als Change-Block und bleibt damit im Verlauf/Undo nachvollziehbar. ([#439](https://github.com/thomas682/HA-Addons/issues/439))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.484

### Fix

- Dashboard / Messwertwahl: Selector-Abfragen fuer Measurements, Fields, `entity_id`, `friendly_name`, `resolve_signal` und Tag-Kombinationsbereiche verwenden jetzt denselben Zeitraum wie die aktuelle Dashboard-Auswahl. Fuer `All` bleibt die Messwertwahl standardmaessig unlimitiert; optional kann sie in den Einstellungen bewusst auf X Tage begrenzt werden. Custom-Start/Stop behaelt dabei Vorrang. ([#438](https://github.com/thomas682/HA-Addons/issues/438))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.483

### Enhancement

- Jobs & Cache / Timer Jobs: Deaktivierte Timer zeigen jetzt links einen `deaktiviert`-Status und werden in der Tabelle grau dargestellt. Farbe und Deckkraft lassen sich in den Einstellungen unter `Jobs & Cache` anpassen. ([#436](https://github.com/thomas682/HA-Addons/issues/436))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.482

### Fix

- Jobs & Cache: Die Jobs-Tabelle besitzt jetzt einen `Loeschen`-Button fuer markierte, bereits abgeschlossene History-Eintraege. Laufende Jobs bleiben vor versehentlichem Loeschen geschuetzt und muessen weiterhin zuerst abgebrochen werden. ([#435](https://github.com/thomas682/HA-Addons/issues/435))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.481

### Enhancement

- Support Bundle: Im Dialog koennen jetzt Support-Bundle-Snapshots erzeugt und aus einer Snapshot-Liste ausgewaehlt werden. Der neueste Snapshot ist vorselektiert und kann bei Preview/Download als `snapshot.json` ins Bundle aufgenommen werden. Der Dialog zeigt ausserdem seine Footer-Metadaten (`pk` / `tpl`). ([#433](https://github.com/thomas682/HA-Addons/issues/433))

### Fix

- Tabellen/Jobs & Cache: Die Tabellenregeln wurden geschaerft. Jobs-/Cache-/Timer-/Usage-Tabellen beschreiben ihre Toolbar-/Checkbox-/Fensterbreite-/Select-All-Controls jetzt vollstaendiger im Info-Dialog, und auf der Jobs-&-Cache-Seite bleiben `table_title` und `table_head` oberhalb des Scrollbereichs fixiert. ([#434](https://github.com/thomas682/HA-Addons/issues/434))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.480

### Enhancement

- Logs/Configuration: Neue Option `logge Config` auf der Logs-Seite. Persistierte UI-/Config-Aenderungen werden jetzt performant ueber eine clientseitig persistente Batch-Queue an den Server uebergeben und dort als `INFO`-Eintraege `Config speicherung ...` protokolliert. Die Queue bleibt bis zum Server-Ack im Browser erhalten und wird serverseitig vor dem Ack dauerhaft in `/data` gesichert. ([#432](https://github.com/thomas682/HA-Addons/issues/432))
- Instrumentiert in der ersten Ausbaustufe: Dashboard-`saveState`, Flow-UI-State, serverseitige `app_state`-Saves, Tabellen-Spaltenbreiten, Wrap/Filter, Tabellenhoehen, Sortierung/Spaltensichtbarkeit sowie lokale Persistenzpfade der Settings-Icon-/Outlier-Tabellen. ([#432](https://github.com/thomas682/HA-Addons/issues/432))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.479

### Enhancement

- Einstellungen/Icon-Manager: Die Icon-Tabelle folgt jetzt deutlicher dem Tabellen-Template: Standard- und Customer-Actions sind getrennt, der Status steht in einem eigenen Panel unter der Standard-Action-Leiste, die Zeilenhoehe wird nicht mehr durch lange SVG-Code-Texte aufgeblasen und die Tabellen-Rowcount-Anzeige ist dort ausgeblendet. ([#430](https://github.com/thomas682/HA-Addons/issues/430))
- Tabellen: `Fensterbreite` ist jetzt der Default fuer Tabellen ohne gespeicherte Spaltenbreiten. Die Template-Dokumentation beschreibt dies sowie den separaten Status-/Info-Panel-Block unterhalb der Standard-Action-Leiste. ([#430](https://github.com/thomas682/HA-Addons/issues/430))
- Einstellungen/Icon-Manager: Unter `Nur ueberschrieben` wird jetzt direkt erlaeutert, dass nur geaenderte Iconsaetze angezeigt werden, die ueber die Einstellungen angepasst wurden. ([#431](https://github.com/thomas682/HA-Addons/issues/431))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.478

### Enhancement

- Statistik/Messwertauswahl: Ein gemeinsames Auswahl-Template auf Basis des Dashboard-Layouts wurde eingeführt und die Statistik-Seite verwendet dieses Template jetzt statt einer separaten Struktur. ([#427](https://github.com/thomas682/HA-Addons/issues/427))
- Dashboard/Raw: Die Raw-Aktionsleisten wurden in Standard- und Customer-Actions getrennt, `Abbruch` steht direkt neben `Aktualisieren`, `Reparatur-Assistent` und `Automatikkorrektur` stehen neben `Fensterbreite`, das Icon von `Zeile kopieren` wurde entfernt und der Refresh nutzt das bestehende Raw-Fenster ohne den sichtbaren Zeilenumfang zu verkürzen. ([#426](https://github.com/thomas682/HA-Addons/issues/426))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.477

### Enhancement

- Dashboard/Raw Graph: Der Tooltip im Kontext-Graph (`graph_ctx_plot`) zeigt jetzt wieder alle verfuegbaren Informationen zum Messwertpunkt unter dem Mauszeiger an, inklusive Zeit, Wert, Aggregation, Measurement, Field, `entity_id` und `friendly_name`. ([#425](https://github.com/thomas682/HA-Addons/issues/425))

### Fix

- Dashboard/Raw: Die serverseitige Delete-/Change-Engine wurde fuer InfluxDB-Sonderfaelle weiter gehaertet, damit der reproduzierte Raw-Delete-Flow stabil `200` liefert. ([#424](https://github.com/thomas682/HA-Addons/issues/424))
- Datenpflege / DQ: Der Fallback fuer problematische Serieninventar-Abfragen ist jetzt im produktiven DQ-Lauf aktiv; reproduzierte Runs erreichen `done` statt `error`. ([#429](https://github.com/thomas682/HA-Addons/issues/429))
- Verdichtung: Der JSON-Fehlerpfad fuer fehlende Rollup-Source-Buckets bleibt aktiv und verhindert den generischen HTML-500 in der Preview. ([#428](https://github.com/thomas682/HA-Addons/issues/428))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.476

### Fix

- Dashboard/Raw: Das Loeschen markierter Raw-Werte liefert keinen HTML-500 mehr. Auf InfluxDB-Servern ohne feldgenaue Delete-Unterstuetzung wird der Delete-Pfad jetzt serverseitig kontrolliert abgefangen und als funktionsfaehiger API-Flow ausgefuehrt. ([#424](https://github.com/thomas682/HA-Addons/issues/424))
- Verdichtung: Die Rollup-Preview faellt bei fehlendem Source-Bucket nicht mehr als HTML-500 aus, sondern liefert einen strukturierten API-Fehler zurueck. ([#428](https://github.com/thomas682/HA-Addons/issues/428))
- Datenpflege: Der DQ-/Datenpflege-Lauf bricht bei problematischen Serien-Inventar-Abfragen nicht mehr mit einem Influx-Panic ab; es gibt jetzt einen robusteren Fallback-Inventarpfad, sodass der Lauf bis `done` durchlaufen kann. ([#429](https://github.com/thomas682/HA-Addons/issues/429))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.475

### Fix

- Issue-Report: Der Issue-Composer bleibt jetzt innerhalb des Viewports scrollbar und der Submit-Button ist direkt bedienbar. Die Anhang-Hilfe nutzt keinen fehlenden Bildpfad mehr, sodass der Bugreport-Flow auf dem Dashboard wieder sichtbar und benutzbar ist. ([#423](https://github.com/thomas682/HA-Addons/issues/423))
- Dashboard: Die Analysis-Checklist erzeugt bei fehlenden Step-Keys nun stabile Fallback-Schluessel pro Schritt und verursacht dadurch keine wiederholten Pickkey-/Instancekey-Kollisionen mehr. ([#423](https://github.com/thomas682/HA-Addons/issues/423))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.474

### Fix

- Einstellungen/Console: Die verbleibenden kaputten `data-ui`-Selektor-Strings in `_topbar.html` wurden repariert und die Auto-Pickkey-Statistik wird im Normalbetrieb nicht mehr als Warnung ausgegeben. Die Einstellungsseite ist damit im Standardbetrieb ohne Console-Meldungen. 
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.473

### Fix

- Einstellungen/Icon-Manager: Die Settings-Seite rendert Icon-Palette und Vorschau jetzt nur noch mit dem extrahierten SVG-Markup statt mit kompletten UI-Elementen. Dadurch verschwindet der verbleibende `Invalid regular expression`-Fehler auf `/config`, und die dort vorher mitgerenderten Fremd-Buttons erzeugen keine Pickkey-Kollisionen mehr. 
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.472

### Fix

- Picker/Registry: Die Registry ignoriert jetzt Template-/Blueprint-Knoten explizit, mehrere statische Doppelbelegungen in `performance`, `restore`, `export`, `import`, `history` und `stats` wurden entkoppelt, und ein Test-Gate blockiert neue statische Pickkey-Duplikate im Markup. ([#422](https://github.com/thomas682/HA-Addons/issues/422))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.471

### Enhancement

- Dialoge: Reaktions-/Bestaetigungsdialoge nutzen jetzt einen separaten Confirm-Dialog statt des bisherigen Info-/Status-Popups. Die migrierten Raw-/Job-/Backup-/Restore-Aktionen zeigen `OK`/`Abbrechen` in einem eigenen Template und jeder Popup-/Confirm-Dialog blendet rechts unten seinen Picker-Key und den verwendeten Template-Namen ein. ([#420](https://github.com/thomas682/HA-Addons/issues/420))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.470

### Fix

- Einstellungen/Icon-Manager: Doppelte SVGs in der Palette werden nur noch einmal gezeigt, die ersten vier Tabellenspalten bleiben beim horizontalen Scrollen fixiert, und `Edit` sowie Doppelklick oeffnen den Inline-Editor wieder zuverlaessig. ([#420](https://github.com/thomas682/HA-Addons/issues/420))
- Picker/UI: Backup-Query-Detailbereiche verwenden eigene Panel-Pickkeys statt Button-Pickkeys, und die letzten bekannten button-spezifischen `width:100%`-Sonderregeln wurden auf normale Breiten zurueckgestellt. ([#420](https://github.com/thomas682/HA-Addons/issues/420))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.469

### Fix

- Einstellungen/Icon-Manager: Die ersten vier Spalten der Icon-Tabelle (`Area`, `data-ui Key`, `Label`, `SVG (Override)`) bleiben jetzt beim horizontalen Scrollen fixiert; die Icon-Palette zeigt gleiche SVGs nur einmal, und der Inline-Editor wird bei Doppelklick oder `Edit` wieder zuverlässig geöffnet. ([#420](https://github.com/thomas682/HA-Addons/issues/420))
- Picker/UI: Echte Pickkey-Duplikate in Backup-Query-Detailbereichen wurden entkoppelt, und bekannte `button width:100%`-Spezialregeln wurden auf normale Button-Breiten zurückgestellt. ([#420](https://github.com/thomas682/HA-Addons/issues/420))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.468

### Fix

- Einstellungen/Icon-Manager: Config-JavaScript parst wieder fehlerfrei, die Icon-Tabelle behaelt ihre Sortierung bei Zeilenselektion, `SVG (Override)` startet mit dem sichtbaren SVG-Code im Editor, `Enter` speichert direkt, und die Toolbar-Buttons bleiben auf normaler Breite. ([#420](https://github.com/thomas682/HA-Addons/issues/420))
- Einstellungen/Icon-Manager: Eine Drag-and-Drop-Icon-Palette oberhalb der Tabelle erlaubt das Uebernehmen von SVGs auf Zielzeilen sowie das Kopieren von Icons zwischen Tabellenzeilen per Drag-and-Drop. ([#420](https://github.com/thomas682/HA-Addons/issues/420))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.467

### Fix

- Einstellungen/Picker: Wiederholte Config-Sektionen verwenden jetzt eindeutige fachliche Bereichskeys statt mehrfach `config_settings.section_root`, und die automatische `instancekey`-Deduplizierung nutzt stabile Geschwister-/Pfad-Signaturen ohne endlose `.auto...auto...`-Ketten. ([#420](https://github.com/thomas682/HA-Addons/issues/420))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.466

### Enhancement

- Picker/S-Picker: Auch die verbliebenen statischen Dashboard-Markup-Bereiche setzen jetzt explizite lesbare `data-ib-pickkey`-Werte direkt im Template, sodass `data-ui` und Pickkey repo-weit sichtbar gepaart sind. ([#420](https://github.com/thomas682/HA-Addons/issues/420))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.465

### Enhancement

- Picker/S-Picker: Verbleibende dynamische UI-Builder verwenden jetzt repo-weit lesbare explizite Picker-Keys statt kryptischer Auto-Pfade, und der Fallback verwendet vorhandene `data-ui`/`id`-Werte lesbar weiter. ([#420](https://github.com/thomas682/HA-Addons/issues/420))
- Maintenance: Tested with Home Assistant Core: unknown

## 1.12.464

### Fix

- Einstellungen (Iconbilder): Die Icon-Tabelle listet jetzt auch Dialog-/Overlay-Buttons aus dynamisch erzeugten UIs vollstaendig auf, inklusive `Schliessen`- und `S-Picker`-Buttons der generischen Dialoge.

## 1.12.463

### Enhancement

- Dialoge/Overlays: Aktionsbuttons mit `Schliessen`, `Abbrechen` und `OK` sitzen jetzt konsistent unten rechts; relevante Dialoge bieten zusaetzlich direkt einen `S-Picker`-Einstieg, ohne erst zur Topbar wechseln zu muessen.

## 1.12.462

### Fix

- Dashboard (Raw Daten): Nach dem Loeschen wird die Raw-Tabelle sofort neu geladen und springt auf die naechste verbleibende Zeile. Der Hauptgraph markiert zusaetzlich den aktuell im Kontextgraph sichtbaren Zeitraum.

### Enhancement

- Einstellungen (Iconbilder): Die bestehende Volltextsuche besitzt jetzt `Zurueck`/`Weiter` fuer Trefferzellen in der Icon-Tabelle; die Toolbar-Buttons fuer Auto-/Fensterbreite bleiben kompakt.
- Logs / Popup: Die Logs-Aktionsleiste ist in zwei Reihen aufgeteilt, die beiden Suchfelder behalten eine Mindestbreite, und das Popup-Suchfeld nutzt keine feste Mindestbreite mehr.

## 1.12.461

### Fix

- Dashboard (Raw Daten): Doppelte Zeitstempel (ms-Anzeige) werden jetzt pro Zeile eindeutig behandelt (separate Markierung/Selection). Reparatur-Assistent und Automatikkorrektur erkennen diesen Fall und schlagen vor, einen der Duplikate zu loeschen.

## 1.12.459

### Enhancement

- Datenpflege (DQ): Multi-Resolution Graph im Detaildialog (Raw/Clean/Rollup Vergleich) via neuer API `/api/dq/multi_resolution`. Teil von Epic [#406](https://github.com/thomas682/HA-Addons/issues/406).

## 1.12.460

### Enhancement

- Datenpflege (DQ): Debug/Support Karte im DQ Center via neuer API `/api/dq/debug` (Info/HA/Influx/Logs/Jobs + letzte DQ Runs). Teil von Epic [#406](https://github.com/thomas682/HA-Addons/issues/406).

## 1.12.455

### Enhancement

- Datenpflege (DQ): neue API `/api/dq/orphans` und UI-Karte "Verwaiste Messwerte (HA fehlt)" basierend auf dem letzten DQ-Lauf (Finding `ha_missing`). Teil von Epic [#406](https://github.com/thomas682/HA-Addons/issues/406).

## 1.12.456

### Enhancement

- Datenpflege (DQ): neue API `/api/dq/merge_candidates` und UI-Karte "Zusammenfuehren (Kandidaten)" fuer Umbenennungs-/Merge-Hinweise (gleicher `friendly_name`, aber HA fehlt vs. HA ok). Teil von Epic [#406](https://github.com/thomas682/HA-Addons/issues/406).

## 1.12.457

### Enhancement

- Datenpflege (DQ): "Zusammenfuehren" Kandidaten koennen jetzt `Kombinieren` mit vorausgefuellten Feldern oeffnen (Query-Prefill in `/combine`). Teil von Epic [#406](https://github.com/thomas682/HA-Addons/issues/406).

## 1.12.458

### Enhancement

- Datenpflege (DQ): neue API `/api/dq/migration_candidates` und UI-Karte "Migration (Kandidaten)" fuer entity_id ohne Domain (object_id), die auf eine konkrete HA Entity aufgeloest werden koennen. Teil von Epic [#406](https://github.com/thomas682/HA-Addons/issues/406).

## 1.12.454

### Enhancement

- Verdichtung (Rollup): neue Seite `Verdichtung` fuer Clean -> Rollup Downsampling mit Pflicht-Backup (ZIP + sha256), Preview, Run-Historie und One-Click Restore inkl. Restore-Preview. Rollup nutzt ChangeBlocks fuer Writes/Deletes/Restore und kann optional die Quelle im Zeitfenster loeschen (nach erfolgreichem Write). ([#412](https://github.com/thomas682/HA-Addons/issues/412))

### Maintenance

- Timer: `rollup` ist in `/api/timers` integriert (Schedule/Start/Cancel) und kann optional automatisch laufen (`rollup_auto_update` + `rollup_refresh_mode`).
- API: neue Endpunkte `/api/rollup/*` (Profiles/Preview/Backup/Run/Restore/Jobs).
- QA: `python3 -m py_compile influxbro/app/app.py`.

## 1.12.447

### Enhancement

- Change-Service Basis: persistente ChangeBlocks (Schema v1) inkl. ChangeItems und vollständiger Point Identity. Payloads werden unter `/data/change_blocks` gespeichert (inline oder als JSON-Gzip), inkl. zentraler Save/Load/List/Validate-Funktionen. ([#401](https://github.com/thomas682/HA-Addons/issues/401))

### Maintenance

- API: neue read-only Endpunkte `/api/change_blocks_v2` und `/api/change_block` (Storage-basiert, unabhängig von Influx).

## 1.12.448

### Enhancement

- Change-Service Engine: execute/undo/repeat fuer ChangeBlocks inkl. Konfliktpruefung (ok/conflict/missing/ambiguous/type_mismatch/already_applied) und idempotentem Verhalten. ([#402](https://github.com/thomas682/HA-Addons/issues/402))

### Maintenance

- API: neue Endpunkte `/api/change_block/validate`, `/api/change_block/execute`, `/api/change_block/undo`, `/api/change_block/repeat`.

## 1.12.450

### Enhancement

- ChangeBlocks UI: History-Seite zeigt jetzt eine ChangeBlocks-Liste inkl. Detailansicht, Undo/Repeat Preview (validate) und Konfliktanzeige. API `/api/change_block` kann Items optional paginieren (`items_offset/items_limit`). ([#404](https://github.com/thomas682/HA-Addons/issues/404))

## 1.12.451

### Enhancement

- Theme-System (MVP): globales Farbschema (`ui_theme_mode`) + Akzentfarbe (`ui_theme_accent`) inkl. Sofortwirkung ohne Neustart. Basis-UI nutzt zentrale Tokens (Background/Surface/Text/Border/Inputs/Buttons/Tables) und Plotly-Layouts werden theming-sensitiv gesetzt. ([#405](https://github.com/thomas682/HA-Addons/issues/405))

## 1.12.453

### Enhancement

- ChangeBlocks UI: Detailansicht zeigt jetzt ChangeItems (Alt/Neu) und nutzt Preview-Ergebnisse fuer aktuellen DB-Wert (cur/exp) pro Item, inkl. Paging fuer grosse Blocks. Validate liefert dazu `current_value/current_point/expected_value` je Item. ([#404](https://github.com/thomas682/HA-Addons/issues/404))

## 1.12.452

### Maintenance

- Change-Service Härtung: Schreiboperationen sind jetzt konsequent auf InfluxDB v2 beschraenkt. v1-Schreibpfade (z.B. raw_overwrite/fullrestore) sind deaktiviert, um direkte Influx Writes ausserhalb des Change-Service zu vermeiden. Undo-Status blendet Aktionen mit `undo_supported=false` aus. ([#400](https://github.com/thomas682/HA-Addons/issues/400))

## 1.12.449

### Enhancement

- Change-Service Migration: Bulk- und Range-Schreibpfade laufen jetzt ueber persistente ChangeBlocks (Chunking via `child_blocks`), inkl. Restore/Copy, Combine, Import und Delete. Undo/Repeat nutzt ChangeBlock-Referenzen (ref-only) statt direkte Writes. UI zeigt `change_block_id` bei relevanten Jobs/Aktionen. ([#403](https://github.com/thomas682/HA-Addons/issues/403))

## 1.12.440

### Enhancement

- Diagnose: neue Best-effort "Series Inventory / Storage Advisor" Ansicht inkl. Measurements-Uebersicht, lauteste Serien (Schreibrate im Zeitfenster), Mapping-Probleme, Stale-Liste und Export (JSON/CSV/MD). ([#387](https://github.com/thomas682/HA-Addons/issues/387))

### Maintenance

- API: neue Endpunkte `/api/series_inventory` und `/api/series_inventory_export`.
- QA: `python3 -m py_compile influxbro/app/app.py` (pytest in dieser Umgebung nicht verfuegbar).

## 1.12.441

### Enhancement

- Monitor: Watchlists/Health-Scans (persistente Watchlists, geplante Laeufe via Timer Jobs, Inbox mit Delta-Logik). Inbox ist als auffaellige Karte im Monitor sichtbar und zusaetzlich global als Topbar-Badge verlinkt (Jump zu Monitor Inbox).

### Maintenance

- API: neue Endpunkte `/api/watchlists`, `/api/watchlists/run`, `/api/watchlists/runs`, `/api/watchlists/inbox`, `/api/watchlists/inbox/mark`, `/api/watchlists/inbox_summary`.
- Timer-Jobs: Watchlists erscheinen zusaetzlich in `/api/timers` und koennen dort (Modus/History/Start) genutzt werden.
- QA: `python3 -m py_compile influxbro/app/app.py`.

## 1.12.442

### Fix

- Watchlists/Inbox: `Mute/Snooze` unterdrueckt Wiederauftauchen korrekt (Snooze-Expiry reaktiviert), Inbox Default-Filter zeigt wirklich nur offene Items.

### Enhancement

- Monitor: Minimal-UI fuer Watchlists + Runs (Edit/Save/Run Selected) ergaenzt.

## 1.12.443

### Enhancement

- Datenpflege Center Phase 1: neue Seite `Datenpflege` inkl. QualityRun/Findings, Score (0-100), Ampelstatus und read-only Analyse mit HA-Metadaten als Primaersignal (Quelle: Home Assistant). Export als JSON/Markdown, Jump zum Dashboard und Supportdaten-Download. ([#407](https://github.com/thomas682/HA-Addons/issues/407))

### Maintenance

- API: neue Endpunkte `/api/dq/quality_run/start`, `/api/dq/quality_run`, `/api/dq/quality_runs`, `/api/dq/quality_run/export`.

## 1.12.444

### Enhancement

- Datenpflege Center Phase 2: Repair Proposals + Repair Plans aus Phase-1-Findings ableiten (Preview-only). Proposals zeigen Risiko/Confidence und bereiten Preview-Payloads fuer `/api/change_preview` vor (keine Ausfuehrung). ([#408](https://github.com/thomas682/HA-Addons/issues/408))

### Maintenance

- API: neue Endpunkte `/api/dq/repair/generate`, `/api/dq/repair/plans`, `/api/dq/repair/proposals`, `/api/dq/repair/proposal`.

## 1.12.445

### Enhancement

- Datenpflege Center Phase 3: Freigabe-Warteschlange, Automatikprofile und AutoRules (A/B/C/D Klassifikation) inkl. Protokollierung. Ausfuehrung bleibt explizit gesperrt, bis #400 integriert ist. ([#409](https://github.com/thomas682/HA-Addons/issues/409))

### Maintenance

- API: neue Endpunkte `/api/dq/phase3/state`, `/api/dq/phase3/profile/save`, `/api/dq/phase3/rules/save`, `/api/dq/phase3/approve`.

## 1.12.446

### Enhancement

- Datenpflege Center Phase 4: HA-Metadaten-Vorschlaege (Quelle: Home Assistant) inkl. YAML Snippets und Patch-Dateien als Preview/Export. Keine automatische Aenderung unter `/config`, keine HA Reloads. ([#410](https://github.com/thomas682/HA-Addons/issues/410))

### Maintenance

- API: neue Endpunkte `/api/dq/ha/generate`, `/api/dq/ha/proposals`, `/api/dq/ha/proposal`, `/api/dq/ha/patch`.

## 1.12.439

### Enhancement

- Logs/Bugreport: Support-Bundle als ZIP (Preview + Download) mit konfigurierbaren Inhalten und serverseitiger Redaction. In Logs als neuer Button verfuegbar; im Git Bugreport-Flow optional zusaetzlich erzeugbar. ([#388](https://github.com/thomas682/HA-Addons/issues/388))

### Maintenance

- API: neue Endpunkte `/api/support_bundle/preview` und `/api/support_bundle/download`.

## 1.12.438

### Enhancement

- Tabellen-Standard: dynamische Action-Leiste fuer Tabellen (Spec-gesteuert) mit Statuszeile direkt unter den Buttons. Fuer `raw_outlier_tbl` (Dashboard Ausreißer) werden jetzt alle Tabellen-Buttons dynamisch erzeugt und in einer festen Reihenfolge angeordnet: Aktualisieren, Abbruch, Tabelleninfo, Spalten ein-/ausblenden, Autobreite, Fensterbreite, Umbruch, Spaltenfilter, Kopieren, Zeile kopieren, Export (CSV). (User-Request)
- Tabellen: Export-Button (CSV) hinzugefuegt.
- Tabellen: Spalten-Resizer arbeitet jetzt am Spaltenrand und veraendert nur die beiden Nachbarspalten (konstante Gesamtbreite am Zugpunkt).

### Maintenance

- Tooltips/Spec: Tabelleninfo fuer `raw_outlier_tbl` aktualisiert.

## 1.12.437

### Enhancement

- Dashboard Ausreißer: Info-Button in der Tabellen-Aktionsleiste entfernt (TS-2026-0005). Die Abschnittsbeschreibung wird nicht mehr aus diesem Button abgeleitet. (User-Request)

### Maintenance

- Tombstone: `.tombstones.yml` aktualisiert (TS-2026-0005) und TS-2026-0004 Migration-Text angepasst.

## 1.12.436

### Enhancement

- Picker/S-Picker: neues Referenzformat mit 2-stufigem Modell `pk` + `ik`: `<PICK:<Page>|v=1;pk=...;ik=...>`. `data-ib-pickkey` ist `pk`, `data-ib-instancekey` ist `ik` (runtime-eindeutig). Legacy-Strings `<PICK:<Page>|<pickkey>>` bleiben lesbar. ([#399](https://github.com/thomas682/HA-Addons/issues/399))
- Topbar: direkte Pick-String Eingabe im Suchfeld (Enter) inkl. Validierung, klarer Fehlermeldungen, Page-Mismatch und exakter Navigation/Highlight. ([#398](https://github.com/thomas682/HA-Addons/issues/398))

### Maintenance

- AGENTS.md: Pickkey-Regeln um `pk`/`ik` (v1) erweitert.

## 1.12.435

### Enhancement

- Einstellungen: Organizer erweitert. Hauptpunkte und Unterpunkte koennen jetzt verschoben und umbenannt werden (Titel aendert nur die Anzeige, IDs bleiben stabil). Loeschen ist nur bei wirklich leeren benutzerdefinierten Punkten moeglich; Systempunkte zeigen eine klare Sperr-Meldung. Undo/Export/Import arbeiten weiter ueber `settings_layout`. ([#396](https://github.com/thomas682/HA-Addons/issues/396))

### Maintenance

- Backend: `settings_layout` Schema erweitert (Reihenfolge/Titel fuer Gruppen/Untergruppen), Sanitizing/Validierung angepasst.
- QA: `python3 -m py_compile influxbro/app/app.py` (pytest in dieser Umgebung nicht verfuegbar).

## 1.12.434

### Enhancement

- Dashboard Raw: neuer Button `Reparatur-Assistent` (Wizard) fuer typische Datenreparaturen im aktuell sichtbaren Raw-Fenster. Presets fuer bekannte Ausreisser-Typen, Pflicht-Vorschau via `/api/change_preview`, Bulk-Ausfuehrung als Undo-Block via `/api/apply_changes`. ([#385](https://github.com/thomas682/HA-Addons/issues/385))

### Maintenance

- QA: JS/Template-Update (kein neuer Backend-Code).

## 1.12.433

### Enhancement

- Ausreisser: Counterreset-Erkennung in der Suche (Reset-Beginn + Vorfehler-Spikes werden als `counterreset` markiert); GUI: neuer Typ `Counterreset` in der Typauswahl/Anzeige; Raw: `Automatikkorrektur` ist typbasiert und bereinigt bei `Counterreset` die pre-fault Spike-Werte (Reset bleibt erhalten) inkl. Pflicht-Vorschau. ([#390](https://github.com/thomas682/HA-Addons/issues/390))

### Docs

- `MANUAL.md`: `Automatikkorrektur` Verhalten fuer `Counterreset` dokumentiert. ([#390](https://github.com/thomas682/HA-Addons/issues/390))

### Maintenance

- QA: `python3 -m py_compile influxbro/app/app.py` (pytest in dieser Umgebung nicht verfuegbar).

## 1.12.429

### Enhancement

- Dashboard Graph: Kontext- und Haupt-Graph klar getrennt (Marker/Refresh nur Kontext), Detailleiste liegt ueber dem Haupt-Graph, zusaetzliche Min/Max-Leiste fuer den Haupt-Graph, Auswahl-Infozeile ist global fuer beide Graphen. Raw: `Info`-Button zeigt wieder einen Dialog mit Details/History. ([#392](https://github.com/thomas682/HA-Addons/issues/392))

### Docs

- `MANUAL.md`: Topbar-Profil-Info Button entfernt; Graph-Beschreibung an neue Kontext/Haupt-Graph Logik angepasst. ([#392](https://github.com/thomas682/HA-Addons/issues/392))

### Maintenance

- QA: `python3 -m py_compile influxbro/app/app.py` (pytest in dieser Umgebung nicht verfuegbar).

## 1.12.430

### Enhancement

- Backend: technische Basis fuer Vorschauplaene/Change-Blocks/Undo-Preview eingefuehrt: neue API-Endpunkte `/api/change_preview`, `/api/change_blocks`, `/api/change_blocks/undo_preview`; `apply_changes` schreibt zusaetzliche Metadaten (`detected_outlier_type`, `strategy_*`, `source_action`) in die persistente History und in Undo-Meta. ([#394](https://github.com/thomas682/HA-Addons/issues/394))

### Maintenance

- QA: `python3 -m py_compile influxbro/app/app.py` (pytest in dieser Umgebung nicht verfuegbar).

## 1.12.431

### Enhancement

- Dashboard Raw: neuer Vorschau-/Bestaetigungsdialog (Tabelle Alt/Neu) fuer Korrekturen; Smart-Korrektur und Editiermodus nutzen jetzt `/api/change_preview` bevor geschrieben wird. Neuer Button `Automatikkorrektur` (Basis: Nachbar-Interpolation) inkl. Vorschau. Undo fuer Change-Blocks zeigt jetzt ebenfalls eine Undo-Vorschau (via `/api/change_blocks/undo_preview`) vor dem Rollback. ([#395](https://github.com/thomas682/HA-Addons/issues/395))

### Maintenance

- QA: `python3 -m py_compile influxbro/app/app.py` (pytest in dieser Umgebung nicht verfuegbar).

## 1.12.432

### Bugfix

- GUI: Ausreißer-Info Button wurde aus dem Section-Header entfernt und fest in die Ausreißer-Tabellen-Actionbar verschoben (links neben Autobreite); Settings: `config_settings.tbl_icons` hat jetzt eine echte Tabellen-Actionbar (Auto-/Fensterbreite, Umbruch, Spaltenfilter) und Spaltenbreite ist wieder veraenderbar; Spalte "SVG (Override)" zeigt jetzt den effektiven SVG-Code (Override oder Default) statt nur Overrides. ([#397](https://github.com/thomas682/HA-Addons/issues/397))

### Maintenance

- QA: `python3 -m py_compile influxbro/app/app.py` (pytest in dieser Umgebung nicht verfuegbar).

## 1.12.428

### Enhancement

- Einstellungen Export/Import: deterministischer Key-Satz (nur portable `/config`-Settings), fehlende sichtbare Keys (Navigationshilfe, Tooltip-Doc-Mode, Log-Farben) sind enthalten; interne/transiente Keys (z.B. `ui_open_*`, `backup_migrated_to_config`) werden nicht mehr exportiert. ([#393](https://github.com/thomas682/HA-Addons/issues/393))

### Maintenance

- Tests: `.venv/bin/python -m py_compile influxbro/app/app.py`, `.venv/bin/python -m pytest -q tests/test_api_config_io.py`

## 1.12.427

### Enhancement

- UI Picker: kanonische, eindeutige Referenzen via `data-ib-pickkey`; S-Picker kopiert jetzt `<PICK:<Page>|<pickkey>>` und vergibt Pickkeys automatisch auch fuer bestehende UI-Elemente. ([#391](https://github.com/thomas682/HA-Addons/issues/391))
- Dashboard: Rowcount-Anzeige wird fuer die Ausreisser-Tabelle (`raw_outlier_tbl`) ausgeblendet (Opt-out). ([#391](https://github.com/thomas682/HA-Addons/issues/391))

### Docs

- `Template.md` und `AGENTS.md`: Pickkey-Pflicht fuer alle sichtbaren UI-Elementtypen dokumentiert.

### Maintenance

- Tests: `.venv/bin/python -m py_compile influxbro/app/app.py`, `.venv/bin/python -m pytest -q tests/test_api_ui_support.py`, `npx playwright test tests/e2e/dashboard.spec.js -g "desktop keeps main content visible across widths"`

## 1.12.426

### Enhancement

- Einstellungen: neuer Topbar-Button `Verschieben` inkl. Auswahl a-e (Parameterzeilen zwischen Bereichen verschieben, Haupt-/Unterpunkte anlegen/loeschen) mit globaler Speicherung und Undo. Export/Import der Einstellungen sichert die Zuordnungen mit. ([#389](https://github.com/thomas682/HA-Addons/issues/389))
- Dashboard Tabellen: Kopfzeilenfarben der Raw-Tabellen folgen jetzt global `ui_table_header_bg`/`ui_table_header_fg` (Template). ([#389](https://github.com/thomas682/HA-Addons/issues/389))

### Maintenance

- Tests: `.venv/bin/python -m py_compile influxbro/app/app.py`, `.venv/bin/python -m pytest -q tests/test_api_ui_support.py`, `npx playwright test tests/e2e/dashboard.spec.js -g "desktop keeps main content visible across widths"`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.425

### Bugfix

- Desktop Navigation/Layout: `ib_nav_mobile_overlay` wird per JS auf `body` gemountet (nicht mehr als Grid-Child in `.shell`), damit der Overlay-DIV nicht die 2. Grid-Spalte belegt und `main.content` scheinbar "verschwindet". ([#383](https://github.com/thomas682/HA-Addons/issues/383))

### Maintenance

- Tests: `.venv/bin/python -m py_compile influxbro/app/app.py`, `.venv/bin/python -m pytest -q tests/test_dashboard_script_integrity.py tests/test_api_ui_support.py`, `npx playwright test tests/e2e/dashboard.spec.js -g "desktop keeps main content visible across widths"`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.424

### Bugfix

- Desktop Layout: Fallback `height: max(240px, ...)` fuer Sidebar/Content, damit der Inhalt auch dann sichtbar bleibt, wenn Topbar/Pagecard-Hoehenvariablen kurzfristig falsch gemessen werden. ([#383](https://github.com/thomas682/HA-Addons/issues/383))

### Maintenance

- Tests: `.venv/bin/python -m py_compile influxbro/app/app.py`, `.venv/bin/python -m pytest -q tests/test_dashboard_script_integrity.py tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.423

### Bugfix

- Desktop Layout: `shell` Grid nutzt jetzt `minmax(0, 1fr)` + `main.content { min-width:0; }`, damit breite Inhalte (Dashboard/Statistik) den Hauptbereich nicht aus dem Viewport druecken. ([#383](https://github.com/thomas682/HA-Addons/issues/383))

### Maintenance

- Tests: `.venv/bin/python -m py_compile influxbro/app/app.py`, `.venv/bin/python -m pytest -q tests/test_dashboard_script_integrity.py tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.422

### Bugfix

- Mobile Navigation: der Sidebar-Drawer verdeckt beim App-Start nicht mehr den Hauptinhalt (Open-State wird nicht mehr dauerhaft persistiert). ([#382](https://github.com/thomas682/HA-Addons/issues/382))

### Maintenance

- Tests: `.venv/bin/python -m py_compile influxbro/app/app.py`, `.venv/bin/python -m pytest -q tests/test_dashboard_script_integrity.py tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.421

### Enhancement

- Backup/Restore: Speicherziel-Auswahl ("Lokal" + "Share") via neuer Konfiguration `backup_targets`, inkl. Erkennung vorhandener `/share/*` Mounts und Umschaltbarkeit in Backup/Restore UI. ([#381](https://github.com/thomas682/HA-Addons/issues/381))

### Maintenance

- Tests: `.venv/bin/python -m py_compile influxbro/app/app.py`, `.venv/bin/python -m pytest -q tests/test_api_ui_support.py tests/test_api_config_io.py tests/test_dashboard_script_integrity.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.420

### Bugfix

- Backup API: Fix 500 bei `/api/backups` durch fehlendes `return` in `backup_dir()` (konnte zu `None` und damit zu Server-Error beim Listen von Backups fuehren). ([#380](https://github.com/thomas682/HA-Addons/issues/380))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_time_and_stats.py tests/test_api_yaml_flow.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.419

### Bugfix

- Dashboard Ausreißer: rechte Kopf-/Status-Spalte entfernt; Zeilenzaehler (`raw_outlier_row_count`) steht jetzt oberhalb der Tabelle; Info-Icon sitzt in der Tabellen-Action-Leiste. ([#375](https://github.com/thomas682/HA-Addons/issues/375))
- Dashboard: `analysis_status` entfernt; Flow-Checklists zeigen Laufzeit (`ib_flow_dur`) direkt neben der Startzeit (`ib_flow_time`). ([#375](https://github.com/thomas682/HA-Addons/issues/375))
- Raw Daten (DB): `raw_info_inline` ist linksbuendig (keine `space-between`-Ausrichtung mehr). ([#375](https://github.com/thomas682/HA-Addons/issues/375))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py tests/test_dashboard_script_integrity.py tests/test_api_time_and_stats.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.418

### Enhancement

- Dashboard Graph: beim Wiederherstellen des gespeicherten Graph-Zeitraums werden leere/null Werte nicht mehr zu `0` (1970) umgewandelt; die X-Achse startet damit immer im Messwertbereich. ([#376](https://github.com/thomas682/HA-Addons/issues/376))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py tests/test_dashboard_script_integrity.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.417

### Enhancement

- Dashboard: InfoZeile (`div.ib_section_desc_row`) sitzt jetzt direkt unter der Summary und nutzt damit immer die volle Summary-Breite. ([#373](https://github.com/thomas682/HA-Addons/issues/373))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.416

### Bugfix

- Tooltips: native Browser-Tooltips (grau) werden jetzt global und robust unterdrueckt (auch wenn JS irgendwo ein `title` setzt). Alle Tooltips laufen nur noch ueber das dunkle HTML-Overlay. ([#360](https://github.com/thomas682/HA-Addons/issues/360))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py tests/test_api_time_and_stats.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.415

### Bugfix

- Einstellungen: Iconbilder Tabelle nach Template-Layout; Actions-Spalte entfernt, Zeilenselektion und Toolbar-Buttons `Edit`/`Undo`/`Jump`. SVG Override wird direkt in der Tabelle editiert. ([#379](https://github.com/thomas682/HA-Addons/issues/379))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`, `npx playwright test tests/e2e/dashboard.spec.js -g "Settings Page"`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.414

### Bugfix

- Dashboard Graph: Refresh-Button nutzt den gleichen guarded Load-Flow wie "Aktualisieren" und verhindert damit Mehrfachklick-Fetch-Fehler ("Failed to fetch"). ([#378](https://github.com/thomas682/HA-Addons/issues/378))
- Popup: Volltextsuche sucht immer im aktuell angezeigten Inhalt (z.B. nach "Logs (5min)"). ([#377](https://github.com/thomas682/HA-Addons/issues/377))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`, `pytest -q tests/test_dashboard_script_integrity.py`, `npx playwright test tests/e2e/dashboard.spec.js`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.413

### Enhancement

- iPhone adaption: Safe-Area Insets (top/left/right/bottom), iOS Input-Font >= 16px (verhindert Auto-Zoom), 44px Touch-Targets und mobile Navigation als Drawer (Hamburger) ueber die Titelzeile. ([#370](https://github.com/thomas682/HA-Addons/issues/370))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`, `pytest -q tests/test_dashboard_script_integrity.py`, `npx playwright test tests/e2e/dashboard.spec.js`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.412

### Enhancement

- Dashboard Raw: Neue Aktionsleiste "Intelligente Korrektur" mit Block-Aenderungen fuer ausgewaehlte Bereiche (Linear-Interpolation oder Erstwert kopieren), inkl. Vorschau-Dialog und Undo als Block. ([#372](https://github.com/thomas682/HA-Addons/issues/372))

### Maintenance

- API: `apply_changes` begrenzt die Anzahl Aenderungen pro Request (max 2000)
- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`, `pytest -q tests/test_dashboard_script_integrity.py`, `npx playwright test tests/e2e/dashboard.spec.js`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.411

### Enhancement

- UI: Schriftgroessen sind jetzt auf 4 GUI-Gruppen und 3 Tabellen-Gruppen zusammengefasst (Einstellungen nennen die betroffenen Kategorien explizit). Zoom +/- skaliert die gesamte UI proportional (Controls/Abstaende/Tabellen/Graphen). ([#371](https://github.com/thomas682/HA-Addons/issues/371))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`, `pytest -q tests/test_api_time_and_stats.py`, `npx playwright test tests/e2e/dashboard.spec.js`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.410

### Enhancement

- Topbar (iPhone): `nav.donate` wird rechts neben dem Brand-Block angezeigt (statt als eigene Zeile), um die Titelzeile kompakter zu halten. ([#369](https://github.com/thomas682/HA-Addons/issues/369))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`, `pytest -q tests/test_api_time_and_stats.py`, `npx playwright test tests/e2e/dashboard.spec.js`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.409

### Enhancement

- Topbar: Auf sehr schmalen Breiten (iPhone) kann der rechte Block (Profil/Picker/Zoom/Suche/Buttons) ueber einen Toggle ein- und ausgeklappt werden. ([#368](https://github.com/thomas682/HA-Addons/issues/368))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`, `pytest -q tests/test_api_time_and_stats.py`, `npx playwright test tests/e2e/dashboard.spec.js`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.408

### Enhancement

- Dashboard: `analysis_checklist` nutzt jetzt die moderne kompakte Abarbeitungsliste (ausklappbare Details, Progress-Header, Fehler-Filter) und dasselbe Design wird fuer `load_status`/Cacheflow verwendet. ([#365](https://github.com/thomas682/HA-Addons/issues/365))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`, `npx playwright test tests/e2e/dashboard.spec.js`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.407

### Bugfix

- UI: `ib_cfg_icon` + Info-Button werden nicht mehr in der Summary-Titelzeile angezeigt, sondern als Zeile im Section-Body (mit Kurzbeschreibung). ([#362](https://github.com/thomas682/HA-Addons/issues/362))
- Tabellen: Kopfzeilen-Design (Hintergrund/Textfarbe) ist global parametrierbar und leere Tabellen zeigen mindestens N Zeilen (global). ([#362](https://github.com/thomas682/HA-Addons/issues/362))
- Dashboard: Ausreisser-Typen-Panel (`analysis_types_selected`) wurde vor die Ausreisser-Tabellenaktionen verschoben; Reset-Button und "Ignoriert" Checkbox wurden aus der UI entfernt. ([#362](https://github.com/thomas682/HA-Addons/issues/362))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`, `npx playwright test tests/e2e/dashboard.spec.js`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.406

### Bugfix

- Diagnose: `storage_tbl` sortiert Groessen jetzt korrekt (unabhaengig von der Einheit/Anzeige) und `mtime` wird lesbar formatiert; Diagnose-Tabellen zeigen wieder sichtbare Kopf-/Zeilen-/Spaltenlinien. Trend-Graph nutzt eine solid Linie und zeigt X-/Y-Achsenbeschriftungen. ([#358](https://github.com/thomas682/HA-Addons/issues/358))

### Security

- Diagnose: Tabellen-Rendering verwendet jetzt `textContent` statt `innerHTML`, um XSS ueber Dateinamen/Pfade/Log-Details zu vermeiden. ([#358](https://github.com/thomas682/HA-Addons/issues/358))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.405

### Bugfix

- Dashboard: Beim Verlassen der Seite und erneuten Aufruf werden jetzt alle relevanten Panels/States wiederhergestellt (u.a. Caching `load_status`, Analyse-Checkliste/Status, Ausreisser/Raw/Graph State). Playwright-Coverage ergaenzt. ([#363](https://github.com/thomas682/HA-Addons/issues/363))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_ui_support.py`, `npx playwright test tests/e2e/dashboard.spec.js`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.404

### Bugfix

- Einstellungen: Speichern-Button wurde entfernt; Aenderungen werden jetzt sofort (debounced) automatisch gespeichert (input/change) und YAML-Import triggert ebenfalls Auto-Save. ([#364](https://github.com/thomas682/HA-Addons/issues/364))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.403

### Bugfix

- Tooltips: Native Browser-Tooltips (grau) werden jetzt konsequent deaktiviert (title -> data-ib-title), damit kein Doppel-Tooltip mehr erscheinen kann. ([#360](https://github.com/thomas682/HA-Addons/issues/360))

### Enhancement

- Einstellungen: `Iconbilder` zeigt jetzt auch Default-/effektive Icons in Preview/SVG und der Editor ist robuster initialisiert (nach Settings-Restructure); Edit/Doppelklick funktionieren wieder zuverlaessig. ([#366](https://github.com/thomas682/HA-Addons/issues/366))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.402

### Enhancement

- Einstellungen: Neues Kapitel `Iconbilder` (project-wide Inventar der `data-ui` Keys) mit SVG-Editor pro Key inkl. Preview, Sanitization + Groessenlimit; Speicherung im aktiven UI-Profil und sofortige Anwendung auf Buttons. ([#361](https://github.com/thomas682/HA-Addons/issues/361))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.401

### Bugfix

- Dashboard: Summary-Interaktionen (Buttons/Links innerhalb von `summary`) sind wieder klickbar; der globale Stopper blockiert keine Target-Events mehr. ([#359](https://github.com/thomas682/HA-Addons/issues/359), [#360](https://github.com/thomas682/HA-Addons/issues/360))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.400

### Bugfix

- Tooltips: Das Tooltip-Overlay blockiert keine Klicks mehr, wenn es unsichtbar ist; dadurch funktionieren Buttons in Summary-Actions (z.B. `ib_cfg_icon` -> Einstellungen) wieder zuverlaessig. ([#360](https://github.com/thomas682/HA-Addons/issues/360), [#359](https://github.com/thomas682/HA-Addons/issues/359))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.399

### Bugfix

- Dashboard: Statusleiste unten (`errors_main.panel_statusbar`) ist auch bei Wrap/Mobile vertikal sauber ausgerichtet; Tooltips sind konsistent (kein Doppel-Tooltip) und zeigen unten immer den Element-Key als `<data-ui>`. Tooltips enthalten zusaetzlich einen Doku-Button (oeffnet `Handbuch`, Suchbegriff = Key; Open-Mode konfigurierbar). ([#360](https://github.com/thomas682/HA-Addons/issues/360))
- Picker: S-Picker/Picker kopieren bei Fallback-Elementen (ohne data-ui/id) jetzt einen expliziten `Fallback:` Marker statt `<Dashboard,,>`. ([#359](https://github.com/thomas682/HA-Addons/issues/359))
- Dashboard/Caching: Der Button `löschen` (`dashboard_caching.btn_loeschen`) wird wieder korrekt als Icon-only Button erkannt. ([#360](https://github.com/thomas682/HA-Addons/issues/360))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.398

### Bugfix

- Dashboard: Snapshot-Persistenz fuer Cache-Check/Ergebnisse ist robuster (kein Ueberschreiben des letzten gueltigen Snapshots durch fruehe/leere Renders; Snapshot-Groessen sind begrenzt, um sessionStorage-Quota-Probleme zu reduzieren). ([#356](https://github.com/thomas682/HA-Addons/issues/356))

### Enhancement

- Topbar (Dashboard): Profile-Buttons sind jetzt icon-only und nutzen neue Icons fuer `Anwenden`, `Speichern`, `Info`, `Picker` und `S-Picker` (dark-mode via `currentColor`). ([#357](https://github.com/thomas682/HA-Addons/issues/357))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.397

### Bugfix

- Dashboard/Raw: Raw-Kontext in der Ausreisser-Tabelle bleibt stabil und schrumpft nicht mehr bei wiederholter Selektion; zusaetzlich gibt es einen echten Editiermodus (staged Inline-Edits mit `Editieren` + `Uebernehmen`), und `Aktualisieren` startet die Ausreisserpruefung fuer den Bereich erneut. ([#352](https://github.com/thomas682/HA-Addons/issues/352))

### Enhancement

- History: Serverseitiges Undo/Repeat (Redo als "Repeat") fuer schreibende Messwertaktionen inkl. persistenter Undo-History unter `/config/influxbro/history`, Konfliktpruefung sowie Sperre/Reset bei inkompatibler History. Neues Setting: `undo_history_max` (Default 100). ([#354](https://github.com/thomas682/HA-Addons/issues/354))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.396

### Enhancement

- Dashboard/UX: Query-Verlauf und Query-Dialoge zeigen Laufzeiten jetzt als `dur_ms` in Millisekunden; Analyse-Typen werden in einem Panel als Chips dargestellt (abgewaehlte Typen durchgestrichen), Cache-Timeline-Toggles nutzen denselben Chip-Style und Analyse kann per "abbrechen" sauber gestoppt werden. ([#355](https://github.com/thomas682/HA-Addons/issues/355))
- Picker/Settings: Picker kopiert bei Cache-Outlier-Typ Buttons zusaetzlich den `data-cache-oltype` Wert; S-Picker Fallback ist informativer (CSS + kurzer Text) und dynamische Chips/Buttons erhalten stabile `data-ui` Tokens. Settings-Dashboard ist in Subsections gegliedert und deren Reihenfolge wird global (serverseitig) gespeichert. ([#355](https://github.com/thomas682/HA-Addons/issues/355))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.395

### Enhancement

- UI: Tooltips werden jetzt als eigenes HTML Tooltip-Overlay angezeigt (statt ausschliesslich Browser-`title`). Zusaetzlich werden kleine Text-Buttons (`.btn_sm`) bei exakt passenden Labels global auf Icon-only umgestellt (Label bleibt als `aria-label`/Tooltip erhalten). ([#353](https://github.com/thomas682/HA-Addons/issues/353))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.394

### Enhancement

- Dashboard/Caching: Ausreisser-Marker im Analysecache-Zeitstrahl sind jetzt nach Typ eingefaerbt und koennen pro Typ ein-/ausgeblendet werden (wirkt nur auf den Zeitstrahl, nicht auf Tabellen/Counts). ([#353](https://github.com/thomas682/HA-Addons/issues/353))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.393

### Bugfix

- Tabellen: Client-Sortierung parst de-DE Zeitstempel (`dd.mm.yyyy HH:MM:SS(.mmm)`) jetzt robust, statt auf unzuverlaessiges `Date.parse` zu setzen. ([#353](https://github.com/thomas682/HA-Addons/issues/353))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.392

### Bugfix

- S-Picker: Fallback-Ausgabe ist jetzt stabil als `fallback:<css>` (keine leeren Platzhalter wie `<Logs,,>` mehr) und wird im Multi-Pick ebenso im `<page,data-ui,id>` Format abgebildet. ([#353](https://github.com/thomas682/HA-Addons/issues/353))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.391

### Bugfix

- Analyse/Worklog: `/api/analysis_history_event` speichert `trace_id` und `dur_ms` als Top-Level-Felder und loggt sie auch in die Add-on Logs, sodass History/Performance sauber korrelierbar sind. Zusaetzlich erzeugt das Dashboard fuer langsame "Daten laden" Phasen (Query/Statistik) eigene Detail-Events. ([#353](https://github.com/thomas682/HA-Addons/issues/353))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_analysis_history.py`, `pytest tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.390

### Bugfix

- Dashboard/Caching: Hybrid-Restore aus `sessionStorage` stellt nach Reload wieder Timeline und Aenderungs-Liste aus dem gespeicherten Cache-Plan her (inkl. Handler fuer Toggles/Info), statt nur die Summary anzuzeigen. ([#353](https://github.com/thomas682/HA-Addons/issues/353))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py::test_dashboard_cache_restore_renders_timeline_and_changes_from_restored_plan`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.389

### Bugfix

- Dashboard/Ausreißer: Outlier-Tabelle startet mit 15 sichtbaren Zeilen (statt 5), Row-Counter ist kompakt (`filtered / total`), Tabellenhoehe-Resize greift auch dann sauber, wenn zuvor ein Row-basiertes `max-height` aktiv war, und Spalten-Resize triggert keinen Sort-Klick mehr. ([#351](https://github.com/thomas682/HA-Addons/issues/351))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.388

### Bugfix

- Dashboard/Analyse: `/api/outlier_windows` berechnet before/after Fenster wieder deterministisch (Center-Punkt wird sicher ausgeschlossen), normalisiert Sort/Limit lokal (robust gegen FakeQueryApi in Tests) und loest `point_index` aus dem Zeitstempel auf. ([#349](https://github.com/thomas682/HA-Addons/issues/349))
- Selector-Defaults: Selector-Endpunkte und `resolve_signal` nutzen ohne explizites `range/start/stop` wieder All-Time (`1970-01-01T00:00:00Z`) statt implizit 24h bzw. 30d Safety-Clamp. ([#349](https://github.com/thomas682/HA-Addons/issues/349))

### Maintenance

- Tests: brittle UI-Assertions/obsolete Endpoints aktualisiert, `pytest tests/` wieder gruen. ([#350](https://github.com/thomas682/HA-Addons/issues/350))
- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.387

### Bugfix

- Topbar/HA Ingress: `page_view` und `ui_event` POSTs senden die CSRF-Header (`X-InfluxBro-Request`, `X-Requested-With`) jetzt explizit, unabhaengig vom globalen fetch-Monkey-Patch aus `_nav.html`. Damit entfaellt die 403-Ablehnung unter HA Ingress auch dann, wenn der Topbar-Code vor dem Monkey-Patch ausgefuehrt wird oder ein Proxy den Header entfernt. Client-seitige `page_view`-Fehler werden zusaetzlich per `./api/client_log` ins Add-on-Log gemeldet. ([#342](https://github.com/thomas682/HA-Addons/issues/342))
- Dashboard/Caching: Info-Button im Analysecache-Zeitstrahl (`cache_timeline.btn_info`) zeigt wieder Details an. Ursache war, dass der globale `ib_info_icon`-Delegator in `_tooltips.html` den Klick vor dem spezifischen Handler abfing und mit leerem `data-info-title/body` ein leeres Popup anzeigte. Fix: der globale Delegator ueberspringt Buttons mit `data-cache-info` bzw. `data-info-skip-global` oder ohne `data-info-title/body`. Der Cache-Detail-Handler hat zusaetzlich Debounce, robustere Fehlerbehandlung (Meldung bei Netz-/API-Fehler) und loggt Fehler an `./api/client_log`. ([#343](https://github.com/thomas682/HA-Addons/issues/343))

### Enhancement

- Dashboard/Caching: Analysecache-Zeitstrahl modernisiert. Ausreisser-Markierungen sind nun breiter, abgerundet und zeigen beim Hover einen Tooltip mit Zeitstempel, Typ und Wert. Backend liefert zusaetzlich `outlier_details` (Zeit, Typen, Wert) pro Segment; das bestehende `outlier_times`-Feld bleibt fuer Rueckwaertskompatibilitaet erhalten. ([#346](https://github.com/thomas682/HA-Addons/issues/346))
- Dashboard/Analyse: Button-Leiste der `analysis_section` nutzt jetzt das standardisierte `table_wrap` / `tbl_actions` Pattern aus Template.md, konsistent mit anderen Toolbars. ([#344](https://github.com/thomas682/HA-Addons/issues/344))
- Dashboard/Analyse: Typen-Auswahl (gewaehlt/abgewaehlt) im Chip-Grid-Pattern mit Farbindikator, Hover-Effekten und Active/Inactive States, konsistent mit der Performanceanalyse. ([#345](https://github.com/thomas682/HA-Addons/issues/345))
- Dashboard: Analyse-Zustand (Cache-Plan-Auswahl, Status-Text, Caching-Summary) wird in `sessionStorage` persistiert und beim erneuten Oeffnen sofort wiederhergestellt. Zusaetzlich validiert das UI asynchron gegen den Server (Hybrid-Modus) und aktualisiert die Anzeige still, falls sich der Serverzustand geaendert hat. ([#347](https://github.com/thomas682/HA-Addons/issues/347))
- Picker/S-Picker: Erweiterter Multi-Pick-Modus. Shift+Klick auf Picker oder S-Picker startet die Mehrfachauswahl. Unterhalb der Pagecard erscheint eine Statusleiste mit den erfassten Elementen als anklickbare Chips (Klick = Entfernen). Buttons: "Ende" (kopiert alles als `<page,data-ui,id>;<page,data-ui,id>;...`), "Letztes loeschen", "Abbruch". Picked-Elemente erhalten solange sie in der Liste sind einen farbigen Rahmen; ESC bricht ab. ([#348](https://github.com/thomas682/HA-Addons/issues/348))

### Security

- Topbar-Fetches (`page_view`, `ui_event`, `client_log`) setzen explizit `credentials: 'same-origin'` und die CSRF-Header, um HA Ingress Proxies tolerant zu bleiben.
- `#347` Wiederherstellung der Caching-Summary aus `sessionStorage` verwendet eine defensive HTML-Saeuberung (Entfernen von `<script>`, `<iframe>`, `on*`-Handlern, `javascript:` URLs) und begrenzt die maximale Groesse auf 200.000 Zeichen, auch wenn die Snapshot-Quelle same-origin ist.

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest tests/` (142 passed, 37 pre-existing failures unrelated to dieser Aenderung — unveraenderter Ausgangszustand).
- Tested with Home Assistant Core: 2026.4.3

## 1.12.386

### Enhancement

- Jobs & Cache: Timer-Jobs Toolbar hat neue Buttons "Deaktivieren"/"Aktivieren" zum Umschalten der Automatik fuer selektierte Timer; History-Dialog kann initial nach selektierten Timern filtern und der Filter ist im Dialog anpassbar; Timer-Zeilen zeigen Fehlerzustand (rot) und Laufdauer. ([#341](https://github.com/thomas682/HA-Addons/issues/341))
- Scheduler: Neuer Nightly-Job `analysis_nightly` aktualisiert den Analysecache fuer alle bereits analysierten Serien (1x pro Nacht) und protokolliert OK/Fehler inkl. Dauer in History/Worklog. ([#338](https://github.com/thomas682/HA-Addons/issues/338))
- Picker/S-Picker: Kopiert nur noch `<page,data-ui,id>` in die Zwischenablage (kein JSON mehr). ([#340](https://github.com/thomas682/HA-Addons/issues/340))
- Dashboard: Analysecache Info-Dialog zeigt logische Dateipfade unter `/data/analysis_cache/...`.

### Bugfix

- Raw: Overwrite/Inline-Edit Zeitstempel-Parsing behoben (`_parse_time` war nicht definiert). ([#337](https://github.com/thomas682/HA-Addons/issues/337))
- UI: Copy-to-Clipboard im Popup/Modal robuster (Fallback fuer Ingress/unsichere Kontexte), damit die Zwischenablage nicht leer bleibt. ([#339](https://github.com/thomas682/HA-Addons/issues/339))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest tests/test_api_analysis_cache.py`, `pytest tests/test_api_raw_points_center.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.385

### Enhancement

- UI: Wenn im Browser noch keine Zoomstufe gespeichert ist, wird beim ersten Laden eine Default-Zoomstufe passend zur Viewport-Breite gesetzt (mobil groesser, desktop 100%). ([#335](https://github.com/thomas682/HA-Addons/issues/335))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.384

### Enhancement

- Dashboard/Caching: In der Liste der Analysecache-Segmente gibt es pro Cache-Block einen Info-Button, der Dateiname und Dateigroesse (meta + data) sowie alle bekannten Metadaten anzeigt. ([#334](https://github.com/thomas682/HA-Addons/issues/334))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.383

### Enhancement

- Security/UI: Host-Port ist standardmaessig deaktiviert (optional aktivierbar in Supervisor Netzwerk). XSS-Haertung bei UI-Renderings und CSRF-Schutz fuer API-Schreibaktionen via Custom Header. Security-Review-Pflicht in AGENTS.md dokumentiert. ([#333](https://github.com/thomas682/HA-Addons/issues/333))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.382

### Bugfix

- Dashboard: Fix JS-Syntaxfehler beim Start (doppelte `const cb` Deklaration in `loadUiConfig()`). ([#332](https://github.com/thomas682/HA-Addons/issues/332))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.381

### Enhancement

- UI: Sidebar-Menu verwendet jetzt SVG-Icons (aus `demo/icons1.html`) pro Menuepunkt; Variants A/B/C gemaess Zuordnung. ([#331](https://github.com/thomas682/HA-Addons/issues/331))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.3

## 1.12.380

### Enhancement

- Dashboard/Graph: Neuer Kontext-Graph zeigt den aktuell in Raw sichtbaren Bereich plus konfigurierbaren Puffer davor/danach. Sampling ist pixel-gebunden und Verdichtung nutzt Min/Max statt Durchschnitt (umschaltbar). Graph-Interaktionen (Zoom/Selektion/Klick) wirken nur noch innerhalb des Graph-Bereichs und loesen keine Aktionen in anderen Panels aus. ([#325](https://github.com/thomas682/HA-Addons/issues/325))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.379

### Enhancement

- UI: Seitensuche (Topbar) durchsucht jetzt auf jeder Seite auch wichtige sichtbare Textbereiche (nicht nur Controls) und springt zu Treffern. ([#327](https://github.com/thomas682/HA-Addons/issues/327))
- Einstellungen: Parameter aus verschachtelten Untersektionen (z.B. Backup/Restore Details) werden direkt in die passenden Gruppen einsortiert; Picker/S-Picker kopiert zusaetzliche Metadaten (id/title/open/selector/section-path) fuer eindeutige UI-Zuordnung. ([#326](https://github.com/thomas682/HA-Addons/issues/326))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.378

### Enhancement

- UI: Sidebar ist auf Desktop einklappbar (Icon-Only) und per Splitbar in der Breite verstellbar; Breite und Collapse-Status werden gespeichert. ([#328](https://github.com/thomas682/HA-Addons/issues/328))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.377

### Bugfix

- Schreibschutz: Wert-Aenderungen (Raw Overwrite + apply_changes overwrite) werden serverseitig gegen die Outlier-Regeln geprueft (Bounds + Max-Sprung zu Nachbarn). Bei Verstoß blockiert InfluxBro standardmaessig (HTTP 409) und bietet im UI einen Dialog mit exakter Erklaerung plus Force-Override. ([#329](https://github.com/thomas682/HA-Addons/issues/329))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.376

### Bugfix

- Dashboard: Bearbeitungsliste wurde entfernt (inkl. zugehoeriger UI) und die Raw-Bedienung wurde vereinfacht (Raw-Status immer sichtbar, Abbruch fuer Raw-Ladevorgaenge, Inline-Edit per Doppelklick mit sauberem Revert). ([#330](https://github.com/thomas682/HA-Addons/issues/330))
- Dashboard: Ausreißer-Suchleiste wurde entfernt; Outlier-Tabelle-Resize funktioniert wieder ueber den Shared-Resize-Helper. ([#330](https://github.com/thomas682/HA-Addons/issues/330))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.375

### Enhancement

- Performanceanalyse: Neuer Tab "API Dokumentation" im Diagramm-Bereich (UI basiert auf `demo/api-docs.html`), mit Suche/Filter, Live Trace-Counts und Code-Beispielen. ([#324](https://github.com/thomas682/HA-Addons/issues/324))
- API Docs: Add-on stellt eine Vollstaendigkeitsliste aller registrierten `/api/*` Routes als JSON bereit (`/api/api_docs`), inkl. best-effort Key-Extraktion aus Handlern. ([#324](https://github.com/thomas682/HA-Addons/issues/324))

### Maintenance

- Added `.agents.md` policy: API endpoints must be documented. ([#324](https://github.com/thomas682/HA-Addons/issues/324))
- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.374

### Enhancement

- Performanceanalyse: Trace-Liste und Details sind nicht mehr nebeneinander (kein Horizontal-Overflow). Stattdessen werden sie vertikal gestapelt und ueber einen Splitter in der Hoehe verstellbar angezeigt; Copy-Buttons bleiben sichtbar. ([#323](https://github.com/thomas682/HA-Addons/issues/323))
- Performanceanalyse: Korrelations-Dep-Graph hat einen globalen Zoom (0=Auto-Fit in X+Y, sonst Prozent). UI: - / % / +; Einstellung wird gespeichert und ist in den Settings parametrierbar. ([#323](https://github.com/thomas682/HA-Addons/issues/323))
- Performanceanalyse: InfluxBro native Hover-Tooltips sind im Waterfall- und Korrelationsbereich deaktiviert. ([#323](https://github.com/thomas682/HA-Addons/issues/323))
- Dashboard Query: Wenn `/api/query` aus dem Dash-Cache bedient wird, wird dies im Trace protokolliert und im Waterfall-Tooltip als Cache-Hit inkl. Query-Metadaten sichtbar. ([#323](https://github.com/thomas682/HA-Addons/issues/323))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.373

### Enhancement

- UI Picker/S-Picker: Outline-Farbe ist jetzt je nach Hintergrund (Auto, live beim Hover) gut sichtbar; Farben und Auto-Modus sind in den Einstellungen konfigurierbar. ([#322](https://github.com/thomas682/HA-Addons/issues/322))
- Performanceanalyse: Diagramm-Bereich hat jetzt Tabs (Diagramm + neuer Tab "Korrelation"). Korrelation-Ansicht basiert auf `demo/korrelationsdiagramm.html` und nutzt echte Trace-Daten (inkl. nicht-API URLs); Heuristik-Schwellenwerte sind in den Einstellungen parametrierbar. ([#322](https://github.com/thomas682/HA-Addons/issues/322))
- Performanceanalyse Tooltips: Browser-Title-Tooltips sind im Diagramm-Bereich unterdrueckt; stattdessen zeigen die dunklen Tooltips den UI-Key unten. Waterfall/Korrelation Tooltips wurden um Trigger/Query-Metadaten sowie Diagnosewerte erweitert. ([#322](https://github.com/thomas682/HA-Addons/issues/322))
- Jobs&Cache: Seite scrollt wieder korrekt; Cache-Section ist visuell konsistent (kein doppelter Titel im Body). ([#322](https://github.com/thomas682/HA-Addons/issues/322))
- Jobs: dash_cache Jobs erkennen v2 Config zuverlaessig und erzeugen keine falschen v1 "requires database" Fehler mehr. ([#322](https://github.com/thomas682/HA-Addons/issues/322))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.372

### Enhancement

- Dashboard: Trace-Copy kopiert jetzt exakt die angezeigte Trace-ID (nicht eine evtl. zuletzt im Hintergrund gelaufene). ([#321](https://github.com/thomas682/HA-Addons/issues/321))
- Performanceanalyse: Endpoint-Filter wurde erweitert (Klick im Waterfall toggelt Endpoints, Suchfeld filtert ChipGrid, Tooltip auf Chips; Query-Text wird im Tooltip angezeigt). Deaktivierte Endpoints werden gespeichert; Filterstatus ist ueber beiden Waterfalls sichtbar. Zeitachsen und Zeitangaben zoomen/berechnen sich anhand gefilterter Endpoints (+10% Padding rechts). Export-Buttons kopieren Waterfall-Datenbasis ungefiltert/gefiltert in die Zwischenablage. ([#321](https://github.com/thomas682/HA-Addons/issues/321))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.371

### Enhancement

- Performanceanalyse: Scroll-Container wurden korrigiert (Section-Root scrollt nicht, stattdessen `list_box`/`detail_box`; Diagramm-Section-Root ohne Scrollbar, Body darf scrollen). ([#320](https://github.com/thomas682/HA-Addons/issues/320))
- Performanceanalyse: Diagramm wurde 1:1 an das Demo-Layout `demo/analyse_demo.html` angeglichen (inkl. Endpoint-Chips/Filterpanel, Cards, Phasebar, Waterfall Full/Zoom, Stats, Tooltip) und wird mit Realwerten des selektierten Traces befuellt. ([#320](https://github.com/thomas682/HA-Addons/issues/320))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.370

### Enhancement

- Dashboard: Caching-UX wurde verbessert (Gesamtdauer in `load_progress_text`, `analysis_start_info` oben im Caching-Bereich, zentrale Trace-ID + Copy in `dashboard_caching.panel_status`, Checklisten kompakter) und Hinweise vom Typ `Fehlend: ...` werden farbig hervorgehoben (Farbe konfigurierbar). ([#319](https://github.com/thomas682/HA-Addons/issues/319))
- Dashboard: Gefiltertes Logging zeigt jetzt pro Zeile immer `trace_id` und `dur_ms`; der Dialog bietet einen direkten Sprung zur Performanceanalyse mit letzter bekannter Trace-ID. Performanceanalyse unterstuetzt `?trace_id=...` fuer direktes Laden eines Traces (auch ausserhalb der Recent-Liste). ([#319](https://github.com/thomas682/HA-Addons/issues/319))
- UI Picker/S-Picker: deaktivierte Controls (disabled button/input/select) sind jetzt zuverlaessig pickbar. ([#319](https://github.com/thomas682/HA-Addons/issues/319))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.369

### Enhancement

- Analyse: Raw-Fenster (N Punkte davor/danach) werden jetzt bevorzugt waehrend des `/api/outliers` Scans berechnet und im Analyse-Cache persistent gespeichert. Chunk-Randfaelle werden ueber `window_state`/`window_updates` inkrementell vervollstaendigt und per `analysis_cache/patch_windows` gepatcht. Cache-Preload kann fehlende/veraltete Fenster gezielt nachberechnen und einmalig in den Cache schreiben. ([#318](https://github.com/thomas682/HA-Addons/issues/318))

### Maintenance

- Docs: Technisches Handbuch `TECHNICAL.md` (Caching + Ausreisser-Suche)
- Tests: `python3 -m py_compile influxbro/app/app.py`, `pytest -q tests/test_api_outliers_window_state.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.368

### Enhancement

- Analyse-Cache: Dirty-Patch-Fenster verwendet jetzt punktbasierten Kontext (N davor/N danach) ueber `outlier_context_before_points`/`outlier_context_after_points` statt fixer Sekunden-Padding. ([#317](https://github.com/thomas682/HA-Addons/issues/317))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.367

### Enhancement

- Analyse: Punktbasierter Kontext ist jetzt getrennt konfigurierbar (davor/danach) und wird fuer Raw-Fenster um Ausreisser verwendet. Raw-Fenster-Logs enthalten jetzt Center-Zeitpunkt, N davor/N danach, Counts, Reason/Types und optional die Anzahl weiterer Ausreisser im Fenster; Duplikate werden dedupliziert. ([#316](https://github.com/thomas682/HA-Addons/issues/316))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.366

### Bug Fix

- Config: Runtime-Config-Normalisierung verhindert, dass v2 Setups (token+org+bucket vorhanden) in Query/Dashboard-Cache Jobs faelschlich als v1 behandelt werden ("v1 requires database"). ([#315](https://github.com/thomas682/HA-Addons/issues/315))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.365

### Enhancement

- Performanceanalyse Diagramm: Endpoint-Filter ist jetzt ein Dropdown mit allen im aktuellen Trace sichtbaren `/api/...` Endpoints. Alle sind initial aktiv; einzelne Endpoints koennen deaktiviert werden (persistiert). Summary Cards berechnen sich aus den gefilterten Spans; Hinweis-Badge zeigt aktive Filterung. ([#314](https://github.com/thomas682/HA-Addons/issues/314))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.364

### Enhancement

- Performanceanalyse Diagramm: Endpoint-Filter (Toggle + Text) wirkt auf Summary Cards, Waterfall (Vollansicht/Zoom) und Endpoint-Statistiken; Filterzustand wird gespeichert. ([#310](https://github.com/thomas682/HA-Addons/issues/310))
- Performanceanalyse: Vertikaler Splitter zwischen Trace-Liste/Details (oben) und Diagramm (unten) mit persistierter Hoehe (Default ~1/3). ([#311](https://github.com/thomas682/HA-Addons/issues/311))
- Dashboard: Analyse-Checklist zeigt TraceID (mit Copy-Button); Raw-Fenster-Logging ist granular (pro Fenster, inkl. Quelle cache/influx). ([#312](https://github.com/thomas682/HA-Addons/issues/312))

### Bug Fix

- Jobs & Cache: Laden der Untersektionen (Cache/Analysecache/Timers/Usage) bricht nicht mehr komplett ab, wenn ein einzelner API-Call fehlschlaegt; Fehler werden pro Sektion angezeigt. ([#313](https://github.com/thomas682/HA-Addons/issues/313))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest -q` (derzeit im Repo mehrfach rot; als pre-existing/unrelated eingestuft)
- Tested with Home Assistant Core: 2026.4.2

## 1.12.363

### Bug Fix

- Performanceanalyse Diagramm: Vollstaendige Analyse-Ansicht nach verbindlicher `analyse.html` Vorlage (Zeitleiste, Waterfall Vollansicht/Zoom, Endpoint-Statistiken, Tooltip) inkl. UI-Event Toggle, Endpoint-Erklaerungen und Missing-Endpoint Logging. ([#309](https://github.com/thomas682/HA-Addons/issues/309))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_settings_defaults_highlight.py -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.362

### Enhancement

- Performanceanalyse: Seite nutzt jetzt Section-Layout mit ausfuehrlicher Hilfe; Trace-Liste markiert selektierte Zeile, zeigt Start/Ende/Dauer und bietet Copy-Buttons; Details sind scrollbar/resizable; neuer Diagramm-Abschnitt (Waterfall) fuer selektierten Trace. ([#308](https://github.com/thomas682/HA-Addons/issues/308))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_settings_defaults_highlight.py -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.361

### Enhancement

- Einstellungen: Seitensuche markiert nicht mehr grosse Gruppen-Container, sondern springt filigran zum konkreten Textelement; neue Defaultwerte fuer Trefferrahmen (Breite=5px, Dauer=8000ms). ([#307](https://github.com/thomas682/HA-Addons/issues/307))
- Einstellungen: Farbpicker fuer Seitensuche/Navigationshilfe/Analysecache zeigen jetzt Picker + Hex-Wert (wie Section-Farben). ([#307](https://github.com/thomas682/HA-Addons/issues/307))
- Einstellungen: Statusleisten-Hintergrundpicker hat wieder die gleiche Breite wie der Textfarben-Picker. ([#307](https://github.com/thomas682/HA-Addons/issues/307))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.360

### Bug Fix

- UI Picker: Waehren Picker/S-Picker aktiv ist, werden Tooltips nicht mehr nachtraeglich re-injiziert, damit keine Overlaps entstehen. ([#304](https://github.com/thomas682/HA-Addons/issues/304))

### Enhancement

- Einstellungen: Seitensuche findet jetzt auch sichtbare Texte (Labels/Hints) und springt zum exakten Treffer; Suchbegriff wird markiert. ([#305](https://github.com/thomas682/HA-Addons/issues/305))
- Diagnose: Speicher/Worklog wurde aus Einstellungen auf die Diagnose-Seite verschoben; Groesse ist numerisch sortierbar; Backup-Verzeichnis ist im Inventar enthalten; 12M Verlauf + Limit/Prognose via `min freier Cachespeicher`. ([#306](https://github.com/thomas682/HA-Addons/issues/306))
- Settings: Default-Anzeige rechts entfernt; Defaults werden als Teil der Hint-Zeile angezeigt; neue Defaults `backup_min_free_mb=10` und `storage_budget_mb=5` inkl. Validierung (backup_min_free_mb > storage_budget_mb). ([#306](https://github.com/thomas682/HA-Addons/issues/306))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_storage_budget_validation.py -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.359

### Enhancement

- Settings/Diagnose: Neuer Worklog (Analyse/Statistik/Raw) inkl. Retention (max. Eintraege und max. Tage) sowie neue Diagnose-Ansicht fuer Speicherverbrauch (freie Platte + Inventar aller persistierten /data-Artefakte). ([#302](https://github.com/thomas682/HA-Addons/issues/302))
- Settings: Kompakteres Padding in der Settings-Liste und robustere Breite fuer `ui_filter_control_width_px`. ([#287](https://github.com/thomas682/HA-Addons/issues/287))

### Bug Fix

- Logs: Doppelte Controls/IDs entfernt, damit Suche/Wrap/Markieren wieder stabil funktionieren. ([#301](https://github.com/thomas682/HA-Addons/issues/301))
- Dashboard/Raw: Bei `range=all` wird das Raw-Zeitfenster nicht mehr auf Epoch (1970) gesetzt, sondern sinnvoll begrenzt (Default: `ui_analysis_max_age_years`, optional anhand bekannter Serien-Bounds). ([#303](https://github.com/thomas682/HA-Addons/issues/303))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_storage_usage.py -q`
- Tests: `pytest tests/test_api_config_io.py::test_trace_recent_endpoint_exists -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.358

### Maintenance

- Release: Reine Versionsmarke (keine Codeaenderungen) vor dem naechsten Umsetzungspaket.
- Tested with Home Assistant Core: 2026.4.2

## 1.12.357

### Bug Fix

- Analyse/Dashboard: `/api/resolve_signal` nutzt bei `range=all` ohne explizite Start/Stop-Zeit jetzt ein begrenztes Resolve-Fenster (`30d`), um teure All-Time Scans zu vermeiden. Das verhindert InfluxDB-internen Fehler (panic: negative WaitGroup counter) beim Analysestart fuer grosse Buckets. ([#300](https://github.com/thomas682/HA-Addons/issues/300))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_resolve_signal_range_safety.py -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.356

### Bug Fix

- Dashboard: Redundantes, zeitversetztes Nachladen der Selector-Listen beim Seitenstart entfernt (kein zweiter fire-and-forget Lauf fuer Fields/TagValues). Dadurch weniger Influx-Last und keine spaeten Fehlermeldungen durch ablaufende Selector-Requests. ([#299](https://github.com/thomas682/HA-Addons/issues/299))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.355

### Bug Fix

- Dashboard/Selector: Wenn bei `/api/fields` und `/api/tag_values` kein `range`/start/stop uebergeben wird, wird jetzt standardmaessig ein begrenzter Zeitraum (`24h`) verwendet statt eines All-Time-Scans. Das verhindert timeouts und InfluxDB-internen Fehler (panic) beim spaeten Nachladen von Vorschlagslisten. ([#298](https://github.com/thomas682/HA-Addons/issues/298))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_selector_default_range.py -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.354

### Bug Fix

- Dashboard/Stats: `POST /api/stats` (stats_scope=inf) nutzt jetzt einen persistenten, inkrementellen Per-Serie Cache (Checkpoint/Delta ab letztem covered_stop), damit Total-Statistiken nicht mehr bei jedem Lauf vollstaendig aus InfluxDB neu berechnet werden muessen. ([#297](https://github.com/thomas682/HA-Addons/issues/297))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_stats_total_cache.py -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.353

### Bug Fix

- Dashboard: Waehren einer laufenden Analyse werden `Analyse mit Cache` und `Analyse ohne Cache` gesperrt, damit kein zweiter Lauf parallel gestartet werden kann. Der `Analyse-Abbruch` entsperrt die Buttons sofort. ([#296](https://github.com/thomas682/HA-Addons/issues/296))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.352

### Enhancement

- Tracing/Performanceanalyse: App-weite Action/Trace-IDs fuer Button-Aktionen inkl. Korrelation von UI-Events, API-Requests, Client-Netzwerkzeiten und Influx-Queries. Traces sind persistent (Default 1000, in Settings parametrierbar) und es gibt einen neuen Menuepunkt `Performanceanalyse` zur Auswertung/Drilldown. Flux Queries werden zusaetzlich mit `// trace_id=...` kommentiert. ([#293](https://github.com/thomas682/HA-Addons/issues/293))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_config_io.py::test_trace_recent_endpoint_exists -q`
- Tests: `pytest -k "nav_includes_performance_page_link or settings_has_tracing_controls" -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.351

### Bug Fix

- Analyse: Raw-Fenster (`/api/outlier_windows`) werden jetzt ohne Vollscan des kompletten Analysefensters berechnet (lokale Nachbarschaftsqueries pro Treffer). Die Raw-Fensterberechnung ist ausserdem als eigener Checklisten-Schritt `Raw-Fenster berechnen` sichtbar und faellt nicht mehr unter die reine Suchlaufzeit. ([#292](https://github.com/thomas682/HA-Addons/issues/292))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest -k analysis_has_separate_raw_windows_step_and_does_not_compute_windows_inside_raw_search -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.350

### Bug Fix

- Logs: Der HA/Vendor Fehler `No Listener: tabs:outgoing.message.ready` wird global im `unhandledrejection` Handler abgefangen (Console bleibt sauber), aber weiterhin mit Navigationskontext ins Add-on Log geschrieben. ([#291](https://github.com/thomas682/HA-Addons/issues/291))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest -k global_unhandledrejection_suppresses_tabs_outgoing_ready_noise -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.349

### Enhancement

- Dashboard: Alle Elemente in `dashboard_caching.panel_status` sind jetzt linksbuendig ausgerichtet. ([#290](https://github.com/thomas682/HA-Addons/issues/290))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest -k dashboard_caching_status_panel_is_always_visible_and_has_text_fields -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.348

### Bug Fix

- Dashboard: Das Caching-Statuspanel `dashboard_caching.panel_status` bleibt jetzt immer sichtbar (kein Auto-Hide mehr) und zeigt wieder Status-Text sowie Laufzeit. ([#289](https://github.com/thomas682/HA-Addons/issues/289))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest -k dashboard_caching_status_panel_is_always_visible_and_has_text_fields -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.347

### Bug Fix

- `Analyse mit Cache` aktualisiert den Bereich `dashboard_caching.section_root` nicht mehr automatisch im Hintergrund (kein implizites `Cache pruefen`/Refresh der Caching-UI waehrend der Analyse). Der Caching-Bereich bleibt stabil und aendert sich nur noch bei expliziten Aktionen wie `Cache pruefen` oder `kombinieren`. ([#284](https://github.com/thomas682/HA-Addons/issues/284))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest -k analysis_does_not_refresh_caching_section_ui -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.346

### Enhancement

- Der Dialog `Ausreisser-Parameter` im Dashboard arbeitet jetzt global mit den Settings: Werte werden aus den Einstellungen geladen und bei Aenderungen direkt global gespeichert, inklusive `config_settings.tbl_outliers_table` (Max-Sprung je Einheit/Zeile), Messwertluecke, Bounds-Defaults und Recovery-Streak. ([#283](https://github.com/thomas682/HA-Addons/issues/283))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_config_io.py -q`
- Tests: `pytest -k dashboard_outlier_params_dialog_is_global_config_based -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.345

### Enhancement

- Default-UI in den Einstellungen: neue Standardfarben/Schriftgroessen fuer Bereich-Titel Ebene 2/3 sowie neue Schriftgroesse fuer Bereich-Titel (Details). Zusaetzlich gibt es einen Block `Default / Import / Export` fuer JSON-Export, JSON-Import (mit Strukturpruefung) und Reset auf Defaultwerte; unter jedem Eingabefeld wird der Default als `Default = ...` angezeigt. ([#282](https://github.com/thomas682/HA-Addons/issues/282))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_config_io.py -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.344

### Enhancement

- In den Einstellungen hat die Ausreisser-Tabelle jetzt `+ Zeile` und `- Zeile` Buttons: Zeilen werden per Klick markiert, und `- Zeile` ist nur bei markierter Zeile aktiv. Neue Zeilen erlauben die manuelle Eingabe von `_measurement` und `max_step`. ([#286](https://github.com/thomas682/HA-Addons/issues/286))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest -k settings_outliers_table_has_add_delete_buttons_and_tooltips -q`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.343

### Enhancement

- Die Einstellungs-Parameterzeilen haben jetzt keine festen Breiten-Constraints mehr. Dadurch laufen Felder wie `ui_status_bar_bg` nicht mehr rechts aus `config_settings.section_root`, sondern brechen sauber um. ([#285](https://github.com/thomas682/HA-Addons/issues/285))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "dashboard_cache_timeline_has_hl_ac_toggles_and_combine_buttons or dashboard_caching_panel_has_logs_button_progress_and_range_details"`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.342

### Enhancement

- In der Cache-Timeline ist `ol` fuer neue Cache-Segmente jetzt standardmaessig aktiv und bleibt serienweit erhalten, auch nach erneutem `Cache pruefen`. Die Zeilen `Neu lesen` werden wie Cache-Zeilen mit `hl`/`ac`/`ol` dargestellt; `ol` bleibt dort immer deaktiviert. ([#281](https://github.com/thomas682/HA-Addons/issues/281))
- Die Einstellungen-UI bricht Parametrierungen wie `ui_section_title_fg` jetzt sauber um, statt rechts aus `config_settings.section_root` herauszulaufen. ([#281](https://github.com/thomas682/HA-Addons/issues/281))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "dashboard_cache_timeline_has_hl_ac_toggles_and_combine_buttons or dashboard_caching_panel_has_logs_button_progress_and_range_details"`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.341

### Enhancement

- `Cache pruefen` im Dashboard zeigt jetzt einen eigenen kleinen Fortschrittsblock mit Caching-Checkliste, Prozentanzeige und deutlich detaillierterem Logging. Fehlende bzw. geaenderte Bereiche werden dabei nicht nur gezaehlt, sondern mit konkreten Zeitbereichen in UI und Logs aufgefuehrt. Rechts neben der Gesamtstatistik gibt es zusaetzlich einen `Logs`-Button fuer den gefilterten Cache-Dialog. ([#277](https://github.com/thomas682/HA-Addons/issues/277))
- Der Analyse-Schritt `Fehlende Restbereiche lesen` nennt jetzt ebenfalls die konkreten fehlenden bzw. geaenderten Zeitbereiche, statt nur deren Anzahl zu melden. ([#277](https://github.com/thomas682/HA-Addons/issues/277))

### Maintenance

- `AGENTS.md` verlangt die Ermittlung der getesteten Home-Assistant-Core-Version jetzt explizit ueber `curl -s -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://192.168.2.200:8123/api/config | jq -r '.version'`. `unknown` bleibt nur noch als Fallback erlaubt, wenn genau diese Abfrage fehlschlaegt oder keinen verwertbaren Wert liefert. ([#280](https://github.com/thomas682/HA-Addons/issues/280))
- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "dashboard_caching_panel_has_logs_button_progress_and_range_details or dashboard_caching_section_has_visible_cache_targets_and_no_old_dialog or dashboard_cache_timeline_has_hl_ac_toggles_and_combine_buttons or analysis_cache_hit_summary_replaces_interval_hint_line"`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.340

### Enhancement

- Das gemeinsame Tabellen-Template besitzt jetzt einen Shared-Helper `Zeile kopieren`. Im Dashboard wurden dafuer zunaechst die Buttons fuer Raw- und Ausreißer-Tabelle ergaenzt; kopiert werden jeweils `...`, die Titelzeile, die markierte Zeile und ein abschliessendes `...` in die Zwischenablage. ([#279](https://github.com/thomas682/HA-Addons/issues/279))
- Beim Klick auf einen Ausreißer laedt `Raw Daten` jetzt punktbasiert exakt `N davor / N danach` statt ein grosses Zeitfenster ueber `center_minutes`. Falls vorberechnete Fenstergrenzen vorhanden sind, werden sie nur noch zum Einengen der Query genutzt. Dadurch passen Query-Umfang, geladene Zeilen und angezeigter Raw-Kontext besser zusammen. ([#279](https://github.com/thomas682/HA-Addons/issues/279))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_outlier_windows.py -q`
- Tests: `pytest tests/test_api_raw_points_center.py -q`
- Tests: `pytest tests/test_api_ui_support.py -q -k "table_template_and_dashboard_actions_support_copy_selected_row_and_point_based_raw_context or raw_outlier_table_uses_column_filter_suggestions_and_context_rows_save_immediately or dashboard_outlier_section_is_separate_and_above_raw_section or outlier_table_header_is_explicitly_sticky_and_search_bar_tracks_outlier_section"`
- Tested with Home Assistant Core: unknown

## 1.12.339

### Bug Fix

- Die Dashboard-Analyse erklaert beim Schritt `Cache-Hit pruefen` jetzt genauer, warum vorhandener Cache nur teilweise genutzt wird: wiederverwendbare Segmente, lokal bereinigte dirty Segmente, verbleibende Luecken und blockierende Dirty-Gruende werden direkt in der Checkliste angezeigt. Die wenig hilfreiche Zeile `dashboard_analysis.txt_interval_info` wurde entfernt. ([#276](https://github.com/thomas682/HA-Addons/issues/276))
- Dirty Analyse-Cache wird jetzt nicht mehr pauschal komplett verworfen. Beim Cache-Plan und beim `Combine`-Ablauf werden dirty Segmente zuerst ueber die vorhandene Checkpoint-/Patchlogik lokal repariert; nur wirklich verbleibende dirty Fenster werden neu analysiert oder blockieren weiterhin die Gruppenbildung. ([#276](https://github.com/thomas682/HA-Addons/issues/276))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_cache.py -q`
- Tests: `pytest tests/test_api_ui_support.py -q -k "analysis_cache_hit_summary_replaces_interval_hint_line or dashboard_cache_timeline_has_hl_ac_toggles_and_combine_buttons"`
- Tests: `pytest tests/test_api_ui_support.py -q -k "jobs_page_has_analysis_cache_section_and_actions or jobs_and_cache_tables_use_selection_toolbar_actions"`
- Tested with Home Assistant Core: unknown

## 1.12.338

### Bug Fix

- Die Dashboard-Ausreißertabelle bleibt jetzt innerhalb von `raw_outlier_table_wrap`, statt horizontal ueber den Elterncontainer hinauszulaufen. Gleichzeitig wurde die doppelt registrierte Hoehen-Resize-Logik bereinigt, sodass der Griff `dashboard_outliers.tbl_resize` wieder sauber nach oben und unten arbeitet. ([#274](https://github.com/thomas682/HA-Addons/issues/274))
- Der alte Bereich mit `Markieren` / `Suche beenden` / Typbutton wurde im Dashboard-Ausreißerblock entfernt. Stattdessen kann die Spalte `Ausreißer` jetzt direkt ueber die Tabellen-Filterzeile gefiltert werden, inklusive Vorschlagsliste vorhandener Werte und freiem Texteingabefilter. ([#274](https://github.com/thomas682/HA-Addons/issues/274))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "raw_outlier_table_uses_template_structure_and_helpers or dashboard_outlier_section_is_separate_and_above_raw_section or outlier_table_header_is_explicitly_sticky_and_search_bar_tracks_outlier_section or outlier_table_uses_column_filter_suggestions_and_context_rows_save_immediately"`
- Tested with Home Assistant Core: unknown

## 1.12.337

### Enhancement

- `Jobs & Cache` laedt jetzt wieder ohne JavaScript-Syntaxfehler. Die doppelte Deklaration der Selektionsmengen wurde entfernt, damit Mehrfachauswahl und Toolbars sauber initialisieren. ([#275](https://github.com/thomas682/HA-Addons/issues/275))
- Die Einstellungsseite wurde fuer die Bedienung und Struktur bereinigt: neue Obergruppe `Oberflaeche`, konsistentes Hover-/Titelverhalten wie auf dem Dashboard, getrennte Farben/Schriftgroessen fuer Section-Ebene 2 und 3, keine doppelte Logs-Section mehr und einheitliche Color-Picker fuer Log-ERROR/WARN-Farben. ([#275](https://github.com/thomas682/HA-Addons/issues/275))
- Veraltete oder nicht mehr gewollte Settings-Pfade wurden entfernt: die Open-on-load-Parameter der Dashboard-Details entfallen zugunsten fester Start-Defaults `geoeffnet`, und `Repository URL` / `PayPal Donate URL` sind nicht mehr parametrierbar, sondern fest im Add-on hinterlegt. ([#275](https://github.com/thomas682/HA-Addons/issues/275))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "jobs_page_has_analysis_cache_section_and_actions or settings_layout_and_null_safe_bindings_are_present or page_search_setting_present_across_pages or settings_restructure_script_and_general_navigation_params_exist"`
- Tests: `pytest tests/test_api_ui_support.py -q -k "settings_include_bugreport_log_history_hours or jobs_and_cache_tables_use_selection_toolbar_actions or jobs_page_has_analysis_cache_section_and_actions or cache_timeline_hidden_color_and_jobs_analysis_table_features_exist or dashboard_and_settings_expose_gap_outlier_controls or config_tooltips_include_page_search_highlight_settings"`
- Tested with Home Assistant Core: unknown

## 1.12.336

### Enhancement

- Die Analyse-Checkliste im Dashboard zeigt jetzt fuer jeden festen Schritt ein eigenes Info-Icon mit sehr ausfuehrlicher technischer Erklaerung. Zusaetzlich werden Startzeit und Laufzeit pro Schritt durchgaengig mit Millisekunden angezeigt. ([#273](https://github.com/thomas682/HA-Addons/issues/273))
- Der Schritt `Cache-Segmente kombinieren` meldet jetzt genauer, ob keine sauberen zusammenhaengenden Gruppen existieren oder ob dirty Segmente mit konkreten `patch_status`-/`dirty_reason`-Gruenden die Kombination blockieren. Die alte separate Chunk-Statuszeile unter der Checkliste entfaellt. ([#273](https://github.com/thomas682/HA-Addons/issues/273))
- Der gemeinsame Popup-Splitter `influxbro_popup_split` laesst sich jetzt deutlich freier nach oben und unten ziehen. Beide Bereiche behalten nur noch eine kleine Resthoehe, statt frueh hart zu begrenzen. ([#273](https://github.com/thomas682/HA-Addons/issues/273))

### Maintenance

- Tests: `python3 -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_cache.py -q`
- Tests: `pytest tests/test_api_ui_support.py::test_dashboard_cache_timeline_has_hl_ac_toggles_and_combine_buttons -q`
- Hinweis: `pytest tests/test_api_ui_support.py -q` enthaelt weiterhin mehrere vorbestehende String-/Snapshot-Fails in nicht von dieser Aenderung beruehrten Bereichen.
- Tested with Home Assistant Core: unknown

## 1.12.335

### Bug Fix

- Analyse-Cache-Patchjobs bestimmen den Minimalbereich fuer dirty Segmente jetzt ueber echte Vor-/Nachbarpunkte aus InfluxDB. Dadurch wird der Rebuild-Bereich enger als beim reinen Zeitfallback und bleibt auch bei Legacy-Segmenten klein. ([#272](https://github.com/thomas682/HA-Addons/issues/272))
- `Jobs & Cache -> Analysecache` zeigt fuer Segmente jetzt zusaetzliche Patchdetails wie Modus, verwendeten Checkpoint und Kontextpunkte in der Timeline/Segmentanzeige. ([#272](https://github.com/thomas682/HA-Addons/issues/272))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_cache.py -q`
- Tests: `pytest tests/test_api_ui_support.py -q -k "jobs_page_has_analysis_cache_section_and_actions"`
- Tested with Home Assistant Core: unknown

## 1.12.334

### Bug Fix

- Legacy-Analyse-Cache-Segmente ohne verwertbare Checkpoints verwenden fuer den Hintergrund-Patchjob jetzt einen kleinen Fallbackbereich um die geaenderten History-Zeitpunkte. Dadurch bleiben auch aeltere Cache-Dateien oefter lokal patchbar, statt direkt auf `patch_not_safe` zu landen. ([#271](https://github.com/thomas682/HA-Addons/issues/271))
- Neue Analyse-Cache-Segmente schreiben jetzt zusaetzlich einen Start-Checkpoint ab Segmentbeginn, damit auch fruehe Segmentaenderungen checkpoint-basiert lokal repariert werden koennen. ([#271](https://github.com/thomas682/HA-Addons/issues/271))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_cache.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.333

### Bug Fix

- Analyse-Cache-Segmente speichern jetzt Checkpoints des Analysezustands und werden nach `overwrite`/`delete`/`import`/Rollback automatisch ueber einen Hintergrund-Job lokal repariert. Dadurch bleiben geaenderte Segmente sichtbar patchbar, statt spaeter beim `kombinieren` grosse Requeries gegen InfluxDB auszufuehren. ([#270](https://github.com/thomas682/HA-Addons/issues/270))
- Das serverseitige `combine` ueberspringt dirty oder noch nicht gepatchte Analyse-Cache-Segmente jetzt explizit und meldet diese im Ergebnis zurueck, statt fuer diese Gruppen Timeout-anfaellige Voll-Requeries auszufuehren. ([#270](https://github.com/thomas682/HA-Addons/issues/270))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_cache.py -q`
- Tests: `pytest tests/test_api_time_and_stats.py -q -k "api_jobs_includes"`
- Tests: `pytest tests/test_api_ui_support.py -q -k "jobs_page_has_analysis_cache_section_and_actions"`
- Tested with Home Assistant Core: unknown

## 1.12.332

### Bug Fix

- Die Einstellungsseite haertet den Lade- und Speicherpfad fuer die Log-Farbfelder (`ui_log_error_bg`, `ui_log_error_fg`, `ui_log_warn_bg`, `ui_log_warn_fg`) jetzt mit lazy DOM-Rebind und Null-Guards. Dadurch fuehren fehlende oder spaet gebundene Felder nicht mehr zu Statusbar-Fehlern wie `TypeError: null is not an object`. ([#269](https://github.com/thomas682/HA-Addons/issues/269))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "settings_layout_and_null_safe_bindings_are_present"`
- Tests: lokaler Render-Smoke fuer `/config` via Flask-Testclient
- Tested with Home Assistant Core: unknown

## 1.12.331

### Bug Fix

- Das serverseitige Kombinieren von Analyse-Cache-Segmenten nutzt fuer Dirty-Segmente jetzt wieder den aktuellen Outlier-Endpoint. Dadurch schlagen Combine-Laeufe mit geaenderten Segmenten nicht mehr mit `name 'api_outlier_search' is not defined` fehl. ([#268](https://github.com/thomas682/HA-Addons/issues/268))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_cache.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.330

### Bug Fix

- Der Endpoint `/api/analysis_cache/combine` gibt bei Merge-Fehlern jetzt immer eine saubere JSON-Fehlerantwort statt einer HTML-500-Seite zurück. Dadurch zeigt das Dashboard bei Fehlern im Analyse-Cache-Kombinieren den eigentlichen Backend-Fehler statt `Invalid JSON`. ([#268](https://github.com/thomas682/HA-Addons/issues/268))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_cache.py -q -k "analysis_cache_combine_merges_contiguous_segments or analysis_cache_combine_returns_json_error_on_merge_exception"`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.329

### Bug Fix

- Den verbleibenden abgeschnittenen Abschluss von `highlightOutlierAtIndex` und den doppelten `rawUndo`-Handler im Dashboard-Script bereinigt. Dadurch verschwinden weitere JavaScript-Abbrüche wie `Unexpected end of input` im Dashboard. ([#267](https://github.com/thomas682/HA-Addons/issues/267))

### Maintenance

- Neue wiederkehrende QA fuer Dashboard-Scriptintegritaet: extrahierte `<script>`-Blöcke werden per `node --check` validiert, und kritische Dashboard-Funktionen duerfen nur einmal definiert sein.
- Neuer Playwright-Smoke-Test fuer Dashboard-Konsole/Pageerrors: `tests/e2e/dashboard-console.spec.js`
- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_dashboard_script_integrity.py -q`
- Tests: lokaler Browser-Smoke-Test gegen `http://127.0.0.1:8099/` ohne kritische Console-/Pageerrors
- Tests: `npx playwright test tests/e2e/dashboard-console.spec.js`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.328

### Bug Fix

- Einen zweiten, versehentlich doppelt eingefügten `rawUndo`-Handler im Dashboard entfernt. Dadurch verschwindet ein weiterer Script-Duplikatblock im Raw-Bereich, der zusammen mit den vorherigen Doppeldefinitionen zu kaputtem/abgeschnittenem Dashboard-JavaScript geführt hat. ([#266](https://github.com/thomas682/HA-Addons/issues/266))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Duplikatprüfung für `clearAnalysisCacheForCurrentSeries`, `showRawManualDialog`, `promptForValue`, `editRawValueInline`, `doRawOverwrite` und `rawUndo`-Listener
- Tested with Home Assistant Core: 2026.4.2

## 1.12.327

### Bug Fix

- Die doppelte Definition von `clearAnalysisCacheForCurrentSeries` im Dashboard-Script wurde entfernt. Dadurch verschwindet der Browserfehler `Identifier 'clearAnalysisCacheForCurrentSeries' has already been declared` beim Aufruf des Dashboards. ([#265](https://github.com/thomas682/HA-Addons/issues/265))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Duplikatpruefung fuer `clearAnalysisCacheForCurrentSeries` und direkte Funktionsduplikate im betroffenen Dashboard-Bereich
- Tested with Home Assistant Core: 2026.4.2

## 1.12.326

### Bug Fix

- Duplizierten `refreshAll`-Block und zweite `_prepareStep`-Definition entfernt, die `SyntaxError: Unexpected token 'catch'` verursacht haben. ([#262](https://github.com/thomas682/HA-Addons/issues/262))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.325

### Bug Fix

- Duplizierte `_prepareStep`-Funktion entfernt, die einen `SyntaxError: Identifier '_prepareStep' has already been declared` verursacht hat. ([#262](https://github.com/thomas682/HA-Addons/issues/262))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.324

### Bug Fix

- Duplizierter Code-Block in `highlightOutlierAtIndex` entfernt, der einen `SyntaxError: Unexpected token '}'` beim Laden des Dashboards verursacht hat. ([#262](https://github.com/thomas682/HA-Addons/issues/262))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.323

### Enhancement

- Raw-Werte koennen jetzt direkt in der Tabelle durch Klick auf den Wert bearbeitet werden. Ein Bestaetigungsdialog fragt vor dem Ueberschreiben nach. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- Neuer Button `Manuell` neben `Einfuegen` in der Raw-Toolbar. Eroeffnet einen Dialog mit Interpolations- und Nachbarwert-Vorschlaegen fuer Einzelausreisser. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- Backend-Endpoint `/api/raw_overwrite` zum Ueberschreiben einzelner Raw-Werte mit History-Protokollierung. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- Undo-Dialog zeigt bei mehreren History-Eintraegen eine Auswahlliste, damit der Benutzer gezielt eine Aenderung rueckgaengig machen kann. ([#262](https://github.com/thomas682/HA-Addons/issues/262))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.322

### Bug Fix

- Cache-Performanz: Bei `Analyse mit Cache` wurden bisher alle Chunks neu gelesen, auch wenn nur `dirty_ranges` vorhanden waren. Die Bedingung prueft jetzt, ob die Arrays tatsaechlich Eintraege enthalten, statt nur auf Existenz zu pruefen. ([#262](https://github.com/thomas682/HA-Addons/issues/262))

### Enhancement

- Resize-Handle fuer Ausreisser-Tabelle explizit im Markup ergaenzt mit eigener Drag-Logik. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- `raw_outlier_display_limit_per_type` aus dem Dashboard entfernt. Wert kann nur noch in den Einstellungen parametriert werden. Bei Ueberschreitung erscheint ein Hinweis in der Suchleiste. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- S-Picker erfasst jetzt auch disabled/graue Elemente und kennzeichnet sie im Badge mit `[disabled]`. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- Copy-Icon auf allen Tabellen vereinheitlicht (Raw, Ausreisser, Logs). ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- Refresh-Button laedt nur den aktuellen Raw-Zeitbereich neu. ([#262](https://github.com/thomas682/HA-Addons/issues/262))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.321

### Enhancement

- Resize-Handle fuer Ausreisser-Tabelle explizit im Markup ergaenzt. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- `raw_outlier_display_limit_per_type` aus dem Dashboard entfernt, Hinweis bei Ueberschreitung ergaenzt. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- S-Picker erfasst jetzt auch disabled Elemente. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- Copy-Icon auf allen Tabellen vereinheitlicht. ([#262](https://github.com/thomas682/HA-Addons/issues/262))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.320

### Bug Fix

- Raw-Kontext Zeiten in der Ausreisser-Tabelle zeigten falsche Start-/Endwerte, weil `point_index` sich auf Chunk-Ergebnisse statt auf die gesamte Datenreihe bezog. Das Backend loest den Index jetzt ueber den Zeitstempel direkt auf. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- Row-Highlight-Versatz in der Ausreisser-Tabelle behoben: Zeilen werden jetzt ueber `data-time`-Attribut statt ueber Index-Position markiert. ([#262](https://github.com/thomas682/HA-Addons/issues/262))
- fault_phase-Eintraege zeigen jetzt `aggregiert` statt `kein Raw-Fenster`, da es sich um zusammengefasste Stoerphasen handelt. ([#262](https://github.com/thomas682/HA-Addons/issues/262))

### Enhancement

- Logs-Seite: Suchfeld-Breite auf `min-width: 40px` reduziert und `flex:1` entfernt. Clear-Button neben `Markieren`-Eingabefeld ergaenzt. ([#259](https://github.com/thomas682/HA-Addons/issues/259))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.319

### Enhancement

- Der Schritt `Analyse vorbereiten` wird jetzt in sichtbare Detailschritte aufgeteilt. Jeder Teilschritt (`UI-Zustand speichern`, `Serie aufloesen`, `Entity-ID ergaenzen`, `Daten laden`, `Analysefenster bestimmen`, `Cache-Status pruefen`) wird mit eigener Dauer-Messung ins Analyse-Log geschrieben und ist im Dashboard unter `dashboard_analysis.btn_logs` einsehbar. ([#263](https://github.com/thomas682/HA-Addons/issues/263))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.318

### Bug Fix

- Die Settings-Seite (`/config`) hat bei leeren Gruppen (`Handbuch`, `Profilverwaltung`, `Einstellungen`) `insertBefore`-Fehler geworfen, weil `saveCard` waehrend der Restrukturierung verschoben wurde. Der Code prueft jetzt vor jedem Einfuegen, ob `saveCard` noch Kind von `main` ist, und faellt sonst auf `appendChild` zurueck. ([#260](https://github.com/thomas682/HA-Addons/issues/260))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.317

### Bug Fix

- Die Settings-Seite (`/config`) wurde robuster gegen Initialisierungsfehler gemacht. `restructureSettings()` protokolliert jetzt Fehler pro Gruppe ins Server-Log statt sie still zu schlucken. `setForm()` verwendet jetzt Null-sichere Setter, damit fehlende Felder nicht mehr die gesamte Seite zum Absturz bringen. ([#260](https://github.com/thomas682/HA-Addons/issues/260))
- JavaScript-Fehler auf der Settings-Seite werden jetzt explizit ins Add-on-Log gemeldet, inkl. Vendor-/Ingress-Fehlern wie `No Listener: tabs:outgoing.message.ready`. ([#260](https://github.com/thomas682/HA-Addons/issues/260))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "settings_layout_and_null_safe_bindings_are_present"`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.316

### Bug Fix

- Die Dashboard-Ausreisseranalyse berechnet und protokolliert Raw-Fenster jetzt im aktiven Hauptpfad fuer `Analyse mit Cache` und `Analyse ohne Cache`. Dadurch wird die neue Spalte `Raw-Kontext` konsistent gefuellt und `missing_window`-Faelle enthalten aussagekraeftigere Diagnoseinformationen. ([#258](https://github.com/thomas682/HA-Addons/issues/258))
- Das Ausreisser-Tabellenlayout wurde auf eine vertikale Anordnung ohne rechte Nebenspalte umgebaut, damit `dashboard_outliers.tbl_ausreisser` nicht mehr ueber die Breite des Mutterobjekts hinausragt. ([#258](https://github.com/thomas682/HA-Addons/issues/258))
- Browser-/Vendor-Fehler beim Menuewechsel wie `No Listener: tabs:outgoing.message.ready` werden jetzt global mit Navigationskontext ins Add-on-Log gemeldet. ([#258](https://github.com/thomas682/HA-Addons/issues/258))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "raw_outlier_params_dialog_has_explanations_and_recovery_override or dashboard_outlier_section_is_separate_and_above_raw_section or navigation_helper_controls_and_config_exist"`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.315

### Bug Fix

- Der Dashboard-Dialog `Ausreisser-Parameter` nutzt `Recovery-Streak` jetzt wirklich fuer die laufende Ausreisseranalyse. Die Felder wurden visuell ueberarbeitet und enthalten erklaerende Hinweise zu Wirkung und Leerwert-/Default-Verhalten statt missverstaendlicher `auto`-Platzhalter. ([#257](https://github.com/thomas682/HA-Addons/issues/257))
- Die Settings-Seite meldet Initialisierungs- und Browserfehler jetzt frueher ins Add-on-Log. Dadurch werden auch Fehler wie `No Listener: tabs:outgoing.message.ready` aus dem Startup-/Vendor-Kontext besser sichtbar, statt die Seite nur leer erscheinen zu lassen. ([#257](https://github.com/thomas682/HA-Addons/issues/257))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_outliers_fault_phase.py tests/test_api_ui_support.py -q -k "recovery_valid_streak_override or raw_outlier_params_dialog_has_explanations_and_recovery_override or settings_layout_and_null_safe_bindings_are_present or fault_phase_preset_present_in_dashboard_ui"`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.314

### Enhancement

- Die Dashboard-Ausreisser-Tabelle zeigt jetzt eine neue Spalte `Raw-Kontext`. Dort siehst du pro Treffer die tatsaechlich verfuegbaren Raw-Punkte vor und nach dem Ausreisser sowie den exakten Zeitbereich `Start -> Ausreisser -> Ende` des vorberechneten Kontextfensters. Zusaetzlich wurde der zugrundeliegende Endpoint `api/outlier_windows` auf das bestehende v2-Client-Muster umgestellt. ([#256](https://github.com/thomas682/HA-Addons/issues/256))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_outlier_windows.py tests/test_api_ui_support.py -q -k "outlier_windows_returns_exact_counts_and_bounds or raw_outlier_table_uses_template_structure_and_helpers"`
- Tested with Home Assistant Core: 2026.4.2

## 1.12.313

### Enhancement

- Drittes Teilpaket fuer `#250`: Die Einstellungsseite wurde auf die gewuenschte neue Oberstruktur umgestellt. Vorhandene Cards werden jetzt unter Gruppen wie `Anbindung`, `Dashboard`, `Statistik`, `Backup`, `Restore`, `Logs`, `Jobs & Cache`, `History`, `Diagnose` und `Einstellungen` einsortiert; Bereiche ohne eigene Felder erscheinen als klare Platzhalter statt zu verschwinden. ([#250](https://github.com/thomas682/HA-Addons/issues/250))

### Maintenance

- Tests: Script-Balance und Marker fuer `restructureSettings()` geprueft
- Tested with Home Assistant Core: unknown

## 1.12.312

### Fix

- Zweites Teilpaket fuer `#250`: Tabellen-Tooltips zeigen bei Tabellenzellen jetzt den Zelltext und den bisherigen Elementnamen in Klammern. Ausserdem wurden die geforderten Bereiche in Monitor, Backup und Jobs & Cache in einklappbare Sections umgebaut. Die Log-Redaction maskiert zusaetzlich `admin_token`, `secret`, `private_key`, `public_key` und `access_key` aggressiver. ([#250](https://github.com/thomas682/HA-Addons/issues/250))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Script-Balance fuer `monitor.html`, `backup.html`, `jobs.html` und `_tooltips.html` geprueft
- Tests: Marker fuer `#250` Teilpaket 2 geprueft
- Tested with Home Assistant Core: unknown

## 1.12.311

### Enhancement

- Jobs & Cache: Tabellen im Bereich Jobs, Cache, Analyse-Cache, Timer und Cache-Nutzung lassen sich jetzt per Zeilenklick mehrfacht selektieren. Neue Buttons `selektiere alle` und `selektiere keine` stehen in den Tabellenleisten bereit; vorhandene Aktionen wie Loeschen, Neu aufbauen, Start oder Abbruch arbeiten auf den selektierten Zeilen. In der Analyse-Cache-Tabelle wurden ausserdem die Spalten umgestellt (`entity_id`, `friendly_name`, `Groesse`, `series` am Ende) und `Alle loeschen` in die Tabellenaktionen verschoben. ([#255](https://github.com/thomas682/HA-Addons/issues/255))

### Maintenance

- Tests: Script-Balance fuer `jobs.html` geprueft
- Tests: Marker fuer Mehrfachauswahl, Select-All/None und Analyse-Cache-Spaltenlayout geprueft
- Tested with Home Assistant Core: unknown

## 1.12.310

### Fix

- Erstes Teilpaket fuer GUI-Settings/UI-Qualitaet: sichtbarer Tooltip-Textrest unter der letzten Section entfernt, Summary-Aktionsbuttons toggeln Details nicht mehr ungewollt, `admin_token_test` speichert/testet jetzt robuster mit sichtbarer Rueckmeldung, und die Statistik-Tabelle ist als einklappbare Section `Messwertuebersicht` umgesetzt. ([#250](https://github.com/thomas682/HA-Addons/issues/250))

### Maintenance

- Tests: Template-Script-Balance fuer `config.html`, `stats.html`, `_topbar.html` und `_tooltips.html` geprueft
- Tests: Marker fuer `#250` Teilpaket 1 geprueft
- Tested with Home Assistant Core: unknown

## 1.12.309

### Fix

- Verbliebene userrelevante 5000-Hardlimits wurden auf bestehende Einstellungen umgestellt: die Ausreisser-Suche nutzt jetzt `ui_raw_outlier_search_limit` auch in der Frontend-Begrenzung, und die Measurement/Field/Tag-Selector-Flux-Queries verwenden `ui_query_max_points` statt fester `limit(n: 5000)`. ([#253](https://github.com/thomas682/HA-Addons/issues/253))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Marker fuer konfigurierbare 5000-Grenzen in Backend und Frontend geprueft
- Tested with Home Assistant Core: unknown

## 1.12.308

### Fix

- Ein fehlendes Raw-Window fuer den automatisch ausgewaehlten ersten Ausreisser loescht den frisch erzeugten Analyse-Cache nicht mehr. Stattdessen bleibt der Analyse-Cache erhalten und die GUI zeigt nur noch einen Hinweis, dass fuer diesen Ausreisser noch kein Raw-Fenster verfuegbar ist. ([#254](https://github.com/thomas682/HA-Addons/issues/254))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Marker fuer den Raw-Window-Fix und Script-Balance in `index.html` geprueft
- Tested with Home Assistant Core: unknown

## 1.12.307

### Maintenance

- Das Analyse-Cache-Diagnoselogging wurde erweitert: Store, List und Plan schreiben jetzt detaillierte Diagnoseeintraege mit `cache_id`, `series_key`, Dateipfaden, Anzahl gefundener Metadateien sowie `selected`/`dirty`-Zustaenden. Auch das Frontend loggt jetzt die Store-Responses mit Cache-Metadaten explizit. ([#252](https://github.com/thomas682/HA-Addons/issues/252))
- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Marker fuer Analyse-Cache-Diagnoselogging in Backend und Frontend geprueft
- Tested with Home Assistant Core: unknown

## 1.12.306

### Fix

- Analyse-Cache-Segmente werden bei Plan- und Listenaufbau nicht mehr vollstaendig ueber den bisherigen `cfg_fp`-Filter ausgeblendet. Dadurch bleiben frisch gespeicherte Analyse-Cache-Segmente fuer dieselbe Serie in `Cache pruefen` sichtbar, auch wenn sich query-nahe UI-Settings oder Fingerprints geaendert haben. ([#251](https://github.com/thomas682/HA-Addons/issues/251))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.305

### Fix

- Der Analyse-Logdialog mischt jetzt serverseitige Analyse-History mit den lokal gespeicherten Analyse-Events, sodass alle sichtbaren Analyse-/Checklist-Schritte und Chunk-Details im Volltextdialog auftauchen. ([#249](https://github.com/thomas682/HA-Addons/issues/249))
- Die Cache-Verifikation unterscheidet jetzt zwischen physisch vorhandenen und direkt wiederverwendbaren Analyse-Cache-Segmenten. Dadurch wird sichtbar, wenn Segmente gespeichert wurden, der frische Cache-Plan sie aber noch nicht wiederverwendet. ([#249](https://github.com/thomas682/HA-Addons/issues/249))
- Der hängende Status `Raw laedt... dashboard.raw` wird in zusätzlichen Frühabbruch-/Cleanup-Pfaden beendet. Gleichzeitig wurde die Mindestbreite des Topbar-Suchfelds gelockert, damit `page_main.input_search` bei kleiner Fensterbreite nicht mehr von den folgenden Controls überdeckt wird. ([#249](https://github.com/thomas682/HA-Addons/issues/249))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Marker fuer Analyse-Logdialog, Cache-Physik/Wiederverwendung, Raw-Status-Cleanup und Topbar-Suchfeld geprueft
- Tests: Script-Balance fuer `index.html` und `_topbar.html` geprueft
- Tested with Home Assistant Core: unknown

## 1.12.304

### Enhancement

- Der Analyse-Fortschrittsbalken startet jetzt sofort nach dem Buttondruck und bildet alle Hauptphasen des Analyseflows ab, statt nur auf der Chunk-Anzahl zu basieren. Die Checkliste hat zusaetzlich den neuen Schritt `Gespeicherten Cache pruefen`, damit physisch gespeicherte Segmente und direkt wiederverwendbare Segmente sichtbar unterschieden werden. ([#248](https://github.com/thomas682/HA-Addons/issues/248))

### Fix

- Tooltips bleiben jetzt auch im `S-Picker` deaktiviert. Der Tooltip-Renderer setzt keine `title`-Attribute mehr nach, solange Picker oder S-Picker aktiv sind. ([#248](https://github.com/thomas682/HA-Addons/issues/248))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Marker fuer Fortschrittsmodell, Cache-Verifikationsschritt und S-Picker-Tooltip-Unterdrueckung geprueft
- Tests: Script-Balance fuer `index.html` und `_tooltips.html` geprueft
- Tested with Home Assistant Core: unknown

## 1.12.303

### Fix

- Analyse-Cache-Segmente gelten jetzt nur dann als erfolgreich gespeichert, wenn Payload und Metadatei danach wirklich vorhanden und wieder lesbar sind. Dadurch wird der Widerspruch behoben, dass die Analyse `gespeichert` meldet, `Cache pruefen` danach aber keinen Analyse-Cache sieht. ([#247](https://github.com/thomas682/HA-Addons/issues/247))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.302

### Enhancement

- Die Fehler-Statusleiste hat jetzt direkte Schnellaktionen fuer `Bugreport`, `5 min Logs` und `Jump Logs`. Die Analyse-Sektion besitzt zusaetzlich einen eigenen Volltext-Logdialog mit Filtern fuer `Ausloeser`, `Bereichsfilter` und Freitextsuche. ([#246](https://github.com/thomas682/HA-Addons/issues/246))
- Die Analyse verwendet jetzt dieselben Icons fuer `Query anzeigen`, `Query testen` und `Gesamtstatistik` wie der Caching-Bereich. Der Chunk-Zeitstrahl ist als durchgaengiger Balken ohne Zwischenabstaende ausgefuehrt und nutzt die volle Breite des Analyse-Bereichs. ([#246](https://github.com/thomas682/HA-Addons/issues/246))

### Fix

- Die adaptive Chunk-Vergoesserung funktioniert wieder fuer grosse Restbereiche: verbleibende zusammenhaengende Chunk-Bereiche werden vor dem Neuaufbau wieder zusammengefasst, sodass schnelle Tages-Chunks jetzt zu groesseren Intervallen anwachsen koennen statt bei hunderten Ein-Tages-Chunks zu bleiben. ([#246](https://github.com/thomas682/HA-Addons/issues/246))
- Nach der Analyse wird die Caching-Sektion jetzt immer frisch aktualisiert, damit neu gespeicherte Analyse-Cache-Segmente auch in `Cache pruefen` sichtbar werden. ([#246](https://github.com/thomas682/HA-Addons/issues/246))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Marker fuer Statusbar-Buttons, Logdialog, kontinuierlichen Chunk-Zeitstrahl und Cache-Refresh geprueft
- Tests: Template-Klammer-Balance fuer `index.html`, `config.html`, `_topbar.html` und `_tooltips.html` geprueft
- Tested with Home Assistant Core: unknown

## 1.12.301

### Enhancement

- Die Analyse-Sektion hat jetzt eigene Aktionsbuttons fuer Abbruch, Query anzeigen, Query testen und Gesamtstatistik. Die Checkliste zeigt Zeitstempel und Dauer links vor dem Schritttext, und die Analyse visualisiert Chunks zusaetzlich in einem farbigen Zeitstrahl mit Prozentanzeige und kompakter Chunk-Zusammenfassung. ([#245](https://github.com/thomas682/HA-Addons/issues/245))
- Fehlende/geaenderte Cache-Bereiche werden bei `Analyse mit Cache` vor dem ersten Request in Tages-Chunks zerlegt, adaptiv weiter angepasst und bei Fehlern bis zu drei Mal mit kleineren Chunks erneut versucht. Sichtbare Chunk-/Checklist-Infos werden weiterhin ins Logfile geschrieben. ([#245](https://github.com/thomas682/HA-Addons/issues/245))

### Fix

- Die Einstellungsseite zeigt wieder die vollstaendige vorhandene Settings-Ansicht, statt durch die nachtraegliche DOM-Umsortierung viele Werte zu verstecken. Zusaetzlich ist `ui_raw_outlier_search_limit` jetzt wieder als eigenes Eingabefeld sichtbar und speicherbar. ([#245](https://github.com/thomas682/HA-Addons/issues/245))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Marker fuer Analyse-Toolbar, Chunk-Planung, Settings-Feld und Template-Klammer-Balance geprueft
- Tested with Home Assistant Core: unknown

## 1.12.300

### Fix

- Analyse mit Cache: Der 500-Fehler \`NameError: name 'limit' is not defined\` im Endpunkt \`/api/outliers\` ist behoben. Das Limit wird jetzt aus der Konfiguration gelesen und korrekt an die Scan-Funktion uebergeben.

### Maintenance

- Tests: \`python -m py_compile influxbro/app/app.py\`
- Tested with Home Assistant Core: unknown

## 1.12.299

### Fix

- Analyse mit Cache: Der 500-Fehler \`NameError: name 'search_types' is not defined\` ist behoben. Der Endpunkt \`/api/outliers\` extrahiert jetzt \`search_types\` aus dem Request-Body und leitet die individuellen Flags (\`include_null\`, \`bounds_enabled\`, etc.) daraus ab. ([#242](https://github.com/thomas682/HA-Addons/issues/242))

### Maintenance

- Tests: \`python -m py_compile influxbro/app/app.py\`
- Tested with Home Assistant Core: unknown

## 1.12.298

### Fix

- Analyse mit Cache: Der 404-Fehler bei der Ausreisser-Suche ist behoben. Das Frontend ruft jetzt korrekt `/api/outliers` statt des nicht existierenden `/api/outlier_search` auf. ([#240](https://github.com/thomas682/HA-Addons/issues/240))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Dashboard-Skript auf Klammer-Balance geprueft
- Tested with Home Assistant Core: unknown

## 1.12.297

### Enhancement

- Die rechte Titelzeile ist jetzt in `topbar_main.panel_profile` als gemeinsamer Wrapper zusammengefasst. `topbar_main.panel_zoom`, Seitensuche, Suchnavigation und Open/Close-All umbrechen dadurch sauber gemeinsam, und `nav_main.panel_donate` zeigt PayPal und Buy-me-a-coffee nebeneinander an. ([#239](https://github.com/thomas682/HA-Addons/issues/239))
- Die Analyse-Checkliste zeigt jetzt den echten Cache-Workflow: Cache-Plan laden, Cache-Hit pruefen, fehlende Restbereiche lesen, neue Cache-Segmente speichern und Cache-Segmente kombinieren. Alle sichtbaren Checklist-Schritte werden zusaetzlich als Analyse-Events ins Add-on-Logfile geschrieben. ([#239](https://github.com/thomas682/HA-Addons/issues/239))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Dashboard-Skript auf Klammer-Balance und Cache-Checklist-Marker geprueft
- Tests: `_topbar.html` auf Topbar-Wrapper- und Donate-Layout-Marker geprueft
- Tested with Home Assistant Core: unknown

## 1.12.296

### Fix

- Die Seitensuche in der Topbar bleibt bei schmaler Fensterbreite benutzbar: `page_main.input_search` bricht jetzt vor die Seitensuch-Buttons um, statt von `page_search.btn_prev` und den rechts folgenden Buttons ueberdeckt zu werden. ([#238](https://github.com/thomas682/HA-Addons/issues/238))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `_topbar.html` auf responsive Marker fuer Suchfeld-Umbruch geprueft
- Tested with Home Assistant Core: unknown

## 1.12.295

### Enhancement

- Die Dashboard-Analyse-Checkliste zeigt jetzt feste Schritte mit HH:MM:SS-Zeitstempeln. Noch nicht durchlaufene Schritte erscheinen mit `?`, erfolgreiche Schritte mit gruenem Haken und Fehler mit rotem Kreuz.
- Direkt nach Klick auf `Analyse mit Cache` oder `Analyse ohne Cache` erscheinen sofort fruehe Statuszeilen wie `Analyse durch Button gestartet` und `Cache-Status pruefen`, damit die GUI schon vor dem eigentlichen Suchlauf sichtbares Feedback gibt. ([#237](https://github.com/thomas682/HA-Addons/issues/237))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: eingebettetes Dashboard-Skript auf Klammer-Balance und Checklist-Marker geprueft
- Tested with Home Assistant Core: unknown

## 1.12.294

### Fix

- Analyse-Cache kombinieren liefert bei nicht kombinierbaren Segmenten keinen 400-Fehler mehr. Wenn keine zusammenhaengenden Segmente vorhanden sind, antwortet die API jetzt erfolgreich mit `groups_combined: 0` statt mit `no contiguous segments to combine`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.293

### Fix

- Dashboard-Analysefunktionen wieder verfuegbar: Der versehentlich zu weit reichende Kommentarblock um eine alte `runRawOutlierSearch`-Implementierung wurde auf den Legacy-Block selbst begrenzt. Dadurch ist `getRawOutlierFilterTypes()` wieder im aktiven Script verfuegbar und `Cache pruefen` funktioniert wieder.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Klammer-Balance des eingebetteten Dashboard-Skripts geprueft
- Tested with Home Assistant Core: unknown

## 1.12.292

### Fix

- Dashboard-JavaScript repariert: Die versehentlich doppelt vorhandene alte `runRawOutlierSearch()`-Implementierung wird nicht mehr mitgeparst. Dadurch verschwindet der Browser-Fehler `Unexpected end of input` beim Laden des Dashboards.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: Klammer-Balance des eingebetteten Dashboard-Skripts geprueft
- Tested with Home Assistant Core: unknown

## 1.12.291

### Fix

- SyntaxError `Unexpected end of input` beim Dashboard-Aufruf behoben. Ursache: Duplizierter outlier_windows-Code-Block in `runRawOutlierSearch()` hatte falsche Klammer-Struktur.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.290

### Enhancement

- Raw-Daten-Laden bei Klick auf Ausreisser: Die expandierende Zeitschleife (bis zu 19+ API-Aufrufe) entfällt komplett. Stattdessen wird während der Analyse für jeden Ausreisser das optimale Zeitfenster (N Punkte vor/nach) berechnet und im Cache gespeichert. Beim Klick: ein einziger API-Aufruf mit dem korrekten Fenster.
- Neuer Backend-Endpunkt `/api/outlier_windows`: Berechnet nach der Analyse einmalig für alle Ausreisser die Fenstergröße basierend auf Point-Index-Arithmetik.
- Alter Cache ohne `window`-Feld wird beim Klick automatisch gelöscht und muss neu analysiert werden.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "tooltip"`
- Tested with Home Assistant Core: unknown

## 1.12.289

### Enhancement

- Ausreisser-Tabelle: Neuer "Kopieren"-Button kopiert alle Zeilen und Spalten als TSV in die Zwischenablage.
- "Nicht mehr ignorieren"-Button funktioniert jetzt korrekt: Beim Klick auf eine ignorierte Zeile wird der Button aktiviert.

### Fix

- Einstellungsseite: TypeError `Cannot set properties of null (setting 'value')` behoben. Ursache waren 10 fehlende HTML-Elemente (`ui_open_selection`, `ui_open_graph`, `ui_open_filterlist`, `ui_open_editlist`, `ui_open_stats_total`, `ui_tooltips_enabled`, `ui_log_error_bg`, `ui_log_error_fg`, `ui_log_warn_bg`, `ui_log_warn_fg`).
- Null-Guards in `setForm()` und `getForm()` verhindern, dass einzelne fehlende Elemente die gesamte Form-Population abbrechen.
- Duplikat im `ids`-Array (`outlier_gap_seconds_default`) entfernt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "tooltip"`
- Tested with Home Assistant Core: unknown

## 1.12.288

### Enhancement

- Alle Dashboard-Tooltips verwenden jetzt explizite `data-ui`-Keys mit passenden Beschreibungen im TIPS-Dictionary. Dynamisch generierte Buttons (hl/ac/ol im Cache-Zeitstrahl) sowie bisher ohne `data-ui` versehene Elemente (Ausreisser-Suche, Jump-Buttons, Typauswahl) erhalten jetzt korrekte Tooltips.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "tooltip"`
- Tested with Home Assistant Core: unknown

## 1.12.287

### Enhancement

- Große Messwertlücken werden jetzt als eigener Ausreißer-Typ `Messwertlücke` erkannt und nicht mehr automatisch als normaler `step > max_step`-Sprung oder fortgesetzte `fault_active`-Phase behandelt. ([#236](https://github.com/thomas682/HA-Addons/issues/236))
- Für Messwertlücken gibt es jetzt einen konfigurierbaren Schwellwert `outlier_gap_seconds_default` in den Einstellungen sowie Override-Felder im Dashboard (`raw_param_gap_seconds`, `out_gap_seconds`). ([#236](https://github.com/thomas682/HA-Addons/issues/236))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_outlier_search.py tests/test_api_ui_support.py -q -k "gap"`
- Tested with Home Assistant Core: unknown

## 1.12.286

### Fix

- Native Tooltips wurden vereinheitlicht: kurze Funktionsbeschreibung plus Elementname in Klammern, und waehrend `Picker`/`S-Picker` erscheinen keine Tooltips mehr. ([#234](https://github.com/thomas682/HA-Addons/issues/234))
- Unter der Analyse-Cache-Summary werden die im Cache gefundenen Ausreißer jetzt nach Typ aufgelistet. Zusaetzlich gibt es pro Cache-Segment den Toggle `ol`, der vertikale Marker fuer Ausreißer-Zeitpunkte im Zeitstrahl ein-/ausblendet. ([#234](https://github.com/thomas682/HA-Addons/issues/234))
- `Analyse mit Cache` und `Analyse ohne Cache` kombinieren nach erfolgreichem Lauf jetzt automatisch zusammenhaengende Cache-Segmente wie der Dashboard-Button `kombinieren`. ([#235](https://github.com/thomas682/HA-Addons/issues/235))
- `dashboard_analysis.txt_inline_stats` verwendet jetzt ein Info-Symbol statt Haken. In `dashboard_outliers.section_root` gibt es zusaetzlich `ignorieren` / `nicht mehr ignorieren`, und `dashboard_raw.btn_kopieren` kopiert jetzt alle sichtbaren Spalten und Inhalte als TSV. ([#235](https://github.com/thomas682/HA-Addons/issues/235))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "tooltip_template_uses_short_description_plus_key_and_mentions_picker_suppression or dashboard_cache_summary_lists_type_counts_and_has_outlier_toggle or dashboard_issue235_controls_exist"`
- Tested with Home Assistant Core: unknown

## 1.12.285

### Fix

- Die Statistik-Seite behandelt abgelaufene `global_stats`-Jobs jetzt still: alte Job-IDs werden aus dem Browser-Storage entfernt und die Seite faellt ohne lauten 404-Fehler auf Cache-/Snapshot-Laden zurueck. ([#233](https://github.com/thomas682/HA-Addons/issues/233))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "stats_page_clears_expired_last_job_ids_before_cache_fallback"`
- Tested with Home Assistant Core: unknown

## 1.12.284

### Fix

- `Analyse mit Cache` behaelt vorgeladene Analyse-Cache-Treffer jetzt bis zum Ende des Suchlaufs, sodass `dashboard_outliers.tbl_ausreisser` und `dashboard_analysis.txt_found_info` nach Cache-Nutzung wieder befuellt werden. ([#230](https://github.com/thomas682/HA-Addons/issues/230))
- `nav_main.btn_ui_picker` und `nav_main.btn_ui_picker_super` akzeptieren jetzt auch deaktivierte Elemente ueber `mousedown`, und waehrend des Picker-Modus werden native `title`-Tooltips temporaer unterdrueckt. ([#231](https://github.com/thomas682/HA-Addons/issues/231))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "cache_analysis_keeps_preloaded_results_before_search or picker_suppresses_titles_and_handles_disabled_elements_via_mousedown"`
- Tested with Home Assistant Core: unknown

## 1.12.283

### Enhancement

- Die Dashboard-Caching-Zeilen wurden auf `hl`/`ac`-Toggles umgestellt. `hl` hebt ein Segment im Zeitstrahl hervor, `ac` blendet es rein visuell grau aus/ein. Rechts wird pro Segment die Ausreißer-Summe angezeigt. ([#232](https://github.com/thomas682/HA-Addons/issues/232))
- In der Caching-Zone gibt es jetzt die Buttons `kombinieren` und `löschen` für den aktuellen Messwert-Cache. Zusammenhängende Analyse-Cache-Segmente werden serverseitig kombiniert; dabei werden Dirty-Bereiche frisch integriert und die alten Segmente entfernt. ([#232](https://github.com/thomas682/HA-Addons/issues/232))
- Der Dashboard-Block `Auswahl` heißt jetzt `Messwertauswahl`; der zusätzliche sichtbare Text `Quelle` entfällt. ([#232](https://github.com/thomas682/HA-Addons/issues/232))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_cache.py tests/test_api_ui_support.py -q -k "analysis_cache_combine_merges_contiguous_segments or dashboard_cache_timeline_has_hl_ac_toggles_and_combine_buttons or cache_timeline_hidden_color_and_jobs_analysis_table_features_exist"`
- Tested with Home Assistant Core: unknown

## 1.12.282

### Enhancement

- `Messwertauswahl` ersetzt auf dem Dashboard den bisherigen Titel `Auswahl`; der sichtbare Text `Quelle` entfällt. In der Caching-Zone gibt es jetzt die Buttons `kombinieren` und `löschen` fuer den aktuellen Messwert-Cache. ([#228](https://github.com/thomas682/HA-Addons/issues/228))
- Die Segmentzeilen im Dashboard-Zeitstrahl besitzen jetzt die zwei Toggle-Buttons `hl` und `ac`. `hl` markiert ein Segment im Zeitstrahl, `ac` blendet es rein visuell grau aus/ein. Rechts wird pro Cache-Segment die Summe der Ausreißer angezeigt. ([#228](https://github.com/thomas682/HA-Addons/issues/228))
- `kombinieren` fasst zusammenhängende Analyse-Cache-Segmente serverseitig zu neuen Cache-Dateien zusammen, integriert bekannte Messwertänderungen direkt in den kombinierten Cache, entfernt die alten Einzel-Segmente und setzt das Aktualisierungsdatum neu. ([#228](https://github.com/thomas682/HA-Addons/issues/228))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_cache.py tests/test_api_ui_support.py -q -k "analysis_cache_combine_merges_contiguous_segments or dashboard_cache_timeline_has_hl_ac_toggles_and_combine_buttons or cache_timeline_hidden_color_and_jobs_analysis_table_features_exist"`
- Tested with Home Assistant Core: unknown

## 1.12.281

### Enhancement

- Der Dashboard-Zeitstrahl des Analyse-Cache verwendet jetzt unterschiedliche Farben pro Cache-Segment. Die Segmentzeilen darunter sind klickbar und blenden Segmente rein visuell grau aus bzw. wieder ein; die Ausblendefarbe ist jetzt in den Einstellungen konfigurierbar. ([#229](https://github.com/thomas682/HA-Addons/issues/229))
- `Jobs & Cache: jobs_analysis_cache.tbl_table` verwendet jetzt dieselbe Zeitstrahl-Optik wie das Dashboard, inklusive Segmentfarben und Zeitlabels. Zusaetzlich gibt es dort eine Pfad-Spalte sowie die ueblichen Tabellenaktionen (Auto-Breite, Fensterbreite, Umbruch, Spaltenfilter). ([#229](https://github.com/thomas682/HA-Addons/issues/229))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "cache_timeline_hidden_color_and_jobs_analysis_table_features_exist"`
- Tested with Home Assistant Core: unknown

## 1.12.280

### Enhancement

- Die Caching-Section besitzt jetzt rechts im Titel eine `.ib_summary_actions`-Zone mit Info-Button. In der Cache-Summary gibt es zusaetzlich rechts neben `Geaendert` einen `?`-Button mit Erklaerung der Cache-Zustaende. ([#227](https://github.com/thomas682/HA-Addons/issues/227))
- Unter dem Cache-Zeitstrahl werden jetzt Start-/Endzeiten und die Zeiten der einzelnen Cache-, Neu-lesen- und Geaendert-Bereiche sichtbar aufgelistet. ([#227](https://github.com/thomas682/HA-Addons/issues/227))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "caching_section_has_info_button_timeline_labels_and_summary_actions"`
- Tested with Home Assistant Core: unknown

## 1.12.279

### Fix

- Ein nach der `data-ui`-Migration versehentlich umbenannter normaler JS-State-Key im Dashboard wurde korrigiert; dadurch ist der Browser-Syntaxfehler `Unexpected token '.'` in `index.html` behoben. ([#226](https://github.com/thomas682/HA-Addons/issues/226))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: JS-Syntaxpruefung des eingebetteten Dashboard-Scripts in `index.html` via `node`/`vm.Script`
- Tested with Home Assistant Core: unknown

## 1.12.278

### Enhancement

- `tip.selection` auf dem Dashboard wurde entfernt und `analysis_start_info` direkt unter `analysis_status` in die sichtbare Caching-Zone verschoben. Beim Start `Analyse mit Cache` bleiben nun bereits bekannte Cache-Ausreißer erhalten; fehlende Bereiche werden ergänzt statt den vorgeladenen Bestand wieder zu verwerfen. ([#223](https://github.com/thomas682/HA-Addons/issues/223))
- Die restlichen Seiten und Shared-Templates wurden auf das strukturierte `data-ui`-Schema `page_section.role_action` migriert, inklusive Jobs, Settings, Stats, Backup/Restore, Logs, History, Import/Export, Topbar und Navigation. ([#225](https://github.com/thomas682/HA-Addons/issues/225))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "issue223_removed_tip_selection_and_moved_start_info or non_dashboard_pages_use_structured_data_ui_samples"`
- Tested with Home Assistant Core: unknown

## 1.12.277

### Enhancement

- Die Dashboard-Seite verwendet jetzt ein strukturiertes `data-ui`-Namensschema im Format `page_section.role_action`, z. B. `dashboard_caching.btn_cache_pruefen`, `dashboard_analysis.btn_analyse_mit_cache` oder `dashboard_raw.tbl_rohdaten`. ([#224](https://github.com/thomas682/HA-Addons/issues/224))
- `Template.md` dokumentiert das neue `data-ui`-Schema; das Folge-Issue fuer die restlichen Seiten bleibt separat offen. ([#224](https://github.com/thomas682/HA-Addons/issues/224))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "structured_data_ui_naming_scheme_samples"`
- Tested with Home Assistant Core: unknown

## 1.12.276

### Fix

- Die Cache-Summary, der Zeitstrahl und die Cache-Aenderungen werden jetzt in der sichtbaren `Caching`-Section gerendert statt in einem versteckten Alt-Dialog. ([#222](https://github.com/thomas682/HA-Addons/issues/222))
- `dashboard.AnalyseStart` schreibt die Cache-Pruefung jetzt mit sichtbaren Plan-/Aenderungsinformationen in den Analyse-Verlauf. ([#222](https://github.com/thomas682/HA-Addons/issues/222))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "caching_section_has_visible_cache_targets_and_no_old_dialog"`
- Tested with Home Assistant Core: unknown

## 1.12.275

### Fix

- `InfluxBroLogo.png`, `logo.png` und `icon.png` wurden bei gleicher 3:2-Proportion randärmer beschnitten, damit das Add-on-Logo auf der Home-Assistant-Info-Seite größer wirkt. ([#221](https://github.com/thomas682/HA-Addons/issues/221))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Dateien: `influxbro/images/InfluxBroLogo.png`, `influxbro/logo.png`, `influxbro/icon.png` verifiziert (`1200x800`)
- Tested with Home Assistant Core: unknown

## 1.12.274

### Enhancement

- Eine neue Section `Caching` sitzt jetzt vor `section.analysis`. Der bisherige Aktionsblock wurde dorthin verschoben; der modale Analyse-Startdialog ist fuer den Normalablauf nicht mehr noetig. In `section.analysis` gibt es stattdessen direkte Buttons fuer `Analyse mit Cache` und `Analyse ohne Cache`. ([#220](https://github.com/thomas682/HA-Addons/issues/220))
- `raw.outlier_table` ist wieder stabil klickbar markierbar. Sowohl `raw.table` als auch `raw.outlier_table` zeigen jetzt auch ungefuellt immer mindestens 5 sichtbare Leerzeilen. ([#220](https://github.com/thomas682/HA-Addons/issues/220))
- Das Feld `raw_outlier_display_limit_per_type` ist im `raw_search_bar` optisch an den Typ-Selektor angeglichen. ([#220](https://github.com/thomas682/HA-Addons/issues/220))
- `fault_phase`-Treffer werden in der Ausreißer-Tabelle jetzt als zusammengefasste Stoerphasen mit Start/Ende und Punktanzahl dargestellt, statt viele einzelne `fault_active`-Zeilen zu zeigen. ([#220](https://github.com/thomas682/HA-Addons/issues/220))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "issue219_analysis_controls_and_limits_exist"`
- Tested with Home Assistant Core: unknown

## 1.12.273

### Enhancement

- Der Dashboard-Button `dashboard.load` wurde auf `dashboard.AnalyseStart` umgestellt; Aktionen und Hinweistext sitzen jetzt direkt unter dem Analyse-Titel. ([#219](https://github.com/thomas682/HA-Addons/issues/219))
- Die Analyse zeigt die Gesamtstatistik direkt im Analyse-Bereich als kompakte Liste; doppelte Zeitraum-/Stats-Infos wurden aus `analysis_info` entfernt. ([#219](https://github.com/thomas682/HA-Addons/issues/219))
- Die Typ-Auswahl im Analyse-Bereich wurde korrigiert: Ein Klick verschiebt Typen jetzt wirklich zwischen `Gewaehlte Typen` und `Abgewaehlte Typen`. Zusaetzlich gibt es `Reset` und die Checkbox `Ignoriert`. ([#219](https://github.com/thomas682/HA-Addons/issues/219))
- Im `raw_search_bar` ist jetzt `Max je Typ` parametrierbar; intern werden weiterhin alle Ausreißer berechnet, in der GUI aber pro Typ begrenzt angezeigt. Der Wert ist auch in den Einstellungen verfuegbar. ([#219](https://github.com/thomas682/HA-Addons/issues/219))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "issue219_analysis_controls_and_limits_exist"`
- Tested with Home Assistant Core: unknown

## 1.12.272

### Enhancement

- Die Dashboard-Analyse besitzt jetzt einen persistenten serverseitigen `Analysecache` mit Zeitstrahl im `analysis_confirm_dialog`; vorhandene Segmente, neu zu lesende Bereiche und nachtraeglich geaenderte Cache-Bereiche werden dort direkt sichtbar. ([#214](https://github.com/thomas682/HA-Addons/issues/214))
- Die Ausreissersuche baut den Analyse-Cache immer mit allen Typen (`bounds`, `counter`, `decrease`, `fault_phase`, `null`, `zero`) auf und nutzt beim naechsten Lauf vorhandene Cache-Segmente wieder, waehrend nur Luecken oder geaenderte Bereiche neu gelesen werden. ([#214](https://github.com/thomas682/HA-Addons/issues/214))
- Auf `Cache & Jobs` gibt es jetzt einen eigenen Bereich `Analysecache` mit Serienliste, farbigem Zeitstrahl, Groessenanzeige sowie Aktionen zum Loeschen und kompletten Neuaufbau. ([#214](https://github.com/thomas682/HA-Addons/issues/214))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_cache.py tests/test_api_ui_support.py -q -k "analysis_cache"`
- Tested with Home Assistant Core: unknown

## 1.12.271

### Maintenance

- Die Quelldatei des Logos im Repository wurde auf `influxbro/images/InfluxBroLogo.png` vereinheitlicht; die kleine `90 x 60`-Ansicht in GitHub war nur die Vorschau, die echte Bildgroesse ist `1536 x 1024`. ([#218](https://github.com/thomas682/HA-Addons/issues/218))
- Tests: `python -m py_compile influxbro/app/app.py`
- Dateien: `influxbro/images/InfluxBroLogo.png`, `influxbro/icon.png`, `influxbro/logo.png` verifiziert
- Tested with Home Assistant Core: unknown

## 1.12.270

### Fix

- `icon.png` und `logo.png` des Add-ons verwenden jetzt das gewuenschte Bild `InfluxBroLogo.png`. ([#217](https://github.com/thomas682/HA-Addons/issues/217))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Dateien: `influxbro/icon.png`, `influxbro/logo.png` verifiziert
- Tested with Home Assistant Core: unknown

## 1.12.269

### Enhancement

- Root-README und Add-on-README enthalten jetzt einen direkten Home-Assistant-Installationslink fuer das Repository. ([#216](https://github.com/thomas682/HA-Addons/issues/216))
- Das Add-on liefert jetzt eigene `icon.png`- und `logo.png`-Dateien fuer die Home-Assistant-Darstellung im Stil des gewuenschten Referenz-Add-ons. ([#216](https://github.com/thomas682/HA-Addons/issues/216))
- Changelog-Eintraege mit Issue-Bezug wurden auf klickbare GitHub-Issue-Links nachgezogen; kuenftige Pflicht dazu ist in `AGENTS.md` festgehalten. ([#216](https://github.com/thomas682/HA-Addons/issues/216))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.268

### Enhancement

- Analysebezogene Cache-Plan- und Cache-Aenderungsinformationen werden jetzt in den Analyse-Verlauf uebernommen, statt im Bereich `dashboard.load_status` gerendert zu werden. ([#215](https://github.com/thomas682/HA-Addons/issues/215))
- Die Live-Analyse in `section.analysis` zeigt keine einzelnen Chunk-Zeilen mehr; die Chunk-Details bleiben ausschliesslich im Analyse-Verlauf sichtbar. ([#215](https://github.com/thomas682/HA-Addons/issues/215))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.267

### Enhancement

- Der `S-Picker` (`nav.ui_picker_super`) kann jetzt alle relevanten Treffer unter dem Mauszeiger als Trefferliste bereitstellen; mit dem Mausrad laesst sich zwischen ueberdeckten Elementen wie `section.analysis` und `analysis_checklist` wechseln, bevor der gewuenschte Treffer per Klick kopiert wird. ([#213](https://github.com/thomas682/HA-Addons/issues/213))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.266

### Fix

- Die Dashboard-Analyse verwendet ihren Session-Cache jetzt auch bei `0` Treffern wieder korrekt und bildet fuer `range=all` einen stabileren Cache-Key, damit direkte Wiederholungen nicht jedes Mal erneut alle Chunks durchlaufen. ([#212](https://github.com/thomas682/HA-Addons/issues/212))
- Der Analyse-Dialog startet die Dashboard-Analyse nicht mehr doppelt; damit entfaellt der zweite `analysis / start` mit nachfolgendem `blocked`-Reset. ([#212](https://github.com/thomas682/HA-Addons/issues/212))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.265

### Fix

- Der `S-Picker` (`nav.ui_picker_super`) kann im Super-Modus jetzt auch Elemente ohne `data-ui`, aber mit stabiler `id`, direkt erfassen, z. B. `analysis_start_info`. ([#211](https://github.com/thomas682/HA-Addons/issues/211))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.264

### Fix

- Dashboard-Analyse konsolidiert Status- und Fortschrittseintraege jetzt in `analysis_checklist`; doppelte Eintraege entfallen und einzelne Chunks werden dort direkt mit angezeigt, waehrend `dashboard.load_status` keine separaten Chunk-Zeilen mehr ausgibt. ([#210](https://github.com/thomas682/HA-Addons/issues/210))
- Der `S-Picker` (`nav.ui_picker_super`) nutzt im Super-Modus wieder vorrangig das direkt getroffene Element wie in den frueheren Versionen und faellt erst danach auf tiefere Stack-Treffer zurueck. ([#210](https://github.com/thomas682/HA-Addons/issues/210))

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.263

### Fix

- Analyse-Verlauf (`dashboard.analysis_history`) wird jetzt als reiner Plain-Text ohne HTML-Wrapper oder `{ bodyHtml: true }` an das Popup uebergeben.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.262

### Fix

- `dashboard.load_status` ist jetzt dauerhaft sichtbar (nicht nur waehrend des Ladens). ([#209](https://github.com/thomas682/HA-Addons/issues/209))
- `nav.ui_picker_super` (S-Picker) kann wieder alle Elemente auf der Seite selektieren. ([#209](https://github.com/thomas682/HA-Addons/issues/209))
- Analyse-Verlauf wird jetzt als reiner Text im Modal angezeigt (nicht als HTML). ([#209](https://github.com/thomas682/HA-Addons/issues/209))
- Neuer Info-Panel-Bereich zeigt aktuelle Messwert-Statistiken (Anzahl Werte, Min/Max, aeltester/neuster Zeitstempel). ([#209](https://github.com/thomas682/HA-Addons/issues/209))
- Ausreisser-Tabelle markiert Zeilen nicht mehr automatisch beim Rendern. ([#209](https://github.com/thomas682/HA-Addons/issues/209))
- `currentPageLabel` ReferenceError behoben (Funktion jetzt global verfuegbar). ([#209](https://github.com/thomas682/HA-Addons/issues/209))
- Analyse-Button oeffnet jetzt einen Bestaetigungsdialog mit Uebersicht aller Parameter vor dem Start. ([#209](https://github.com/thomas682/HA-Addons/issues/209))
- `raw.outlier_actions` Layout umstrukturiert – Suchleiste oben, Aktionen und Tabelle nebeneinander, `raw_outlier_info` entfernt. ([#208](https://github.com/thomas682/HA-Addons/issues/208))
- `dashboard.cancel` (Abbruch-Button) wird jetzt waehrend der Analyse sichtbar und beendet alle laufenden Anfragen. ([#207](https://github.com/thomas682/HA-Addons/issues/207))

### Enhancement

- Neuer API-Endpunkt `POST /api/series_stats` liefert Basis-Statistiken fuer eine Measurement/Field-Serie.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.261

### Enhancement

- Paket C: Die Einstellungen werden jetzt in Hauptbereiche fuer `Datenbank`, `Allgemein` und menuebezogene Bereiche gegliedert; der alte Sammelblock `settings.section.ui` wird zur Laufzeit aufgeloest.
- Mehrfach genutzte Parameter werden unter `Allgemein` gebuendelt, waehrend Fachbereiche statt doppelter Werte gezielt auf globale Parameter verlinken.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "settings_restructure_script_and_general_navigation_params_exist or settings_layout_and_null_safe_bindings_are_present or navigation_helper_controls_and_config_exist"`
- Tested with Home Assistant Core: unknown

## 1.12.260

### Enhancement

- Paket B: `page.title.card` bietet jetzt eine Navigationshilfe mit Verlauf, Vor/Zurueck-Sprung und einer Parametrierhilfe fuer verknuepfte Elemente.
- Die Navigationshilfe kann Highlight-Farbe, Highlight-Dauer und Verlaufsgroesse ueber neue Einstellungen steuern.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "navigation_helper_controls_and_config_exist or navigation_helper_uses_pending_target_and_html_badges or picker_supports_disabled_targets_and_angle_bracket_labels or dashboard_load_runs_cache_path_and_stats_reload"`
- Tested with Home Assistant Core: unknown

## 1.12.259

### Fix

- Paket A: Dashboard-Analyse nutzt jetzt wieder den eigentlichen Dashboard-Ladepfad mit Cache-Pruefung, fuellt danach die Gesamtstatistik neu und bietet den Ausreißer-Abbruch direkt in `dashboard.actions` an.
- Picker erfassen jetzt auch deaktivierte Elemente zuverlaessiger und kopieren Labels im Format `<Seite: data-ui>`.
- Die Einstellungsseite entfernt den alten `summary::after`-Pfeil und den Ruecksprung-Button, behebt weitere null-unsichere Feldzuweisungen und korrigiert Layout-Ueberlaeufe bei breiten Parametern.
- Die Standardbreite von `page.search` wurde reduziert.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "picker_supports_disabled_targets_and_angle_bracket_labels or dashboard_load_runs_cache_path_and_stats_reload or settings_layout_and_null_safe_bindings_are_present or dashboard_abort_buttons_and_search_width_are_updated or summary_actions_are_inline_in_topbar_and_back_icon_uses_return_svg"`
- Tested with Home Assistant Core: unknown

## 1.12.258

### Fix

- Der Dialog `dashboard.analysis_history` rendert seine Inhalte jetzt als formatierte HTML-Ansicht statt als escaped Roh-Markup.
- Analyse-, Cache- und zugehoerige Verlaufseintraege werden im Dialog jetzt lesbar nach Eventtyp dargestellt, statt rohe JSON-Strings anzuzeigen.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_history.py -q`
- Tests: `pytest tests/test_api_ui_support.py -q -k "analysis_history_uses_event_log_and_dashboard_actions_params_button"`
- Tested with Home Assistant Core: unknown

## 1.12.257

### Fix

- `dashboard.analysis_history` rendert jetzt korrekt und liest seine Inhalte primaer aus einer neuen serverseitigen Analyse-History statt nur aus browserlokalem Storage.
- Analyse-, Cache- und Markierungsereignisse werden serverseitig gesammelt und gemeinsam im Verlauf angezeigt, inklusive Cache-Nutzung und Cache-Entscheidungen.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_analysis_history.py -q`
- Tests: `pytest tests/test_api_ui_support.py -q -k "analysis_history_uses_event_log_and_dashboard_actions_params_button"`
- Tested with Home Assistant Core: unknown

## 1.12.256

### Fix

- Browser-Debug- und Analyse-Ablaufmeldungen laufen jetzt ueber den neutralen Endpoint `api/client_log` statt ueber `api/client_error`, damit harmlose Netzwerk-Events in DevTools nicht mehr wie echte Fehler wirken.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_client_log.py -q`
- Tests: `pytest tests/test_api_ui_support.py -q -k "analysis_history_uses_event_log_and_dashboard_actions_params_button"`
- Tested with Home Assistant Core: unknown

## 1.12.255

### Enhancement

- Summary-Aktionen stehen jetzt global direkt rechts neben dem jeweiligen Section-Titel statt als separat ueberlagerte Aktionsgruppe.
- Das Ruecksprung-Icon auf der Einstellungsseite nutzt jetzt das neue Return-SVG.
- Im Dashboard wurde `raw_outlier_params` in `dashboard.actions` verschoben, `raw_outlier_context_rows` speichert sofort ab Eingabe, und `raw_search_run` markiert jetzt den aktuell gefilterten Typ in der vorhandenen Ausreißer-Tabelle statt erneut serverseitig zu suchen.
- `dashboard.analysis_history` zeigt jetzt zusaetzlich die echten Durchfuehrungsprotokolle mit Zeitstempeln, und die Dashboard-Cache-Planung protokolliert sichtbare Gruende, wenn kein `Cache verwenden`-Dialog erscheint.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_dashboard_cache_plan.py -q`
- Tests: `pytest tests/test_api_outlier_search.py -q`
- Tests: `pytest tests/test_api_ui_support.py -q -k "summary_actions_are_inline_in_topbar_and_back_icon_uses_return_svg or analysis_history_uses_event_log_and_dashboard_actions_params_button or outlier_search_button_marks_existing_table_and_context_rows_save_immediately or outlier_table_header_is_explicitly_sticky_and_search_bar_tracks_outlier_section or dashboard_load_supports_cache_plan_prompt_and_time_savings"`
- Tested with Home Assistant Core: unknown

## 1.12.254

### Fix

- Die Headerzeile der Dashboard-Ausreissertabelle ist jetzt explizit sticky wie bei `raw.table` und scrollt nicht mehr mit dem Tabelleninhalt weg.
- Die Outlier-Suchleiste richtet sich jetzt nach dem Open/Close-Zustand der eigenen Section `Ausreißer` statt nach `Raw Daten Analyse`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "outlier_table_header_is_explicitly_sticky_and_search_bar_tracks_outlier_section or dashboard_outlier_section_is_separate_and_above_raw_section or raw_outlier_table_uses_template_structure_and_helpers"`
- Tested with Home Assistant Core: unknown

## 1.12.253

### Fix

- Die Dashboard-Ausreissertabelle behaelt jetzt die echten Millisekunden aus `api/outlier_search`, statt Zeitstempel immer auf volle Sekunden zu runden.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_outlier_search.py -q`
- Tests: `pytest tests/test_api_ui_support.py -q -k "raw_outlier_table_uses_template_structure_and_helpers or raw_and_outlier_tables_share_same_font_size_rule or dashboard_outlier_section_is_separate_and_above_raw_section"`
- Tested with Home Assistant Core: unknown

## 1.12.252

### Enhancement

- Der Dashboard-Ausreißerbereich ist jetzt eine eigene Section `Ausreißer` oberhalb von `Raw Daten Analyse`, statt innerhalb des Raw-Bereichs verschachtelt zu sein.
- Die neue Section behaelt die bestehende Ausreißer-Suche, Navigation und Tabelle bei und speichert ihren Open/Close-Zustand lokal im Dashboard-State.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "dashboard_outlier_section_is_separate_and_above_raw_section or raw_outlier_table_uses_template_structure_and_helpers or raw_and_outlier_tables_share_same_font_size_rule or dashboard_load_supports_cache_plan_prompt_and_time_savings"`
- Tested with Home Assistant Core: unknown

## 1.12.251

### Enhancement

- Die Dashboard-Ausreißer-Tabelle folgt jetzt der gemeinsamen Table-Template-Struktur mit eigenem Rahmen, Tabellenkopf, Tabelleninfo sowie Standard-Helpern fuer Spaltenbreite, Umbruch, Spaltenfilter und Hoehenanpassung.
- Die Ausreißer-Tabelle zeigt ihre Zeilenanzahl jetzt als `filtered / total` und nutzt denselben Tabellen-Helper-Stack wie andere Listen im Add-on.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "raw_outlier_table_uses_template_structure_and_helpers or raw_and_outlier_tables_share_same_font_size_rule or dashboard_load_supports_cache_plan_prompt_and_time_savings"`
- Tested with Home Assistant Core: unknown

## 1.12.250

### Fix

- Dashboard `raw.table` und `raw.outlier_table` verwenden jetzt dieselbe erzwungene Tabellen-Schriftgroesse und haben keine abweichende Inline-Schriftgroesse mehr in der Ausreisser-Spalte.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_ui_support.py -q -k "raw_and_outlier_tables_share_same_font_size_rule or dashboard_load_supports_cache_plan_prompt_and_time_savings"`
- Tested with Home Assistant Core: unknown

## 1.12.249

### Enhancement

- Dashboard `Analyse` prueft jetzt serverseitige Cache-Treffer und teilweise passende Cache-Segmente, zeigt bei vorhandener Teilabdeckung fehlende Restbereiche und kann beim Verwenden nur diese Luecken nachladen.
- Die Dashboard-Abarbeitungsliste zeigt jetzt Cache-Segmente, Restabfragen, Merge-Schritte, rote Aenderungswarnungen und eine geschaetzte Zeitersparnis auf Basis der Cache-Nutzungsprotokolle.
- Neue technische Richtlinie `influxbro/caching.md` dokumentiert die bestehenden und neuen Cache-Regeln zentral fuer kuenftige Cache-Funktionen.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tests: `pytest tests/test_api_dashboard_cache_plan.py -q`
- Tests: `pytest tests/test_api_ui_support.py -q -k "cache_plan_prompt_and_time_savings"`
- Tested with Home Assistant Core: unknown

## 1.12.248

### Fix

- Handbuch-Bilder werden jetzt ueber einen abgesicherten Add-on-Pfad ausgeliefert, sodass die eingebetteten Screenshots auf der Handbuch-Seite wieder sichtbar sind.
- Popup- und Logs-Volltextsuche verwenden jetzt die konfigurierbare Highlight-Farbe aus den Einstellungen statt fest verdrahteter Gelb/Orange-Werte.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.247

### Enhancement

- Diagnose (`dbinfo`): `Aktualisieren` und `Query testen` jetzt optisch gleich groß und sauber nebeneinander.
- Handbuch: fehlerhaften Bildpfad für die Übersicht korrigiert.
- `influxbro_profile_modal`: Text jetzt mit 10px (über bestehende Popup-Textgröße steuerbar) und zusätzlicher Checkbox `Zeilenumbruch`.
- `influxbro_popup_card`: Volltextsuche mit Vor/Zurück und gelber Markierung ergänzt.
- Logs-Seite: zweite Textsuche mit Vor/Zurück und gelber Markierung ergänzt.
- Einstellungsseite: `TypeError` durch fehlende Checkbox-Elemente mit null-sicherem Lesen/Schreiben abgefangen.
- Einstellungs-Back-Button verwendet jetzt das gewünschte neue Icon.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.246

### Enhancement

- `Dashboard: raw.actions` erweitert um `Ignorieren` und `Nicht mehr ignorieren`.
- Neuer Ausreißertyp `Ignoriert` für bewusst ausgeblendete Treffer.
- Ignorierte Ausreißer werden global/serverseitig im App-State gespeichert.
- Analyse-Typ-Listen wurden getauscht: `Gewählte Typen` jetzt links, `Abgewählte Typen` rechts.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.245

### Enhancement

- Dashboard `section.raw`: Tabellenkopf-Informationen sind jetzt sichtbarer den jeweiligen Tabellen zugeordnet.
- Ausreißer-Tabelle hat eigenen Kopf-/Info-Bereich.
- Raw-Tabelle hat eigenen Kopf-/Info-Bereich.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.244

### Fix

- `Dashboard: raw.table` zeigt bei Ausreißer-Navigation jetzt nur noch genau `x` Werte davor und `x` Werte danach an (gemäß `raw_outlier_context_rows`).

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.243

### Fix

- `Jobs & Cache: timers.table` speichert den geänderten Modus jetzt sofort beim Ändern des Select-/Zeit-/Intervall-Werts statt erst beim erneuten Klick auf den Modus-Button.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.242

### Fix

- `analysis_debug` und andere reine Debug-Events aus `client_error` werden nicht mehr als ERROR geloggt, sondern als INFO.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.241

### Enhancement

- Section-Header wurden accessibility-freundlich umgestellt: interaktive Buttons werden nun außerhalb von `<summary>` in einem separaten Action-Container gerendert.
- Gilt appweit für Info-, Settings- und Back-Buttons in Section-Headers.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Playwright: `tests/e2e/dashboard-analysis.spec.js` 4/4 bestanden
- Tested with Home Assistant Core: unknown

## 1.12.240

### Fix

- `Startalter löschen` löscht den gespeicherten ältesten Datensatz jetzt sichtbar aus der Dashboard-Anzeige.
- `refreshAnalysisStartInfo()` liest den Startwert nur noch aus dem Cache (`resolve_if_missing: false`) und löst keine sofortige Neuermittlung mehr aus.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Template verification: `resolve_if_missing: false` gesetzt
- Tested with Home Assistant Core: unknown

## 1.12.239

### Enhancement

- Dashboard-Auswahl wird jetzt serverseitig/global unter `dashboard_selection` gespeichert und wiederhergestellt.
- Fachliche Dashboard-Zustände (`measurement`, `field`, `measurement_filter`, `entity_id`, `friendly_name`, `range`, `start`, `stop`, `raw_outlier_types`) sind damit nicht mehr nur browserlokal.
- Neue App-State-API: `GET /api/app_state`, `POST /api/app_state/set`.
- Dashboard lädt globale Auswahl beim Start und schreibt Auswahländerungen direkt serverseitig weg.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Playwright: `tests/e2e/dashboard-analysis.spec.js` 4/4 bestanden
- API: `/api/app_state` lokal verifiziert
- Tested with Home Assistant Core: unknown

## 1.12.238

### Fix

- Analyse verwendet bei `Zeitraum = Alle` jetzt den serverseitig ermittelten effektiven Startwert auch tatsaechlich fuer die Ausreissersuche.
- `runRawOutlierSearchWithProgress()` akzeptiert nun das bereits berechnete Analyse-Zeitfenster aus `resolveEffectiveAnalysisWindow()` statt erneut `_rawWindowIso()` zu verwenden.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Playwright: `tests/e2e/dashboard-analysis.spec.js` 4/4 bestanden
- API: `/api/series_oldest` lokal verifiziert
- Tested with Home Assistant Core: unknown

## 1.12.237

### Enhancement

- Analyse merkt sich serverseitig pro Messwert den aeltesten bekannten Datensatz und nutzt ihn bei Zeitraum `Alle` als effektiven Start, begrenzt durch `Max. Alter der Datenanalyse (Jahre)`.
- Dashboard zeigt unter der Quellauswahl jetzt `Analyse-Start`, `Ältester bekannter Datensatz` und `Ermittelt am` sowie den Button `Startalter löschen`.
- Neue API-Endpunkte fuer Analyse-Startwert: `POST /api/series_oldest` und `POST /api/series_oldest/reset`.
- Einstellungen erweitert um `ui_analysis_max_age_years` und `ui_raw_target_chunk_ms`.
- Analyse-History zeigt den erweiterten Analysezustand inkl. Gesamtzeitraum, letztem Chunk und Typ-Details.

### Maintenance

- Tests: vom Benutzer explizit uebersprungen
- Tested with Home Assistant Core: unknown

## 1.12.236

### Enhancement

- `raw.table` und `raw.outlier_table` verwenden jetzt dieselbe Monospace-Schriftdarstellung.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.235

### Fix

- Analyse: Fehler `entry.rows.forEach is not a function` behoben. Chunk-Logs verwenden jetzt `byType`, `totalFound` und `totalScanned` statt ein Zeilen-Array zu erwarten.
- `analysis_found_info` zeigt jetzt zusaetzlich den Suchfilter mit gruenem Haken fuer aktive und rotem Kreuz fuer inaktive Typen.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Playwright: `tests/e2e/dashboard-analysis.spec.js` 4/4 bestanden
- Tested with Home Assistant Core: unknown

## 1.12.234

### Enhancement

- Analyse-Section vervollstaendigt: Gesamtzeitraum und aktueller Chunk-Zeitraum werden angezeigt.
- Fortschrittsanzeige nutzt konsistent den Analysezustand (Chunks/Fortschritt/Fundzahlen).
- Ausreisser-Typ-Auswahl als Zwei-Listen-UI (abgewaehlt/gewaehlt) mit Speicherung im Browser.
- Resize-Bar unter `raw.outlier_table` ist jetzt funktional.
- Neue Setting-Grundlage fuer adaptive Chunk-Zielzeit vorbereitet (`ui_raw_target_chunk_ms`).
- Einstellungen speichern jetzt automatisch bei Aenderungen auf der Einstellungsseite.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Playwright: `tests/e2e/dashboard-analysis.spec.js` 4/4 bestanden
- Tested with Home Assistant Core: unknown

## 1.12.233

### Enhancement

- Analyse-Verlauf zeigt jetzt die kompletten Analyse-Ereignisse und den gespeicherten Analysezustand an.
- Analyse-Section merkt sich ihren Open/Closed-Zustand ueber Seitenwechsel hinweg.
- Analyse-Section initialisiert Typ-Listen und Analyse-UI nach dem Laden des gespeicherten Zustands.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.230

### Enhancement

- Neue "Analyse" Section unterhalb von Quellauswahl mit detailliertem Fortschritt.
- Zeigt: Quellparameter, Fortschrittsbalken (0-100%), Checkliste der Analyseetappen, aktueller Chunk mit Zeitbereich/Dauer, Intervall-Info mit Timeout-Warnung, gefundene Ausreisser nach Typ.
- Section "Raw Daten" wird jetzt VOR "Grafische Analyse" angezeigt.
- Console-Fehler werden automatisch ins Server-Log geschrieben (alle Seiten).
- Statistik-Seite: Erkennt abgelaufene Jobs und faellt auf Cache zurueck.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.229

### Enhancement

- Console-Fehler werden jetzt automatisch ins Server-Log geschrieben (alle Seiten).
- Erfasst: JavaScript-Fehler, unhandled promise rejections, 404-Fehler.
- Log-Eintrag enthaelt: Fehlertyp, Nachricht, Dateiname, Zeilennummer, Stack-Trace, URL, Zeitstempel.
- Statistik-Seite: Erkennt abgelaufene Jobs (expired: true) und faellt automatisch auf Cache zurueck.
- Backend loggt Warning wenn global_stats_job nicht gefunden wird.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.228

### Fix

- Analyse-Button: `runRawOutlierSearchWithProgress` nutzte `TABLE_TIME.graph_start_ms` (null bei Zeitraum "Alle") statt `_rawWindowIso()`.
- Verwendet jetzt `Date.parse(win.start)` und `Date.parse(win.stop)` aus `_rawWindowIso()`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.227

### Fix

- Analyse-Button: Safety-Reset fuer `RAW_OUTLIER_SEARCHING` Flag falls von vorherigem Aufruf blockiert.
- Erweitertes Debug-Logging: cache_check, cache_hit, cache_miss, search_init, blocked.
- Console.log fuer jeden Schritt zur lokalen Diagnose.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.226

### Fix

- Analyse-Debug-Logging: `_logAnalysis()` sendet jetzt korrektes Format an `/api/client_error` (message + extra Felder).
- Console.log Ausgabe fuer jeden Analyse-Schritt zur lokalen Diagnose.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.225

### Enhancement

- Analyse-Debug-Logging: Jeder Schritt der Analyse wird ins Server-Log geschrieben.
- Log-Eintraege: start, validate, window, types, search_start, fetch_start, fetch_response, fetch_json, fetch_error, search_done, search_error.
- Ermöglicht Diagnose warum Analyse-Button auf Live-System nichts tut.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.224

### Enhancement

- Analyse-Button: Neue Statuszeile zeigt aktuelle Parameter (Measurement, Field, Entity, Zeitraum).
- Measurement/Field Anzahl zeigt jetzt tatsächliche Datalist-Optionen statt API-Gesamtzahl.
- Zeitspanne wird nach Seitenwechsel korrekt wiederhergestellt.
- Statuszeile aktualisiert sich bei jeder Filter-Änderung.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Playwright: 4/4 Tests bestanden
- Tested with Home Assistant Core: unknown

## 1.12.223

### Enhancement

- Analyse: Fetch-Timeout auf 120s gesetzt um HA Ingress-Abbrueche zu vermeiden.
- Chunk-Log zeigt jetzt Abbruch-Dauer an (z.B. "Abgebrochen nach 58.3s").
- Timeout-Chunks werden mit orangem Warn-Icon (⏱) angezeigt statt rotem Fehler-Icon.
- Backend loggt Chunk-Dauer fuer jeden einzelnen Scan-Schritt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.222

### Enhancement

- Analyse: Adaptive Chunk-Groesse startet bei 1 Tag und passt sich dynamisch an.
- Bei schneller Antwort (< 15s) wird Chunk-Groesse verdoppelt (max 14 Tage).
- Bei langsamer Antwort (> 30s) wird Chunk-Groesse halbiert (min 1 Tag).
- Bei Timeout (> 60s) wird Chunk-Groesse halbiert und Chunk wiederholt.
- Backend Timeout fuer outlier_search auf 60s erhoehen.
- Chunk-Messung: Laufzeit, Anzahl Messwerte, Zeitbereich und Chunk-Groesse werden protokolliert.
- Neues Analyse-Log unter der Checklist zeigt jeden Chunk mit Details an.
- Neuer Analyse-Verlauf Button (neben Analyse) zeigt History aller Analysen mit ausfuehrlichem Protokoll.
- Analyse-Eintraege werden in localStorage gespeichert (max 50 Eintraege).

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.221

### Enhancement

- Analyse-Checklist: Fortschrittsbalken zeigt 0-100% waehrend der Chunk-Suche.
- Analyse-Checklist: Typen-Aufschluesselung unter Ausreisser-Suche (z.B. "→ Counter: 44").
- Jeder Schritt zeigt Laufzeit an.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.220

### Enhancement

- Analyse-Button: Neue Checkliste zeigt jeden Schritt mit Status und Laufzeit an.
- Gruene Haken (✓) fuer erfolgreiche Schritte, rote Kreuze (✗) fuer Fehler.
- Angezeigte Schritte: Eingaben pruefen, Zeitraum, Ausreisser-Typen, Ausreisser-Suche (mit Anzahl und Dauer), Ausreisser-Tabelle fuellen.
- Nur Counter-Ausreisser als Default, andere Typen koennen im Dropdown aktiviert werden.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.219

### Enhancement

- Analyse-Button fuehrt NUR noch Ausreisser-Suche aus, ohne Graph oder Raw-Tabelle zu veraendern.
- Graph und Raw-Tabelle bleiben waehrend der Analyse unveraendert.
- Ausreisser-Tabelle wird mit Suchergebnissen gefuellt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.218

### Enhancement

- Ausreisser-Typ-Auswahl: Default ist jetzt nur "Counter Ausreisser" (statt alle Typen). Andere Typen koennen im Dropdown aktiviert werden.
- Ausreisser-Typ-Auswahl wird im Browser-Speicher gespeichert.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Playwright: 4/4 Tests bestanden
- Tested with Home Assistant Core: unknown

## 1.12.217

### Fix

- Statistik: `NameError: min_chunk_seconds is not defined` behoben. Variable war in `_series_stats()` definiert, wurde aber in `_series_first_span_split()` und `_series_last_span_split()` verwendet die in anderen Scopes liegen. Auf `_global_stats_job_thread`-Ebene verschoben.

### Enhancement

- Analyse-Button nutzt jetzt die Ausreisser-Typ-Auswahl aus dem Dropdown-Filter statt immer alle Typen zu suchen.
- Ausreisser-Typ-Auswahl wird jetzt im Browser-Speicher gespeichert und beim Laden wiederhergestellt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.215

### Fix

- Dashboard: Doppelte Deklaration von `RAW_CENTER_RANGE` (Zeile 1146 und 4428) verursachte JavaScript-Fehler der das gesamte Dashboard-Skript blockierte. Dadurch waren alle Auswahlfelder (Measurement, Field, Entity, Friendly-Name) nicht funktionsfaehig.
- Playwright-Tests: 2 neue Tests hinzugefuegt - Field-Auswahl nach Measurement und Friendly-Name-Filterung nach Entity-ID.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Playwright: 4/4 Tests bestanden
- Tested with Home Assistant Core: unknown

## 1.12.214

### Fix

- Feld-Auswahl auf Dashboard blieb leer weil `loadMeasurements()` und `loadDashboardFields()` im `silent`-Modus Input-Werte loeschten.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.212

### Enhancement

- Ausreisser-Suche verwendet jetzt immer den bei Quellauswahl eingestellten Zeitraum (nicht mehr Graph-Zeitraum).
- Checkbox "Zeit gefuehrt durch Graph" entfernt.
- Raw-Tabelle wird NUR noch geladen wenn ein Ausreisser in der Uebersichtstabelle selektiert wird.
- Raw-Daten werden mit Anzahl Zeilen (nicht Minuten) um den Ausreisser geladen.
- Wenn im Start-Fenster nicht genug Zeilen gefunden werden, wird das Suchfenster schrittweise erweitert bis Anfang/Ende des Zeitbereichs erreicht ist.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.211

### Enhancement

- Ausreisser-Uebersichtstabelle zeigt jetzt Anzahl pro Ausreissertyp an (z.B. "5 Ausreisser | Counter: 3 | Grenzen: 2").

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.210

### Enhancement

- Serverseitige Analyse-Logs fuer `/api/outliers` erweitert.
- Loggt jetzt: Validierung, Zeitfenster, Spanne, Chunk-Logik, Split-Entscheidungen, Overflow, Ergebnis-Zusammenfassung.
- DEBUG-Level: Jeder Chunk-Eintritt, Chunk-Splitting.
- WARNING-Level: Rejections, Overflow bei kleinstem Chunk.
- INFO-Level: Start, Spanne, Scan-Loop, `_scan_span` ENTER/DONE, `_scan_span_split` PROCESSING/SPLITTING/OVERFLOW, Ergebnis mit scanned/found/dur.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.209

### Enhancement

- Serverseitige Analyse-Logs fuer `/api/outlier_search` erweitert.
- Loggt jetzt: Validierung, Zeitfenster, Spanne, Chunk-Logik, Split-Entscheidungen, Overflow, Ergebnis-Zusammenfassung.
- DEBUG-Level: Jeder Chunk-Eintritt, gefundene Ausreisser, Chunk-Splitting.
- WARNING-Level: Rejections, Overflow bei kleinstem Chunk.
- INFO-Level: Start, Spanne, Scan-Loop, Ergebnis mit scanned/found/dur/limit/truncated.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.208

### Enhancement

- Detaillierte Console-Logs fuer Analyse und Ausreisser-Suche hinzugefuegt.
- Logs zeigen: RAW_OUTLIER_SEARCHING flag, Zeitfenster, Cache-Status, Chunk-Verarbeitung, API-Antworten, Abbruch-Signale.
- Hilft bei der Diagnose warum nicht alle Chunks durchlaufen werden.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.207

### Enhancement

- Raw-Tabelle wird NUR noch geladen wenn ein Ausreisser in der Ausreisser-Tabelle selektiert wird.
- Alle automatischen Raw-Tabelle Ladevorgänge entfernt:
  - Cache-Wiederherstellung (lokal und Server)
  - Graph-Zoom/Range-Änderung (plotly_relayout)
  - Graph-Doppelklick (reset zoom)
  - Auto-Tuning Dashboard
  - "Alle" Button in Raw
  - Raw-Zeitbereich-Checkbox Wechsel
  - Raw-Section auf/zuklappen
  - Raw-Zeitraum-Einstellung Wechsel
- Manuelles Laden über Raw-Refresh-Button bleibt erhalten.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.206

### Fix

- Auswahl-Felder auf Dashboard waren leer weil `loadMeasurements()` im Init-Flow fehlte. Measurement-Dropdown hatte keine Optionen, wodurch auch Fields und entity_id/friendly_name nicht geladen wurden.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.205

### Enhancement

- Analyse-Logik ueberarbeitet: Nur Analyse liest alle Daten und fuehrt Stoerstellenanalyse durch.
- Nach Analyse: Graph und Tabellen werden einmalig gefuellt, keine weiteren automatischen Updates.
- Raw-Tabelle bleibt nach Analyse leer (5 leere Zeilen).
- Raw-Tabelle wird NUR geladen wenn ein Ausreisser in der Ausreisser-Tabelle selektiert wird.
- `scheduleRawReload(true)` aus `loadData()` entfernt um automatische Raw-Updates zu verhindern.
- Zoom-Nachladen wird nach Analyse fuer 5 Sekunden blockiert.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.204

### Fix

- "Maximum call stack size exceeded" beim Analyse-Button behoben. Nach `loadData()` wurde `_tryLoadZoomData()` durch das asynchrone `plotly_relayout` Event erneut aufgerufen. Neuer Guard `_ZOOM_BLOCK_UNTIL` blockiert Zoom-Nachladen fuer 2 Sekunden nach Analyse.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.203

### Enhancement

- Error- und Warning-Zeilen in Log-Ansicht werden farblich hervorgehoben (konfigurierbar in Einstellungen).
- ERROR-Zeilen (` ERROR `, `EXCEPTION`, `TRACEBACK`, `TypeError`, `Cannot set properties`): Hintergrund- und Textfarbe einstellbar.
- WARNING-Zeilen (` WARNING `): Eigene Hintergrund- und Textfarbe einstellbar.
- Vier neue Einstellungsfelder: `ui_log_error_bg`, `ui_log_error_fg`, `ui_log_warn_bg`, `ui_log_warn_fg`.

### Fix

- `graph.reset_time` Button: "Maximum call stack size exceeded" behoben. `_SUPPRESS_RELAYOUT` Flag verhindert Rekursionsschleife im `plotly_relayout` Handler waehrend `loadData()`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.202

### Fix

- Kritischer Merge-Fehler aus Version 1.12.198 behoben: `renderRawTable()` hatte duplizierten Code ausserhalb der Funktion, der die gesamte JavaScript-Ausfuehrung blockierte.
- Alle Buttons (dashboard.load, dashboard.query_details, dashboard.query_test) und Auswahlfelder funktionieren wieder.
- Optional Chaining (`?.`) fuer DOM-Element-Referenzen verhindert Absturz bei fehlenden Elementen.
- Drag/Drop-Funktionalitaet in Raw-Tabelle korrekt integriert.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.201

### Fix

- Dashboard Buttons (dashboard.load, dashboard.query_details, dashboard.query_test) und Auswahlfelder reagieren wieder.
- Optional Chaining (`?.`) fuer alle DOM-Element-Referenzen ($mf, $n, $e, $r, $start, $stop) verhindert JavaScript-Absturz bei fehlenden Elementen.
- Verbessertes Error-Logging in Event-Handlern statt stummem `.catch(()=>{})`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.200

### Enhancement

- Issue #167: Alle Info-Buttons auf allen Seiten (Dashboard, Einstellungen, Logs, Backup, Restore, Combine, Export, Import, Qualität, Monitor, History) haben jetzt einheitliches SVG-Icon statt Text "i".
- Issue #168: Return-Button auf Einstellungsseite hat neues SVG-Icon (ionicons back arrow).
- Issue #168: Settings-Button (`.ib_cfg_icon`) auf Einstellungsseite entfernt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.199

### Enhancement

- Issue #166: Summary-Zeilen in Einstellungen bekommen konfigurierbare Hintergrundfarbe via CSS-Variable `--ib-section-title-bg`.
- Issue #166: "Standardmaessig geoeffnete Bereiche" entfernt (default alle zugeklappt).

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.198

### Enhancement

- Issue #165: Dashboard Button "Aktualisieren" in "Analyse" umbenannt.
- Issue #165: "Analyse"-Button fuehrt chunkweise Ausreisser-Suche im gewaehlten Zeitraum durch.
- Issue #165: Nach Analyse: Graph zeigt kompletten Zeitraum, Ausreisertabelle wird gefuellt, Raw-Tabelle wird geloescht (leere Zeilen).
- Issue #165: Klick auf Ausreisser-Zeile laedt Raw-Daten mit Kontextzeilen (`raw_outlier_context_rows`).
- Issue #165: Zeilenanzahl wird ueber jeder Tabelle angezeigt.
- Issue #165: Leere Tabellen zeigen mindestens 3 leere Zeilen.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.197

### Fix

- "Maximum call stack size exceeded" nach Laden erneut behoben. `_tryLoadZoomData` prueft jetzt ob der gleiche Zeitbereich bereits geladen wurde (`_LAST_ZOOM_RANGE`), bevor ein neuer API-Aufruf erfolgt. Verhindert dass das asynchrone `plotly_relayout` Event nach `_mergeAndDraw()` dieselbe Abfrage erneut ausloest.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.196

### Enhancement

- Issue #155: Settings-Button und Info-Button sind jetzt in einer Gruppe rechtsbuendig im Section-Titel angeordnet.
- Issue #155: Info-Button hat jetzt ein SVG-Icon statt Text "i".
- Neue CSS-Klasse `.ib_btn_group` fuer die Button-Gruppierung in `.ib_summary_row`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.195

### Fix

- "Maximum call stack size exceeded" bei dashboard.load und graph.refresh behoben. `_ZOOM_LOADING` Flag wurde in `.finally()` zu frueh zurueckgesetzt (vor dem asynchronen `plotly_relayout` Event), was eine Endlosrekursion ausloeste. Flag wird jetzt erst NACH `_mergeAndDraw()` zurueckgesetzt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.194

### Fix

- Settings-Button (Zahnrad-Icon) in Sections war nicht sichtbar weil das JavaScript zu frueh ausgefuehrt wurde (vor dem Laden der Section-Elemente). Jetzt in `DOMContentLoaded` eingepackt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.193

### Enhancement

- Einstellungen: Untergeordnete Bereiche (Sub-Sektionen) jetzt als integrierte Liste innerhalb der Hauptbereiche dargestellt.
- Sub-Sektionen haben keine eigene Rahmen mehr, sondern sind durch Trennlinien und hellen Hintergrund visuell eingebettet.
- Tiefer verschachtelte Bereiche (Sub-Sub-Sektionen) werden eingerueckt dargestellt.
- CSS: Neue Styles fuer `details.card > .card_body > details.card` und tiefere Verschachtelungen.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.192

### Enhancement

- Umfassendes Logging fuer alle API-Endpunkte und UI-Aktionen hinzugefuegt.
- `/api/outlier_search`: Entry-Log (measurement, field, search_types, start, stop), Ergebnis-Log (scanned, found, duration), Error-Log mit Stacktrace.
- `/api/window_points`: Entry-Log (measurement, mode), Ergebnis-Log (rows, duration), Error-Log.
- `/api/raw_points`: Entry-Log (measurement, field, mode), Error-Log.
- `/api/query`: Entry-Log (measurement, field, range), Ergebnis-Log (rows, duration), Error-Log.
- `/api/test`: Ergebnis-Log (OK/Fehler, version), Error-Log.
- `/api/config` POST: Log aller geaenderten Felder (changed_keys), Ergebnis-Log.
- Neuer Endpunkt `/api/page_view`: Loggt Seitenaufrufe mit Seitenname und IP.
- Client-seitig: Automatischer Page-View beim Laden jeder Seite.
- Client-seitig: Globaler Action-Reporter fuer Button-Klicks, Select-Aenderungen, Checkbox-Aenderungen.
- `ui_event` Log-Level von DEBUG auf INFO erhoehen fuer bessere Sichtbarkeit.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.191

### Fix

- Graph Reset Button: "Maximum call stack size exceeded" behoben. `_tryLoadZoomData` hatte keine Re-Entry-Sperre, wodurch `plotly_relayout` nach `_mergeAndDraw` eine Endlosschleife ausloeste.
- Guard-Flag `_ZOOM_LOADING` verhindert rekursive Aufrufe.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.190

### Enhancement

- Raw-Tabelle wird jetzt NUR noch bei Ausreisser-Navigation befuellt (Suche abgeschlossen, Naechster/Vorheriger Button, Klick auf Ausreisser-Zeile).
- Raw-Tabelle wird NICHT mehr bei Entity-Wechsel, Graph-Zoom oder Graph-Klick befuellt.
- Graph-Klick markiert jetzt nur noch den entsprechenden Ausreisser in der Uebersichtstabelle (falls vorhanden), ohne Raw-Daten zu laden.
- Ausreisser-Ergebnisse bleiben beim Wechsel des Graph-Zeitraums erhalten.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.189

### Enhancement

- Alle Funktionsseiten: Settings-Button (Zahnrad-Icon) jetzt automatisch in jedem aufklappbaren Bereich links neben dem Info-Button.
- Wird zentral ueber `_topbar.html` fuer alle Seiten eingefuegt (Dashboard, Statistik, Logs, Backup, Restore, Combine, Export, Import, Quality, Monitor, History, Jobs, etc.).
- Klick auf den Settings-Button springt direkt zu den Einstellungen (`./config`).
- Einstellungsseite selbst ist ausgenommen (hat bereits Zurueck-Buttons).

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.188

### Enhancement

- Raw-Tabelle: Ausreisser-Uebersichtstabelle jetzt immer sichtbar (auch ohne Suchergebnis), zeigt leeren Zustand mit Hinweistext.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.187

### Fix

- Raw-Tabelle: `jumpToOldestOutlier` und `jumpToNewestOutlier` waren nicht als `async` deklariert, wodurch `.catch()` einen Fehler ausloeste ("undefined is not an object").
- Event-Listener rufen jetzt korrekt `.catch(()=>{})` auf.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.186

### Enhancement

- Graph: Neuer Reset-Button in der Graph-Toolbar setzt den Graph auf den gesamten verfuegbaren Zeitraum (aeltester bis neuester Messwert).
- Graph: Downsampling verwendet jetzt `fn: max` statt `fn: last` um Ausreisser-Spitzen sicher sichtbar zu halten.
- Graph: Beim Reinzoomen werden automatisch zusaetzliche Datenpunkte fuer den sichtbaren Bereich nachgeladen, bis die Ziel-Punktdichte erreicht ist.
- Graph: Neue Daten werden mit bestehenden zusammengeführt (Deduplizierung nach Zeitstempel).

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.185

### Enhancement

- Einstellungen: Komplett neues iOS-Style Layout mit Parameter-Zeilen (Label links, Eingabefeld rechts) statt bisheriger Karten-Ansicht (Label ueber Eingabefeld).
- Einstellungen: Untergeordnete Bereiche als aufklappbare Sub-Sektionen innerhalb der Hauptbereiche.
- Einstellungen: Neue CSS-Klassen `.param_row`, `.param_label`, `.param_control`, `.section_note`, `.sub_section` fuer das neue Layout.
- Einstellungen: Farb-Picker und Checkboxen in das neue Zeilen-Layout integriert.
- Einstellungen: Speichern-Button als eigene `save_card` Sektion am Ende.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.184

### Enhancement

- Alle Funktionsseiten: Neuer Settings-Button (Zahnrad-Icon) in der Titelzeile, springt direkt zu den Einstellungen.
- Einstellungsseite: Jeder Bereich hat jetzt einen Zurueck-Button (Pfeil-Icon) links neben dem Info-Icon, springt zurueck zum Dashboard.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.183

### Fix

- `$rawSearchNext is not defined` Fehler beim Druecken von "Aktualisieren" behoben. Referenz durch `$rawJumpOldest`/`$rawJumpNewest` ersetzt.
- Logs: Button-Texte von "Alt"/"Ende" auf "ältester"/"neuester" geaendert.
- Bugreport-Button schliesst jetzt den modalen Dialog nach dem Oeffnen des Issue-Composers.

### Enhancement

- Raw-Tabelle: Ausreisser-Typ-Auswahl jetzt als Dropdown mit Checkboxen (Standard: alle selektiert).
- Raw-Tabelle: Uebersichtstabelle immer sichtbar (default 5 Zeilen).
- Raw-Tabelle: Detail-Tabelle immer sichtbar (default 5 Zeilen).
- Raw-Tabelle: `raw_center_range` Input vom Dashboard entfernt (nur noch in Einstellungen).
- Raw-Tabelle: Neuer Parameter-Dialog fuer Ausreisser-Einstellungen (Max Sprung, Min/Max, Recovery-Streak), geoeffnet per Settings-Button.
- Raw-Tabelle: Suchergebnisse werden in sessionStorage gecached; erneute Suche nutzt Cache.
- Graph: Downsampling verwendet jetzt `fn: last` statt `fn: mean` um Ausreisser-Spitzen sichtbar zu halten.
- Backend: Neues Setting `ui_raw_outlier_context_rows` (default 10).

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.182

### Enhancement

- Raw-Tabelle: Neuer Button "Alle" neben "Aktualisieren" setzt den Graph-Zeitraum auf alle verfuegbaren Messwerte.
- Raw-Tabelle: Neues Eingabefeld "Zeilen vor/nach Ausreisser" (default 10, konfigurierbar 1-500) steuert die Anzahl Kontextzeilen beim Sprung zu einem Ausreisser.
- Raw-Tabelle: Ausreisser-Suche prueft jetzt immer alle Typen auf einmal; die Typ-Auswahl dient nur noch als Filter fuer die Anzeige.
- Raw-Tabelle: Neue Uebersichtstabelle zeigt alle gefundenen Ausreisser; Klick auf eine Zeile springt zum Ausreisser in der Raw-Tabelle.
- Raw-Tabelle: "Suchen" startet die Suche ohne Typ-Auswahl-Pflicht; nach Abschluss wird automatisch der aelteste Ausreisser zentriert angezeigt.
- Raw-Tabelle: Buttons "ältester" und "neuster" Ausreisser (Icons wie Logs jump_oldest/jump_newest) ersetzen die bisherigen Prev/Next-Buttons.
- Raw-Tabelle: Filteraenderung in der Typ-Auswahl aktualisiert sofort die Uebersichtstabelle.
- Backend: Neues Setting `ui_raw_outlier_context_rows` (default 10).

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.181

### Enhancement

- Raw-Tabelle: Beim Sprung zu einem Ausreisser werden jetzt automatisch Datenpunkte davor und danach geladen. Nutzt den bestehenden Centered-Load-Mechanismus: Startet mit `Bereich +- (Minuten)` und erweitert das Zeitfenster schrittweise bis die eingestellte Mindestanzahl von Datenpunkten pro Seite erreicht ist oder Anfang/Ende des Zeitbereichs.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.180

### Fix

- Raw-Tabelle: Mindestanzahl sichtbarer Zeilen von 3 auf 5 erhöht, damit die Tabelle immer mindestens 5 Zeilen anzeigt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.179

### Fix

- Raw-Tabelle: Verbliebene Referenz auf `$rawSearchStatus` (nicht mehr deklariert) in Zeile 5156 verursachte JavaScript-Fehler, der das gesamte Dashboard-Skript stoppte. Raw-Tabelle blieb dadurch leer. Ersetzt durch `$rawOutlierStatusTxt`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.178

### Enhancement

- Raw-Tabelle: Ausreisser-Suche erfolgt jetzt chunk-basiert (1-14 Tage je nach Zeitspanne) wie bei der Bearbeitungsliste, um Abfrage-Timeouts zu verhindern.
- Raw-Tabelle: Neuer Button "Suchen" startet die chunk-basierte Suche ueber den gesamten Zeitraum.
- Raw-Tabelle: "Suche ab Beginn" umbenannt in "Anzeige ab Beginn" – laedt gefundene Ausreisser in die Tabelle, markiert sie und zentriert die Ansicht.
- Raw-Tabelle: "Weitersuchen" umbenannt in "Naechster" – springt zum naechsten Ausreisser mit Wrap-around zum Anfang.
- Raw-Tabelle: Neuer Button "Zurueck" vor "Naechster" – springt zum vorherigen Ausreisser mit Wrap-around zum Ende.
- Raw-Tabelle: Statusanzeige zeigt jetzt Chunk-Fortschritt, gepruefte Punkte, gefundene Ausreisser und elapsed time (wie Bearbeitungsliste).
- Raw-Tabelle: Neuer Abbruch-Button waehrend der Suche.
- Raw-Tabelle: Optionale Eingabefelder fuer Grenzen (Min/Max) und Max Sprung bei entsprechenden Ausreisser-Typen.
- Backend: `/api/outlier_search` unterstuetzt jetzt State-Parameter (`prev_value`, `counter_base_value`, `scan_state`) fuer chunk-uebergreifende Kontinuitaet.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.177

### Fix

- Raw-Tabelle: Ausreisser-Suche (`/api/outlier_search`) verwendete nicht existierende JavaScript-Variablen (`$measurement`, `$field`, `$entityId`, `$friendlyName`). Verwendet jetzt die korrekten Dashboard-Selektorvariablen (`$mf`, `$f`, `$e`, `$n`).

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.176

### Enhancement

- Raw-Tabelle: Sticky Header – die Titelzeile bleibt beim Scrollen fixiert.
- Raw-Tabelle: Neue Ausreisser-Suchleiste mit Multi-Select fuer Ausreisser-Typen (Counter, Grenzen, Stoerphasensuche, NULL, 0-Werte) sowie Buttons "Alle" und "Keiner".
- Raw-Tabelle: "Suche ab Beginn" ruft alle Ausreisser im aktuellen Zeitfenster vom Backend ab (einmalig) und springt zum ersten Treffer.
- Raw-Tabelle: "Weitersuchen" springt lokal zum naechsten Ausreisser, markiert ihn in der Tabelle und im Graph.
- Raw-Tabelle: Neue Spalte "Ausreisser" zeigt den Grund fuer gefundene Ausreisser an.
- Raw-Tabelle: Ausreisser-Zeilen werden rot hervorgehoben.
- Backend: Neuer Endpunkt `/api/outlier_search` mit konfigurierbarem Limit (Einstellung: `ui_raw_outlier_search_limit`).

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.175

### Fix

- Query-Test-Dialog: Schliessen stellt jetzt den urspruenglichen Dialog-Zustand korrekt wieder her. Vorher blieben `pre`, `meta` und `controls` ausgeblendet, sodass nachfolgende Dialoge (Query-Details, Statistik) leer angezeigt wurden.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.174

### Fix

- Query-Test-Dialog: Resultat wird jetzt tabellarisch statt als JSON dargestellt.
- Query-Test-Dialog: Button "Ausfuehren" hat kein Icon mehr.
- Query-Test-Dialog: Button "Loeschen" leert nur das Eingabefeld. Neuer Button "Last" stellt die letzte Query vor dem Loeschen wieder her.
- Query-Test-Buttons verwenden jetzt das Listen-Icon statt des Lupen-Icons.
- Dialog-Trennung: Query-Details-Buttons (`dashboard_query_open`, `graph_query_open`, `raw_query_open`) oeffnen weiterhin den bestehenden Query-Details-Dialog mit History. Query-Test-Buttons oeffnen den separaten Query-Test-Dialog. `section.stats_total` oeffnet weiterhin den Statistik-Dialog.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.173

### Enhancement

- Query-Test-Dialog: Neuer modaler Dialog zum Ausfuehren beliebiger Flux (v2) oder InfluxQL (v1) Queries direkt aus der UI.
- Sicherheitspruefung: Mutierende Statements (DELETE, DROP, SELECT INTO, to(), delete) werden erkannt und blockiert.
- Abbruch-Button: Laufende Queries koennen waehrend der Ausfuehrung abgebrochen werden (AbortController).
- Einstiegspunkte: Query-Test-Button im Dashboard (neben Query-Icon), Graph-Bereich, Raw-Bereich und Diagnose-Seite.
- Backend: Neuer Endpunkt `/api/query_test` mit Query-Spracherkennung, Mutations-Check und Laufzeitmessung.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.170

### Fix

- Popup Query-History: Die Hoehenberechnung beim Ziehen von `influxbro_popup_split` verwendet jetzt eine echte Resthoehen-Berechnung fuer den unteren Bereich. Dadurch kann `influxbro_popup_history` beim Hochziehen des Trenners nicht mehr groesser als der Dialog werden.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`, `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.169

### Fix

- Query-History: Die Steuerelemente oberhalb des unteren History-Felds verwenden jetzt ein kompaktes Links-Layout ohne streckendes `space-between`. Dadurch bleiben `Umbruch` und `Client time` als gleich grosse Checkboxen sichtbar.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`, `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.168

### Fix

- Query-History: Die Checkbox `Client time` verwendet jetzt dieselbe kompakte Checkbox-Darstellung wie `Umbruch` direkt daneben.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`, `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.167

### Fix

- Query-Dialoge blenden die untere Query-History jetzt immer sichtbar ein, inklusive horizontalem Trenner. Der gemeinsame Popup-Pfad erzwingt die Anzeige fuer Query-Dialoge auch dann, wenn ein Browser noch einen aelteren Dialogzustand gespeichert hatte.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`, Browser-Pruefung gegen lokal und Live-System
- Tested with Home Assistant Core: unknown

## 1.12.166

### Fix

- Live-Fix fuer Query-Dialoge: `_latestHistoryEntry` wurde in den gemeinsamen Popup-Scope verschoben. Dadurch funktionieren die neuen Ausloeser-/Zeit-Metadaten im Live-System wieder ohne JavaScript-Fehler beim Oeffnen des Query-Dialogs.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`, Live-Pruefung gegen ausgeliefertes Frontend
- Tested with Home Assistant Core: unknown

## 1.12.165

### Fix

- Query-History protokolliert jetzt zusaetzliche Metadaten zum Ausloeser jeder Abfrage: Funktionsseite, ausloesender Button oder Programm sowie Ausloesezeitpunkt.
- Query-Dialoge zeigen die History jetzt immer automatisch im unteren Bereich an. Der bisherige `History`-Button im Dialog wurde zu einem Refresh-Button mit neuem Icon fuer die aktuelle Query-History umgebaut.
- Die untere Query-History besitzt jetzt eine Checkbox `Client time` fuer lokale Zeitdarstellung vs. Roh-ISO-Zeit sowie eine eigene konfigurierbare Schriftgroesse `ui_popup_history_font_px`.
- Dashboard Raw: Neuer Button `Query` im Bereich `raw.actions`, um die zuletzt verwendete Raw-Abfragequery im gemeinsamen Query-Dialog anzuzeigen.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`, `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.164

### Fix

- Popup Query-History: Der untere Bereich stellt History-Eintraege nicht mehr als klickbare Buttons dar, sondern als reine Textansicht im Stil der Log-Anzeige.
- Popup Query-History: Ueber dem unteren Textfeld gibt es jetzt ein Volltextsuchfeld sowie eine eigene Checkbox `Umbruch`, damit Suche und Zeilenumbruch fuer die History getrennt vom oberen Query-Feld steuerbar sind.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`, `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.163

### Fix

- Popup Query-History: Die History-Helfer und der gemeinsame History-Zustand wurden aus lokalen `_ensureUi()`-Scopes in den geteilten Popup-Scope gezogen. Dadurch funktionieren Auto-Open, Toggle und das Rendern des unteren History-Bereichs jetzt auch im echten Browserlauf stabil.
- Verifiziert im lokalen sichtbaren Browserlauf: Query-History wird unterhalb von `influxbro_popup_pre` angezeigt, ein History-Eintrag laedt seine Query oben, und der aktive Eintrag wird markiert.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`, `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.162

### Fix

- Popup Query-History: Der untere Bereich blieb trotz gesetztem `historyScope` leer, weil im Auto-Open-Pfad die Variable `CURRENT_HISTORY_SELECTED_AT` ohne Deklaration verwendet wurde und der Fehler intern geschluckt wurde. Die History wird jetzt wieder korrekt unterhalb von `influxbro_popup_pre` gerendert.
- Popup Query-History: Der aktive Verlaufseintrag wird jetzt sichtbar markiert; optionale Response-Vorschauen werden ebenfalls im unteren Bereich angezeigt.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.161

### Fix

- Query-History verwendet jetzt keinen separaten Text-Popup mehr. Alle History-Buttons oeffnen die Query-History direkt im bestehenden `influxbro_popup_card` unterhalb von `influxbro_popup_pre` mit dem verschiebbaren Trenner.
- Der untere Bereich `influxbro_popup_history` zeigt jetzt die Query-History kompakt mit Query-Vorschau und optionaler Response-Vorschau. Beim Klick auf einen Eintrag wird dessen Query oben geladen und der aktive Verlaufseintrag sichtbar markiert.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.160

### Fix

- Dashboard: `Einheit` zeigt wieder die Anzahl der verfuegbaren `_measurement`-Eintraege; `Aktualisieren` nutzt nur noch die benoetigte Textbreite. Die Sections wurden in `Grafische Analyse` und `Raw Daten Analyse` umbenannt.
- Popup: `influxbro_popup_copy` verwendet das neue Copy-SVG, `influxbro_popup_pre` nutzt standardmaessig 10px und kann jetzt ueber `ui_popup_pre_font_px` konfiguriert werden. Der `Logs (5min)`-Button schaltet den Popup-Inhalt jetzt als Toggle um und bleibt dabei sichtbar aktiv, ohne den Ursprungstitel zu aendern.
- Dashboard Raw: Die Tabelle besitzt jetzt eine kompakte Spalte `Aenderung`, einen `Info`-Button fuer Details und neue Buttons `Loeschen` sowie `Undo`. Raw-Aenderungen ueber `Einfügen` und `Löschen` werden mit Ausloeser-Metadaten in der History protokolliert; `Undo` macht genau die letzte direkte Button-Aenderung fuer den selektierten Raw-Wert rueckgaengig und laedt die Tabelle anschliessend neu.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.159

### Fix

- Alle Felder, die zuvor ueber die alte Laufzeitlogik automatisch einen Clear-Button erhalten haben, besitzen jetzt statische `.ib_clear_btn`-Buttons direkt im HTML. Dadurch ist die Clear-Funktion wieder auf allen betroffenen Seiten vollstaendig sichtbar verfuegbar.
- Die Clear-Buttons verwenden wieder das urspruengliche Papierkorb-SVG statt eines Text-`X`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.158

### Fix

- Die angeforderten Filter- und Suchfelder verwenden jetzt statische, immer sichtbare `.ib_clear_btn`-Buttons statt dynamisch nachgeruesteter Buttons. Das betrifft u. a. Dashboard, Statistik, Restore, Kombinieren, Export, Logs, Jobs & Cache, History, Changelog, Handbuch und Profilverwaltung.
- Export: Der Block `Auswahl (aufgeloest)` wurde entfernt; die Export-Seite zeigt stattdessen nur noch die kompakte Serieninfo. Backup: Die festen Breiten fuer `backup.range`, `backup.entity_id` und `backup.friendly_name` wurden aufgehoben.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.157

### Fix

- Restore: Ein ueberschuessiges `</div>` im Bereich `Ziel (Messwert)` wurde entfernt. Dadurch bleibt die `details`-Struktur der Restore-Seite korrekt verschachtelt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.156

### Fix

- Dashboard: Ein ueberschuessiges `</div>` im Auswahl-Block wurde entfernt. Dadurch beendet der Browser `dashboard.page` nicht mehr implizit vorzeitig, und `section.graph`, `section.raw` sowie `section.filterlist` bleiben im Live-DOM sauber innerhalb von `main.content`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.155

### Maintenance

- Regeln und Handbuch praezisiert: Jede Codeaenderung erzwingt jetzt explizit eine neue Add-on-Version, und das Dashboard-Handbuch dokumentiert die Reihenfolge `Graph` -> `Raw Daten (DB)` -> `Bearbeitungsliste` direkt unter `Auswahl`.
- Tests: nicht ausgefuehrt (nur Regeln/Dokumentation/Metadaten)
- Tested with Home Assistant Core: unknown

## 1.12.154

### Fix

- Dashboard: `section.graph`, `section.raw` und `section.filterlist` sind jetzt direkte Kinder von `dashboard.page`. Die alte Zwischenebene `.main` wurde entfernt, und `section.raw` ist nicht mehr in `section.graph` verschachtelt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_time_and_stats.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.153

### Fix

- Dashboard: Die sichtbare Kopfzeile `Gesamtstatistik (Alles)` und der alte Tipps-Text unterhalb der Statistik wurden entfernt. Die angeforderten Bereiche `tip.selection`, `section.graph`, `section.raw` und `section.filterlist` bleiben innerhalb von `dashboard.page`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_time_and_stats.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.152

### Fix

- Dashboard-/Topbar-Filter: `ib_pagecard_title` wurde entfernt, der Buttonblock unterhalb von `dashboard.filters` ausgegliedert und `superpicker` durch einen direkten `S-Picker`-Button ersetzt.
- Dashboard/History/Editlist/Backup: Such-/Filterfelder wie `reason_filter` und `history.search` sind jetzt sauber fuer den globalen Clear-Button-Pfad markiert; `editlist.right` bleibt unter `edit.left`, `editlist.class_filter` zeigt seinen Text vollstaendig, und die Backup-Aktionszeile ist oben ausgerichtet.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_time_and_stats.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.151

### Enhancement

- Query-Dialoge besitzen jetzt einen eingebetteten History-Bereich unterhalb des Haupt-Query-Textes. Zwischen Query und History gibt es einen horizontalen Hoehen-Splitter zum direkten Anpassen beider Bereiche.
- Das modale Popup-Fenster schliesst sich nicht mehr automatisch bei Aussenklick und kann per Resize-Griff breiter bis an die Browsergrenze gezogen werden.

### Maintenance

- Das GUI-Template dokumentiert jetzt die Regeln fuer `Modales Fenster / Query Fenster`.
- Tests: `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.150

### Fix

- Der globale Popup-/Dialogpfad verwendet jetzt eine gemeinsame Decode-Hilfsfunktion. Dadurch schlagen `Dashboard: dashboard.query_details`, `Dashboard: section.stats_total` und Test-Popups nicht mehr mit `ReferenceError: _decodeEscapedInfoText is not defined` fehl.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.149

### Fix

- Bei aktivem `Dashboard: nav.ui_picker_super` pickt der UI-Picker jetzt das direkt gehoverte Unterelement selbst. Dadurch werden nicht mehr nur naechste `data-ui`-Container, sondern auch darunterliegende Elemente per Fallback-Metadaten sichtbar.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.148

### Fix

- Button-Klicks werden jetzt global als `ui_event` mit `button_press` geloggt. Wenn ein Button-Handler einen Fehler wirft, wird dieser nicht mehr still geschluckt, sondern als Button-Fehler in UI-Fehlerlog und Add-on-Log geschrieben.
- `Dashboard: dashboard.query_details` und `Dashboard: section.stats_total` melden Dialogfehler jetzt explizit und haben einen Popup-Fallback, falls das Dialogsystem nicht verfuegbar ist.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.147

### Fix

- `Dashboard: page.title.card` trennt jetzt statische Mindesthoehe und live gemessene Layout-Hoehe. Dadurch schrumpft die Kartenhoehe nach automatischen Erweiterungen wieder auf die kleinstmoegliche volle Hoehe zurueck.

### Maintenance

- Das GUI-Template dokumentiert jetzt explizit, dass dynamische Titel-/Pagecards ihre Minimalhoehe wiederherstellen muessen und gemessene Runtime-Hoehen nicht in die Basis-Minimalhoehe zurueckgeschrieben werden duerfen.
- Tests: `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.146

### Fix

- `Dashboard: nav.ui_picker_super` verwendet jetzt dieselbe Checkbox-Skalierung wie Standard-Checkboxen im Dashboard, z. B. `Dashboard: graph_markers`.

### Maintenance

- Das GUI-Template dokumentiert die Checkbox-Regel jetzt explizit: Toolbar-/Topbar-Checkboxen sollen die Standardklasse `row_sel` und damit dieselbe Groesse wie die uebrigen GUI-Checkboxen verwenden.
- Tests: `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.145

### Enhancement

- Der UI-Picker hat jetzt optional einen `superpicker`-Modus. Wenn die Checkbox aktiv ist, koennen auch Elemente ohne `data-ui` ueber Fallback-Metadaten wie Tag, ID, Klassen, Rolle oder sichtbaren Text erfasst werden.

### Maintenance

- Tests: `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.144

### Enhancement

- Neue Seite `Datenqualitaet` hinzugefuegt. Sie deckt Bucket-Assistent, Bucket-Verwaltung, Regelpflege, Bereinigungslauf, Rollup-Task-Erzeugung, Query-Beispiele und Debug-Log ab.
- Button-Look global auf eine deutlich Material-orientierte Optik umgestellt: runde Pill-Buttons, weichere Farben, aktive Filled-Variante und einheitliches Verhalten ueber alle Seiten.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.143

### Fix

- Statistik: Ein veralteter Dev-Referenzfehler durch `$influxDbRefresh` wurde entfernt. Dadurch bricht die Statistik-Seite im Browser-Debugmodus nicht mehr an dieser Stelle ab.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.142

### Enhancement

- Statistik: Gleitende Zeitraeume koennen jetzt einen ersten Trim+Append-Schritt nutzen. Wenn sich das Zeitfenster nur nach rechts verschiebt, werden nur die in den linken/rechten Randbereichen betroffenen Serien neu berechnet, waehrend unveraenderte Cache-Serien direkt uebernommen werden.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.141

### Enhancement

- Statistik: Hintergrund-Rebuilds aus einer Cache-Vorabansicht nutzen jetzt die im Cache bekannten Serien als Startmenge und ergaenzen nur noch neue Serien seit Cache-Ende. Dadurch wird der teure Vollscan der Serienliste fuer viele Folgeaufrufe reduziert.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.140

### Enhancement

- Statistik: Wenn fuer gleitende Zeitraeume noch kein echter Delta-Append moeglich ist, zeigt `Statistik laden` jetzt wenigstens sofort eine passende Cache-Vorabansicht und aktualisiert diese parallel im Hintergrundjob weiter.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.139

### Enhancement

- Statistik-Cache kann fuer verankerte Zeitraeume (`all`, `this_year`) jetzt nicht nur frische Treffer direkt verwenden, sondern bei veralteten Caches auch den fehlenden rechten Zeitraum per Append-Update nachladen und mit dem vorhandenen Cache zusammenfuehren.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.138

### Enhancement

- Dashboard: Bearbeitungsliste und Details-Liste nutzen jetzt denselben gemeinsamen Hoehen-Resizer wie die anderen Tabellen. Damit lassen sich die Listen auf der Seite direkt ueber den horizontalen Griff vergroessern.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.137

### Fix

- Dashboard: Nach Raw- oder Bearbeitungs-Aenderungen werden Graph, Raw-Sicht und eine bereits aktive Ausreissersuche jetzt gemeinsam aktualisiert, ohne den aktuellen Ausschnitt zu verlieren.
- Statistik: `stats.info` beendet die Sanduhr nach Abschluss sauber, `stats.table.resize` nutzt den gemeinsamen Hoehen-Resizer, und `Statistik laden` verwendet zuerst einen passenden frischen Cache statt immer sofort einen neuen Hintergrundjob zu starten.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.136

### Fix

- Dashboard: Die aufgeloeste Quellen-Box sowie `section.stats_current` wurden entfernt; damit verschwinden auch die zugehoerigen Buttons, Toggle-Optionen und Hintergrundabfragen.
- Dashboard: Die Bearbeitungsliste erzwingt bei aktiver Ausreissersuche jetzt eine eigene Mindesthoehe aus den Einstellungen (`ui_outlier_visible_rows`), damit gefundene Treffer nicht in einer zu kleinen Liste verschwinden.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_time_and_stats.py::test_dashboard_no_longer_has_resolved_selection_info_box -q`
- Tested with Home Assistant Core: unknown

## 1.12.135

### Fix

- Dashboard: `graph.refresh` laedt die aktuelle Serie jetzt neu aus der Datenbank statt nur den vorhandenen Plot neu zu zeichnen. Der aktuelle Ausschnitt bleibt dabei erhalten.
- Dashboard/Raw: Der nicht mehr benoetigte Query-Bereich wurde entfernt. Stattdessen gibt es oberhalb der Raw-Tabelle einen eigenen Refresh-Button, der die aktuelle Raw-Sicht mit demselben Zeitfenster neu laedt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.134

### Fix

- Query-/Text-Dialoge arbeiten wieder als modale Dialoge. Dadurch reagieren `dashboard.query_details`, Statistik-Dialoge sowie Backup-/FullBackup-Query-Buttons wieder sichtbar und konsistent.
- Query-Logging wurde fuer Selector-, Resolve- und Backup-Abfragen ergaenzt, damit diese Diagnose-Daten bei aktiviertem Detail-/Query-Logging ebenfalls im Logfile erscheinen.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.126

### Enhancement

- Dashboard-Ausreissersuche besitzt jetzt das neue Preset `Stoerphasensuche`. Damit bleiben Stoerungen nach einem starken Sprung oder ungueltigen Zustand als zusammenhaengende Fault-Phase aktiv, bis eine Recovery-Regel wieder greift.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_outliers_fault_phase.py tests/test_api_ui_support.py tests/test_api_raw_points_center.py tests/test_api_yaml_flow.py tests/test_api_monitoring.py tests/test_api_debug_report.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.125

### Fix

- Dashboard: Query-/Statistik-Dialoge reagieren wieder konsistent. `dashboard.query_details`, `section.stats_total`, `section.stats_current`, `graph.refresh` und die Raw-Query-Aktion arbeiten jetzt ueber sichtbare modale Dialoge bzw. einen erweiterten Redraw-Button.
- Raw-Overwrite nutzt jetzt einen InfluxBro-eigenen modalen Bestaetigungsdialog statt des Browser-Dialogs; dabei wurde der JavaScript-Fehler `_countDecimals is not defined` behoben.
- Die Dashboard-Bearbeitungsliste hat keine Action-Spalte mehr; die Aktionen `Ueberschreiben`, `Loeschen`, `Uebernehmen` und `Undo` sitzen jetzt oberhalb der Tabelle.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_raw_points_center.py tests/test_api_yaml_flow.py tests/test_api_monitoring.py tests/test_api_debug_report.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.124

### Enhancement

- Dashboard/Raw laedt zentrierte Rohdaten jetzt symmetrisch um den angeklickten Graph-Punkt und erweitert den Suchbereich bei zu wenigen Datenpunkten je Seite automatisch in 100-Minuten-Schritten.
- Dashboard/Raw ueberschreibt Zielwerte jetzt direkt nach Bestaetigung per `Wert kopieren`/`Einfügen` oder per Drag-and-Drop zwischen zwei Raw-Zeilen; die Quellzeile bleibt dabei sichtbar markiert.

### Fix

- Veraltete Raw-Navigation sowie `raw.copy_query`, `raw.more` und `raw.tune.link` wurden entfernt, damit die Aktionsleiste direkt ueber der Tabelle bleibt und keine inkonsistente Nachladung mehr ausloest.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_raw_points_center.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.123

### Enhancement

- Statistik zeigt in `stats.info` jetzt deutlich mehr Laufzeitinformationen je Phase und markiert laufende Berechnungen mit einer Sanduhr.
- Jobs & Cache: `jobs.table`, `cache.table` und `timers.table` arbeiten jetzt mit Zeilenselektion und Toolbar-Aktionen oberhalb der Tabelle statt mit einer Action-Spalte.

### Fix

- `jobs.table` zeigt jetzt `job_id` als eigene Spalte, blendet `%` aus und zeigt in `message` keinen zusaetzlichen `Modus:`-Text mehr.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_yaml_flow.py tests/test_api_monitoring.py tests/test_api_raw_points_center.py tests/test_api_debug_report.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.122

### Fix

- Dashboard: `filter_field` zeigt jetzt wieder die Anzahl der verfuegbaren Feldoptionen direkt im Label an.
- Seitensuche: Bei Fokus auf `page.search` mit bereits vorhandenem Suchtext wird die Trefferliste erneut eingeblendet. Der Suchdialog besitzt jetzt zusaetzlich `Direkt Text` als Suchquelle; alle Checkboxen sind gleich gross.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_yaml_flow.py tests/test_api_monitoring.py tests/test_api_raw_points_center.py tests/test_api_debug_report.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.121

### Fix

- Der funktionslose Dashboard-Button `Einstellungen pruefen` wurde aus der Aktionsleiste entfernt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`
- Tested with Home Assistant Core: unknown

## 1.12.120

### Enhancement

- `Changelog` und `Handbuch` beruecksichtigen jetzt den festen Topbar-/Title-Card-Abstand korrekt und besitzen jeweils eine eigene Volltextsuche mit Trefferanzahl, aktueller Trefferposition sowie `Vor`/`Zurueck`-Navigation inkl. Wrap-around.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_yaml_flow.py tests/test_api_monitoring.py tests/test_api_raw_points_center.py tests/test_api_debug_report.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.119

### Fix

- Seitensuche: Der Filterdialog aktualisiert seine Vorschau jetzt sofort bei jeder Checkbox-Aenderung auf Basis des aktuellen Suchtexts. Der Dialog schliesst nicht mehr durch Klick auf den Hintergrund, sondern nur noch ueber `Schliessen`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_yaml_flow.py tests/test_api_monitoring.py tests/test_api_raw_points_center.py tests/test_api_debug_report.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.118

### Enhancement

- `page.search` hat jetzt `Zurueck`/`Weiter`-Buttons fuer Treffer-Navigation, ein Einstellungsdialog mit Suchquellen-Filtern (inkl. Tooltiptexte) sowie eine gespeicherte Filterkonfiguration fuer alle Seiten.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_yaml_flow.py tests/test_api_monitoring.py tests/test_api_raw_points_center.py tests/test_api_debug_report.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.117

### Enhancement

- Import: Analyse zeigt jetzt Quellwerte fuer `entity_id` und `friendly_name`, fuellt Ziel-Felder bei eindeutiger Analyse automatisch vor und aktiviert `Transformation testen` / `Import starten` nur noch bei gueltiger Zielkombination.
- Logs: Der Logbereich ist jetzt einklappbar; die Aktionsbuttons zeigen zusaetzlich kurze Textlabels.
- Restore/History: Zentrale Bereiche sind jetzt einklappbar. Summary-Titel erhalten automatisch ein Zahnrad-Icon, das direkt zu den Einstellungen springt.

### Fix

- Timer Jobs: In `timers.table` steht in der Modus-Spalte nur noch der aktuelle Modus als Text; die Umstellung erfolgt ueber den neuen Button `Modus` in der Action-Spalte.
- Tabellen-/Spaltenpersistenz verwendet jetzt stabile seitenbezogene Storage-Keys ohne HA-Ingress-Token, damit Spalteneinstellungen seitenuebergreifend erhalten bleiben.
- Alle Seiten lassen unterhalb der unteren Statusleiste jetzt genug Scrollraum; verdeckte Inhalte am Seitenende sind beseitigt.
- Backup: `backup.space` sitzt direkt unter der Einleitung, und die Action-Zeile des Einzelbackups ist sauberer ausgerichtet.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_yaml_flow.py tests/test_api_monitoring.py tests/test_api_raw_points_center.py tests/test_api_debug_report.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.116

### Enhancement

- `Import: Analysieren` zeigt jetzt nach erfolgreicher Analyse ein Popup mit Datei, gueltigen Zeilen, Zeitraum und Fehlerzaehlern. Bei Fehlern wird zusaetzlich ein Fehler-Popup mit dem Rueckgabetext angezeigt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.115

### Fix

- Dashboard-Auswahlelemente setzen jetzt keine Inline-`width` mehr per JavaScript. Dadurch greift die gewuenschte `max-width: 60%` wieder korrekt auch nach dynamischen Nachladevorgaengen.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_debug_report.py tests/test_api_raw_points_center.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.114

### Enhancement

- Alle Summary-Balken (`ib_summary_row`) laufen jetzt ueber die komplette Summary-Zeile inklusive Auf-/Zuklappsymbol und verwenden ein einheitliches Balken-Layout mit Rand und Radius.
- Die Dashboard-Auswahlelemente nutzen jetzt schmalere Breiten (`max-width: 60%`), angepasste Feldnamen (`Einheit`, `Feld`, `Entity`, `Name`) sowie gleich breite Labels/Hinweiszeilen.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_debug_report.py tests/test_api_raw_points_center.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.113

### Fix

- `page.search` zeigt Treffer jetzt wieder mit einem sichtbaren Rahmen auf allen Seiten an. Farbe, Rahmenbreite und Sichtdauer sind zusaetzlich in den Einstellungen konfigurierbar.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_debug_report.py tests/test_api_raw_points_center.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.112

### Fix

- Die Desktop-Navigation und der Inhaltsbereich beruecksichtigen jetzt die tatsaechliche Hoehe von `page.title.card`. Dadurch ueberlappt die Seitenleiste bei schmaleren Breiten nicht mehr mit der Titelkarte.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_debug_report.py tests/test_api_raw_points_center.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.111

### Fix

- Monitor-Seite: Die globale Seitensuche `page.search` verwendet jetzt dieselbe Breitenlogik wie auf den anderen Seiten und wird nicht mehr durch die Monitor-Formular-CSS auf `100%` gedehnt.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_debug_report.py tests/test_api_raw_points_center.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.110

### Fix

- `raw.paste` kann Zielzeilen jetzt auch direkt aus der Raw-Tabelle in die Bearbeitungsliste uebernehmen. Falls eine Zielzeile trotzdem nicht vorgemerkt werden kann, erscheint eine klare Fehlermeldung statt eines stillen No-Op.

### Enhancement

- Bugreport/Issue-Composer: Die Log-Historie im Debug-Report ist jetzt auf die letzten konfigurierbaren Stunden begrenzt (Default 1h). Zusaetzlich muss der Bediener vor dem Anlegen eine Funktion bzw. einen Menueeintrag auswaehlen.
- Info-Popup: Die Groesse wird jetzt pro Dialogtitel lokal gespeichert und beim erneuten Oeffnen wiederhergestellt. Beim Umschalten des Issue-Typs bleibt der bereits eingegebene Beschreibungstext erhalten.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_debug_report.py tests/test_api_raw_points_center.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.109

### Fix

- Alle zentralen einklappbaren Dashboard-Bereiche haben jetzt einen Info-Button mit Bereichserklaerung, darunter auch `Gesamtstatistik (Alles)`, `Graph`, `Statistik Zeitraum` und `Bearbeitungsliste`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_raw_points_center.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.108

### Enhancement

- Dashboard-Raw-Aktionen `Kopieren`, `Wert kopieren`, `Einfügen` und `Query kopieren` zeigen jetzt zusaetzlich sichtbare Rueckmeldungen im Popup.
- Der Button `Dashboard: Letzter Fehler` wurde aus der Dashboard-Aktionsleiste entfernt; die Fehleranzeige bleibt ueber die globale Statusleiste unten verfuegbar.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_raw_points_center.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.107

### Enhancement

- Raw-Daten um den selektierten Messpunkt nutzen jetzt ein Zeitfenster `+- Minuten` statt einer Punktezahl. Das Dashboard erweitert beim Nachladen das Zeitfenster schrittweise und die Query arbeitet direkt mit Minuten um den Ankerzeitpunkt.
- Bugreport-Composer zeigt jetzt zusaetzlich einen sichtbaren Hinweis, dass das Logfile bzw. der Debug-Report manuell in GitHub angehaengt werden muss, inklusive Vorschaubild fuer `Add files`.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_raw_points_center.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.106

### Fix

- Bugreport-Flow fragt jetzt vor dem Anlegen eines GitHub-Issues nach `Bug` oder `Erweiterung`, verlangt einen ausfuellbaren Beschreibungstext und setzt automatisch das passende GitHub-Label (`type/bug` oder `type/enhancement`).
- Bugreports bleiben mit Debug-Report-Anhang verknuepft; Erweiterungen oeffnen denselben Composer ohne Log-Zwang.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.105

### Fix

- Dashboard Auto-Tuning sendet benutzerdefinierte `start`/`stop` Werte jetzt immer als UTC-Zeitstempel mit Zeitzone, damit `/api/raw_autotune` nicht mehr mit `datetime must include timezone` fehlschlaegt.
- Einstellungen: Die betroffenen Zahlenfelder fuer Filterbreiten und Auswahl-Schriftgroesse sind jetzt als breitere Mono-Inputs ausgefuehrt, damit Werte beim Hoch-/Runterzaehlen sichtbar bleiben.
- Info-Dialoge dekodieren jetzt literal gespeicherte Escapes wie `\n\n`, damit Beschreibungen mit Umbruechen sauber dargestellt werden.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_ui_support.py tests/test_api_monitoring.py tests/test_api_yaml_flow.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.104

### Feature

- Neue Seite `Monitor`: Konfiguration ueberwachter Messwert-Keys, persistente Fault-Phase mit Recovery-Regeln, Listen fuer Ausreisser/kritische Werte/offene Korrekturen sowie Template-JSON fuer Weiterverarbeitung.
- Monitoring-API: `/api/monitoring/evaluate` erkennt jetzt u. a. `steigt zu stark`, `faellt zu stark`, `ausserhalb Min/Max` und `ungueltiger Wert`, startet eine persistente Stoerphase und kann Korrekturen sofort intern anwenden oder als offene Korrektur ablegen.

### Support

- Monitoring-Status ist jetzt ueber dedizierte Endpunkte (`/api/monitoring/config`, `/api/monitoring/events`, `/api/monitoring/pending`, `/api/monitoring/critical`, `/api/monitoring/templates`) strukturiert abrufbar.

### Maintenance

- Tests: `python -m py_compile influxbro/app/app.py`, `pytest tests/test_api_monitoring.py -q`
- Tested with Home Assistant Core: unknown

## 1.12.103

### UI

- Dashboard/Raw: `raw.paste` gibt jetzt wieder sichtbares Feedback, oeffnet die Bearbeitungsliste und zeigt die vorgemerkte Uebernahme per Popup an. Zusaetzlich gibt es ueber der Raw-Tabelle den persistenten Regler `Bereich +-` samt konfigurierbarer Obergrenze/Standardwert in den Einstellungen.
- Query-Anzeigen bleiben jetzt auf Dashboard, Statistik und Backup dauerhaft sichtbar. Raw-, Graph- und Apply-Preview-Queries zeigen zusaetzlich Zeitstempel und History-Buttons.
- Titelkarte: Der Seitentitel ist standardmaessig groesser und seine Schriftgroesse ist jetzt in den Einstellungen parametrierbar. Der Abstand zwischen Titelkarte und Navigation/Inhalt ist auf 20px korrigiert.

### Support

- Bugreport: Bedieneraktionen werden serverseitig protokolliert und als `Aktionsliste` mit den letzten 5 Aktionen in den vorbefuellten GitHub-Bugreport sowie in den Debug-Report uebernommen.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.102

### UI

- Titelzeile: `topbar.zoom.out` und `topbar.zoom.in` initialisieren sich jetzt erst, wenn die Buttons wirklich im DOM vorhanden sind. Dadurch reagieren die Zoom-Buttons wieder zuverlässig auf allen Seiten.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.101

### UI

- Einstellungen: `main.content button` greift jetzt nicht mehr auf `.ib_info_icon` durch. Die Info-Buttons behalten damit auch auf der Einstellungsseite wieder die feste 22x22-Darstellung wie auf den anderen Seiten.
- Navigation: `nav.dashboard` und die gesamte Sidebar starten jetzt global mit 20px Abstand unterhalb von `page.title.card`.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.100

### UI

- Titelzeile: `sections.open_all` und `sections.close_all` sitzen jetzt wieder als Icon-Buttons direkt rechts neben `page.search`. `page.search` initialisiert sich jetzt erst, wenn die gemeinsame `page.title.card` im DOM vorhanden ist, damit die Suche auf allen Seiten zuverlässig funktioniert.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.99

### UI

- Einstellungen: Die verbleibenden seitenlokalen Global-CSS-Regeln wurden auf `main.content` begrenzt. Dadurch wirkt die gemeinsame `page.title.card` auf der Einstellungsseite jetzt visuell gleich wie auf dem Dashboard und bekommt keine abweichenden Button-/Input-Breiten mehr von der Seite selbst.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.98

### UI

- Einstellungen: Letzte alte Layout-/Such-Stile der früheren Settings-Sonderkarte entfernt, damit die Seite vollständig auf die gemeinsame `page.title.card`-Darstellung zurückgeführt ist.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.97

### UI

- Titelzeile: `sections.open_all` und `sections.close_all` sind jetzt wieder in `page.title.card` integriert und sitzen rechts neben `page.search`. Die alte Einblendung dieser Buttons im Seiteninhalt wurde entfernt.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.96

### UI

- Einstellungen: Die separate Settings-Suchkarte und der doppelte Seitentitel wurden entfernt. Die Einstellungen-Seite nutzt jetzt 1:1 dieselbe `page.title.card`-Darstellung wie das Dashboard.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.95

### UI

- Titelzeile: Der Picker initialisiert sich jetzt erst, nachdem `ui_picker_toggle` wirklich im DOM vorhanden ist. Dadurch reagiert der Button wieder zuverlässig auf allen Seiten.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.94

### UI

- Titelzeile: `ui_profile_hint` steht jetzt unter `by Thomas Schatz` in 12px. `ui_profile_sel` hat jetzt 80px Breite und 34px Höhe. `Buy me a coffee` steht unter dem PayPal-Button, beide linksbuendig untereinander.
- Layout: `ib_pagecard` bleibt fuer alle Seiten zentral identisch, und das Seitenmenue startet weiter mit kleinem Abstand darunter.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.93

### UI

- Titelzeile: Nachbesserung zu `#95`. `nav.profile.select` ist jetzt auf 40px fixiert, `nav.donate` sitzt in der Titelzeile neben `InfluxBro`, und das Menü startet mit Abstand unterhalb von `ib_pagecard`.
- Seitensuche: `page.search` bleibt als einzelnes Suchfeld in der Titelzeile und durchsucht weiterhin nur die aktuell geöffnete Seite.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.92

### UI

- Titelzeile: Die feste Titelkarte wurde umgebaut. `nav.donate` sitzt jetzt neben `InfluxBro`, darunter steht `by Thomas Schatz`. `topbar.profile` und `topbar.zoom` wurden in die Titelzeile integriert. Die alten Buttons `sections.open_all`, `sections.close_all` und `page.search.clear` sind aus der Titelzeile entfernt; die Seitensuche bleibt als einzelnes Suchfeld erhalten.
- Einstellungen: `ui_status_bar_bg` und `ui_status_bar_fg` besitzen jetzt links einen Color Picker vor dem Farbtext.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.91

### UI

- Allgemein: Neue feste Titelkarte auf allen Seiten mit Seitentitel, `sections.open_all`, `sections.close_all` und globaler Seitensuche. Die untere Statusleiste ist jetzt dauerhaft sichtbar und in Höhe/Farben konfigurierbar.
- History: Die Zusatzfilter `measurement`, `entity_id` und `reason` wurden entfernt.
- Export: Der alte Bereich `export.advanced` wurde entfernt; die Auswahl nutzt jetzt nur noch `_measurement`, `_field`, `entity_id` und `friendly_name` im sichtbaren Bereich.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.90

### UI

- Allgemein: Der Picker kopiert jetzt nicht mehr nur den `data-ui`-Namen, sondern das Format `Menüname: data-ui`, z. B. `Import: import.analyze`.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.89

### UI

- Allgemein: Neuer Button `Picker` in der Topbar neben `Info`. Der Hover-Inspektor markiert beim Ueberfahren von UI-Elementen deren `data-ui`-Namen und kopiert ihn bei Klick in die Zwischenablage. `Esc` beendet den Modus.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.88

### UI

- Statistik: Die alte Auswahl wurde entfernt. Stattdessen nutzt die Statistik-Seite jetzt 1:1 die Quellauswahl aus `Kombinieren` mit `_measurement`, `_field`, `entity_id` und `friendly_name` im identischen Quellfluss.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.87

### UI

- Dashboard: `dashboard.selection` ist jetzt auf 500px Breite gesetzt (mit `max-width: 100%`), damit die aufgeloeste Auswahl kompakter und konsistent angezeigt wird.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.86

### UI

- Import: Die alte Zielauswahl wurde entfernt. Stattdessen nutzt die Import-Seite jetzt 1:1 die Quellauswahl aus `Kombinieren` mit `_measurement`, `_field`, `entity_id` und `friendly_name` im identischen Quellfluss.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.85

### UI

- Allgemein: Die Bestaetigungsphrase wurde aus UI und Laufzeit-Konfiguration entfernt. Destruktive Aktionen arbeiten jetzt nur noch mit einfachen Browser-Bestaetigungsdialogen, ohne dass ein Wort eingetippt werden muss.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.84

### UI

- Allgemein: Filter- und Auswahlfelder erhalten jetzt automatisch einen Loesch-Button direkt neben dem Feld. Der Button leert die aktuelle Eingabe/Auswahl und triggert danach dieselben `input`-/`change`-Events wie eine manuelle Bearbeitung.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.83

### UI

- Allgemein: Persistierte Seiteneinstellungen greifen jetzt auch fuer `Logs -> Follow`, weil der Follow-Modus beim Seitenstart den bereits restaurierten Checkbox-Zustand verwendet.
- Allgemein: Export-, Download- und Bugreport-Aktionen verwenden jetzt konsistent ueber die betroffenen Seiten hinweg die aktualisierten Icons.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.82

### UI

- Jobs & Cache: Die Jobs-Liste zeigt jetzt neben aktuell laufenden Jobs auch die letzten abgeschlossenen Jobs aus einer kleinen Historie an. Damit bleibt die Liste nachvollziehbar und ist nicht mehr leer, sobald ein Job bereits fertig ist.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.81

### UI

- Export: Der Button `Export` bietet jetzt einen klickbaren Client-Ordnerbrowser fuer Chromium-basierte Browser. Du waehlt einen lokalen Root-Ordner und kannst danach Unterordner im Dialog mit der Maus ansteuern; die fertige Export-Datei wird direkt clientseitig dorthin geschrieben.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.80

### UI

- Export: Der Button `Export` verwendet jetzt den im Dialog gewaehlten `Zielordner` wirklich als `target_dir` fuer den Export-Job. Damit kann die Export-Datei serverseitig gezielt unter `/data/...` bzw. unter erlaubten absoluten Pfaden abgelegt werden, zusaetzlich zum lokalen Browser-Speichern.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.79

### UI

- Dashboard: Ein JavaScript-Syntaxfehler im Query-Pfad (`q0` doppelt deklariert) wurde behoben. Dadurch wird das Dashboard-Skript wieder vollstaendig geladen und die Selektor-Logik fuer `_measurement`, `_field`, `entity_id` und `friendly_name` kann im Browser wieder korrekt laufen.

### Maintenance

- Fehlerbehebung fuer den Browser-JS-Pfad der Dashboard-Seite
- Tested with Home Assistant Core: unknown

## 1.12.78

### UI

- Dashboard: Die sichtbare Quellauswahl triggert Nachlade-Requests fuer `_measurement`, `friendly_name` und `entity_id` jetzt zusaetzlich sofort ueber direkte Helper auf `input`, `change` und `blur`. Damit werden `fields` und `tag_values` auch bei browserspezifischem Datalist-Verhalten sicher angefragt.

### Maintenance

- Weitere Browser-Ereignis-Absicherung fuer Dashboard-Selektoren
- Tested with Home Assistant Core: unknown

## 1.12.77

### UI

- Dashboard: Die sichtbare Quellauswahl reagiert jetzt nicht nur auf `input`, sondern auch auf `change`. Dadurch werden `fields` und `tag_values` auch dann nachgeladen, wenn ein Datalist-Eintrag wie `EUR` direkt mit der Maus ausgewaehlt wird und der Browser dafuer nur ein `change`-Event liefert.

### Maintenance

- Zusätzliche Absicherung fuer Browser-Datalist-Verhalten im Dashboard
- Tested with Home Assistant Core: unknown

## 1.12.76

### UI

- Dashboard: Die sichtbare Quellauswahl verwendet fuer `entity_id` und `friendly_name` jetzt auch denselben direkten Datalist-Befuellpfad wie `Kombinieren` (`dashboardLoadTagValues` + direktes Schreiben in die Datalist) und entfernt dabei weitere Dashboard-spezifische Seiteneffekte aus den Input-Handlern.

### Maintenance

- Weitere Testversion fuer den JS-Pfadvergleich zwischen Dashboard und `Kombinieren`
- Tested with Home Assistant Core: unknown

## 1.12.75

### UI

- Dashboard: Das alte versteckte Measurement-Feld ist jetzt auch aus dem Selektorfluss entfernt. Die sichtbare Dashboard-Quellauswahl verwendet fuer Measurement nur noch `measurement_filter` und hat damit keinen zweiten parallelen Measurement-Pfad mehr.

### Maintenance

- Finale Nachkorrektur fuer den 1:1-Abgleich der Dashboard-Quellauswahl
- Tested with Home Assistant Core: unknown

## 1.12.74

### UI

- Dashboard: Letzte Abweichungen zur `Kombinieren`-Quellauswahl entfernt. Die sichtbare Auswahl entkoppelt jetzt auch das versteckte interne Measurement-Feld und nutzt keinen eigenen `_field`-Eingabe-Refresh-Pfad mehr.

### Maintenance

- Finale HA-Testversion fuer den 1:1-Abgleich der Dashboard-Quellauswahl
- Tested with Home Assistant Core: unknown

## 1.12.73

### UI

- Dashboard: Die sichtbare Quellauswahl folgt jetzt auch in der Eventkette 1:1 der einfachen `Kombinieren`-Logik. `_measurement` triggert nur `loadFields(measurement)` und danach das Nachladen von `entity_id`/`friendly_name`; `entity_id` und `friendly_name` triggern nur das einfache Suggestion-Refresh plus Auto-Resolve, wenn `_measurement` leer ist.

### Maintenance

- Neue HA-Testversion fuer den exakten `Kombinieren`-Abgleich der Dashboard-Quellauswahl
- Tested with Home Assistant Core: unknown

## 1.12.72

### UI

- Dashboard: Die sichtbare Quellauswahl ist jetzt 1:1 an die einfache Quell-Refresh-Logik von `Kombinieren` angeglichen. `_measurement` laedt `_field` separat, `entity_id` wird mit `_measurement` plus optional `friendly_name` geladen und `friendly_name` mit `_measurement` plus optional `entity_id`, jeweils fest mit `range=24h` wie in `Kombinieren`.

### Maintenance

- Live-Selektorpruefung gegen `http://192.168.2.200:8099` mit `measurement=EUR`, `friendly_name=sensor Cost`, `entity_id=watermeter_value_cost`
- Tested with Home Assistant Core: unknown

## 1.12.71

### Maintenance

- Neue Testversion fuer Home Assistant, damit der aktuelle Dashboard-Stand als Update erkannt und installiert werden kann.
- Tested with Home Assistant Core: unknown

## 1.12.70

### UI

- Dashboard: Die neue Quellauswahl verwendet jetzt die einfache Refresh-Logik von `Kombinieren` statt der alten iterativen Dashboard-Kaskade. `_measurement` laedt `_field` separat und `entity_id`/`friendly_name` werden nur mit `_measurement` plus optional genau einem Gegenfilter nachgeladen.
- Dashboard: `_field` wird im Quellenblock weiterhin aus der Datenbankspalte `_field` geladen, fuer das Dashboard aber auf `value` fokussiert, wenn dieses Field vorhanden ist.

### Maintenance

- Live-Selektorpruefung gegen `http://192.168.2.200:8099` mit Beispiel `measurement=EUR`
- Tested with Home Assistant Core: unknown

## 1.12.69

### UI

- Dashboard: Die Quellauswahl aus `Kombinieren` wurde als neuer sichtbarer Auswahlblock ins Dashboard uebernommen. Sichtbar sind jetzt wieder `_measurement`, `_field`, `entity_id` und `friendly_name` in der Quellenstruktur.
- Dashboard: Das Infofeld zeigt jetzt die aufgeloeste Quellauswahl (`Quelle (aufgeloest)`) auf Basis dieser neuen Dashboard-Quellauswahl.

### Maintenance

- Zwischenstand fuer Sichtpruefung der neuen Dashboard-Quellauswahl
- Tested with Home Assistant Core: unknown

## 1.12.68

### UI

- Dashboard: Die vier sichtbaren Auswahlfelder oberhalb von `Aktualisieren` (`_measurement`, `_field`, `friendly_name`, `entity_id`) wurden fuer den Neuaufbau vollstaendig aus der sichtbaren UI entfernt.

### Maintenance

- Zwischenstand fuer Sichtpruefung des Dashboard-Rebuilds
- Tested with Home Assistant Core: unknown

## 1.12.67

### UI

- Dashboard: Der Auswahlblock oberhalb von `Aktualisieren` nutzt jetzt dieselbe Kaskadenlogik wie die Backup-Seite. Die Felder heissen konsistent `_measurement`, `_field`, `friendly_name` und `entity_id` und laden die jeweils anderen Listen bei jeder Auswahl neu aus den gefilterten Datenbankwerten.
- Dashboard: `_field` ist jetzt ebenfalls ein Datalist-Auswahlfeld wie die anderen Selektoren und wird bei Mehrdeutigkeit bevorzugt auf `value` gesetzt.

### Maintenance

- Live-Selektortests gegen `http://192.168.2.200:8099`
- Tested with Home Assistant Core: unknown

## 1.12.66

### UI

- Dashboard: Alle Auswahlaktionen fuer `_measurement`, `_field`, `friendly_name` und `entity_id` werden jetzt im Debug-Log protokolliert. Zusaetzlich werden bei jedem Nachladen die komplette geladene Eintragsliste und die dazu verwendeten Filter im Logfile mitgeschrieben.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.65

### UI

- Dashboard: Die `_field`-Liste wird jetzt auch fuer Measurements mit Sonderzeichen wie `°F` direkt aus den vorhandenen Daten aufgebaut. Dadurch filtern `_measurement`, `_field`, `friendly_name` und `entity_id` wieder konsistent gegeneinander - analog zum Verhalten auf der Backup-Seite.
- Export: Export-Dateien sind nicht mehr auf eine Datenpunktzahl begrenzt. Der Browser fragt fuer `Export` jetzt bevorzugt ein Zielverzeichnis bzw. Save-As-Ziel ab und schreibt die fertige Datei dorthin.
- Import: Die Analyse zeigt jetzt Quell-Measurements, Quell-Fields und die ersten drei Datenzeilen. Zusaetzlich gibt es einen Transformations-Check mit Test-Button und Vorschau der ersten zehn transformierten Zeilen.
- Einstellungen: Neue editierbare Transformationsliste fuer Measurement-Umrechnungen beim Import.

### Maintenance

- Hinweis dokumentiert: HA-Tests nur noch gegen `http://192.168.200:8099`
- Tested with Home Assistant Core: unknown

## 1.12.64

### UI

- Dashboard: Unter der Filterauswahl gibt es jetzt wie im Export ein Infofeld `Auswahl (aufgeloest)`. Es zeigt den finalen Stand von `_measurement`, `_field`, `friendly_name`, `entity_id` sowie den aktiven Zeitraum und die Anzahl der aktuell verfuegbaren Optionen je Filter.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.63

### UI

- Dashboard: Die `_measurement`-Auswahl reagiert jetzt zusaetzlich auf `change` wie im Export. Dadurch greifen die gegenseitigen Filter auch dann sofort, wenn ein Measurement direkt aus der Datalist angeklickt wird.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.62

### UI

- Dashboard: Die Filterauswahl fuer `_measurement`, `_field`, `friendly_name` und `entity_id` wird jetzt nicht mehr vom eingestellten Zeitraum eingeschraenkt. Dadurch bleiben die Selektoren gegenseitig konsistent, auch wenn im aktuell gewaehlten Zeitfenster gerade keine Datenpunkte liegen.

### Maintenance

- Direkt gegen HA getestet: Dashboard-HTML + `api/tag_values`, `api/measurements`, `api/fields` auf `http://192.168.2.200:8099`
- Tested with Home Assistant Core: unknown

## 1.12.61

### UI

- Export: Die `_field`-Auswahl wird jetzt mit denselben Filtern wie die restliche Export-Auswahl geladen (`_measurement`, `friendly_name`, `entity_id`, Zeitraum). Dadurch wird kein unpassendes `value` mehr erzwungen und Exporte liefern wieder Daten statt nur Kopfzeilen.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.60

### UI

- Dashboard: Die Auswahlfelder `_measurement`, `_field`, `friendly_name` und `entity_id` werden jetzt iterativ zusammen nachgefuehrt. Sobald eine Kombination nur noch einen gueltigen Wert zulaesst, wird dieser direkt uebernommen.
- Dashboard: `_field` heisst in der sichtbaren Auswahl jetzt konsistent `_field`, bevorzugt automatisch `value`, und `Entity ID` steht direkt rechts neben `Messwert`.
- Dashboard: Der Zeitraum-Block steht innerhalb des Auswahlrahmens jetzt wieder ganz unten.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.59

### UI

- Dashboard: Die Auswahlfelder filtern sich jetzt gegenseitig. Bereits gesetzte Werte in `_measurement`, `friendly_name`, `entity_id` und `field` schränken die jeweils noch offenen Vorschlagslisten ein.
- Dashboard: `field` verhält sich wie die anderen Filterfelder. Wenn `value` in den verfügbaren Feldern enthalten ist, wird es automatisch vorausgewählt; andernfalls bleibt das Feld leer.
- Dashboard: Der ausgeblendete Bereich `Erweitert: Measurement / Field` ist für die Bedienung nicht mehr nötig.

### API

- `GET /api/measurements` unterstützt jetzt zusätzliche Filter über `field`, `friendly_name`, `entity_id`, `range`, `start` und `stop`.
- `GET /api/fields` unterstützt jetzt neben `measurement` auch eine Einschränkung über `friendly_name`, `entity_id`, `range`, `start` und `stop`.
- `GET /api/tag_values` kann `friendly_name`/`entity_id` nun zusätzlich über `field` eingrenzen.

### Maintenance

- Direkt gegen HA getestet: `http://192.168.2.200:8099/api/measurements`, `/api/fields`, `/api/tag_values`, `/api/resolve_signal`
- Tested with Home Assistant Core: unknown

## 1.12.58

### UI

- Dashboard: `Aktualisieren` funktioniert wieder, auch wenn die Auswahl zunaechst nur ueber `friendly_name` erfolgt. Vor dem Laden wird die `entity_id` bei Bedarf automatisch aus den gefilterten Vorschlaegen uebernommen.
- Dashboard: Statt einer blockierenden Fehlermeldung nur wegen fehlender `entity_id` prueft die Seite jetzt auf eine vollstaendige Signal-Auswahl (`friendly_name` oder `entity_id` plus Measurement/Field).
- Dashboard: Beim Klick auf `Aktualisieren` wird jetzt immer sofort ein sichtbarer Status gestartet (`Auswahl wird geprueft...`, `Auswahl wird aufgeloest...`, `Daten werden geladen...`) und bei Validierungsfehlern auch sauber als Fehlerstatus stehen gelassen.
- Dashboard: Der Bereich `Erweitert: Measurement / Field` ist aus der sichtbaren UI entfernt.
- Dashboard/Export: `Field` ist nicht mehr blind auf `value` fixiert. Wenn `value` in den verfuegbaren Fields existiert, wird es automatisch vorausgewaehlt; andernfalls bleibt das Feld leer.
- Export: `friendly_name` bleibt bei automatischer `entity_id`-Uebernahme erhalten und wird nicht mehr direkt wieder geloescht.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.56

### UI

- Dashboard: `friendly_name` reagiert jetzt auch bei echter Datalist-Auswahl (`change`) und setzt die erste gefilterte `entity_id` automatisch. `Field (intern)` bleibt standardmäßig auf `value` vorbelegt.
- Statistik: Die Auswahlfelder für `_measurement`, `friendly_name` und `entity_id` verhalten sich jetzt wie im Dashboard. Vorschläge werden beim Seitenaufruf geladen, `friendly_name` filtert `entity_id`, und der erste passende Eintrag wird automatisch übernommen.
- Export: Die Auswahlfelder wurden an das Dashboard angeglichen. Vorschläge werden serverseitig vorbefüllt und clientseitig nachgeladen; `friendly_name` setzt die erste passende `entity_id`, `Field (intern)` startet mit `value`.
- Logs: `Follow` ist jetzt eine Checkbox statt eines Toggle-Buttons.
- Jobs: Timer-Jobs verwenden im Feld `Modus` jetzt Auswahlboxen (`hours`, `daily`, `weekly`, `manual`) mit passenden Eingabefeldern statt Prompt-Textdialogen. Die Werte werden per `Speichern` persistent übernommen.

### Fixes

- Export geprüft: Der Export schreibt wieder vollständige Datenzeilen. Verifiziert gegen `http://192.168.2.200:8099` mit `2840` exportierten Zeilen statt nur Headern.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.55

### UI

- Dashboard: Die `friendly_name`-Auswahl reagiert jetzt sowohl auf Eingabe als auch auf echte Datalist-Auswahl (`change`). Dadurch wird die erste gefilterte `entity_id` zuverlässig sofort übernommen und `Aktualisieren` startet ohne manuelles Nachsetzen der Entity ID.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.54

### UI

- Dashboard: Bei Auswahl eines `friendly_name` wird die gefilterte `entity_id`-Liste sofort nachgeladen und automatisch auf den ersten passenden Eintrag gesetzt.
- Dashboard: `Field (intern)` startet mit der Standardauswahl `value` und bleibt auch bei leerem Measurement verwendbar.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.53

### UI

- Dashboard: `Field (intern)` ist jetzt nie mehr leer. Das Auswahlfeld enthält standardmäßig `value` und bleibt auch bei leerem oder noch nicht aufgelöstem Measurement benutzbar.
- Dashboard: Bei Eingabe oder Auswahl eines gültigen Measurements werden die verfügbaren Fields sofort nachgeladen; bei leerem Measurement wird automatisch auf `value` zurückgesetzt.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.52

### UI

- Dashboard: Auswahl-Vorschläge für `_measurement`, `friendly_name` und `entity_id` werden nun zusätzlich serverseitig vorgerendert und beim Seitenaufruf aktiv nachgeladen. Dadurch bleiben die Datalists auch dann sichtbar, wenn die clientseitige Initialisierung verzögert ist.

### Fixes

- Statistik: Flux-Queries verwenden kein `typeOf()` mehr, damit die Abfragen auch mit InfluxDB/Flux-Versionen funktionieren, in denen diese Funktion nicht verfügbar ist.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.51

### UX

- Einstellungen: Wenn `Influx Verbindung testen` erfolgreich ist und gültige `token`, `org` und `bucket` im Formular stehen, werden diese Werte jetzt automatisch persistent gespeichert (Save), sodass Dashboard‑Auswahllisten direkt befüllt werden.

## 1.12.50

### Fix

- Einstellungen: Testverbindung ist jetzt tolerant gegenüber Backend‑Antworten mit `connected:true` und zeigt zuverlässig Status/Modal an, selbst wenn das Template-HTML nicht im DOM vorhanden ist (Runtime-Fallback erzeugt Status/Modal bei Bedarf).

## 1.12.49

### UI

- Einstellungen: Bei `Influx Verbindung testen` wird jetzt direkt unter dem Button ein sichtbarer Statustext angezeigt und zusätzlich ein kleines Bestätigungs‑Modal aktiviert, wenn die Verbindung erfolgreich ist. Fehlermeldungen erscheinen wie bisher in rot.

## 1.12.48

### UI

- Dashboard: Besseres Feedback wenn erforderliche Felder fehlen — beim Drücken von `Aktualisieren` ohne `entity_id` oder bei Aktionen wie Ausreisser‑Suche ohne `measurement`/`field` wird nun eine klarere Fehlermeldung angezeigt und das fehlende Feld fokussiert/hervorgehoben.

## 1.12.47

### UI

- Raw: Füge Copy/Paste Werkzeuge für einzelne Raw‑Zeilen hinzu (Zeile anklicken → `Wert kopieren` → andere Zeile anklicken → `Einfügen`). Staging verwendet die bestehende Bearbeitungsliste (EDIT_LIST) und respektiert Dezimal‑Limits.
- Raw: Sichtbare Kopiert‑Info in der Toolbar; Paste deaktiviert bis Quelle + Ziel gesetzt.

## 1.12.46

### UI

- Harmonisierung der Section Title Bars: Info-Icon Grösse/Ausrichtung vereinheitlicht und Details-Pfeil vergrössert für bessere Lesbarkeit.
- `Zeitraum` Anzeige: Die konkrete `von bis` Anzeige (`range_from_to`) wird jetzt konsistent unter der Zeitraum-Auswahl angezeigt.
- Help/Popup: Help‑Buttons können nun optional einen direkten Link zu `Einstellungen` anzeigen; Popup hat einen Settings‑Button (nur sichtbar wenn konfiguriert).
- Query Details: `Query anzeigen` zeigt jetzt Start, Ende und Ausführungsdauer (Dauer wird gemessen und angezeigt).

### Features

- Server-side Auto-Tuning API: `POST /api/raw_autotune` (benchmarks, persistiert `ui_raw_max_points`). Client UI wired.

## 1.12.45

### UI

- Fehlerdialog: Bugreport Modal implementiert (Copy + Open on GitHub) und Bugreport-Button in Statusleiste nutzt dieses Template.
- UI: Info-Icon (`i`) Sichtbarkeit verbessert (kontrastreiche Farbe bei verschiedenen Themen).
- Dashboard: `Auto-Tuning` Button aus Raw-Bereich entfernt; stattdessen in den Einstellungen unter `UI -> Dashboard` als "Auto-Tuning (Dashboard)" verlinkt.

### Fixes

- Kleinere UI-Harmonisierung: Abschnittstitel/Icon-Farben und Responsive-Topbar-Variablen angepasst.

## 1.12.44

### UI

- Backup: Download nutzt jetzt `showSaveFilePicker` wenn vom Browser unterstuetzt (forcing Save-As). Fallback auf normalen Download.
- Einstellungen: Button `Token testen` prueft konfiguriertes `admin_token` auf notwendige Rechte.

### Fixes

- FullBackup (native v2): Preflight-Check fuer authorizations ruft `find_authorizations()` ohne inkompatible Parameter auf (fix fuer client-API Inkompatibilitaeten).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.43

### UI

- Kombinieren: Auswahl fuer Quelle/Ziel ist an Dashboard angelehnt (entity_id/friendly_name als datalist) und measurement/field werden best-effort automatisch aufgeloest.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.42

### Fixes

- Kombinieren: Seite laedt wieder korrekt; HA Template-Snippet (`{{ states(...) }}`) wird nicht mehr von Jinja ausgewertet.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.41

### Fixes

- FullBackup (native v2): Vorab-Check fuer admin_token Rechte (All-Access) mit klarer 401 Fehlermeldung.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.40

### Fixes

- Export: Auswahl-Textfeld nutzt jetzt die volle Breite des Bereichs.
- Export: Button "Download" + zusaetzlicher Button "Export" (Save-As, wenn verfuegbar).
- Logs: Default ist "neuster" + Follow ein; Buttons sind Icons.
- Dashboard: Versionsbox rechts neben Titel entfernt.
- Details: "Alle oeffnen" / "Alle schliessen" sind Icons.
- Dashboard: alle einklappbaren Bereichstitel sind farblich hervorgehoben (wie Raw).
- Einstellungen: Job-Farben haben Colorpicker + Texteingabe.
- Tabellen: "Liste aktualisieren" Buttons sind Icons.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.38

### UI

- Backup: FullBackup (LP) Toolbar linksbuendig; "Modus" heisst jetzt "Backupmodus"; "Liste aktualisieren" steht ueber der FullBackupliste.
- Tabellen-Toolbar: Buttons "Spaltenbreite automatisch" und "Fensterbreite" sind jetzt Icons.
- Details: "Alle oeffnen" / "Alle schliessen" stehen neben dem Seitentitel (wie Dashboard).
- Details: Default-Farben fuer Bereichstitel (Hintergrund/Text) sind jetzt gesetzt; Einstellungen bieten Colorpicker.
- UI Logging: Select/Checkbox Aenderungen werden best-effort in den Add-on Logs erfasst (debug).

### Fixes

- Kombinieren: API ist robuster gegen unerwartete Fehler (liefert JSON statt HTML 500; zusaetzliches Logging).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.37

### Fixes

- Kombinieren: fruehe Validierung (measurement/field + Tags) und Delete-Guard (ALLOW_DELETE).

### UI

- Jobs: neue Spalte "Ausloeser" zeigt trigger_page + timer_id (Scheduler/Timer besser erkennbar).
- Statusleiste unten: Influx Verbindung (OK/ERR) wird angezeigt (best-effort, cached).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.36

### Fixes

- Statistik: "no column _value exists" behoben (Series-span oldest Query).

### UI

- Query Details: Start-Zeitstempel + History (Dashboard/Backup/Statistik).
- Fehlerfenster: Buttons "Logs (5min)" und "Jump Logs".
- Statusleiste unten: auf allen Seiten sichtbar, inkl. Button "Git Bugreport" (profi Template).
- Timer Jobs: Button "History" zeigt die letzten Timer-Aktivitaeten.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.35

### UI

- Einstellungen: Suchfeld bleibt beim Scrollen sichtbar.
- Fehleranzeige: globale Statuszeile am unteren Rand zeigt den letzten Fehler inkl. Zeitstempel; "Fehlerdialog" zeigt Verlauf.
- Dashboard: Button "Letzter Fehler" zeigt den letzten Fehlerdialog erneut.

### Jobs

- Job Details: Dialog zeigt laufende/letzte Queries inkl. Zeitstempel (global_stats).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.34

### Fixes

- Dashboard: Timeout-Fehler bei "Aktualisieren" zeigen jetzt eine klare Hinweis-Meldung (timeout_seconds/Zeitraum) statt nur dem Raw-HTTP Fehler.
- Zoom: Zoom wirkt nicht mehr auf Plotly via CSS-zoom (verhindert versetztes Klick-Selecting); Zoom skaliert stattdessen Schrift (und triggert Resize).
- Statistik Vollscan (Scheduler): Sicherheitslimit fuer Zeitraum (max Tage) verhindert zu grosse Scans, die Timeouts/InfluxDB-Fehler ausloesen koennen.

### Docs

- Screenshots in `influxbro/README.md` verwenden raw.githubusercontent URLs.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.33

### Fixes

- UI/Fehlermeldung: Error-Popup enthaelt einen Bugreport-Button (Debug report Download + GitHub Issue vorbefuellt mit HA/Influx-Versionen).

### Maintenance

- Repo: `README.md` und `LICENSE.md` nach `influxbro/` verlegt (License-Datei heisst dort `license`); Root-README zeigt auf die Add-on Doku.
- Tested with Home Assistant Core: unknown

## 1.12.32

### UI

- Farben: Bereichstitel (Details/Sektionen) sind global konfigurierbar (Hintergrund + Textfarbe).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.31

### Features

- Diagnose: Menu "Diagnose" ausgebaut (Status-Kacheln + Health Summary), inkl. Best-effort InfluxDB Prometheus KPIs ueber `/metrics`.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.30

### Fixes

- Dashboard: Klick auf Graph-Punkt springt robust in die Raw-Daten (keine Zeitverschiebung durch Plotly-X-Parsing); markierter Punkt bleibt in der Raw-Liste dauerhaft hervorgehoben.
- Statistik: Serienlisten-Scan robuster, wenn Tags wie `entity_id`/`friendly_name` fehlen; Fehlermeldungen werden korrekt angezeigt (keine abgeschnittenen "no column ..." Messages).

### UI

- Dashboard: Plotly-Legende ist unter dem Graph angeordnet.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.29

### Fixes

- Docker/HA: Influx CLI Installation repariert (Tarball enthaelt `./influx`) und wird nur noch auf `amd64`/`aarch64` installiert (Upstream-Arch-Support). Andere Plattformen bauen wieder; Native v2 FullBackup/FullRestore ist dort gesperrt.
- UI/Backup/Restore: Hinweistext zeigt `HA Plattform` und ob Native v2 (influx CLI) verfuegbar ist.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.28

### Features

- Kombinieren: Vorschau mit Timeline (Maus-Selektion) und Mini-Graph fuer Quelle/Ziel; Richtung Quelle<->Ziel direkt umschaltbar.
- Kombinieren: Rollback-sicher durch optionales Ziel-Range-Backup vor dem Schreiben; optionales Loeschen des Zielbereichs vor dem Kopieren (DELETE erforderlich).
- UI/Template: Info-Icon neben Bereichstiteln (Details/Sektionen) oeffnet resizable Info-Popup mit Copy/Umbruch.

### Fixes

- Einstellungen: Checkboxen sind linksbuendig ausgerichtet und in der Hoehe konsistenter.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.27

### Fixes

- Backup/FullBackup Listen: Auswahl per `Alles` wirkt jetzt nur auf die aktuell sichtbaren Zeilen (Filter), ohne andere Selektionen zu verlieren; Download-Button wird auch bei leerer Liste korrekt ausgeblendet.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.26

### Features

- Jobs & Cache: Timer Jobs `Modus` unterstuetzt jetzt `hours/daily/weekly/manual` (inkl. Wochentag + Uhrzeit) fuer `dash_cache`, `stats_cache` und `stats_full`.
- stats_full: kann jetzt zeitgesteuert laufen (Scheduler) statt nur manuell.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.25

### Features

- FullBackup (InfluxDB v2): neuer Modus `Native v2 (influx backup)` (CLI-basierter Backup-Export), gespeichert als ZIP (Meta + native Payload) und in der Liste per Spalte `format` erkennbar.
- FullRestore (InfluxDB v2, native): Zielbucket kann frei gewaehlt werden (`--new-bucket`), optional `Ueberschreiben` (loescht Zielbucket vor Restore; erfordert Confirm-Phrase).
- Einstellungen: neues Feld `admin_token` (maskiert) fuer Native Backup/Restore (v2).

### Maintenance

- Docker: `influx` CLI wird im Add-on Image installiert (Multi-Arch), um Native v2 Backup/Restore auszufuehren.
- Tested with Home Assistant Core: unknown

## 1.12.24

### Fixes

- Dashboard Raw: Klick auf Graph-Punkt laedt jetzt automatisch Raw-Daten nach, wenn der Zeitpunkt nicht in der aktuell geladenen Raw-Liste enthalten ist (damit der Sprung immer funktioniert).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.23

### Fixes

- Ausreisser: Dialog bei Einzel-"uebernehmen" zeigt jetzt detailliert Messwert/Alt/Neu in der Apply-Vorschau.
- History/Rollback: Rollback erfordert keine Delete-Confirm-Phrase mehr (nur normale Sicherheitsabfrage).

### Features

- Jobs & Cache: Cache-Info zeigt deutlich mehr Details (Key/Inhalt/Flags/Events).
- UI: fixe Top-Leiste mit Profil-Auswahl (Anwenden/Speichern/Info, Version) und globalem Zoom +/- (persistiert im Browser).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.22

### Features

- Backup/Restore: Full InfluxDB Backup/Restore als eigene Sektionen (FullBackup/FullRestore) mit separaten Listen, Download/Loeschen/Restore und Job-Status.
- InfluxDB: FullBackup/FullRestore unterstuetzt v1 und v2; v3 wird mit klarer Fehlermeldung abgelehnt.
- Einstellungen/UI: neue Settings fuer Auswahlfelder (Fontgroessen, Auto-Breite, manuelle Breite) und Auswahlfelder auf mehreren Seiten an das Master-Template angepasst.

### Fixes

- Backup/Restore: FullBackups (kind=db_full) werden nicht mehr in der normalen Signal-Backup-Liste angezeigt; normale Backup-Endpunkte blockieren FullBackups.
- FullBackup Download: id-Validierung korrigiert.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.21

### Features

- Dashboard: Letzter Graph wird serverseitig unter `/data` referenziert und beim Oeffnen wiederhergestellt (ohne DB-Query), wenn keine Auswahl gesetzt ist.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.20

### Fixes

- Statistik: Spaltenauswahl-Checkboxen fuer Nachladen wieder vorhanden; Nachladen (markiert/alle im Filter) funktioniert wieder.
- Tabellen: Sortier-Richtung wird in der Tabellen-Kopfzeile angezeigt (Pfeil), aufwaerts/abwaerts toggelbar.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.19

### Features

- UI Profile (global): Profile werden filebasiert unter `/data/ui_profiles` gespeichert (Default: PC/MOBIL). Profil kann global angewendet werden; Profilverwaltung inkl. Anlegen/Loeschen/Umbenennen/Info mit Volltextsuche.

### Fixes

- UI Persistenz: "Darstellung speichern" ist entfernt; GUI-Aenderungen werden automatisch gespeichert und nicht mehr durch Dashboard-Defaults ueberschrieben.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.18

### Fixes

- Tabellen: Struktur gem. `Template.md` vereinheitlicht (Rahmen + Tabellenueberschrift pro Tabelle), so dass Zeilenzaehler und Spalten-Auswahl ueberall konsistent funktionieren.

### Features

- Tabellen: Info-Icon (Buch) ist pro Tabelle mit Zweck/Spalten/Aktionen ausfuehrlich befuellt.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.17

### Fixes

- Jobs & Cache: Buttons im Cache-Toolbar sind linksbuendig (Aktualisieren/Cache loeschen).
- Dashboard Raw: Tagesnavigation (+1/+7/juengster Tag) laedt automatisch nach, wenn der Ziel-Tag noch nicht geladen ist.

### Features

- Cache: Jede Cache-Zeile zeigt eine eindeutige Cache-ID (neue Spalte `id`).
- Cache Nutzung: Cache-ID ist klickbar und springt zur passenden Cache-Zeile (Highlight).
- UI Persistenz: Nicht-sensitive GUI-Auswahlwerte werden filebasiert unter `/data` gespeichert und beim Laden wiederhergestellt; ungueltige Keys werden bereinigt.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.16

### Fixes

- Timer Jobs: `last run` wird persistent gespeichert; Jobs stoppt die Laufzeit-Anzeige nach Abschluss (u.a. Restore/Export).
- Statistik: Letztes Ergebnis + UI-Auswahl werden im Browser gespeichert; Nachladen (Spalten) bleibt konsistent nach Seitenwechsel.

### Features

- Timer Jobs: Button `Modus` zum Aendern der Scheduler-Parameter (hours/daily, hours/daily_at).
- Restore: Download-Button fuer das selektierte Backup (ZIP: Meta + Line Protocol).
- Jobs: Export-Jobs werden in `Jobs & Cache` mit angezeigt und sind abbrechbar.
- Einstellungen: Breitenlimit entfernt; Default `Max Job Laufzeit` = 3600s (1h).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.12.15

### Features

- Sidebar/Status: Refresh-Button loescht abgeschlossene Eintraege; Status-Schriftgroesse ist in Einstellungen parametrierbar.
- Einstellungen/Ausreisser: `_measurement` ist nicht editierbar; Buttons zum Hinzufuegen/Loeschen entfernt.
- Jobs & Cache: Job-Zeilen farblich nach Status (Farben in Einstellungen); Max-Joblaufzeit (Sekunden) mit Auto-Abbruch + Log.
- Jobs & Cache: Cache-Info-Dialog (inkl. Events/Verwendung) und Anzeige der Gesamtgroesse.
- Timer Jobs: Action-Spalte mit Start/Abbruch; neuer manueller Job `stats_full` (Statistik komplett inkl. Details).
- Export: Dialog zur Zielordner-Auswahl (unter /data oder /config).
- Backup: Anzeige Add-on Speicher (belegt unter /data) zusaetzlich zu freiem Speicher; Tabellenkopf bleibt beim Scrollen sichtbar.
- Statistik: Tabellenhoehe per Handle anpassbar und persistent; Checkbox-Groesse wird global skaliert.
- Dashboard/Bearbeitungsliste: Spalte "Aktuell" zeigt optional den Neuwert (aktuell -> neu); Direktbutton "uebernehmen" schreibt sofort in DB; Undo stellt Ursprungswert wieder her.
- Tabellen: (i) Info-Button wird automatisch pro Tabelle eingefuegt (best-effort).

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.14

### Features

- Einstellungen: Layout pro Abschnitt als 1-spaltige Parameterliste (Titel + Beschreibung + Control), mobil/desktop einheitlich.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.13

### Features

- Dashboard/Ausreisser: Details werden im rechten Panel angezeigt (Davor/Ziel/Danach); Klick auf Zeile aktualisiert Detailansicht + fokussierten Edit-Graph.
- Ausreisserliste: Aktion-Spalte hat Direktbuttons `loeschen` und `ueberschreiben`.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.12

### Features

- Einstellungen/Ausreisser: Tabelle wird mit allen bekannten `_measurement` Werten vorbefuellt (leere max_step Werte werden nicht gespeichert).
- Ausreisser-Schwellwert: freie Map wird zuerst gegen `_measurement`, dann gegen `unit_of_measurement` gematcht.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.11

### Features

- Restore: Zwei-Spalten Layout (Quelle/Ziel) auf Desktop; mobil bleibt es untereinander.
- Restore: Boxen sind resizable; Hoehen werden ueber "Darstellung speichern" gemerkt.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.10

### Changes

- Writes/Deletes: Einstellung `Schreiben/Loeschen erlauben` entfernt (Schreiben ist immer aktiv).
- Point-Edits (ueberschreiben/loeschen einzelner Punkte): keine Confirm-Phrase mehr noetig; nur Dialog-Bestaetigung.
- Bulk-Deletes (z.B. Zeitraum loeschen, History Rollback, Import: Vorher loeschen): weiterhin mit `delete_confirm_phrase` geschuetzt.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.9

### Features

- Backup: Download-Button fuer selektiertes Backup (ZIP: Meta + Line Protocol).
- Backup: Anzeige freier Speicher am Backup-Speicherort; optionaler Mindestwert (MB), unter dem Backups abgelehnt werden.
- Backup/Restore: Einstellung fuer "sichtbare Zeilen" der Listen (scrollt bei mehr Eintraegen).

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.8

### Features

- Export: Auswahl-Infofeld ist groesser und resizable; Groesse wird ueber "Darstellung speichern" gesichert.
- Export: Format/Delimiter sind ausgerichtet; kurze Erklaerung unter dem Format.
- Export: "Export starten" loest nach Fertigstellung automatisch den Download aus (Download-Button entfernt).
- Logs: Buttons zum Sprung zum aeltesten/neusten Eintrag.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.7

### Features

- Navigation: Menuepunkt heisst jetzt "Jobs & Cache".
- Jobs & Cache: Cache-Tabelle zeigt zusaetzlich "last used".
- Jobs & Cache: neue Tabelle "Timer Jobs" (naechster Lauf + Kommentar) fuer Intervall-/Nightly-Jobs.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.6

### Fixes

- Import: Analyse robuster (BOM/Header-Varianten, value/time Checks) und zeigt bei `valid=0` konkrete Diagnose + Beispielzeilen.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.5

### Fixes

- Dashboard: Klick auf Messpunkt zentriert die passende Raw-Zeile in der Tabelle (mit Kontextzeilen) und markiert sie.

### Features

- Dashboard: Anzeige des selektierten Messpunkts (Zeit/Wert/Serie) ueber dem Graph.
- Raw: Tagesnavigation-Buttons (aeltester/juengster Tag, +/-1d, +/-7d; lokale Browserzeit).
- Graph: Hover zeigt Zeitstempel im Format `tt.mm.yy hh:mm:ss.msec`.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.4

### Features

- Einstellungen: Suchfeld mit Trefferliste (springt zum Element und klappt Bereiche automatisch auf).
- Einstellungen: Ausreisser-Konfiguration als Tabelle (_measurement/max_step) statt einzelner Eingabefelder.
- Jobs: "Cache"-Tabelle fuer alle Caches (Dashboard + Statistik) inkl. Bereich/Ausloeser/next update/Modus; Cache-Jobs zeigen den Modus.
- Navigation: neuer Menuepunkt "Info" (Influx Datenbank Diagnose); bisheriger Menuepunkt "Info" heisst jetzt "Changelog".
- Dashboard: Klick auf Messpunkt markiert den Punkt und springt in Raw-Daten zum passenden Zeitstempel (Zeile wird hervorgehoben).
- Dashboard: Ausreisser "Abbruch" stoppt nur den laufenden Scan (Treffer bleiben stehen).

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.3

### Features

- UI: Tooltips zeigen jetzt bei Buttons/Checkboxen/Auswahlfeldern eine kurze Erklaerung plus den stabilen UI-Key (z.B. `... (dashboard.load)`), damit Aenderungswuensche eindeutig referenziert werden koennen.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.2

### Fixes

- Dashboard/Bearbeitungsgraph: Plotly Line-Simplification deaktiviert (Spikes/Ausreisser werden nicht "geglattet").

### Features

- Statistik: serverseitiger Cache unter `/data/stats_cache` (letztes Ergebnis kann nach Seitenwechsel/Restart wieder geladen werden).
- Statistik: nightly/inkrementelles Cache-Update als Background-Job (stale/dirty/mismatch werden bevorzugt aktualisiert).
- Jobs: neue Karte "Statistik Cache" (Schedule-Status + Button zum Starten eines Updates + Cache loeschen).
- Einstellungen: neuer Bereich `UI -> Statistik Cache` (Intervall + Limits).

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.1

### Fixes

- Dashboard: Auswahl (Measurement/Field) bleibt beim Seitenwechsel erhalten; zuletzt geladene Daten bleiben sichtbar.
- Dashboard: rote Klick-Info im Graph entfernt; Hover-Info kommt direkt am Messpunkt.
- Sidebar Status: Statusanzeige bleibt bei Seitenwechsel erhalten.

### Features

- Logs: neuer Button `Debug report` exportiert einen GitHub-freundlichen Support-Report als Markdown.
- Statistik: Spalten-Auswahl per Checkbox entfernt; es werden immer `last_value` und `newest_time` geladen.

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.12.0

### Features

- Dashboard: serverseitiger Cache unter `/data/dash_cache` (Graph/Tabelle bleiben beim Zurueckkehren erhalten; deutlich schneller).
- Jobs: zweite Tabelle "Dashboard Cache" mit Aktionen `Pruefen` (best-effort), `Aktualisieren`, `Loeschen`.
- Einstellungen: Cache Intervall (alle X Stunden oder taeglich HH:MM:SS) + Limits (Max Eintraege/MB).

### Maintenance

- Tested with Home Assistant Core: 2026.3.1

## 1.11.98

### Fixes

- Dashboard: Ableitung-Checkboxen sind per Default aktiv (Hintergrund + Farbleiste + Ableitungs-Graph).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.97

### Fixes

- Dashboard: Sections-Toolbar (Alle oeffnen/schliessen/speichern) sitzt jetzt unterhalb der Kopfzeile und ist sauber linksbuendig.
- Dashboard: Graph/Ableitung Defaults werden beim ersten Start gesetzt (Hintergrund + Farbleiste + Ableitungs-Graph + absolut).
- Dashboard: State wird beim Verlassen der Seite sofort gespeichert (pagehide/visibilitychange), damit Graph/Tabelle beim Zurueckkehren schneller wieder da sind.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.96

### Features

- Export: Export-Erzeugung laeuft als Hintergrund-Job und kann abgebrochen werden; Download erscheint erst nach Fertigstellung.
- Export: Anzeige `Auswahl (aufgeloest)` + schnelle Serien-Info (best-effort) fuer den gewaehlten Zeitraum.

### Fixes

- Bearbeitungsliste: Button `Aenderungen in Datenbank uebernehmen` ist linksbuendig unter der Tabelle.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.95

### Features

- Ausreisserliste: neue Spalte `Klasse` (primaer/sekundaer) inkl. Filter; `counter decrease` ist primaer und Rueckspruenge werden als sekundaer markiert.
- Ausreisserliste: Details (Davor/Danach) werden beim Scan automatisch geladen und pro Eintrag als eingeklappter Block angezeigt.
- Ausreisserliste: Buttons fuer Spaltenbreite/Liste/Staging sind jetzt oberhalb der Tabelle; `Aenderungen ... uebernehmen` steht unterhalb.
- Dashboard Ableitungsgraph: Legende unter dem Plot.

### Fixes

- Bearbeitungsgraph: Zeitangaben sind konsistent zur Bearbeitungsliste (lokale Client-Zeit, keine 1h Verschiebung).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.94

### Features

- Bearbeitungsliste: Anzeige der geprueften Punkte (Analyse) + Ausreisseranzahl.
- Bearbeitungsgraph: Anzeige `DB Punkte gesamt/bereich` und `Ausreisser gesamt/bereich`.
- Graph: Klick auf einen Punkt zeigt einen roten Tooltip (Zeit + Wert) im lokalen Format.

### Fixes

- Bearbeitungsgraph: Hover/Axis Zeitformat ist konsistent zur Tabellenanzeige (lokale Client-Zeit).
- Ableitung: Hintergrund + Farbleiste koennen gleichzeitig aktiv sein.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.93

### Features

- Dashboard Graph: Anzeige der verwendeten Punkte (Sichtbereich/Anzeige/Gesamt im Filterbereich).
- Ableitungs-Graph: Outlier-Markierung (rote Punkte) mit einstellbarer Schwelle (Slider).

### Fixes

- Ableitung-UI: Hintergrund und Farbleiste sind jetzt gegenseitig exklusiv (keine Doppelaktivierung).
- Zoom: Ableitung/Farbleiste folgen dem Hauptgraph, sind aber nicht mehr separat zoombar.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.92

### Features

- Dashboard Graph: Details-Modus `Dynamisch/Manuell` (Manuell mit Punktdichte 1..100% und schnellem Redraw ohne neue Query).
- Dashboard Graph: Ableitung-Visualisierung per Checkbox:
  - Hintergrundfaerbung (gruen->rot nach Staerke)
  - Farbleiste unter dem Graph
  - zusaetzlicher Ableitungs-Graph (absolut oder signiert)
- Dynamisches Sampling: erkennt grosse Spruenge (Schwellwert aus den Ausreisser-Settings je Einheit) und laedt um Spruenge herum mehr Rohpunkte nach; Sprungbereiche werden markiert.
- Settings: zusaetzliche Einheiten fuer Sprungschwellen (unit=max step) + `Sprung-Polster (Intervalle)` + `Manual max. Punkte (Dashboard Graph)`.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.91

### Features

- Dashboard: Graph Query kann zwischen Dashboard und Bearbeitungsgraph umgeschaltet und kopiert werden.
- Export: neue Seite "Export" (Text/Excel) inkl. Download; Zeitstempel im lokalen Browser-Format.
- Import: neue Seite "Import" (Browser-Upload) inkl. Analyse, optional Range-Backup vor Import und optional Delete-im-Zeitraum (mit Confirm Phrase).
- Settings: neues UI-Setting `Tabellenzeilen Hoehe (px, Backup)`; UI-Bereich ist pro Seite (Dashboard/Statistik/Backup/...) gruppiert.

### Fixes

- Sidebar Statuspanel: besseres horizontales Scrollen fuer lange Statuszeilen; Head zeigt jetzt ein Sanduhr-Icon.
- Statistik: "Statistik laden" spiegelt Start/Progress/Done/Fail in der Sidebar-Statusbox.

### Maintenance

- Docker: `tzdata` installiert fuer client-lokale Zeitformatierung (Export/Import).
- Tested with Home Assistant Core: unknown

## 1.11.90

### Fixes

- Dashboard: Fehlersuche Ausreisser funktioniert jetzt auch nach Seitenreload/Cache-Restore (Measurement/Field werden wiederhergestellt bzw. neu aufgeloest).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.89

### Features

- Dashboard: neue Box "Graph Query" inkl. Button `Query kopieren`.
- Einstellungen: neue Limits `Query max. Punkte (Dashboard Graph)` und `Raw max. Punkte` (Downsampling/Limit) fuer grosse Abfragen.
- History: Tabelle zeigt friendly_name/entity_id/_measurement/_field in separaten Spalten.

### Fixes

- Sidebar Statuspanel: lange Eintraege umbrechen/scrollen sauberer (kein Layoutbruch).

### Maintenance

- API: Query/Raw Limits sind jetzt konfigurierbar (statt hardcoded 5000/20000).
- Tested with Home Assistant Core: unknown

## 1.11.88

### Features

- Dashboard: Bearbeitungsliste refactor mit Spalten `Aktion` + `Neuwert` (staging) und Toolbar-Aktionen (Details/Bearbeiten/Multi).
- Dashboard: Details-Panel ist separat scrollbar; `Uebernehmen` setzt den selektierten Detailwert als Neuwert.
- Dashboard: optionaler Bearbeitungs-Graph rechts (DB-Punkte im Zeitfenster min/max +/- Puffer; markiert Bearbeitungspunkte; Split-Resizer).
- Dashboard: Daten bleiben beim Seitenwechsel erhalten (sessionStorage Cache).
- History: neuer Menuepunkt mit Filter + Rollback (selektiert oder Zeitraum-Preset; mit Sicherheitsphrase).

### Fixes

- UI: Raw Daten Tabelle nutzt Monospace-Font fuer stabilere Zahlendarstellung.
- Status: Ausreisser-Meta wird in das Sidebar-Statuspanel gespiegelt.

### Maintenance

- API: neue Endpoints `POST /api/apply_changes`, `POST /api/window_points`, `GET /api/history_list`, `POST /api/history_rollback`.
- Tested with Home Assistant Core: unknown

## 1.11.87

### Features

- Backup/Restore: Buttons neben Volltextsuche: `Alle` (Filter leeren) und `aus Dashboardauswahl` (friendly_name/entity_id uebernehmen).
- Statistik: neuer Bereich "Statistik Influx Datenbank" mit `Refresh` (best-effort Infos ueber Health/Version/IP/Buckets).
- Statistik: Query Details hat jetzt einen Button `Query kopieren`.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.86

### Features

- Dashboard: Raw Daten koennen optional dem Zoom folgen (Checkbox "Zeit gefuehrt durch Graph").
- Bearbeitungsliste: "Details" aktiviert automatisch "Bearbeiten" (damit "nehmen" direkt geht).

### Fixes

- Details/Ausreisser: Zeitstempel behalten jetzt Millisekunden (keine ungewollte Rundung auf .000).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.84

### Features

- Dashboard: kein automatisches Neuladen beim Oeffnen; Daten werden nur per `Aktualisieren` geladen.
- Dashboard: Status unter `Aktualisieren` bleibt sichtbar und wird in das Sidebar-Statuspanel gespiegelt.
- Bearbeitungsliste: bleibt leer bis `Fehlersuche Ausreisser` ausgefuehrt wird.

### Fixes

- UI: Dashboard-Content ist wieder scrollbar (Desktop).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.83

### Features

- Backup: Erstellung laeuft als Background-Job (Fortschritt + Abbruch; partielle Dateien werden bei Abbruch geloescht).
- Status: Backup/Restore Aktionen werden im Sidebar-Statuspanel angezeigt.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.82

### Features

- Sidebar: Status-Panel zeigt laufende Aktionen und letzte Meldung.

### Maintenance

- Doku: Handbuch + README mit aktuellen Screenshots aktualisiert.
- Tested with Home Assistant Core: unknown

## 1.11.81

### Features

- Punktliste: neuer Button `Details` pro Zeile (aktiv bei Selektion) zeigt Davor/Danach-Liste direkt unter der Zeile.
- UI: Auf-/Zuklappen von Bereichen wird jetzt automatisch pro Seite gespeichert und beim naechsten Oeffnen wiederhergestellt.

### Bug Fixes

- Punktliste: Ueberschreiben aktualisiert auch Ausreisser-Ansicht sofort.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.80

### Features

- Punktliste: Button in Spalte `Neu` heisst jetzt `Ueberschreiben`.
- Punktliste: pro Datenpunkt History der letzten 3 Ueberschreibungen (Datum/Alt/Neu) inkl. `restore`.

### Bug Fixes

- Punktliste: nach Ueberschreiben wird der neue Wert sofort in der Tabelle aktualisiert.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.79

### Bug Fixes

- Dashboard: Bearbeiten funktioniert auch bei numerischen String-Werten aus der API (Edit-Mode laesst sich wieder aktivieren).

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.78

### Bug Fixes

- Dashboard: repariert JS-Fehler (entfernte Bearbeitungslisten-Referenz), so dass `Aktualisieren` wieder laeuft.

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.77

### Features

- Dashboard: Filterliste und Bearbeitungsliste zu einer einzigen Tabelle (Punktliste) zusammengefuehrt; Bearbeitung pro Zeile per Button (kein Doppelklick).
- Punktliste: Bearbeitungsspalten werden automatisch eingeblendet, sobald mindestens ein Eintrag im Bearbeitungsmodus ist.

### Bug Fixes

- (keine)

### Maintenance

- Tested with Home Assistant Core: unknown

## 1.11.74

### Features

- Links: Standard-Repository-URLs auf GitHub umgestellt (UI + Add-on Metadaten).

### Bug Fixes

- (keine)

### Maintenance

- Dokumentation: entfernt verbleibende Gitea-Hinweise.

## 1.11.73

### Features

- UI: PayPal Donate URL ist jetzt in den Einstellungen parametrierbar (Sidebar Button verweist darauf).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.72

### Features

- UI: PayPal-Donate Button im Sidebar auf das "paypal-donate-button" Layout umgestellt.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.71

### Features

- UI: neue Seite "Jobs" (laufende Background-Jobs anzeigen und abbrechen).

### Bug Fixes

- Statistik: Jobs haengen nicht mehr durch Lock-Deadlocks (Start/Status bleiben nicht mehr auf pending).

### Maintenance

- Logging: job_start/job_cancel werden im Logfile nachvollziehbar protokolliert (inkl. IP/UA).

## 1.11.70

### Features

- Logs: neuer Button "Export" fuer ein Debug-Bundle (Config+Diag+Logs+Client-Fehler).

### Bug Fixes

- UI: "Failed to fetch" wird jetzt als client_error ins Logfile geschrieben.

### Maintenance

- (keine)

## 1.11.69

### Features

- UI: Menuepunkt "Logs" ist jetzt unter "Restore" einsortiert.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.68

### Features

- UI: Spendenlink "Buy me a coffee" im Sidebar hinzugefuegt.

### Bug Fixes

- Statistik: verhindert versehentliches Navigieren/405 durch explizite Button-Typen.

### Maintenance

- (keine)

## 1.11.67

### Features

- HA: Add-on/Paneltitel heisst jetzt "InfluxBro".

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.66

### Features

- UI: Sidebar zeigt jetzt die Add-on Version unter "by Thomas Schatz".

### Bug Fixes

- (keine)

### Maintenance

- UI: Entfernt "Writes: yes/no" aus der Sidebar.

## 1.11.65

### Features

- UI: Menuepunkt "Logs" ist jetzt unter "Backup" einsortiert.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.64

### Features

- (keine)

### Bug Fixes

- Einstellungen: behebt JS-Fehler "Cannot set properties of undefined" (Restore Preview-Zeilen Feld).

### Maintenance

- (keine)

## 1.11.63

### Features

- Restore: Live-Status zeigt jetzt Schreib-Zeitpunkt (bis Millisekunden) und Fortschritt in % waehrend des Schreibens.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.62

### Features

- UI: Fehlermeldungen werden zusaetzlich als Popup angezeigt (alle Seiten).
- Restore: Statuszeile zeigt jetzt zusaetzlich aktuellen Zeitpunkt sowie Kontext (Backup/Ziel/Zeitbereich).

### Bug Fixes

- Dashboard: Eigene Werte in der Bearbeitungsliste akzeptieren jetzt auch weniger Kommastellen (z.B. Ganzzahl) und formatieren auf die eingestellten Stellen.

### Maintenance

- (keine)

## 1.11.60

### Features

- (keine)

### Bug Fixes

- Restore: behebt JS-Fehler "startRunUi is not defined" (Status-/Runtime-Anzeige laeuft wieder).
- Restore: entfernt versehentlich doppelt angehaengten Template-Block am Dateiende.

### Maintenance

- (keine)

## 1.11.59

### Features

- Restore: Laufzeit/Status + Details inkl. Write Preview (erste N umgeschriebene Zeilen) bei "Restore ausfuehren".
- Einstellungen: Restore Preview-Zeilen sind konfigurierbar (Default: 5).
- Bearbeitungsliste: Werte werden ohne Rundung angezeigt und immer mit der eingestellten Stellenzahl formatiert.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.58

### Features

- Restore: "Restore ausfuehren" (Backup Copy) verarbeitet Line Protocol korrekt auch bei escaped Spaces in Tags (z.B. friendly_name).

### Bug Fixes

- Restore: Fix "invalid boolean" durch falsches Parsen von Line Protocol in `backup_copy`.

### Maintenance

- (keine)

## 1.11.57

### Features

- Dashboard: Ausreisser-Status zeigt zuerst Fortschritt/Suchbereich und haengt Messstelle/Tags am Ende an.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.56

### Features

- Add-on: /data/share Symlink wird beim Start immer erzwungen (korrigiert alte Zielpfade automatisch).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.55

### Features

- Logs: UI protokolliert Button-Klicks (Seite + data-ui) im Backend-Log.

### Bug Fixes

- Statistik: Haengender Status "Hintergrundabfrage laeuft..." wird beendet, wenn der Job nicht gefunden wird oder Status-Abfrage fehlschlaegt.

### Maintenance

- (keine)

## 1.11.54

### Features

- Dashboard: Ausreisser-Suche zeigt den aktuellen Chunk/Suchbereich und Fortschritt (geprueft bis Zeit / Punkte).

### Bug Fixes

- Ausreisser: API liefert jetzt last_time/last_value fuer chunked Scans.

### Maintenance

- (keine)

## 1.11.53

### Features

- Dashboard: Button "Liste leeren" in der Fehler-/Filtertabelle funktioniert jetzt.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.52

### Features

- Statistik: Statusanzeige zeigt jetzt aktuellen Messwert sowie Gesamtanzahl und Prozent-Fortschritt.

### Bug Fixes

- Statistik: Fix Serienlisten-Builder (Zeilen werden wieder korrekt gefuellt).

### Maintenance

- (keine)

## 1.11.51

### Features

- Dashboard: Ausreisser-Suche zeigt neben dem Timer Messstelle, Suchbereich und aktuelle Zeit.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.50

### Features

- Backup: Buttons in der Aktionen-Zeile sind oben ausgerichtet.
- Dashboard: Fehler-/Filtertabelle hat einen Button "Liste leeren".
- Add-on: /data/share zeigt jetzt auf <code>/config/influxbro</code> (statt <code>/config/homeassistant/influxbro</code>).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.49

### Features

- Statistik: Serienliste wird nicht mehr per Paging mit Vollscan geladen, sondern chunked/streamed mit Timeout-Splitting (robuster fuer Zeitraum "Alle").

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.48

### Features

- Add-on: /data/share wird nach <code>/config/homeassistant/influxbro/</code> gemountet (sichtbar im HA Filebrowser).
- UI: Grosse Listen-Tabellen haben jetzt resizable Spalten und Button "Spaltenbreite automatisch" (Dashboard/Backup/Restore/Statistik).

### Bug Fixes

- Statistik: Hintergrundjob splittet Chunks bei Timeouts weiter auf (robuster fuer Zeitraum "Alle").
- Ausreisser: Scan laeuft immer chunked und bricht grosse Zeitraeume seltener ab.

### Maintenance

- (keine)

## 1.11.46

### Features

- Einstellungen: Neue Checkbox zum globalen Abschalten der Tooltips.

### Bug Fixes

- Dashboard: Entfernt versehentlich gerenderten Resttext am Seitenende.

### Maintenance

- (keine)

## 1.11.45

### Features

- Dashboard: Bei "Query anzeigen" wird jetzt auch angezeigt, wann der Query ausgeloest wurde.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.44

### Features

- Dashboard/Statistik: stddev und p05/p50/p95 werden nicht mehr automatisch berechnet (schneller, weniger Last).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.43

### Features

- Dashboard: Fehler-/Filtertabelle zeigt eine kompakte Statuszeile (Zeitraum Graph, Eintraege, Sort, Filter, Zeit, Modus).
- Dashboard: Fehlersuche-Ausreisser Statusanzeige bleibt nach Abschluss sichtbar.
- Dashboard: Neuer DB-Scan Preset "nicht ansteigende Spruenge" (findet fallende Werte gegenueber dem Vorwert).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.42

### Features

- Backup: Standard-Backup-Pfad ist jetzt unter <code>/config/homeassistant/influxbro/backup</code> (im HA Filebrowser sichtbar).

### Bug Fixes

- Backup: Beim Update werden vorhandene Backups aus <code>/data/backups</code> automatisch nach <code>/config/homeassistant/influxbro/backup</code> migriert und der alte Ordner geloescht.

### Maintenance

- (keine)

## 1.11.41

### Features

- Backup: Unter den Backup-Buttons wird der jeweilige Zeitraum angezeigt (Full/Zoom/Auswahl).
- Backup: Laufzeit/Sanduhr wird jetzt auch bei den Zeitbereich-Backups angezeigt.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.40

### Features

- Statistik: Button heisst jetzt "Statistik laden".

### Bug Fixes

- Statistik: Fix NameError "total_series is not defined" beim Laden/Na chladen von Detail-Spalten.

### Maintenance

- (keine)

## 1.11.39

### Features

- Dashboard: Button "Abbruch" bricht laufende Abfragen ab; zuletzt genutzter Query ist ausklappbar sichtbar.
- Backup: Zuletzt genutzter Query der Backup-Erstellung ist ausklappbar sichtbar.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.38

### Features

- UI: Tooltips zeigen jetzt immer den Elementnamen zusaetzlich in Klammern.

### Bug Fixes

- Dashboard: Reset startet keine Tag-Value Requests mehr (keine "Lade friendly_name" Timeouts nach Reset).

### Maintenance

- (keine)

## 1.11.37

### Features

- UI: Tooltips zeigen kurze Beschreibungen fuer Buttons und Felder auf allen Seiten.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.36

### Features

- Dashboard: Fehlersuche Ausreisser zeigt jetzt eine eigene Statusanzeige (Sanduhr + laufende Zeit).
- Dashboard: Buttons fuer Ausreisser-Scan/Reset sind direkt unter den Filtern; "in Bearbeitungsliste uebernehmen" steht unter der Tabelle.
- Dashboard: Bearbeitungsliste Buttons umsortiert und Schreib-Button heisst jetzt "Aenderungen in Datenbank uebernehmen" (ganz unten).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.35

### Features

- Dashboard: Datenabfrage (Graph/Tabelle/Stats/Raw) erfolgt nur noch, wenn `entity_id` gesetzt ist.

### Bug Fixes

- Dashboard: Reset bricht auch geplante Hintergrundabfragen ab und laedt keine Daten nach, wenn Filter leer sind.

### Maintenance

- (keine)

## 1.11.34

### Features

- Dashboard: Fehlermeldungen werden immer mit Zeitstempel angezeigt.
- Dashboard: Statusanzeige (Spinner + laufende Zeit) wird bei Abfragen automatisch eingeblendet.
- Dashboard: Reset-Button bricht laufende Abfragen ab und setzt Filter zurueck (Zeitraum bleibt erhalten).

### Bug Fixes

- Dashboard: Auswahl-Listen (Datalist) sind robuster bei schnellen Filteraenderungen (AbortController pro Request-Gruppe).

### Maintenance

- (keine)

## 1.11.33

### Features

- Dashboard: Bei mehrfachen Treffern zeigt eine Liste die moeglichen entity_id/friendly_name inkl. Zeitraum (von/bis) und Anzahl.
- Backup: Button "Messwert aus Dashboard uebernehmen" uebernimmt die aktuelle Auswahl aus dem Dashboard.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.32

### Features

- Backup/Restore: Tabellen harmonisiert (inkl. Zeitraum-Spalte) und Zeiten werden in lokaler Browserzeit angezeigt.
- Backup: Fullbackup zeigt jetzt eine laufende Statusanzeige wie Dashboard.
- Einstellungen: Backup-Verzeichnis ist jetzt konfigurierbar (unter /data).

### Bug Fixes

- Backup: Messwert-/Zeitenanzeige um 1h versetzt behoben (UTC wird als lokale Zeit formatiert).

### Maintenance

- (keine)

## 1.11.31

### Features

- Backup: Auswahl ist jetzt kaskadiert (measurement -> friendly_name -> entity_id) und waehlt bei mehreren entity_ids automatisch den ersten Treffer.
- Backup: Auswahlfelder (measurement, Messwert, entity_id, Zeitraum) sind nebeneinander; neben jedem Feld steht die Anzahl der verfuegbaren Eintraege.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.30

### Features

- Dashboard: "Aktualisieren" zeigt jetzt eine laufende Anzeige und misst Abfragezeit (Query + Gesamt).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.29

### Features

- Dashboard: Preset-Auswahl fuer DB-Scan in der Fehler-/Filtertabelle (Filter frei, Counter-Ausreisser, Grenzen, NULL, 0, alle Werte).

### Bug Fixes

- UI: Sidebar-Menue im Dashboard hat jetzt die gleiche Schriftgroesse wie die anderen Seiten.

### Maintenance

- (keine)

## 1.11.28

### Features

- UI: PayPal Donate-Link ist jetzt im Menue unter "by Thomas Schatz".
- UI: Auswahl zeigt jetzt die Anzahl der verfuegbaren Eintraege (measurement/friendly_name/entity_id) auf Dashboard/Backup/Restore/Statistik.
- Backup: Liste zeigt zusaetzlich friendly_name und entity_id als Spalten.

### Bug Fixes

- Dashboard/Backup/Restore: Auswahl folgt friendly_name -> entity_id (bei mehreren entity_ids wird die erste gesetzt).

### Maintenance

- (keine)

## 1.11.27

### Features

- UI: Auswahl-Filter (measurement/friendly_name/entity_id) sind jetzt als eine Eingabebox mit Vorschlaegen (Datalist) umgesetzt (Dashboard/Backup/Restore).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.26

### Features

- UI: "Auswahl" ist jetzt auch auf Statistik/Backup/Restore ein- und ausklappbar (wie Dashboard).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.25

### Features

- Statistik: _field Filter ist jetzt eine Auswahl (Datalist) wie die anderen Filter und bleibt vorbelegt mit "value".

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.24

### Features

- Statistik: Entfernt das langsame "counting" (Vorzaehlen) und zeigt keinen Prozentbalken/Restzeit mehr.

### Bug Fixes

- Statistik: Abbrechen reagiert schneller durch kleinere per-query Timeouts im Background-Job.

### Maintenance

- (keine)

## 1.11.23

### Features

- Statistik: erweiterte Filter (measurement/friendly_name/entity_id) und Spaltenauswahl mit "Nachladen" (markiert / alle im Filter).

### Bug Fixes

- (keine)

### Maintenance

- markdownlint: MD032 deaktiviert.

## 1.11.22

### Features

- (keine)

### Bug Fixes

- Statistik: Background-Job Fehler werden jetzt ins Log geschrieben (inkl. letztem Query-Label; Query gekuerzt).

### Maintenance

- (keine)

## 1.11.21

### Features

- (keine)

### Bug Fixes

- Statistik: behebt einen Runtime-Fehler beim Erzeugen der Flux-Reduce Query (f-string Klammern/"seen" NameError).

### Maintenance

- (keine)

## 1.11.20

### Features

- Statistik: Hintergrundabfrage laeuft jetzt in Happen (Serien/Zeitchunks), um lange Einzelqueries und Timeouts zu vermeiden.
- Statistik: Info zeigt laufende Aktion, grobe Restzeit und optional ausklappbar den zuletzt ausgefuehrten Query.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.19

### Features

- Statistik: Tabelle bleibt sichtbar waehrend Hintergrundabfrage laeuft; letztes Ergebnis wird beim Zurueckkehren zur Seite automatisch wiederhergestellt.
- Statistik: Restzeit-Schaetzung im Status (falls Prozent-Fortschritt verfuegbar).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.18

### Features

- Logs: neue Option "Influx Query protokollieren" (Query-Strings werden nur in TRACE geloggt, und nur wenn aktiviert).
- Restore: Quelle->Ziel wird zu "Restore ausfuehren"; Button zum Uebernehmen der Quell-Namen ins Ziel; Infofeld + optionaler Pruef-Query fuer den Influx Explorer.
- Tooltips: entfernt Debug-Koordinaten; Tooltips zeigen jetzt Name + kurze Hilfe (wo vorhanden).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.17

### Features

- Statistik: Gesamtstatistik laeuft jetzt als Hintergrundjob (Statusanzeige + abbrechbar) um Timeouts bei grossen Zeitraeumen zu vermeiden.
- Statistik: Anzeige von Laufzeit waehrend der Abfrage; Spaltenbreiten sind per Drag anpassbar und speicherbar.
- UI: Globales Toolbar (Alle oeffnen/Alle schliessen/Darstellung speichern) fuer einklappbare Bereiche auf allen Seiten.
- Dashboard: Bearbeitungsliste hat pro Zeile einen Button "Daten uebernehmen" (Dialog wie Sammelschreiben).
- Dashboard: Graph-Zoom wird beim Seitenwechsel wiederhergestellt.
- Einstellungen: Bereiche UI/Logs/Schreiben neu strukturiert und weiter unterteilt (einklappbar).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.16

### Features

- Schreiben/Loeschen: Freigabe ist jetzt eine UI-Einstellung (`writes_enabled`) und ist standardmaessig erlaubt (Add-on Option `allow_delete` entfernt).
- Statistik: "Gesamtstatistik laden" laedt automatisch alle Serien (weiterhin 10 pro Influx-Request) und Details werden direkt mitgeladen.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.15

### Features

- Logs: Log-Stufenprofile ERROR/DEBUG/TRACE (TRACE loggt zusaetzlich interne Abfragen/Details).
- Logs: Logs-Seite mit Anzeige-Filter (ERROR/DEBUG/TRACE) und Server-Logstufe umschaltbar.
- Bearbeitungsliste: Schreiben zeigt einen Dialog mit Ueberschreib-Vorschau und einklappbarem Influx-Query zum Gegenpruefen.

### Bug Fixes

- Bearbeitungsliste: Hinweis "Writes are disabled..." wird unter dem Schreiben-Button angezeigt (wenn allow_delete aus ist).

### Maintenance

- (keine)

## 1.11.14

### Features

- (keine)

### Bug Fixes

- Raw Daten: "Kopieren" und "Query kopieren" nutzen jetzt einen robusten Clipboard-Fallback (funktioniert auch in restriktiven/embedded Browser-Kontexten).

### Maintenance

- (keine)

## 1.11.13

### Features

- Raw Daten: zeigt den genutzten Influx Query-String an und bietet "Query kopieren" zum direkten Test im Influx Explorer.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.12

### Features

- Dashboard: aufklappbare Tabelle "Raw Daten (DB)" direkt unter dem Graph (folgt dem Graph-Fenster, aktualisiert bei Zoom und bei "Aktualisieren").
- Raw Daten: Kopieren in die Zwischenablage (Zeitformat: DD.MM.YYYY HH:MM:SS) und "Mehr laden" bei grossen Zeitfenstern.
- API: neuer Endpoint `POST ./api/raw_points` fuer direkte DB-Abfrage im Graph-Zeitfenster.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.11

### Features

- Logs: eigenes rotierendes Logfile unter <code>/data/influxbro.log</code> (groessen- und altersbegrenzt, konfigurierbar).
- Logs: Log-Viewer kann Logfile anzeigen (Fallback wenn Supervisor-Logs nicht verfuegbar sind).
- Einstellungen: Logfile/Rotation/Level/HTTP-Request-Logs konfigurierbar.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.10

### Features

- Dashboard: Versionsnummer wird oben im Header angezeigt.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.9

### Features

- UI: Tooltips zeigen zusaetzlich Element-Groesse und Position (size/vp/page) zur UI-Diagnose.

### Bug Fixes

- UI: Tabellenzeilen-Dichte konsistent gemacht (Zeilenhoehe max. +20% ueber Schriftgroesse).

### Maintenance

- Einstellungen: Hinweistext zur Tabellen-Dichte ergaenzt.

## 1.11.8

### Features

- (keine)

### Bug Fixes

- Graph: numerische String-Werte werden wie in der Tabelle geplottet (Punktanzahl konsistenter).

### Maintenance

- (keine)

## 1.11.7

### Features

- Dashboard: Statistik aufgeteilt (Gesamtstatistik unter Auswahl, Zeitraum-Statistik direkt unter Graph).
- Filtertabelle: Button "Alle Werte" (zeigt alle Werte im Graph-Zeitbereich ohne Werte-Filter).
- Bearbeitungsliste: Nachbarwerte (n davor/n danach) unterhalb der Liste; n ist konfigurierbar.
- Restore: nur noch Ja/Nein Bestaetigung (kein Phrase-Input).

### Bug Fixes

- Logs: Supervisor-Logs robuster (Fallback ueber Add-on slug, falls /addons/self/logs fehlschlaegt).

### Maintenance

- Markdownlint: MD013 in `.markdownlint.json` deaktiviert.

## 1.11.6

### Features

- Statistik: Gesamtstatistik laedt schrittweise (Serien seitenweise, Details seitenweise/alle) mit Status + Balken.
- Einstellungen: Tabellenzeilen-Hoehe (px) konfigurierbar.

### Bug Fixes

- (keine)

### Maintenance

- Markdownlint: Repo-Config `.markdownlint.json` (weniger Noise in VSCode).

## 1.11.5

### Features

- Handbuch: als eigene HTML-Seite mit Inhaltsverzeichnis links (Markdown Rendering).
- Restore: neue UI (Backup-Liste mit Volltextsuche, Ziel-Auswahl wie Dashboard, Copy Quelle->Ziel, Restore gleiche Serie, optionaler Zeitfilter).
- Backup: Messwert-Anzeige mehrzeilig + Multi-Select in Backup-Liste.

### Bug Fixes

- Gesamtstatistik: Flux `reduce()` kompatibel (Parameter `accumulator`).
- Logs: Supervisor-Logs Pfad korrigiert (kein `/supervisor/api/...`).

### Maintenance

- Statistik: Controls sauber ausgerichtet.

## 1.11.4

### Features

- Dashboard: Statistik "Zeitraum (Graph/Tabelle)" folgt dem aktuell im Graph selektierten Bereich (Zoom/Range-Slider).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.3

### Features

- UI: Merkt sich GUI-Eingaben (non-sensitive) in Browser storage ueber App-Wechsel/Reload/Update hinweg.
- Dashboard: Graph mit Rahmen und maximaler Breite; Plot-Hoehe bleibt per Drag einstellbar.
- Dashboard: Filter-/Bearbeitungstabellen kompaktere Zeilenhoehe.

### Bug Fixes

- Statistik: Flux query braces korrekt escaped ("seen is not defined" behoben).

### Maintenance

- (keine)

## 1.11.2

### Features

- Statistik: Server-side Aggregation (keine Rohpunkte zur App streamen) + neuer `_field` Filter (Default: `value`).
- Statistik: Tabellenlayout/Spaltenbreiten verbessert + globaler Button "Loeschen" (nur Ansicht).
- Graph: Plot-Hoehe per Ziehen anpassbar (Dashboard).
- Navigation: Branding vergroessert + "by Thomas Schatz".
- Einstellungen: UI und Ausreisser getrennte aufklappbare Bereiche.
- Handbuch: erweitert (Elemente beschrieben) + Screenshot-Platzhalter.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.11.1

### Features

- Statistik: Statusfeld als linksbuendiges Feld + mehr Live-Infos (Zeit/Rate/Fortschritt/Aktuell).
- Statistik: Details-Spalten (count/min/max/mean) erst per "Detail" Button pro Zeile; Button "Lade alle Details".
- Statistik: Anzeige Zeilenanzahl ueber der Tabelle; Loeschen-Button pro Zeile (nur Ansicht).
- Einstellungen: Bereiche einklappbar.

### Bug Fixes

- Logs: Supervisor-Logs nur noch ueber "self" Pfade (kein slug-mismatch mehr).

### Maintenance

- (keine)

## 1.11.0

### Features

- Statistik: Gesamtstatistik als Hintergrund-Job (kein Request-Timeout) mit Fortschritt + Abbrechen.
- Statistik: Zeitraum-Auswahl (wie Dashboard), Default: letzte 30 Tage.
- Backup: Zusaetzlicher Zeitbereich-Backup ueber Zeitraum-Auswahl (neben Zoom-Backup) inkl. von/bis Anzeige.
- UI: Donate-Link im Dashboard und in der Doku.

### Bug Fixes

- Logs: Supervisor-Log-Response robuster (JSON-Wrapper) + Parameter `lines`.
- Graph: Range-Slider Updates werden beim Zoomen korrekt erkannt.

### Maintenance

- Lizenz: MIT (`LICENSE.md`).
- UI: Tooltips/`data-ui` werden konsistent ergaenzt.

## 1.10.0

### Features

- Graph: Y-Achse skaliert automatisch beim Zoomen (sichtbarer Bereich).
- Backup: Fullbackup umbenannt + Zeitbereich-Backup (aktueller Graph-Ausschnitt) + Backup-Pfad angezeigt.

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.9.0

### Features

- Ausreisser: Raw-Fehlersuche im aktuellen Graph-Zeitraum (NULL/0/Grenzen/Counter-Max-Sprung) mit Optionen.
- Einstellungen: Maximaler Sprung je Einheit (W/kW/Wh/kWh) vorbelegt fuer typischen Haushalt.

### Bug Fixes

- Logs: Supervisor-API Pfade robuster + `supervisor_api` aktiviert.

### Maintenance

- (keine)

## 1.8.0

### Features

- Statistik: Gesamtstatistik auf eigener Seite im Menu.
- Dashboard: Bereiche (Auswahl/Graph/Fehler-/Filtertabelle/Bearbeitungsliste/Statistik) klappbar; Default ueber Einstellungen.

### Bug Fixes

- (keine)

### Maintenance

- UI: Filter aktiv als Checkbox; Verb-Logik zwischen Links/Rechts.
- UI: Filtertabelle laedt automatisch beim Seitenstart (wenn Auswahl vorhanden).

## 1.7.0

### Features

- Dashboard: Gesamtstatistik Tabelle fuer alle Messwerte (Suche + sortierbare Spalten).

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.6.0

### Features

- UI: Linkes Menu (Dashboard/Logs/Backup/Restore/Info/Handbuch/Einstellungen).
- Backup/Restore: Sicherung fuer einen Messwert (alle Werte), inkl. Liste/Loeschen/Restore.
- Handbuch: In-App Doku aus `MANUAL.md`.
- Info: Release Notes aus `CHANGELOG.md` + konfigurierbarer Repo-Link.

### Bug Fixes

- HA: `entity_id` ohne Domain wird automatisch als `sensor`/`binary_sensor`/... aufgeloest.

### Maintenance

- (keine)

## 1.5.2

### Features

- (keine)

### Bug Fixes

- Debug: HA Info Fehlermeldung wird in der Statistik angezeigt; zusaetzlicher Endpoint `/api/ha_debug`.

### Maintenance

- (keine)

## 1.5.1

### Features

- UI: Suchfeld steht links neben dem Auswahlfeld; Breite konfigurierbar.

### Bug Fixes

- (keine)

### Maintenance

- UI: Zusaetzliche `data-ui` Namen an Elementen fuer eindeutige Referenzen.

## 1.5.0

### Features

- UI: Workflow von oben nach unten; Statistik als kleine Tabelle mit Toggle.
- UI: Konfigurierbare Schrift-/Checkboxgroessen und Filterbreiten.
- UI: Plotly Marker (Messpunkte) zuschaltbar.

### Bug Fixes

- (keine)

### Maintenance

- HA: Zeigt `device_class`/`state_class` via `SUPERVISOR_TOKEN`.
- UI: "Daten loeschen" Bereich entfernt.

## 1.4.0

### Features

- Tabelle kann optional zeitlich vom Graph-Zoom gefuehrt werden.
- Bearbeitungsliste fuer selektierte Datenpunkte inkl. Undo und "alle uebernehmen".

### Bug Fixes

- (keine)

### Maintenance

- (keine)

## 1.3.0

### Features

- Plotly.js Graph (Zoom/Pan/Range-Slider) statt Canvas.

### Bug Fixes

- Add-on changelog file for Home Assistant install/upgrade dialog.

### Maintenance

- (keine)

## 1.2.1

### Features

- (keine)

### Bug Fixes

- Add-on changelog file for Home Assistant install/upgrade dialog.

### Maintenance

- (keine)

## 1.2.0

### Features

- Zeitraum "Alle" (filtert alle existierenden Daten).
- UI: Zeitraum wird als "von/bis" angezeigt (tt.mm.jjjj hh:mm:ss).
- UI: Graph mit einfacher Zeitachse.

### Bug Fixes

- (keine)

### Maintenance

- Safety: Delete ist fuer Zeitraum=Alle gesperrt.
