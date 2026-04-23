<<FULL FILE OMITTED FOR BREVITY>>

## Env Snippet

- Home Assistant Core Version abfragen:
  - `curl -s -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://192.168.2.200:8123/api/config | jq -r '.version'`

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

### Version / Docs Pflicht

- Wenn sich Laufzeit- oder UI-Verhalten aendert (auch durch Entfernen/Stilllegen):
  - Version bump
  - `CHANGELOG.md` aktualisieren
  - `MANUAL.md` aktualisieren (falls Benutzerfuehrung/Workflows betroffen)

### GitHub Integration

- Issue muss Tombstone-ID referenzieren
- Label Empfehlung: type/ui-removal, requires-tombstone

### Automatische Tombstone-Ausführung bei UI-Entfernungen

Wenn ein Auftrag das Entfernen, Ersetzen oder Stilllegen von UI-Elementen, Templates, Buttons, Tabellen, Dialogen, frontendbezogenen Aktionen, API-gebundenen UI-Funktionen oder Routen umfasst, MUSS der Agent automatisch einen vollständigen Tombstone-Workflow ausführen.

#### Pflichtablauf

1. UI-Relevanz prüfen

- Prüfen, ob die Änderung direkt oder indirekt UI-relevant ist.
- Als UI-relevant gelten insbesondere:
  - Templates (`*.html`)
  - Inline-JavaScript
  - CSS/Selektoren
  - Buttons, Menüs, Dialoge, Tabellen, Karten, Filter, Formulare
  - API-Aufrufe, die von UI-Aktionen ausgelöst werden
  - Routen oder Views mit UI-Bezug

2. Abhängigkeiten vollständig ermitteln

- Vor jeder Entfernung zwingend prüfen:
  - HTML-/Template-Referenzen
  - JavaScript-Funktionen
  - Event-Handler / Listener
  - CSS-Klassen, IDs, Selektoren
  - Fetch-/API-Aufrufe
  - Backend-Endpunkte mit Bezug zur UI
  - Ingress-/Routing-Auswirkungen
  - Dokumentation / MANUAL / Hinweise im UI

3. Tombstone automatisch anlegen

- `.tombstones.yml` MUSS im selben Arbeitsgang ergänzt werden.
- Der Eintrag MUSS mindestens enthalten:
  - `path`
  - `tombstone_id`
  - `reason`
  - `owner`
  - `impacted_selectors`
  - `impacted_actions`
  - `migration_plan`
  - `route_plan`
  - `ci_reference`

4. Folgecode bereinigen

- Funktionen, Selektoren, Event-Handler, API-Aufrufe oder Routen, die ausschließlich zu dem entfernten UI-Element gehören, MÜSSEN ebenfalls entfernt oder stillgelegt werden.
- Funktionen dürfen NICHT entfernt werden, wenn sie an anderer Stelle noch verwendet werden.
- Wenn unklar ist, ob ein Element noch verwendet wird, ist es zu markieren und zu prüfen statt es stillschweigend zu löschen.

5. Migrations- und Ersatzpfad dokumentieren

- Wenn das entfernte UI-Element ersetzt wurde, MUSS der Tombstone-Eintrag den neuen Pfad / die neue Funktion / Route nennen.
- Wenn eine Route entfällt, MUSS geprüft werden, ob ein Redirect oder eine kompatible Ersatzbehandlung erforderlich ist.
- Bei Home Assistant Ingress sind relative Pfade zu verwenden.

6. Abschlussbericht erweitern

- Der Abschlussbericht MUSS enthalten:
  - betroffene UI-Komponente(n)
  - Tombstone-ID(s)
  - entfernte Folgefunktionen
  - bewusst beibehaltene Restfunktionen mit kurzer Begründung
  - Migrations- oder Redirect-Hinweise

### Verification Checklist (Pflicht)

- Repo: `.tombstones.yml` Eintrag vorhanden, `tombstone_id` eindeutig
- Code: `// TOMBSTONE: <id>` Kommentar an der Entfernungs-/Opt-out-Stelle
- Abhaengigkeiten:
  - keine toten Selektoren/CSS-Klassen
  - keine toten JS-Handler/Listener
  - keine UI-Calls auf entfernte API-Endpunkte
  - Ingress/Routes: keine 404s, ggf. Redirect/Migration dokumentiert
- QA:
  - `py_compile`
  - relevante `pytest`
  - UI Smoke Test unter Home Assistant Ingress
- Workflow: HA main-first (rebase auf `origin/main` vor Push, keine stillen Breaking Changes)

#### Automatik-Regel für OpenCode

- Der Agent darf UI-Entfernungen NICHT als reine Löschaufgabe behandeln.
- Jede UI-Entfernung ist automatisch als kombinierte Aufgabe zu behandeln aus:
  - UI-Entfernung
  - Abhängigkeitsanalyse
  - Folgecode-Bereinigung
  - Tombstone-Dokumentation
  - QA-/Ingress-Prüfung

#### Verbotene Verkürzung

- Verboten ist insbesondere:
  - nur HTML zu löschen, ohne JS/CSS/API zu prüfen
  - nur einen Button zu entfernen, ohne den Handler zu prüfen
  - eine UI-Aktion zu löschen, ohne den Backend-Endpunkt zu prüfen
  - Routen zu entfernen, ohne Migrations- oder Redirect-Prüfung

### Verboten

- UI löschen ohne Tombstone
- API entfernen ohne Migration
- Silent Breaking Changes

## UI Picker Eindeutigkeit (Pickkey Pflicht)

Damit UI-Elemente in Issues/Chat immer 100% eindeutig referenzierbar sind, gilt ab jetzt:

- Jedes sichtbare, support-relevante UI-Element MUSS eine stabile `data-ui` Kennung besitzen.
- Jedes sichtbare UI-Element MUSS zusaetzlich eine eindeutige `data-ib-pickkey` Kennung besitzen.
- Das gilt fuer alle Typen:
  - Buttons, Links, Inputs, Selects, Checkboxen, Labels
  - Sektionen (`details/summary`), Cards, Panels
  - Tabellen inkl. Toolbars, Resize-Handles, Filterleisten, Rowcounts
  - Dialoge/Popups/Overlays
  - dynamisch erzeugte UI (per JS/`innerHTML`/DOM APIs)
- Dynamisch erzeugte sichtbare Elemente MUESSEN `data-ui` und `data-ib-pickkey` beim Erzeugen setzen.
- S-Picker Ausgabe muss den kanonischen Referenztext liefern: `<PICK:<Page>|<pickkey>>`.
- Fallback-Referenzen ohne Pickkey sind nur Migrationszustand und nicht akzeptabel als Endzustand.
- `unknown` ist nur als Fallback erlaubt.

Pflicht bei UI-Aenderungen:

- Wenn du sichtbare UI-Elemente anfasst, musst du bestehende betroffene Elemente mit auf `data-ib-pickkey` nachziehen.
- Wenn du UI-Elemente entfernst: Tombstone-Prozess bleibt weiterhin Pflicht.
