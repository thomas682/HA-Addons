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

## Bearbeitungsliste (Ausreisser)

- Linke Checkbox: Zeilen selektieren (Mehrfachauswahl moeglich).
- `Zeit gefuehrt durch Graph`:
  - EIN: Zoombereich im Graph bestimmt die Zeit-Einschraenkung der Tabelle.
  - AUS: Tabelle zeigt wieder den Zeitraum aus der Zeitraum-Auswahl.
- `Filter aktiv`: schaltet den Werte-Filter (Links/Verb/Rechts) an/aus.
- `Links`/`Verb.`/`Rechts`: einfache Regel um Werte als Fehler zu markieren (z.B. kleiner als 0 oder groesser als 999999).

Bearbeitung in der Bearbeitungsliste:

- Pro Zeile in der Spalte `Aktion`: `Bearbeiten` aktiviert den Bearbeitungsmodus fuer diesen Punkt.
- Sobald mindestens ein Punkt in Bearbeitung ist, werden zusaetzliche Spalten eingeblendet: `Alt`, `Neu`, `aelter`, `juenger`, `eigener Wert`.
- `Bearbeitung aus`: beendet den Bearbeitungsmodus fuer die Zeile. Bei ungespeicherten Aenderungen kommt eine Bestaetigung.
- `Undo`: stellt den Wert auf den Originalwert zurueck (vor der Bearbeitung).
- `Details` (nur bei selektierter Zeile): zeigt Davor/Danach-Werte direkt unter der Zeile.

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

Hinweis: Werte in Bearbeitung werden gelb markiert. Geaenderte (dirty) Zeilen werden gruen markiert.

### In Datenbank uebernehmen

- Button: `Aenderungen in Datenbank uebernehmen`
- Sicherheitsmechanismus:
  - Schreiben/Loeschen ist nur aktiv, wenn in den Einstellungen `Schreiben/Loeschen erlauben` aktiviert ist.
  - Zusaetzlich musst du das exakte `delete_confirm_phrase` eintippen (Add-on Option).

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

## Restore

- Waehle ein Backup aus der Liste fuer den Messwert.
- Restore schreibt die Werte zurueck, ohne doppelte Messpunkte zu erzeugen (idempotent, weil gleiche Zeitpunkte/Tags/Field ueberschrieben werden).
- Restore ist ebenfalls an `Schreiben/Loeschen erlauben` (Einstellungen) + `delete_confirm_phrase` gekoppelt.

Tipp: Im Sidebar gibt es ein Status-Panel, das laufende Aktionen (Backup/Restore/Abfragen) und die letzte Meldung anzeigt.

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
- `PayPal Donate URL (Sidebar)`: Linkziel des PayPal-Spendenbuttons im Sidebar.

Ausreisser:

- `W/kW/Wh/kWh (max step)`: Standard-Grenzen fuer Counter-Ausreisser (Spruenge) in der Fehler-/Filtertabelle.

## Info

- Zeigt Release Notes (Changelog).
- Zeigt einen Link zum Repository (GitHub).
