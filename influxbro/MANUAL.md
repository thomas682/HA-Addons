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

### Jobs & Cache

![Jobs](images/Jobs.png)

### Statistik

![Statistik](images/Statistik.png)

## Navigation

Links findest du die Bereiche:

- Dashboard: Messwerte auswaehlen, Graph/Tabelle ansehen, Ausreisser finden und Werte direkt in der Bearbeitungsliste bearbeiten.
- Statistik: Gesamtstatistik ueber viele Serien anzeigen.
- Backup: Backups fuer einen einzelnen Messwert erstellen und verwalten.
- Restore: Ein vorhandenes Backup fuer einen Messwert wiederherstellen.
- Kombinieren: Datenpunkte zwischen zwei Messwerten kopieren (z.B. bei Entity-ID Umbenennung) inkl. Vorschau.
- Logs: Add-on Logs von InfluxBro ansehen (Menuepunkt ist unter Restore einsortiert).
- Jobs & Cache: Laufende Background-Jobs ansehen (Statistik/Restore/Cache) und abbrechen.
- Info: Influx Datenbank Diagnose (best-effort).
- Changelog: Release Notes.
- Handbuch: Diese Dokumentation.
- Einstellungen: Influx-Verbindung und UI-Parameter konfigurieren.

Im Sidebar-Kopf wird ausserdem die aktuell laufende Add-on Version angezeigt.

Neu: Top-Leiste (Profil + Zoom)

- Ganz oben gibt es eine fixe Leiste (scrollt nicht mit), die immer sichtbar bleibt.
- Enthalten:
  - Profil-Auswahl inkl. `Anwenden`, `Speichern`, `Info` und die aktuelle Version.
  - Zoom-Steuerung: `-` / `+` und die aktuelle Zoomstufe in `%`.
- Zoom wird im Browser gespeichert (pro Browser/Client).

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

Hinweis:

- Wenn du das Dashboard oeffnest und noch keine Auswahl (friendly_name/entity_id) gesetzt ist, wird der letzte Graph best-effort aus dem serverseitigen Cache unter `/data` wiederhergestellt.
- `Donate`/`PayPal`: Link zur freiwilligen Unterstuetzung.
- Zusaetzlich gibt es einen "Buy me a coffee" Spendenlink.

Tipp: Wenn du mit der Maus ueber einem Button/Checkbox/Auswahlfeld bleibst, zeigt der Tooltip eine kurze Erklaerung plus den internen UI-Key in Klammern (z.B. `Dieser Button aktualisiert die Liste (dashboard.load)`). Damit kannst du mir exakt sagen, welches Element du meinst.

Hinweis: Zeitstempel werden im gesamten UI inklusive Millisekunden angezeigt.

## Tabellen (Allgemein)

- Jede Tabelle ist als eigener Block mit Rahmen und eindeutiger Tabellenueberschrift dargestellt.
- Ueber jeder Tabelle werden Zeilen angezeigt als `gefiltert / gesamt` (Rows).
- Spalten koennen ueber den Spalten-Button (neben dem Info-Icon) ein-/ausgeblendet werden (wird gespeichert).
- Das Info-Icon (i) erklaert je Tabelle Sinn/Zweck, Spalten und Aktionen.
- Zusaetzlich haben viele Bereiche neben dem Bereichstitel ein Info-Icon, das die komplette Sektion ausfuehrlich erklaert (Popup ist resizable, hat Umbruch + Copy).

## UI-Profile

- In der Sidebar kannst du ein Profil auswaehlen (Default: `PC`, `MOBIL`).
- Profile werden filebasiert unter `/data/ui_profiles` gespeichert.
- Das aktive Profil ist global (gilt fuer alle Clients/Browsers).
- In `Profilverwaltung` kannst du Profile anlegen, umbenennen, loeschen, anwenden und den gespeicherten Inhalt per Volltextsuche einsehen.

## Automatisches Speichern

- GUI-Aenderungen werden automatisch gespeichert (Checkboxen/Selects/Inputs sowie resizable Hoehen).

### 2) Zeitraum setzen

- `Zeitraum (Graph/Tabelle)`: z.B. 24h, 7d, oder `Alle`.
- Bei `Benutzerdefiniert`: Von/Bis setzen (lokale Zeit).

### 3) Aktualisieren

- Erst mit `Aktualisieren` werden Graph und Statistik geladen.
- Die Bearbeitungsliste bleibt dabei leer und wird erst durch `Fehlersuche Ausreisser` gefuellt.
- Sobald einmal geladen wurde, werden die Ergebnisse serverseitig gecacht (unter `/data/dash_cache`) und beim naechsten Aufruf des Dashboards wiederhergestellt (auch nach Seitenwechsel in InfluxBro / Home Assistant).

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

- Wenn kein UI-State gespeichert ist (neue Installation oder Browser-Storage geloescht), sind die Ableitungs-Checkboxen standardmaessig aktiviert (Hintergrund + Farbleiste + Ableitungs-Graph + absolut).

Bearbeitungsliste + Bearbeitungsgraph:

- Bearbeitungsliste: nach der Ausreisser-Analyse wird angezeigt, wie viele Punkte geprueft wurden und wie viele Ausreisser gefunden wurden.
- Bearbeitungsgraph: zeigt `DB Punkte` und `Ausreisser` jeweils im Format `gesamt / Bereich` (Bereich = aktueller X-Zoom).
- Hover ueber einem Messpunkt zeigt Zeit + Wert direkt am Messpunkt (lokales Client-Format).
- Klick auf einen Messpunkt zeigt zusaetzlich oberhalb des Graphs die Auswahl (Zeit/Wert/Serie).

Raw Daten (DB):

- Optional kannst du per Checkbox steuern, ob Raw Daten dem Zoom-Bereich im Graph folgen (oder dem Zeitraum aus der Zeitraum-Auswahl).
- Klick auf einen Messpunkt im Graph markiert den Punkt und springt in der Raw-Tabelle zum passenden Zeitstempel (Zeile wird hervorgehoben).
- Wenn der Zeitstempel in den aktuell geladenen Raw-Zeilen noch nicht enthalten ist, werden automatisch weitere Raw-Seiten nachgeladen und dann zur passenden (naechsten) Zeile gescrollt.
- Der Sprung zentriert die Zeile in der Tabelle, damit vorherige und nachfolgende Werte sichtbar bleiben.
- Ueber der Raw-Tabelle gibt es Buttons zur Tagesnavigation (aeltester/juengster Tag, +/-1d, +/-7d; lokale Browserzeit).
- Wenn du per Tagesnavigation zu einem Zeitpunkt springst, der noch nicht in der Tabelle geladen ist, wird automatisch nachgeladen, bis der Ziel-Tag erreicht ist (oder bis keine weiteren Daten verfuegbar sind).

Konzept fuer sehr grosse Tabellen (z.B. ~2 Mio Zeilen):

- Immer *serverseitig* begrenzen: Raw-API arbeitet mit `start/stop` + `limit/offset` und liefert nie "alles" auf einmal.
- Sofortige Anzeige: erst eine kleine erste Seite laden (z.B. 300-1000 Zeilen) und direkt rendern.
- Progressive Nachladung: Button `Mehr laden` (append) oder Paging; optional im Hintergrund vorladen.
- Zeitbasierte Navigation statt Seitenzahlen: in der Praxis ist "Tag/Zeitraum" fuer Zeitreihen schneller zu bedienen und stabiler.
- Fuer einen schnellen Ueberblick: alternativ (oder zusaetzlich) eine "Preview" mit Downsampling/Reduktion anbieten (Graph ist bereits so optimiert).

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
- `Abbruch`: bricht nur den laufenden Scan ab (Treffer bleiben stehen).

Hinweis: Wenn Daten nach einem Seitenwechsel automatisch wiederhergestellt wurden, kann die Fehlersuche trotzdem direkt gestartet werden (Measurement/Field wird best-effort wiederhergestellt).

Hinweis: Werte in Bearbeitung werden gelb markiert. Geaenderte (dirty) Zeilen werden gruen markiert.

### In Datenbank uebernehmen

- Bearbeitung passiert als Staging in der Tabelle:
  - Spalte `Aktion`: `ueberschreiben` oder `loeschen`
  - Spalte `Neuwert`: neuer Zahlenwert (nur bei `ueberschreiben`)
- Klick auf eine Zeile zeigt rechts das Detailpanel (Davor/Ziel/Danach) und fokussiert den Edit-Graph.
- Im Detailpanel kann ein Wert selektiert und per `Uebernehmen als neuer Wert` als Neuwert vorgemerkt werden.
- Button: `Aenderungen in Datenbank uebernehmen` (ueber der Bearbeitungsliste)
- Sicherheitsmechanismus:
  - Aenderungen muessen im Dialog bestaetigt werden.
  - `delete_confirm_phrase` wird nur fuer Bulk-Loeschungen verwendet (z.B. Zeitraum loeschen, History Rollback, Import: Vorher loeschen).

Wichtig: Die Aenderungen bleiben markiert, bis du sie wirklich uebernimmst.

Neu (Ausreisser-Modus):

- In der Spalte `Aktion` gibt es zusaetzlich den Direktbutton `uebernehmen` (schreibt sofort in die DB, mit Bestaetigung).
- Nach erfolgreichem Schreiben erscheint `undo` (stellt den Ursprungswert wieder her; best-effort).

Tipp: In der Toolbar gibt es Mehrfachaktionen (z.B. Werte davor uebernehmen oder Durchschnitt davor+danach), die automatisch `Aktion/Neuwert` fuellen.

## Statistik

- Per Checkbox `Statistik anzeigen` ein/ausblendbar.
- Letztes Ergebnis + Auswahl (Zeitraum/Filter/Spalten) werden im Browser gespeichert und beim Seitenwechsel best-effort wiederhergestellt.
- Spaltenauswahl: ueber Checkboxen (oldest/count/min/max/mean). Fehlende Spalten koennen mit `Nachladen (markiert)` oder `Nachladen (alle im Filter)` berechnet werden.
- Reihenfolge:
  - Gesamtstatistik (Alles)
  - Statistik Zeitraum (Graph/Tabelle)
- Influx Datenbank Diagnose (Health/Version/IP/Buckets; best-effort) ist im Menuepunkt `Info`.
- HA-Infos:
  - device_class, state_class, unit_of_measurement werden (wenn moeglich) aus Home Assistant geladen.

## Logs

- Zeigt die Add-on Logs von InfluxBro.
- Typische Nutzung:
  - Follow/Refresh fuer Live-Ansicht
  - Buttons `aeltester`/`neuster` springen innerhalb der Ansicht nach oben/unten
  - Suche/Filter um Fehler schneller zu finden
  - Copy/Download fuer Support oder Analyse
- Export: erstellt ein Debug-Bundle (JSON, inkl. Client-Fehler wie "Failed to fetch").
- Debug report: erstellt einen GitHub-freundlichen Report als Markdown-Datei (empfohlen fuer Issue/Kommentar).

## Jobs & Cache

- Zeigt laufende Background-Jobs (z.B. Statistik laden, Restore/Copy).
- Hinweis: Export-Jobs werden hier ebenfalls als Job angezeigt und koennen abgebrochen werden.
- Button `Abbruch`: bricht den Job ab (bestaetigen). Der Button ist immer sichtbar.
- Button `Details`: zeigt, was der Job gerade macht (Message/Current/Trigger-Infos).
- Tipp: `Open Statistik` setzt die Job-ID fuer die Statistik-Seite und wechselt dorthin.

Cache:

- Tabelle `Cache`: zeigt alle Caches (Dashboard + Statistik) inkl. Bereich/Ausloeser/next update/Modus.
- Spalte `id`: eindeutige Cache-ID.
- Aktionen:
  - `Info`: zeigt Details (inkl. Events wie Verwendung/Check/Update; best-effort).
  - Dashboard: `Pruefen`/`Aktualisieren`/`Loeschen`.
  - Statistik: `Aktualisieren`/`Loeschen`.

Cache Nutzung:

- Tabelle `Cache Nutzung`: Zeitstempel-Log der Cache-Verwendung (Dashboard/Statistik).
- Cache-ID ist klickbar und springt zur passenden Cache-Zeile in der Cache-Tabelle (Highlight).
  - `Cache loeschen (alles)`: loescht Cache-Dateien unter `/data` (nur Cache, nicht die Datenbank).
- Automatisches Cache-Update ist in `Einstellungen -> UI -> Dashboard Cache` bzw. `Einstellungen -> UI -> Statistik Cache` konfigurierbar.

Timer Jobs:

- Tabelle `Timer Jobs`: zeigt Intervall-/Nightly-Jobs mit naechstem Lauf (aus Einstellungen abgeleitet) und kurzer Erklaerung.
- Action: `Start` (manuell) und `Abbruch`.
- `last run`: zeigt den letzten Laufzeitpunkt (persistent).
- `Modus`: erlaubt das Aendern der Scheduler-Parameter:
  - `hours`: alle N Stunden
  - `daily`: taeglich um HH:MM:SS
  - `weekly`: woechentlich (Wochentag 0=Mo..6=So) um HH:MM:SS
  - `manual`: nur manuell per `Start`
- Zusaetzlich: `stats_full` laedt Statistik komplett (inkl. Details wie count/min/max/mean) fuer alle Serien.

## Backup (ein Messwert, alle Werte)

- Backups werden fuer den aktuell ausgewaehlten Messwert erstellt und enthalten alle Werte dieses Messwertes.
- Die Erstellung laeuft als Background-Job: du siehst Laufzeit und Groesse waehrend des Exports, und kannst per `Abbruch` stoppen.
- In der Backup-Liste siehst du:
  - Name des Messwertes
  - Zeitpunkt des Backups
  - Anzahl Werte
  - Dateigroesse
 - Anzeige: `Freier Speicher` zeigt freien/gesamten Speicher am Backup-Speicherort; `Addon Speicher` zeigt belegten Platz unter `/data`.
- Wenn genau ein Backup selektiert ist, erscheint `Download` und laedt eine ZIP-Datei (enthaelt `.json` + `.lp`).
- `Alles` (Checkbox in der Kopfzeile) selektiert/deselektiert nur die aktuell sichtbaren Zeilen (z.B. nach Volltextsuche), ohne andere Selektionen zu verlieren.
- Unterhalb des Speicherorts wird der freie Speicher angezeigt; optional kann ein Mindestwert (MB) konfiguriert werden, unter dem Backups abgelehnt werden.
- Die Hoehe der Backup-Liste ist per Einstellung "Sichtbare Zeilen (Backup-Liste)" konfigurierbar.
- Backups koennen geloescht werden (nur die Sicherung, nicht die Datenbank).
- Tipp: In der Volltextsuche gibt es Buttons `Alle` (leeren) und `aus Dashboardauswahl`.

Neu: FullBackup (InfluxDB komplett)

- Zusaetzlich gibt es eine eigene Sektion `FullBackup (InfluxDB komplett)`.
- FullBackup sichert nicht nur einen einzelnen Messwert, sondern exportiert (best-effort) die komplette InfluxDB (v1: alle Measurements; v2: kompletter Bucket).
- FullBackups werden in einer separaten Liste angezeigt (unabhaengig von den normalen Signal-Backups).
- Aktionen: `FullBackup starten`, `Abbruch`, `Liste aktualisieren`, `Download` (ZIP), `Loeschen`.
- Modus:
  - `Line Protocol (kompatibel)`: exportiert best-effort als Line Protocol (wie bisher).
  - `Native v2 (influx backup)`: nutzt die Influx CLI und erzeugt ein natives Backup (ZIP enthaelt Meta + native Payload unter `native/`).
  - Native v2 ist nur auf `amd64`/`aarch64` verfuegbar (Influx CLI). Auf anderen Plattformen ist der Modus deaktiviert; die UI zeigt die erkannte `HA Plattform`.
  - In der FullBackupliste zeigt die Spalte `format`, ob es `lp` oder `native_v2` ist.
- Kompatibilitaet:
  - InfluxDB v2: unterstuetzt.
  - InfluxDB v1: unterstuetzt (best-effort; kann je nach Datenmenge sehr lange dauern).
  - InfluxDB v3: aktuell nicht unterstuetzt (klare Fehlermeldung).
- Hinweis: FullBackup kann sehr gross werden. Achte auf freien Speicher (siehe Anzeige in der Backup-Seite und Option `Min. freier Speicher (MB)`).

## Restore

- Waehle ein Backup aus der Liste fuer den Messwert.
- Download: `Download` laedt das selektierte Backup als ZIP herunter (Meta + Line Protocol).
- Restore schreibt die Werte zurueck, ohne doppelte Messpunkte zu erzeugen (idempotent, weil gleiche Zeitpunkte/Tags/Field ueberschrieben werden).
- Restore fragt per Browser-Dialog nach Bestaetigung; `delete_confirm_phrase` wird nur fuer Bulk-Loeschungen verwendet.
- Tipp: In der Volltextsuche gibt es Buttons `Alle` (leeren) und `aus Dashboardauswahl`.
- Die Hoehe der Restore-Backup-Liste ist per Einstellung "Sichtbare Zeilen (Restore-Liste)" konfigurierbar.
- Restore: Backup-Liste, Query und Detail-Boxen sind resizable; Hoehen werden automatisch gemerkt.

Neu: FullRestore (InfluxDB komplett)

- Zusaetzlich gibt es eine eigene Sektion `FullRestore (InfluxDB komplett)`.
- FullRestore stellt ein selektiertes FullBackup wieder her.
  - `format=lp`: schreibt Line Protocol in die konfigurierte InfluxDB (wie bisher).
  - `format=native_v2`: nutzt `influx restore`.
  - Native v2 Restore ist nur auf `amd64`/`aarch64` verfuegbar (Influx CLI). Auf anderen Plattformen ist es gesperrt; die UI zeigt die erkannte `HA Plattform`.
- Native v2 Restore:
  - Zielbucket kann gesetzt werden (leer = wie Quelle). Wenn Ziel != Quelle, wird `--new-bucket` verwendet.
  - `Ueberschreiben (Bucket loeschen)` loescht den Zielbucket vor Restore (erfordert Confirm-Phrase `DELETE`).
  - Hinweis: `influx restore` kann nicht in existierende Buckets schreiben (ohne vorheriges Loeschen).
- FullBackups erscheinen in einer separaten Liste; normale Restore-Funktionen akzeptieren keine FullBackups.
- Aktionen: `Liste aktualisieren`, `Download`, `FullBackup loeschen`, `FullRestore ausfuehren`, `Abbruch`.
- Sicherheit: FullRestore erfordert eine Bestaetigung im UI (Browser-Dialog).

Tipp: Im Sidebar gibt es ein Status-Panel, das laufende Aktionen (Backup/Restore/Abfragen) und die letzte Meldung anzeigt.

## Dashboard (Raw Daten)

- Klick auf einen Graph-Punkt springt in der Raw-Datenliste zum naechsten passenden Zeitstempel.
- Der markierte Punkt bleibt in der Raw-Liste farblich hervorgehoben, bis du einen anderen Punkt auswaehlst.

## Diagnose

- Menuepunkt `Diagnose` zeigt Best-effort Status (Add-on, Influx Verbindung, Systemlast) und einige KPIs.
- Erweiterte KPIs werden aus InfluxDB `GET /metrics` gelesen (falls erreichbar). Wenn `/metrics` nicht verfuegbar ist, zeigt die Seite trotzdem die Basis-Infos.

## Kombinieren

- Seite `Kombinieren`: kopiert Datenpunkte zwischen zwei Messwerten (z.B. bei Entity-ID Umbenennung).
- Auswahl:
  - Quelle und Ziel jeweils per `_measurement`, `_field`, `entity_id` und/oder `friendly_name` setzen.
  - Wichtig: Mindestens `entity_id` oder `friendly_name` muss pro Seite gesetzt sein (damit die Serie eindeutig ist).
  - `Richtung` bestimmt, welche Seite als Quelle gilt (Quelle->Ziel oder Ziel->Quelle).
- Vorschau:
  - `Timeline`: zeigt die Verteilung der Punkte im Von/Bis Fenster; mit Maus ziehen markierst du den exakten Kopierbereich.
  - `Mini-Graph`: downsampled Linie als schnelle Orientierung.
  - Buttons `Ganz/Aeltester/Juengster` helfen beim Setzen der Markierung.
- Sicherheit / Rollback:
  - Default: `Zielbereich vorher als Backup sichern` erstellt ein Range-Backup (ZIP) fuer den Zielbereich.
  - Optional: `Zielbereich vor dem Kopieren loeschen` (destruktiv) erfordert `DELETE`.
  - Rollback erfolgt ueber die Seite `History` (Eintrag vom Typ `combine_copy`).
- Virtuell/YAML:
  - Button `Virtuell/YAML` zeigt ein Beispiel fuer einen Home Assistant Template-Sensor, falls du einen virtuellen Messwert anlegen willst.

## Export

- Seite `Export`: Auswahl wie im Dashboard; Measurement/Field wird best-effort aus friendly_name/entity_id aufgeloest.
- Feld `Auswahl (aufgeloest)`: zeigt die aktuell aufgeloeste Serie (measurement/field + tags) und den Zeitraum.
- Export-Erzeugung laeuft als Hintergrund-Job und kann mit `Abbrechen` gestoppt werden; nach Fertigstellung startet der Download automatisch.
- Vor dem Start erscheint ein Dialog zur Auswahl des Zielordners (relativ unter `/data` oder absolut unter `/data`/`/config`).
- Das Feld `Auswahl (aufgeloest)` ist resizable; die Groesse wird automatisch gemerkt.
- Formate: Text (Delimiter, Default `;`) oder Excel (`.xlsx`).
- Zeitstempel im Export sind im lokalen Browser-Format (wie in der UI angezeigt).

## Import

- Seite `Import`: Datei via Browser-Upload.
- Button `Analysieren`: zeigt Zeilenanzahl und Zeitraum; bei Problemen zusaetzlich eine kurze Diagnose + Beispielzeilen.
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
- Sicherheit: Rollback erfordert eine normale Sicherheitsabfrage im Browser.

Hinweis (neu)

- Rollback erfordert nur noch eine normale Sicherheitsabfrage (kein Tippen der Delete-Phrase), da kein Loeschen ausgefuehrt wird.

## Einstellungen

- Bereiche sind einklappbar.
- Oben gibt es ein Suchfeld, das Einstellungen findet und per Klick zum passenden Feld springt (Bereiche werden automatisch aufgeklappt).
- Das Suchfeld bleibt beim Scrollen sichtbar.
- Layout: pro Abschnitt als 1-spaltige Parameterliste (ein Parameter pro Block mit Beschreibung).

Neu:

- Status Schriftgroesse (Sidebar) ist konfigurierbar; Refresh loescht abgeschlossene Status-Eintraege.
- Jobs: Max Job Laufzeit (Sekunden) fuer Auto-Abbruch; Job-Farben (running/done/error/cancelled).
- Ausreisser Tabelle: `_measurement` ist nicht editierbar; Zeilen werden automatisch aus bekannten Measurements vorbefuellt.

Verbindung:

- `Influx Version`, `Scheme`, `Host`, `Port`, `verify_ssl`, `timeout_seconds`: steuern die Verbindung zur InfluxDB.
- `InfluxDB v2` (`org`, `bucket`, `token`, `admin_token`): v2 Zugangsdaten.
  - `admin_token` wird nur fuer `Native Backup/Restore (v2)` benoetigt (FullBackup/FullRestore Modus "Native v2").
- `InfluxDB v1` (`database`, `username`, `password`): v1 Zugangsdaten.

UI:

- `Tabellenzeilen (sichtbar)`: Hoehe der Tabellenboxen.
- `Dezimalstellen (Anzeige)`: Rundung in der UI.
- `Query max. Punkte (Dashboard Graph)`: Downsampling-Limit fuer den Dashboard-Graph (Default: 5000).
- `Raw max. Punkte`: Maximale Zeilen/Points pro Raw-DB-Abfrage (Default: 20000).
- `Manual max. Punkte (Dashboard Graph)`: Sicherheitslimit fuer `Details: Manuell` (100%).
- `Sprung-Polster (Intervalle)`: +/- N Downsample-Intervalle fuer Sprung-Markierung/Detail-Nachladen.
- `Tabellenzeilen Hoehe (px, Backup)`: Zeilenhoehe der Backup-Tabelle.
- `Sichtbare Zeilen (Backup-Liste)`: Hoehe der Backup-Liste in Zeilen (scrollt bei mehr Eintraegen).
- `Sichtbare Zeilen (Restore-Liste)`: Hoehe der Restore-Backup-Liste in Zeilen (scrollt bei mehr Eintraegen).
- `Min. freier Speicher (MB)`: wenn kleiner als diese Schwelle, wird das Erstellen eines Backups abgelehnt (0 = deaktiviert).
- `Basis/Kleine Schriftgroesse`: UI Typografie.
- `Checkbox Groesse (Scale)`: Checkbox-Scaling fuer bessere Bedienbarkeit.
- `Bereich-Titel (Details): Hintergrund/Textfarbe`: Farben der einklappbaren Bereichstitel (Details/Sektionen). Leer = Standard; erlaubt: `transparent`/`inherit` oder `#RRGGBB`.
- `Filter ... Breite`: steuert die Layout-Breiten im Dashboard.
- `Bereiche standardmaessig geoeffnet`: welche <details>-Sektionen beim Start offen sind.
- Auswahlfelder (Filter/Zeiten):
  - Fontgroessen (Label / Feld / Beschreibung)
  - Auto-Breite (Default) oder manuelle Breite (px)
  - Wenn Auto aktiv ist, wird die zuletzt berechnete Breite als Vorschlagswert angezeigt.
- `PayPal Donate URL (Sidebar)`: Linkziel des PayPal-Spendenbuttons im Sidebar.

Fehleranzeige:

- Unten wird der letzte Fehler als Statuszeile angezeigt (Zeitstempel + Kurztext).
- Button `Fehlerdialog`: zeigt den aktuellen Fehler plus Verlauf (mit Zeitstempeln).
- Dashboard Button `Letzter Fehler`: oeffnet den letzten Fehlerdialog erneut.

Statistik:

- `Vollscan Refresh Modus`: geplant/aus (manual/hours/daily/weekly) fuer den Background-Vollscan (stats_full).
- `Vollscan max. Zeitraum (Tage)`: Sicherheitslimit fuer den geplanten Vollscan (startet nicht vor "now - N Tage").

## Bugreport / Debug report

- Bei einer Fehlermeldung im Popup kannst du auf `Bugreport` klicken.
- Dabei wird automatisch ein Debug report heruntergeladen (`influxbro_debug_report_*.md`) und eine GitHub Issue Seite geoeffnet (vorbefuellt mit HA/Influx Versionen).
- Wichtig: Debug report Datei in GitHub als Anhang hochladen (enth. Konfig redacted + Logs).

Ausreisser:

 - Tabelle `_measurement / max_step`: Grenzen fuer Counter-Ausreisser (Spruenge) in der Fehler-/Filtertabelle.
 - Die Tabelle wird beim Laden mit allen bekannten `_measurement` Werten vorbefuellt; leere `max_step` Werte werden beim Speichern ignoriert.

## Info / Changelog

- `Info`: Influx Datenbank Diagnose (best-effort).
- `Changelog`: Release Notes + Repository-Link.
