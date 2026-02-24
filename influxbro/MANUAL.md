# InfluxBro Handbuch

InfluxBro hilft dir, InfluxDB-Zeitreihen aus Home Assistant zu durchsuchen, auszuwerten, zu sichern und bei Bedarf Werte gezielt zu korrigieren.

## Navigation

Links findest du die Bereiche:

- Dashboard: Messwerte auswaehlen, Graph/Tabelle ansehen, Werte in eine Bearbeitungsliste uebernehmen.
- Logs: Add-on Logs von InfluxBro ansehen.
- Backup: Backups fuer einen einzelnen Messwert erstellen und verwalten.
- Restore: Ein vorhandenes Backup fuer einen Messwert wiederherstellen.
- Info: Release Notes + Repository-Link.
- Einstellungen: Influx-Verbindung und UI-Parameter konfigurieren.

## Dashboard (typischer Ablauf)

### 1) Messwert auswaehlen

- `_measurement (Filter)`: interne Messreihe (Influx Measurement) filtern.
- `Messwert (Klartext / friendly_name)`: den sichtbaren Namen aus HA auswaehlen.
- `entity_id (optional)`: falls mehrere Entities denselben Namen haben, hier eingrenzen.

Tipp: Wenn du mit der Maus ueber einem Feld bleibst, zeigt der Tooltip den internen Feldnamen (z.B. `filter.friendly.select`). Damit kannst du mir exakt sagen, welches Feld du meinst.

### 2) Zeitraum setzen

- `Zeitraum (Graph/Tabelle)`: z.B. 24h, 7d, oder `Alle`.
- Bei `Benutzerdefiniert`: Von/Bis setzen (lokale Zeit).

### 3) Aktualisieren

- Erst mit `Aktualisieren` werden Graph, Filterliste und Statistik geladen.

## Graph

- Zoom/Pan ist moeglich.
- Option `Messpunkte markieren`: schaltet runde Marker ein/aus.

## Filterliste (Tabelle)

- Linke Checkbox: Zeilen selektieren (Mehrfachauswahl moeglich).
- `Zeit gefuehrt durch Graph`:
  - EIN: Zoombereich im Graph bestimmt die Zeit-Einschraenkung der Tabelle.
  - AUS: Tabelle zeigt wieder den Zeitraum aus der Zeitraum-Auswahl.
- Doppelklick auf eine Zeile: uebernimmt den Punkt direkt in die Bearbeitungsliste.
- Button `In Bearbeitungsliste`: uebernimmt alle markierten Zeilen.

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

- InfluxDB Verbindung (v1/v2) konfigurieren.
- UI-Parameter:
  - Schriftgroessen, Checkbox-Groesse
  - Breiten der Filterfelder

## Info

- Zeigt Release Notes (Changelog).
- Zeigt einen Link zum Repository (Gitea / spaeter GitHub).
