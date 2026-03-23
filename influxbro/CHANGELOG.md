# Changelog

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
