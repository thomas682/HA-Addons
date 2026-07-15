# Funktionshandbuch der Home-Assistant-Add-ons

Audit-Basis: `HEAD 405376f`, Add-on-Version `1.12.640`. Der retrospektive
Produktaudit umfasst 5.740 aktive Einheiten; hinzu kommt der separat gepruefte
Dokumentations-Workflow. Alle 5.741 Katalogeintraege sind mit ihrem exakten
Quellabschnitt, SHA-256-Fingerprint, Kategorievertrag und Review-Batch als
`verified` nachgewiesen.

Die Add-on-Version folgt historisch dem Schema `1.12.640` und damit noch nicht
dem projektuebergreifend vorgesehenen Schema `YYYY.MM.NNN`. Dieser bekannte
Migrationsbedarf bleibt dokumentiert; der reine Dokumentations- und
Tooling-Audit aendert weder die Runtime-Version noch das Updateverhalten.

Dieses Handbuch beschreibt den bedienbaren und technischen Funktionsumfang der
projektspezifischen Add-ons. Der maschinenlesbare Einzelkatalog in
`docs/functions.yaml` ist die kanonische Inventarquelle. Er enthaelt fuer jedes
Python-/JavaScript-Symbol, jede API-Route, jedes stabile oder interaktive
GUI-Element, jede Konfigurationsoption, jede Skriptfunktion und jeden
Add-on-Betriebsweg eine eigene stabile Dokumentations-ID. Jeder Eintrag nennt
konkrete Eingaben, Defaults/Enums, Validierung, Rueckgaben, Aufrufe,
Seiteneffekte, Zustandsverhalten, Sicherheitsgrenzen, Aufrufer und exakte
Testtreffer. Nicht vorhandene Fakten sind explizit als nicht statisch
nachweisbar gekennzeichnet.

## Umfang und Ausschluesse

Am geprueften Stand enthaelt das Repository genau das eigene Add-on
`influxbro`. Nicht zum Produktinventar gehoeren `node_modules/`, das vendorte
`influxbro/app/static/plotly.min.js`, Bilder und sonstige binaere Assets,
Demo-Dateien, Backups unter `saveFiles/`/`savefiles/`, lokale Laufzeitdaten,
generierte Testergebnisse sowie Test- und CI-Hilfsfunktionen. Tests werden nur
als Nachweise zu Produktfunktionen referenziert.

## InfluxBro Add-on-Service

InfluxBro startet automatisch als Home-Assistant-Service, stellt seine
Flask-Anwendung auf dem internen Port 8099 bereit und wird primaer ueber
Home-Assistant-Ingress geoeffnet. Ein direkter Host-Port ist optional. Das
Add-on besitzt Zugriff auf Home-Assistant-/Supervisor-APIs sowie die
beschreibbaren Mounts `/config` und `/share`. Beim Start migriert `run.sh`
vorhandene Share-Daten best-effort nach `/config/influxbro`, richtet den
Kompatibilitaetslink `/data/share` ein und startet danach die Anwendung.

Voraussetzung ist eine erreichbare InfluxDB-Konfiguration. Schreibende oder
loeschende Aktionen sind besonders zu pruefen; Backups, Vorschauen,
Bestaetigungen und die konfigurierten Schutzschalter bleiben massgeblich.

## Dashboard und Zeitreihen

Das Dashboard waehlt Messwert, Feld, Entity, Friendly Name, Tags und Zeitraum
aus. Es laedt InfluxDB-Daten als Graph und Tabelle, begrenzt Abfragemengen,
stellt Messwertprofile aus Home Assistant und InfluxDB zusammen und kann
Namenshistorien vereinigen. Selektoren, Zeitfelder, Filter, Zoom,
Spaltensteuerung, Kopieraktionen und Statusanzeigen sind als einzelne
GUI-Eintraege katalogisiert.

Raw-Daten koennen in einem begrenzten Kontextfenster untersucht werden.
Aenderungen laufen ueber Vorschau, Change-Blocks, Verlauf und Undo/Redo.
Fehler, leere Ergebnisse, Abbruch und Wiederholung werden in den jeweiligen
Statusbereichen angezeigt. Schreibvorgaenge koennen externe InfluxDB-Daten
veraendern und benoetigen passende InfluxDB-Rechte.

## Analyse und Ausreisser

Die Analyse erkennt unter anderem Null-/Nullwert-, Grenzwert-, Sprung-,
Zaehler-, Zeitluecken- und Stoerphasenbefunde. Automatische Strategien werden
aus Messwertprofilen abgeleitet; manuelle Overrides, Parameter und
Korrekturreaktionen koennen messwertbezogen gespeichert werden. Analyse ohne
Cache scannt den Zeitraum neu, Analyse mit Cache verwendet gueltige Segmente
und repariert nur fehlende oder als veraendert markierte Fenster.

Kontextfenster werden bevorzugt waehrend des Scans berechnet. Bei alten oder
unvollstaendigen Cache-Segmenten kann die Anwendung sie nachladen und in den
Analyse-Cache patchen. Vorschau und Ergebnis muessen vor einer Reparatur
geprueft werden.

## Statistik und Serieninventar

Statistikfunktionen berechnen Punktanzahl, Zeitgrenzen, Wertebereiche und
serienbezogene Details. Umfangreiche Berechnungen laufen als Jobs und koennen
gepollt oder abgebrochen werden. Das Serieninventar bietet paginierte
Uebersichten und Exporte. Statistik-Caches reduzieren wiederholte Abfragen und
werden nach Groessen-, Alters- und Zeitplanregeln verwaltet.

## Backup, Restore und Snapshots

Messwert- und Full-Backups koennen erstellt, aufgelistet, heruntergeladen,
kopiert, geprueft und bei ausdruecklicher Auswahl geloescht werden. Restore
zeigt Ziel und Plan vor der Ausfuehrung, arbeitet als abbrechbarer Job und
prueft soweit moeglich Ergebnis und Integritaet. Verify-Jobs verwenden
temporaere Ziele; deren Bereinigung ist eine eigene Betriebsaktion.

Support-Snapshots und Support-Bundles sammeln Diagnoseinformationen. Die
Anwendung maskiert bekannte sensible Werte, dennoch muss der Inhalt vor einer
Weitergabe fachlich geprueft werden.

## Import, Export und Kombinieren

Export filtert Serien und Zeitraum, waehlt Format, Trennzeichen und Ziel und
kann synchron oder als Job arbeiten. Import analysiert Dateien, erkennt
Trennzeichen und Spalten, zeigt transformierte Vorschauen und schreibt erst
nach Startfreigabe. Messwert-Transformationen sind konfigurierbar.

Kombinieren kopiert Daten zwischen Messwertidentitaeten. Timeline und Vorschau
zeigen Umfang und Konflikte vor dem Jobstart. Diese Funktionen koennen grosse
Datenmengen lesen oder schreiben; Ziel, Zeitraum und Tags sind vor Ausfuehrung
zu kontrollieren.

## Datenqualitaet, Verdichtung und Audit

Die Datenqualitaet verwaltet Raw-/Clean-/Rollup-Buckets, Regeln, Vorschauen,
Bereinigungsvorschlaege und Home-Assistant-Patches. Reparaturvorschlaege werden
persistiert, geprueft und freigegeben, bevor schreibende Schritte erfolgen.

Verdichtungsprofile planen Zeitfenster und Aggregationen. Vor jeder
Verdichtung wird ein Backup verlangt. Runs, Restore-Punkte und Audit vergleichen
Raw- und Rollup-Daten, Integritaet und Speicherwirkung. Zeitplaene koennen die
Verdichtung im Hintergrund starten.

## Migration InfluxDB v2 nach v3

Die Migrationsseite verwaltet eine getrennte v3-Zielverbindung, prueft Quelle
und Ziel, teilt die Uebertragung in wiederaufnehmbare Fenster, validiert
Zaehlergebnisse und erstellt einen Bericht. Fehlgeschlagene Fenster koennen
gezielt wiederholt werden. Zielbereinigung betrifft nur das konfigurierte
Migrationsziel. Die produktive Umschaltung auf v3 ist eine separate,
ausdrueckliche Aktion; die v2-Quelle bleibt bis dahin aktiv.

## Monitor und Watchlists

Der Monitor prueft eingehende Werte gegen Grenzen, Spruenge, Nullwert- und
Recovery-Regeln. Er fuehrt persistente Zustandsphasen, offene
Korrekturvorschlaege, kritische Werte und Ereignisse. Vorschlaege koennen
angenommen, ersetzt oder verworfen werden.

Watchlists definieren wiederkehrende Health-Scans. Manuelle und geplante
Laeufe erzeugen Run-Historie und Inbox-Eintraege. Der Scheduler startet nur
faellige, nicht bereits laufende Aufgaben.

## Jobs, Timer und Hintergrundprozesse

Jobs kapseln Backup, Restore, Export, Kombination, Verifikation, Statistik,
Cache-Rebuild, Nachtanalyse, Migration, Verdichtung und Watchlist-Laeufe.
Statusendpunkte liefern Fortschritt und Ergebnis; Abbruch setzt einen
kooperativ ausgewerteten Abbruchzustand. Timer unterstuetzen Stunden-, Tages-
und Wochenplaene. Scheduler-Schleifen laufen als Daemon-Threads und vermeiden
parallele Duplikatlaeufe.

## Cache und Persistenz

Dashboard-, Analyse-, Statistik- und Serienstatistik-Caches liegen unter
`/data`. Signaturen enthalten die abfragerelevante Konfiguration. Metadaten,
Nutzungsprotokolle, Groessenlimits, Dirty-Markierung, Segment-Merge und
inkrementelle Reparatur verhindern die Wiederverwendung unpassender Daten.
Cache-Loeschung und manuelle Aktualisierung sind getrennte Betriebsaktionen.

Weitere persistente Daten umfassen Profile, UI-Zustand, Layout, Jobs,
Watchlists, Monitoring, Verlauf, Change-Blocks, Undo/Redo, Logs und
Performance-Traces. Browserlokaler Zustand dient nur der Darstellung und ist
nicht die fachliche Wahrheit.

## Einstellungen und Eingaben

Die Einstellungsseite verwaltet 217 serverseitige Optionen. Alle Optionen sind
mit Deklaration, Default, Quellverwendungen und vorhandenen
Normalisierungs-/Enumstellen inventarisiert. Kritische Sonderfaelle wie
`active_database_mode` besitzen zusaetzlich manuell gepruefte Overrides. Die
Gruppen sind:

- InfluxDB v1/v2/v3, Authentisierung, SSL, Timeouts und Write-Retry/Gzip
- Tabellen, Graph, Selektoren, Ausreisser und Bearbeitungskontext
- Theme, Farben, Schrift, Zoom, Navigation, Suche, Tooltips und Dialoge
- Backup-Ziel, freier Speicher, Storage-Budget und Undo-Historie
- Logging, Support, Trace, Worklog und Performance-Korrelation
- Dashboard-, Analyse- und Statistik-Cache samt Limits und Zeitplaenen
- Nachtanalyse, Verdichtung und Raw-/Clean-/Rollup-Datenqualitaet

Token und Passwoerter sind geheim zu behandeln. Exporte, Logs, Support-Bundles
und Screenshots duerfen diese Werte nicht enthalten. Host-, Pfad-,
Groessen- und Zahlenfelder werden an der Servergrenze normalisiert und
begrenzt; konkrete Regeln stehen beim jeweiligen Katalogeintrag.

## Navigation, Profile und globale GUI

Die Sidebar oeffnet alle Funktionsseiten und kann auf Desktop skaliert oder
eingeklappt sowie mobil als Drawer verwendet werden. Die Topbar verwaltet
Profile, Theme, Zoom, Seitensuche, Picker, Super-Picker, Tooltip-Schalter und
den Einstellungen-Organizer. UI-Profile speichern Darstellung getrennt von
funktionalem Serverzustand.

Dialoge besitzen Titel, Zweckbeschreibung, Hilfe, Inhalt, Status und
Abschlussaktionen. Picker erzeugen stabile Supportreferenzen; Multi-Pick sammelt
mehrere Elemente. Das integrierte Handbuch kann aus Elementen und Dialogen
kontextbezogen geoeffnet werden. Jedes statische interaktive Element und jedes
Element mit `data-ui`/`data-ib-pickkey` ist einzeln katalogisiert. Elemente ohne
Markup-ID verwenden die zentrale, bijektive Definition `docs/ui-id-map.json`;
Quellverschiebungen blockieren den Validator statt neue Tag-Hashes zu erzeugen.

## API, Diagnose und Support

HTML-Seiten und JSON-/Download-APIs sind je Route einzeln dokumentiert. APIs
decken Konfiguration, Influx-Abfragen, Datenpflege, Backups, Jobs, Caches,
Monitoring, Datenqualitaet, Migration, UI-Zustand, Profile, Logs, Traces,
Performance und Support ab. Ingress uebernimmt im vorgesehenen Betrieb die
Zugriffseinbettung. Schreibende Endpunkte bleiben Vertrauensgrenzen und
validieren ihre Eingaben.

Logs, Client-Events, Worklog, Query-History und Traces helfen bei der Diagnose.
Der Smart-Bug-Assistent rekonstruiert Bedienfolgen und kann einen Snapshot
anfordern. Diagnoseausgaben sind vor externer Weitergabe auf Betriebs- und
personenbezogene Daten zu pruefen.

## Technische interne Funktionen

Interne Python- und JavaScript-Funktionen sind im Einzelkatalog nach Domaene
und Aktion beschrieben. Dazu gehoeren Konfigurationsnormalisierung,
Zeit-/Range-Konvertierung, Query-Erzeugung, Client-Lebenszyklen, Persistenz,
atomare Dateioperationen, Cache-Planung, Jobzustand, Scheduler,
Line-Protocol-Verarbeitung, Change-Blocks, Undo, UI-State, Tabellen-, Dialog-
und Tooltip-Helfer. Verschachtelte Funktionen und Klassenmethoden besitzen
eigene Eintraege. Nicht direkt bedienbare Helfer verweisen auf diesen Abschnitt
und nennen ihre Aufrufer-/Abhaengigkeitsrolle im Katalog.

## Betriebsaktionen

Installation, Start, Stopp, Neustart, Update, Ingress-Oeffnung, optionales
Port-Mapping, Konfigurationspflege, Logpruefung und Datenexport erfolgen ueber
Home Assistant beziehungsweise die InfluxBro-Oberflaeche. Vor Update,
Migration, Restore, Verdichtung oder Massenkorrektur ist ein geprueftes Backup
empfohlen. Loesch-, Restore-, Umschalt- und Bereinigungsaktionen koennen Daten
oder Betriebszustand dauerhaft veraendern und duerfen nur mit kontrolliertem
Ziel und ausreichenden Rechten ausgefuehrt werden.

## Dokumentationspruefung

Der GitHub-Actions-Job `function-docs` laeuft bei Pull Requests und Pushes nach
`main`. Er checkt die vollstaendige Git-Historie fuer die Audit-Vorfahrenpruefung
aus, richtet Python 3.12 ein, installiert ausschliesslich fuer den kurzlebigen
Runner das exakt gepinnte `pytest==8.4.2`, fuehrt die gezielten Validator-Tests
aus und prueft danach den vollstaendigen, quellgebundenen Funktionskatalog. Der
Job benoetigt nur Lesezugriff auf den Checkout, verwendet keine Secrets und
veraendert weder Add-on-Laufzeit noch Repository-Inhalte.
Ein Installations-, Test- oder Validierungsfehler stoppt den Job; ein neuer
Workflow-Lauf nach Behebung wiederholt die Pruefung vollstaendig.

`python3 scripts/validate_function_docs.py` prueft Struktur, deterministische
Abdeckung, UI-ID-Bijektion, Kategorie-Batches, individuelle Quellfingerprints
und Review-Nachweise. Der Befehl schlaegt bei einem Entwurf, einer
Quellaenderung, einer fehlenden Kategorie, ID-Drift oder einem abweichenden
Vertrag fehl. CI und Pre-Commit verwenden diesen strikten Modus.

`python3 scripts/validate_function_docs.py --write` aktualisiert und prueft
den deterministischen Katalog. `docs/audit-evidence.json` belegt Umfang,
Reviewer, Datum, Pruefkriterien und adversariales Sample fuer jede Kategorie.
`docs/function-reviews.json` enthaelt die zusaetzlichen manuellen Overrides fuer
fachlich kritische Sonderfaelle. Eine Quellaenderung entwertet den jeweiligen
Fingerprint automatisch. Die Validator-Fixtures pruefen insbesondere alle 13
Kategorien, Request-Container gegen beliebige `.get()`-Aufrufe, JSON-Aliase,
unbekannte Request-Zugriffe, Manifest-Enums/Defaults, benachbarte GUI-Attribute,
dynamische GUI-Deklarationen sowie UI-ID-Drift.
