# Changelog

<!-- markdownlint-disable MD024 MD013 -->

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

## 1.11.3

### Features
- UI: Merkt sich GUI-Eingaben (non-sensitive) in Browser storage ueber App-Wechsel/Reload/Update hinweg.
- Dashboard: Graph mit Rahmen und maximaler Breite; Plot-Hoehe bleibt per Drag einstellbar.
- Dashboard: Filter-/Bearbeitungstabellen kompaktere Zeilenhoehe.

### Bug Fixes
- Statistik: Flux query braces korrekt escaped ("seen is not defined" behoben).

### Maintenance
- (keine)

## 1.11.4

### Features
- Dashboard: Statistik "Zeitraum (Graph/Tabelle)" folgt dem aktuell im Graph selektierten Bereich (Zoom/Range-Slider).

### Bug Fixes
- (keine)

### Maintenance
- (keine)

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
