# Technical Handbook (InfluxBro)

Dieses Dokument ist das technische Handbuch fuer InfluxBro. Es beschreibt die zentralen Runtime-Mechanismen (Caching, Analyse/Ausreisser-Suche, Raw-Fenster), die fuer Debugging, Weiterentwicklung und Betrieb relevant sind.

Hinweis: Die verbindlichen Cache-Regeln / Design-Constraints sind zusaetzlich in `influxbro/caching.md` dokumentiert.

## 1. Architektur-Ueberblick

InfluxBro ist ein Home Assistant Add-on mit:

- Flask Backend: `influxbro/app/app.py`
- Inline Templates mit JS/CSS: `influxbro/app/templates/*.html` (insb. `index.html`)
- Persistenter Add-on Storage: `/data` (in HA als Volume gemountet)

Design-Grundsatz:

- Funktional relevante Daten (Cache, Logs, Jobs) werden serverseitig unter `/data` gespeichert.
- Browserlokale Caches (sessionStorage/localStorage) sind nur fuer Komfort/Ergonomie und duerfen fachliche Wahrheit nicht ersetzen.

## 2. Cache-Arten (serverseitig)

### 2.1 Dashboard Query Cache (dash_cache)

- Pfad: `/data/dash_cache`
- Zweck: Wiederverwendung von Dashboard-Query-Ergebnissen (Graph/Tabelle) fuer identische Query-Signaturen.

Wichtig:

- Ein Cache-Key muss alle query-relevanten Parameter enthalten (cfg fingerprint + measurement/field + tags + mode + unit + density/auflosung).
- Cache-Nutzung darf nie "ungefaehr" sein. Wenn Signatur nicht passt: Miss.

### 2.2 Analyse Cache (analysis_cache)

- Pfad: `/data/analysis_cache`
- Zweck: Persistente Speicherung der Ausreisser-Ergebnisse (Outlier-Rows) fuer definierte Zeitsegmente, inkl. Checkpoints/Scan-State.
- Ziel: "Analyse mit Cache" kann Segmente preloaden und nur fehlende/geaenderte Bereiche nachscannen.

Dateien:

- `<id>.meta.json`: Segment-Metadaten (covered_start/covered_stop, outlier_count, dirty, patch_status, last_patch_* etc.)
- `<id>.data.json.gz`: Payload (gzip) mit:
  - `rows`: Liste von Outlier-Objekten (time/value/reason/types/class/point_index, optional `window`)
  - `scanned`: Anzahl gescannter Rohpunkte
  - `checkpoints`: Checkpoints fuer inkrementelle Reparatur (state snapshot)
  - `final_state`: Zustand am Segmentende (prev_value/counter_base/scan_state)
  - `meta`: Payload-Meta fuer Debug/Signatur (covered_start/stop, counts, optional windows-meta)

Segment-Gueltigkeit:

- Ein Segment ist nur dann "usable", wenn es die Zeitspanne ueberlappt und nicht dirty ist.
- Dirty bedeutet:
  - History-Aenderungen nach Segment-Erstellung (updated_at) im Segment-Zeitraum
  - oder Segment explizit dirty markiert (z.B. patch_pending/patch_failed)

Dirty-Reparatur (Patch):

- Wenn eine Serie innerhalb eines Segments geaendert wurde, wird ein Patchfenster bestimmt und nur dieser Teil neu gescannt.
- Patch-Window verwendet bevorzugt Checkpoints, sonst Neighbor/Context.
- Seit 1.12.368 wird dabei punktbasierter Kontext (N davor/N danach) aus den UI Settings verwendet.

### 2.3 Statistik Cache (stats_cache)

- Pfad: `/data/stats_cache`
- Zweck: Beschleunigung fuer Statistik-Operationen und Hintergrundjobs.

### 2.4 Cache Usage Log

- Pfad: `/data/influxbro_cache_usage.jsonl`
- Zweck: Zeitliche Protokollierung von Cache-Planung/Treffern/Misses/Stores/Merges.

### 2.5 Verdichtung / Rollup (Downsampling)

- UI: Seite `Verdichtung` (`/rollup`).
- Zweck: Clean -> Rollup Downsampling fuer Langzeitdaten, mit Pflicht-Backup vor jeder Verdichtung und One-Click Restore.

Persistenz unter `/data`:

- Profile: `/data/rollup_profiles.json`
- Runs: `/data/rollup/runs/<run_id>.json`
- Backups: `/data/rollup/backups/<backup_id>.zip`
  - Enthalten: Meta-JSON + Payload `payload/data.lp` (Line Protocol)
  - Integritaet: sha256 wird bei Erstellung berechnet und bei Restore/Preview validiert.

Ausfuehrung:

- Rollup Writes/Deletes/Restore laufen ueber ChangeBlocks (persistente Items, chunking via `child_blocks`).
- Optional: Quelle kann nach erfolgreichem Write im Zeitfenster geloescht werden (exakte Deletes).

## 3. Analyse: Ausreisser-Suche (Outlier Scan)

### 3.1 Einstiegspunkte (UI)

Im Dashboard (index.html) gibt es zwei zentrale Analyse-Modi:

- "Analyse ohne Cache" (refresh): scannt das komplette Analysefenster.
- "Analyse mit Cache":
  - ruft `/api/analysis_cache/plan` auf
  - preloadet wiederverwendbare Segmente via `/api/analysis_cache/segment`
  - scannt nur gap/dirty Bereiche via `/api/outliers`
  - speichert neue Segmente via `/api/analysis_cache/store_segment`

### 3.2 Endpunkt `/api/outliers`

Route: `POST /api/outliers` in `influxbro/app/app.py`.

Input (Auszug):

- `measurement`, `field`, optional `entity_id`/`friendly_name`
- Zeitfenster: `start`, `stop` (Graph/Analysefenster)
- `search_types`: Liste von aktivierten Outlier-Typen
- Zustandsfortschreibung ueber Chunk-Grenzen:
  - `prev_value`, `prev_time`, `counter_base_value`, `scan_state`
- Optional: `return_checkpoints` + `checkpoint_seconds`

Ausgabe (Auszug):

- `rows`: gefundene Ausreisser
- `scanned`: Anzahl gescannter Rohpunkte
- `last_time`, `last_value`, `counter_base_value`, `scan_state`
- `checkpoints` (wenn aktiv)

Chunking:

- Backend scannt die angeforderte Zeitspanne und splittet intern in Chunks, falls ein Chunk zu viele Punkte enthaelt.
- Das Frontend splittet zusaetzlich den Scan in Zeitbloecke, um Timeouts zu reduzieren.

### 3.3 Outlier-Typen (Prinzip)

- `zero`: Wert == 0
- `null`: _value ist NULL
- `gap`: Zeitabstand groesser als `gap_seconds`
- `bounds`: unter/ueber min/max
- `counter` / `decrease`: Counter-Logik, inkl. step / decrease
- `fault_phase`: Zustandsautomat (fault_active/recovering/normal) fuer Stoerphasen

## 4. Raw-Fenster (Kontextfenster um Ausreisser)

### 4.1 Definition

"Raw-Fenster" ist ein Kontextfenster um einen Ausreisser, bestimmt durch:

- `n_before`: N Punkte davor
- `n_after`: N Punkte danach

Das Ergebnis wird als Zeitfenster beschrieben:

- `before_time`: Zeitpunkt des N-ten Punktes davor (best-effort, kann fehlen)
- `after_time`: Zeitpunkt des N-ten Punktes danach (best-effort, kann fehlen)
- `before_count` / `after_count`: wie viele Punkte tatsaechlich gefunden wurden
- `before_minutes` / `after_minutes` / `center_minutes`: Zeitdeltas fuer Anzeige

Wichtig: Fenster sind wie im UI heute definiert.

- Kontext wird strikt im Analysefenster `start/stop` betrachtet.
- Es werden keine Punkte ausserhalb `start/stop` herangezogen.

### 4.2 Settings

Die Kontextgroesse ist getrennt konfigurierbar:

- `outlier_context_before_points`
- `outlier_context_after_points`

### 4.3 Berechnungsmethoden

#### A) Stream-basierte Berechnung waehrend des Scans (bevorzugt)

Seit #318 werden Raw-Fenster moeglichst direkt waehrend `/api/outliers` berechnet.

Mechanik:

- Frontend sendet `window_cfg` (`n_before`, `n_after`) und optional `window_state`.
- Backend fuehrt fuer jeden gescannten Punkt einen kleinen Window-State:
  - Ringbuffer der letzten `n_before` Zeitpunkte (Punkte davor)
  - Pending-Outlier Liste mit Ziel-Index, wann `after_time` erreicht ist
- Wenn ein Pending-Outlier sein Ziel erreicht:
  - Backend emittiert ein `window_updates` Element `{time, window}`.
  - Frontend patcht diese Updates in-memory und serverseitig in den `analysis_cache`.

Vorteile:

- Keine zusaetzlichen Influx-Queries fuer Raw-Fenster.
- Robust ueber Chunk-Grenzen: `window_state` wird zwischen Chunk Requests uebergeben.
- Die berechneten Fenster werden direkt in den gecachten Outlier-Rows persistiert.

#### B) Fallback: `/api/outlier_windows`

Dieser Endpunkt kann Raw-Fenster aus der DB nachberechnen.

Einsatz:

- Backfill alter Cache-Segmente, die noch keine `row.window` Daten enthalten.
- Reparatur bei fehlenden/stalen Fenstern.

Kosten:

- Im Worst-Case 2 Queries pro Outlier (vorher/nachher), daher nur inkrementell fuer fehlende/stale Eintraege verwenden.

### 4.4 Persistenz und Backfill

Ziel: Raw-Fenster sollen nach der ersten Berechnung im `analysis_cache` gespeichert sein, damit Folge-Laeufe keine erneute Berechnung brauchen.

Mechanik:

- Neue Segmente: `row.window` wird direkt beim Scan erzeugt und im Segment gespeichert.
- Chunk-Randfaelle: `window_updates` werden spaeter erzeugt und via `/api/analysis_cache/patch_windows` in den Cache geschrieben.
- Cache-Preload: fehlende/stale Fenster werden gezielt nachberechnet (nur fuer betroffene Outlier) und anschliessend gepatcht.

Endpunkt fuer Persistenz:

- `POST /api/analysis_cache/patch_windows`
  - Input: Serie + `updates: [{time, window}]` (+ optional cache_ids)
  - Patcht `payload.rows[].window` ohne `meta.updated_at` zu aendern.

## 5. Debugging / Troubleshooting

Hilfreiche Hinweise:

- UI Analyse-Log zeigt getrennte Schritte (Scan, Raw-Fenster, Cache Store).
- `analysis_cache` Meta enthaelt Patch-Informationen (`last_patch_*`).
- Bei auffaellig vielen Raw-Fenster Queries:
  - pruefe, ob Segmente alte Payloads ohne `row.window` enthalten
  - pruefe, ob `outlier_context_*` Settings geaendert wurden (stale windows)
