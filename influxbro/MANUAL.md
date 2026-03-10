# InfluxBro Handbuch

[![Donate with PayPal](https://raw.githubusercontent.com/stefan-niedermann/paypal-donate-button/master/paypal-donate-button.png)](https://www.paypal.com/donate/?hosted_button_id=ZWZE3WM4NBUW6)

InfluxBro hilft dir, InfluxDB-Zeitreihen aus Home Assistant zu durchsuchen, auszuwerten, zu sichern und bei Bedarf Werte gezielt zu korrigieren.

Hinweis: In Home Assistant heisst das Add-on/Panel "InfluxBro".

Dieses Handbuch ist absichtlich sehr konkret: Jedes sichtbare Element in der GUI wird beschrieben, damit du immer weisst, wofuer es ist.

## Screenshots

Aktuelle UI (Beispiele):

### Uebersicht (Dashboard)

![InfluxBro Uebersicht](<images/InlfuxBro Übersicht.png>)

### Einstellungen

![Einstellungen](images/Einstellungen.png)

### Backup

![Backup](images/Backup.png)

### Restore

![Restore](images/Restore.png)

### Logs

![Logs](images/LOG.png)

### Jobs

![Jobs](images/Jobs.png)

### Statistik

![Statistik](images/Statistik.png)

## Navigation

Links findest du die Bereiche:

- Dashboard: Messwerte auswaehlen, Graph/Tabelle ansehen, Ausreisser finden und Werte direkt in der Bearbeitungsliste bearbeiten.
- Statistik: Gesamtstatistik ueber viele Serien anzeigen.
- Backup: Backups fuer einen einzelnen Messwert erstellen und verwalten.
- Restore: Ein vorhandenes Backup fuer einen Messwert wiederherstellen.
- Logs: Add-on Logs von InfluxBro ansehen (Menuepunkt ist unter Restore einsortiert).
- Jobs: Laufende Background-Jobs ansehen (Statistik/Restore) und abbrechen.
- Info: Release Notes + Repository-Link.
- Handbuch: Diese Dokumentation.
- Einstellungen: Influx-Verbindung und UI-Parameter konfigurieren.

Im Sidebar-Kopf wird ausserdem die aktuell laufende Add-on Version angezeigt.

## Installation in Home Assistant

1) Add-on Repository hinzufuegen

- Home Assistant: `Einstellungen -> Add-ons -> Add-on Store`
- Oben rechts: `... -> Repositories`
- Repository-URL eintragen: `https://github.com/thomas682/HA-Addons`

2) Add-on installieren und starten

- Add-on `InfluxBro` aus dem Add-on Store auswaehlen
- `Installieren` -> `Starten`
- Optional aber empfohlen: Schalter `In Seitenleiste anzeigen` aktivieren (damit InfluxBro links in der Seitenleiste erscheint)

3) Web UI oeffnen

- Im Add-on: `Open Web UI` (Ingress)

4) InfluxDB konfigurieren

- In der InfluxBro UI: `Einstellungen`
- Optional: YAML Import (Abschnitt "Parametrierung aus Home Assistant YAML")
- `Influx Verbindung testen` -> `Speichern`

## Dashboard (typischer Ablauf)

### 1) Messwert auswaehlen

- `_measurement (Filter)`: interne Messreihe (Influx Measurement) filtern.
- `Messwert (Klartext / friendly_name)`: den sichtbaren Namen aus HA auswaehlen.
- `entity_id (optional)`: falls mehrere Entities denselben Namen haben, hier eingrenzen.

Weitere Elemente:

- `Erweitert: Measurement / Field`: zeigt die intern aufgeloesten Werte `_measurement` und `_field`.
- `Aktualisieren`: laedt Graph und Statistik fuer den aktuellen Zeitraum.
- `Donate`/`PayPal`: Link zur freiwilligen Unterstuetzung.
- Zusaetzlich gibt es einen "Buy me a coffee" Spendenlink.

Tipp: Wenn du mit der Maus ueber einem Feld bleibst, zeigt der Tooltip den internen Feldnamen (z.B. `filter.friendly.select`). Damit kannst du mir exakt sagen, welches Feld du meinst.

Hinweis: Zeitstempel werden im gesamten UI inklusive Millisekunden angezeigt.

### 2) Zeitraum setzen

- `Zeitraum (Graph/Tabelle)`: z.B. 24h, 7d, oder `Alle`.
- Bei `Benutzerdefiniert`: Von/Bis setzen (lokale Zeit).

### 3) Aktualisieren

- Erst mit `Aktualisieren` werden Graph und Statistik geladen.
- Die Bearbeitungsliste bleibt dabei leer und wird erst durch `Fehlersuche Ausreisser` gefuellt.

## Graph

- Zoom/Pan ist moeglich.
- Option `Messpunkte markieren`: schaltet runde Marker ein/aus.
- Ziehen der Groesse: Unter dem Plot gibt es einen horizontalen Griff. Ziehen nach oben/unten aendert die Plot-Hoehe.

Graph Query:

- Bereich `Graph Query`: zeigt den zuletzt genutzten Influx Query-String (aus Dashboard-Abfragen).
- Button `Query kopieren`: kopiert den Query in die Zwischenablage (z.B. fuer den Influx Explorer).
- Auswahl `Dashboard / Bearbeitungsgraph`: schaltet die angezeigte Query-Quelle um (Hauptgraph vs. rechter Bearbeitungsgraph).

Details (Sampling) + Ableitung:

- `Details: Dynamisch`: Graph zeigt weniger Punkte, laedt aber um grosse Spruenge herum automatisch mehr Detail nach (Schwellwert kommt aus den Ausreisser-Settings fuer die Einheit).
- `Details: Manuell`: Punktdichte 1..100% (100% zeigt alle geladenen Punkte bis zum Sicherheitslimit).
- `Ableitung: Hintergrund` und `Ableitung: Farbleiste` koennen gleichzeitig aktiv sein; beide faerben nach Staerke der ersten Ableitung (gruen=0, rot=max), unabhaengig vom Vorzeichen.
- `Ableitungs-Graph`: zeigt die Ableitung zusaetzlich als Graph; umschaltbar `absolut/signiert`.
- `Ableitung Outlier`: Slider-Schwelle; Punkte ueber der Schwelle werden im Ableitungs-Graph rot markiert.

Hinweis (Defaults/Persistenz):

- Beim ersten Start sind die Ableitungs-Checkboxen standardmaessig aktiviert (Hintergrund + Farbleiste + Ableitungs-Graph + absolut).

Bearbeitungsliste + Bearbeitungsgraph:

- Bearbeitungsliste: nach der Ausreisser-Analyse wird angezeigt, wie viele Punkte geprueft wurden und wie viele Ausreisser gefunden wurden.
- Bearbeitungsgraph: zeigt `DB Punkte` und `Ausreisser` jeweils im Format `gesamt / Bereich` (Bereich = aktueller X-Zoom).
- Klick auf einen Punkt im Graph zeigt einen roten Tooltip (Zeit + Wert) im lokalen Client-Format.

Raw Daten (DB):

- Optional kannst du per Checkbox steuern, ob Raw Daten dem Zoom-Bereich im Graph folgen (oder dem Zeitraum aus der Zeitraum-Auswahl).

## Bearbeitungsliste (Ausreisser)

- Linke Checkbox: Zeilen selektieren (Mehrfachauswahl moeglich).
- `Zeit gefuehrt durch Graph`:
  - EIN: Zoombereich im Graph bestimmt die Zeit-Einschraenkung der Tabelle.
  - AUS: Tabelle zeigt wieder den Zeitraum aus der Zeitraum-Auswahl.
- `Filter aktiv`: schaltet den Werte-Filter (Links/Verb/Rechts) an/aus.
- `Grund Filter`: filtert die Ausreisserliste nach Text in der Spalte `Grund`.
- `Klasse`: filtert nach `primaer`/`sekundaer`.
- `Links`/`Verb.`/`Rechts`: einfache Regel um Werte als Fehler zu markieren (z.B. kleiner als 0 oder groesser als 999999).

Details pro Ausreisser:

- Nach `Fehlersuche Ausreisser` werden pro Eintrag automatisch Details (Davor/Ziel/Danach) geladen.
- Die Details sind pro Zeile als eingeklappter Block unterhalb der Zeile sichtbar (standardmaessig zugeklappt).

Bearbeitung in der Bearbeitungsliste:

- Pro Zeile in der Spalte `Aktion`: `Bearbeiten` aktiviert den Bearbeitungsmodus fuer diesen Punkt.
- Sobald mindestens ein Punkt in Bearbeitung ist, werden zusaetzliche Spalten eingeblendet: `Alt`, `Neu`, `aelter`, `juenger`, `eigener Wert`.
- `Bearbeitung aus`: beendet den Bearbeitungsmodus fuer die Zeile. Bei ungespeicherten Aenderungen kommt eine Bestaetigung.
- `Undo`: stellt den Wert auf den Originalwert zurueck (vor der Bearbeitung).
- `Aenderungen in Datenbank uebernehmen`: steht unterhalb der Liste und schreibt/loescht die vorgemerkten Aenderungen.

Ueberschreiben-History:

- Nach dem Ueberschreiben wird der Wert in der Bearbeitungsliste sofort aktualisiert.
- Unter der Zeile erscheint eine eingerueckte History (letzte 3 Ueberschreibungen) mit Datum, Altwert, Neuwert und Button `restore`.

Ausreisser-Fehlersuche:

- `Optionen`: oeffnet Regeln fuer die Scan-Logik.
- `NULL Werte`: markiert NULL/fehlende Werte.
- `0-Werte`: markiert exakte 0.
- `Grenzen` + `Min/Max`: markiert Werte ausserhalb eines Bereichs.
- `Counter-Ausreisser (Spruenge)` + `Max Sprung`: erkennt Spruenge in Counter-Serien (Grenzen kommen aus den Einstellungen).
- `Fehlersuche Ausreisser`: fuehrt den Scan im aktuellen Graph-Fenster aus.
- `Zuruecksetzen`: entfernt Ausreisser-Markierungen.

Hinweis: Wenn Daten nach einem Seitenwechsel automatisch wiederhergestellt wurden, kann die Fehlersuche trotzdem direkt gestartet werden (Measurement/Field wird best-effort wiederhergestellt).

Hinweis: Werte in Bearbeitung werden gelb markiert. Geaenderte (dirty) Zeilen werden gruen markiert.

### In Datenbank uebernehmen

- Bearbeitung passiert als Staging in der Tabelle:
  - Spalte `Aktion`: `ueberschreiben` oder `loeschen`
  - Spalte `Neuwert`: neuer Zahlenwert (nur bei `ueberschreiben`)
- Button: `Aenderungen in Datenbank uebernehmen` (ueber der Bearbeitungsliste)
- Sicherheitsmechanismus:
  - Schreiben/Loeschen ist nur aktiv, wenn in den Einstellungen `Schreiben/Loeschen erlauben` aktiviert ist.
  - Zusaetzlich musst du das exakte `delete_confirm_phrase` eintippen (Add-on Option).

Wichtig: Die Aenderungen bleiben markiert, bis du sie wirklich uebernimmst.

Tipp: In der Toolbar gibt es Mehrfachaktionen (z.B. Werte davor uebernehmen oder Durchschnitt davor+danach), die automatisch `Aktion/Neuwert` fuellen.

## Statistik

- Per Checkbox `Statistik anzeigen` ein/ausblendbar.
- Reihenfolge:
  - Gesamtstatistik (Alles)
  - Statistik Zeitraum (Graph/Tabelle)
- Zusaetzlich gibt es den Bereich `Statistik Influx Datenbank` (Health/Version/IP/Buckets; best-effort) mit Button `Refresh`.
- HA-Infos:
  - device_class, state_class, unit_of_measurement werden (wenn moeglich) aus Home Assistant geladen.

## Logs

- Zeigt die Add-on Logs von InfluxBro.
- Typische Nutzung:
  - Follow/Refresh fuer Live-Ansicht
  - Suche/Filter um Fehler schneller zu finden
  - Copy/Download fuer Support oder Analyse
- Export: erstellt ein Debug-Bundle (inkl. Client-Fehler wie "Failed to fetch").

## Jobs

- Zeigt laufende Background-Jobs (z.B. Statistik laden, Restore/Copy).
- Button `Cancel`: bricht den Job ab (bestaetigen).
- Tipp: `Open Statistik` setzt die Job-ID fuer die Statistik-Seite und wechselt dorthin.

## Backup (ein Messwert, alle Werte)

- Backups werden fuer den aktuell ausgewaehlten Messwert erstellt und enthalten alle Werte dieses Messwertes.
- Die Erstellung laeuft als Background-Job: du siehst Laufzeit und Groesse waehrend des Exports, und kannst per `Abbruch` stoppen.
- In der Backup-Liste siehst du:
  - Name des Messwertes
  - Zeitpunkt des Backups
  - Anzahl Werte
  - Dateigroesse
- Backups koennen geloescht werden (nur die Sicherung, nicht die Datenbank).
- Tipp: In der Volltextsuche gibt es Buttons `Alle` (leeren) und `aus Dashboardauswahl`.

## Restore

- Waehle ein Backup aus der Liste fuer den Messwert.
- Restore schreibt die Werte zurueck, ohne doppelte Messpunkte zu erzeugen (idempotent, weil gleiche Zeitpunkte/Tags/Field ueberschrieben werden).
- Restore ist ebenfalls an `Schreiben/Loeschen erlauben` (Einstellungen) + `delete_confirm_phrase` gekoppelt.
- Tipp: In der Volltextsuche gibt es Buttons `Alle` (leeren) und `aus Dashboardauswahl`.

Tipp: Im Sidebar gibt es ein Status-Panel, das laufende Aktionen (Backup/Restore/Abfragen) und die letzte Meldung anzeigt.

## Export

- Seite `Export`: Auswahl wie im Dashboard; Measurement/Field wird best-effort aus friendly_name/entity_id aufgeloest.
- Feld `Auswahl (aufgeloest)`: zeigt die aktuell aufgeloeste Serie (measurement/field + tags) und den Zeitraum.
- Export-Erzeugung laeuft als Hintergrund-Job und kann mit `Abbrechen` gestoppt werden; der Download wird erst nach Fertigstellung angeboten.
- Formate: Text (Delimiter, Default `;`) oder Excel (`.xlsx`).
- Zeitstempel im Export sind im lokalen Browser-Format (wie in der UI angezeigt).

## Import

- Seite `Import`: Datei via Browser-Upload.
- Button `Analysieren`: zeigt Zeilenanzahl und Zeitraum.
- Zielauswahl: wie Dashboard (Measurement/Field + optionale Tags).
- Optionen:
  - `Vor Import Backup erstellen` (Default an): erstellt ein Range-Backup im Import-Zeitraum fuer die Zielserie.
  - `Vorher loeschen` (optional): loescht Zielserie im Import-Zeitraum (nur mit Confirm Phrase).
- Import schreibt einen Eintrag in `History` (Grund: Import).

## History

- Zeigt ein Protokoll ueber `ueberschreiben`/`loeschen` sowie Rollbacks.
- Filter:
  - Volltextsuche (z.B. Grund, friendly_name, entity_id, _measurement)
  - Aktion / Messwert / entity_id / Grund
- Tabelle: zeigt friendly_name, entity_id, _measurement und _field in separaten Spalten.
- Rollback:
  - selektierte Eintraege
  - oder Zeitraum-Presets (z.B. letzte 15 Minuten)
- Sicherheit: Rollback erfordert eine Bestaetigung und die exakte Phrase `delete_confirm_phrase`.

## Einstellungen

- Bereiche sind einklappbar.

Verbindung:

- `Influx Version`, `Scheme`, `Host`, `Port`, `verify_ssl`, `timeout_seconds`: steuern die Verbindung zur InfluxDB.
- `InfluxDB v2` (`org`, `bucket`, `token`): v2 Zugangsdaten.
- `InfluxDB v1` (`database`, `username`, `password`): v1 Zugangsdaten.

UI:

- `Tabellenzeilen (sichtbar)`: Hoehe der Tabellenboxen.
- `Dezimalstellen (Anzeige)`: Rundung in der UI.
- `Query max. Punkte (Dashboard Graph)`: Downsampling-Limit fuer den Dashboard-Graph (Default: 5000).
- `Raw max. Punkte`: Maximale Zeilen/Points pro Raw-DB-Abfrage (Default: 20000).
- `Manual max. Punkte (Dashboard Graph)`: Sicherheitslimit fuer `Details: Manuell` (100%).
- `Sprung-Polster (Intervalle)`: +/- N Downsample-Intervalle fuer Sprung-Markierung/Detail-Nachladen.
- `Tabellenzeilen Hoehe (px, Backup)`: Zeilenhoehe der Backup-Tabelle.
- `Basis/Kleine Schriftgroesse`: UI Typografie.
- `Checkbox Groesse (Scale)`: Checkbox-Scaling fuer bessere Bedienbarkeit.
- `Filter ... Breite`: steuert die Layout-Breiten im Dashboard.
- `Bereiche standardmaessig geoeffnet`: welche <details>-Sektionen beim Start offen sind.
- `PayPal Donate URL (Sidebar)`: Linkziel des PayPal-Spendenbuttons im Sidebar.

Ausreisser:

- `W/kW/Wh/kWh (max step)`: Standard-Grenzen fuer Counter-Ausreisser (Spruenge) in der Fehler-/Filtertabelle.
- `Weitere Einheiten (unit=max step)`: zusaetzliche Sprung-Grenzen fuer andere Einheiten (z.B. `°C=2`).

## Info

- Zeigt Release Notes (Changelog).
- Zeigt einen Link zum Repository (GitHub).
