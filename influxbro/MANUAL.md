# InfluxBro Handbuch

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://paypal.me/ThomasSchatz)

InfluxBro hilft dir, InfluxDB-Zeitreihen aus Home Assistant zu durchsuchen, auszuwerten, zu sichern und bei Bedarf Werte gezielt zu korrigieren.

Dieses Handbuch ist absichtlich sehr konkret: Jedes sichtbare Element in der GUI wird beschrieben, damit du immer weisst, wofuer es ist.

## Screenshots

### Dashboard (Beispiel)

> Hinweis: Lege das Screenshot-Bild als Datei im Repository ab, dann wird es hier angezeigt.

![Dashboard Beispiel](docs/images/dashboard-hardcopy.png)

## Navigation

Links findest du die Bereiche:

- Dashboard: Messwerte auswaehlen, Graph/Tabelle ansehen, Werte in eine Bearbeitungsliste uebernehmen.
- Statistik: Gesamtstatistik ueber viele Serien anzeigen.
- Backup: Backups fuer einen einzelnen Messwert erstellen und verwalten.
- Logs: Add-on Logs von InfluxBro ansehen (Menuepunkt ist unter Backup einsortiert).
- Restore: Ein vorhandenes Backup fuer einen Messwert wiederherstellen.
- Info: Release Notes + Repository-Link.
- Handbuch: Diese Dokumentation.
- Einstellungen: Influx-Verbindung und UI-Parameter konfigurieren.

Im Sidebar-Kopf wird ausserdem die aktuell laufende Add-on Version angezeigt.

## Dashboard (typischer Ablauf)

### 1) Messwert auswaehlen

- `_measurement (Filter)`: interne Messreihe (Influx Measurement) filtern.
- `Messwert (Klartext / friendly_name)`: den sichtbaren Namen aus HA auswaehlen.
- `entity_id (optional)`: falls mehrere Entities denselben Namen haben, hier eingrenzen.

Weitere Elemente:

- `Erweitert: Measurement / Field`: zeigt die intern aufgeloesten Werte `_measurement` und `_field`.
- `Aktualisieren`: laedt Graph, Fehler-/Filtertabelle und Statistik fuer den aktuellen Zeitraum.
- `Donate`/`PayPal`: Link zur freiwilligen Unterstuetzung.

Tipp: Wenn du mit der Maus ueber einem Feld bleibst, zeigt der Tooltip den internen Feldnamen (z.B. `filter.friendly.select`). Damit kannst du mir exakt sagen, welches Feld du meinst.

### 2) Zeitraum setzen

- `Zeitraum (Graph/Tabelle)`: z.B. 24h, 7d, oder `Alle`.
- Bei `Benutzerdefiniert`: Von/Bis setzen (lokale Zeit).

### 3) Aktualisieren

- Erst mit `Aktualisieren` werden Graph, Filterliste und Statistik geladen.

## Graph

- Zoom/Pan ist moeglich.
- Option `Messpunkte markieren`: schaltet runde Marker ein/aus.
- Ziehen der Groesse: Unter dem Plot gibt es einen horizontalen Griff. Ziehen nach oben/unten aendert die Plot-Hoehe.

## Filterliste (Tabelle)

- Linke Checkbox: Zeilen selektieren (Mehrfachauswahl moeglich).
- `Zeit gefuehrt durch Graph`:
  - EIN: Zoombereich im Graph bestimmt die Zeit-Einschraenkung der Tabelle.
  - AUS: Tabelle zeigt wieder den Zeitraum aus der Zeitraum-Auswahl.
- `Filter aktiv`: schaltet den Werte-Filter (Links/Verb/Rechts) an/aus.
- `Links`/`Verb.`/`Rechts`: einfache Regel um Werte als Fehler zu markieren (z.B. kleiner als 0 oder groesser als 999999).
- Doppelklick auf eine Zeile: uebernimmt den Punkt direkt in die Bearbeitungsliste.
- Button `In Bearbeitungsliste`: uebernimmt alle markierten Zeilen.

Ausreisser-Fehlersuche:

- `Optionen`: oeffnet Regeln fuer die Scan-Logik.
- `NULL Werte`: markiert NULL/fehlende Werte.
- `0-Werte`: markiert exakte 0.
- `Grenzen` + `Min/Max`: markiert Werte ausserhalb eines Bereichs.
- `Counter-Ausreisser (Spruenge)` + `Max Sprung`: erkennt Spruenge in Counter-Serien (Grenzen kommen aus den Einstellungen).
- `Fehlersuche Ausreisser`: fuehrt den Scan im aktuellen Graph-Fenster aus.
- `Zuruecksetzen`: entfernt Ausreisser-Markierungen.

Hinweis: Werte, die bereits in der Bearbeitungsliste sind, werden in der Filterliste farblich markiert und koennen nicht doppelt hinzugefuegt werden.

## Bearbeitungsliste

Hier sammelst du einzelne Datenpunkte zur Korrektur.

- Entfernen:
  - Button `Aus Liste loeschen` oder Doppelklick auf den Eintrag.
- Aendern:
  - Spalten `aelter` / `juenger`: Nachbarwerte (ein Datenpunkt davor/danach).
  - Button `nehmen`: uebernimmt den jeweiligen Nachbarwert als neuen Wert.
  - `eigener Wert`: manueller Wert + `setzen`.
- Undo:
  - Pro Zeile `undo`.
  - Global `Undo alle`.

### In Datenbank uebernehmen

- Button: `Alle Werte in Datenbank uebernehmen`
- Sicherheitsmechanismus:
  - Schreiben ist nur aktiv, wenn in den Add-on Optionen `allow_delete` aktiviert ist.
  - Zusaetzlich musst du das exakte `delete_confirm_phrase` eintippen.

Wichtig: Die Aenderungen bleiben markiert, bis du sie wirklich uebernimmst.

## Statistik

- Per Checkbox `Statistik anzeigen` ein/ausblendbar.
- Reihenfolge:
  - Gesamtstatistik (Alles)
  - Statistik Zeitraum (Graph/Tabelle)
- HA-Infos:
  - device_class, state_class, unit_of_measurement werden (wenn moeglich) aus Home Assistant geladen.

## Logs

- Zeigt die Add-on Logs von InfluxBro.
- Typische Nutzung:
  - Follow/Refresh fuer Live-Ansicht
  - Suche/Filter um Fehler schneller zu finden
  - Copy/Download fuer Support oder Analyse

## Backup (ein Messwert, alle Werte)

- Backups werden fuer den aktuell ausgewaehlten Messwert erstellt und enthalten alle Werte dieses Messwertes.
- In der Backup-Liste siehst du:
  - Name des Messwertes
  - Zeitpunkt des Backups
  - Anzahl Werte
  - Dateigroesse
- Backups koennen geloescht werden (nur die Sicherung, nicht die Datenbank).

## Restore

- Waehle ein Backup aus der Liste fuer den Messwert.
- Restore schreibt die Werte zurueck, ohne doppelte Messpunkte zu erzeugen (idempotent, weil gleiche Zeitpunkte/Tags/Field ueberschrieben werden).
- Restore ist ebenfalls an `allow_delete` + `delete_confirm_phrase` gekoppelt.

## Einstellungen

- Bereiche sind einklappbar.

Verbindung:

- `Influx Version`, `Scheme`, `Host`, `Port`, `verify_ssl`, `timeout_seconds`: steuern die Verbindung zur InfluxDB.
- `InfluxDB v2` (`org`, `bucket`, `token`): v2 Zugangsdaten.
- `InfluxDB v1` (`database`, `username`, `password`): v1 Zugangsdaten.

UI:

- `Tabellenzeilen (sichtbar)`: Hoehe der Tabellenboxen.
- `Dezimalstellen (Anzeige)`: Rundung in der UI.
- `Basis/Kleine Schriftgroesse`: UI Typografie.
- `Checkbox Groesse (Scale)`: Checkbox-Scaling fuer bessere Bedienbarkeit.
- `Filter ... Breite`: steuert die Layout-Breiten im Dashboard.
- `Bereiche standardmaessig geoeffnet`: welche <details>-Sektionen beim Start offen sind.

Ausreisser:

- `W/kW/Wh/kWh (max step)`: Standard-Grenzen fuer Counter-Ausreisser (Spruenge) in der Fehler-/Filtertabelle.

## Info

- Zeigt Release Notes (Changelog).
- Zeigt einen Link zum Repository (Gitea / spaeter GitHub).
