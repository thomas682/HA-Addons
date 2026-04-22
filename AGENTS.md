<<FULL FILE OMITTED FOR BREVITY>>

## UI-Komponenten-Entfernung (Tombstones Pflichtprozess)

Beim Entfernen von UI-Komponenten (HTML, JS, CSS, Backend-Funktionen) muss zwingend ein nachvollziehbarer "Tombstone" hinterlassen werden.

### Pflichtregeln

- Keine stille Entfernung
- Jede entfernte UI-Komponente MUSS in `.tombstones.yml` dokumentiert werden
- Tombstone-Kommentar im Code ist Pflicht
- Abhängigkeiten prüfen (JS, API, CSS, Templates, Ingress)

### Tombstone Datei

- Zentrale Datei: `.tombstones.yml`
- Jeder Eintrag benötigt eindeutige `tombstone_id`

### Code-Kommentar

// TOMBSTONE: TS-XXXX – Beschreibung

### Pflichtprüfungen nach Entfernung

- Keine JS Errors
- Keine 404 durch alte API/UI Calls
- HA Ingress funktioniert weiterhin
- API-Endpunkte korrekt entfernt

### CI / QA Pflicht

- Syntax Check
- API Smoke Tests
- UI Test im HA System

### GitHub Integration

- Issue muss Tombstone-ID referenzieren
- Label Empfehlung: type/ui-removal, requires-tombstone

### Verboten

- UI löschen ohne Tombstone
- API entfernen ohne Migration
- Silent Breaking Changes

