# Caching

Diese Datei beschreibt die verbindlichen Cache-Regeln fuer InfluxBro. Neue Cache-Funktionen muessen diese Regeln beachten.

## Grundsaetze

- Funktionale Cache-Daten sind serverseitig unter `/data` zu speichern.
- Browserlokale Cache-Daten duerfen nur fuer ergonomische Wiederherstellung und nicht fuer die fachliche Wahrheit genutzt werden.
- Cache-Keys muessen alle query-relevanten Einstellungen enthalten.
- Caches duerfen nur wiederverwendet werden, wenn die funktionale Signatur identisch ist.
- Bei Unsicherheit gilt: lieber kein Cache als ein fachlich falscher Cache.

## Cache-Arten

### Dashboard Query Cache

- Speicherort: `/data/dash_cache`
- Zweck: Ergebnis von `dashboard.load` wiederverwenden.
- Gueltigkeit nur bei identischer funktionaler Signatur:
  - Influx-Kontext (`cfg_fp`)
  - `measurement`
  - `field`
  - `entity_id`
  - `friendly_name`
  - `detail_mode`
  - `manual_density_pct`
  - `unit`
- Cache-Meta soll mindestens enthalten:
  - `created_at`, `updated_at`, `last_used_at`
  - `covered_start`, `covered_stop`
  - `row_count`, `bytes`
  - `dirty`, `dirty_reason`, `dirty_at`
  - `mismatch`
  - `outlier_count`
  - `query_ms_original`
  - `cache_strategy`
  - `source_cache_ids` bei Merge-Caches

### Statistik Cache

- Speicherort: `/data/stats_cache`
- Zweck: Statistik-Ergebnisse und Hintergrundjobs beschleunigen.
- Darf Append- oder Sliding-Merge-Strategien verwenden, wenn die bestehende Statistik-Signatur passt.

### Dashboard Last Restore

- Speicherort: `/data/influxbro_dashboard_last.json`
- Zweck: letzten serverseitig bekannten Graph beim Oeffnen best-effort wiederherstellen.
- Das ist ein Zeiger auf einen vorhandenen Dashboard-Cache und kein eigener fachlicher Daten-Cache.

### Browserlokale Session-Restore-Caches

- Beispiele: `sessionStorage`/`localStorage` fuer zuletzt sichtbare Daten, UI-Zustand oder temporaere Hilfsdaten.
- Duerfen nur fuer Komfort/Wiederherstellung genutzt werden.
- Duerfen serverseitige funktionale Cache-Entscheidungen nicht ersetzen.

### Cache Usage Log

- Speicherort: `/data/influxbro_cache_usage.jsonl`
- Zweck: Cache-Treffer, Misses, Store- und Merge-Vorgaenge zeitlich protokollieren.
- Neue Cache-Funktionen sollen dort eigene Schritte mit `dur_ms` und passendem `series_key` erfassen.

## Statusregeln

### dirty

- `dirty` bedeutet: Cache darf nicht blind als frisch betrachtet werden.
- Schreiboperationen fuer eine Serie sollen passende Caches dirty markieren.

### mismatch

- `mismatch` bedeutet: Cache stimmt nicht mehr mit der erwarteten DB-Signatur oder dem erwarteten Zustand ueberein.
- `mismatch`-Caches duerfen nicht fachlich wiederverwendet werden.

### stale

- `stale` ergibt sich aus der konfigurierten Aktualisierungslogik.
- Ein stale Cache kann fuer schnelle Voransicht/Weiterverwendung geeignet sein, wenn die jeweilige Funktion das ausdruecklich so vorsieht.

## Regeln fuer Teilabdeckung

- Teilabdeckung gilt fuer alle Zeitbereiche, wenn sich der Zielzeitraum konkret in `start`/`stop` aufloesen laesst.
- Verwendbar sind nur Cache-Segmente mit identischer funktionaler Signatur.
- Die wiederverwendete Abdeckung ist ueber `covered_start`/`covered_stop` oder gleichwertige konkrete Zeitgrenzen zu bestimmen.
- Es duerfen hoechstens wenige Segmente kombiniert werden; bei starker Fragmentierung ist eine Vollabfrage vorzuziehen.
- Fehlende Restbereiche muessen gezielt nachgeladen werden.
- Nach dem Nachladen sollen Cache-Daten zusammengefuehrt, sortiert, dedupliziert und als neuer zusammenhaengender Cache gespeichert werden.

## Regeln fuer History-Warnungen

- Wenn fuer einen verwendeten Cache nach dessen Erstellung Werte derselben Serie im gewaehlten Zeitraum geaendert wurden, muss die UI das deutlich warnend anzeigen.
- Diese Warnung basiert auf der bestehenden History-Datei und blockiert die Cache-Nutzung nicht automatisch.
- Solche Hinweise sind in der UI rot darzustellen.

## Regeln fuer Zeitersparnis

- Zeitersparnis ist ueber das Cache-Nutzungsprotokoll zu schaetzen oder zu belegen.
- Neue Cache-Funktionen sollen dafuer mindestens protokollieren:
  - Cache-Planung
  - Segment-Treffer
  - Gap-Queries
  - Merge
  - Store
- Die Anzeige fuer den Benutzer darf als Schaetzung ausgewiesen werden, wenn keine ausreichende Referenzhistorie vorliegt.

## Regeln fuer neue Cache-Funktionen

- Vor neuer Implementierung zuerst pruefen, ob bestehende Cache-Meta oder bestehende Logs erweitert werden koennen.
- Keine parallelen, fachlich widerspruechlichen Cache-Quellen fuer dieselbe Funktion einfuehren.
- Neue Cache-Endpunkte muessen klar zwischen:
  - Cache-Planung
  - Cache-Nutzung
  - Cache-Verwaltung
  unterscheiden.
- Jede neue Cache-Funktion braucht:
  - technische Dokumentation in dieser Datei
  - Benutzerdokumentation im Handbuch
  - gezielte Tests fuer Treffer, Miss, Merge und Dirty-/Change-Warnungen
