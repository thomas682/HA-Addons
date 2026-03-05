# Changelog

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

## 1.3.0-beta.2

### Features

- (keine)

### Bug Fixes

- Add-on changelog file for Home Assistant install/upgrade dialog.

### Maintenance

- (keine)

## 1.3.0-beta.1

### Features

- Beta: Plotly.js Graph (Zoom/Pan/Range-Slider) statt Canvas.

### Bug Fixes

- (keine)

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
