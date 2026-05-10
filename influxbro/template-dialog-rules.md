# Dialog Standards

> **Stand:** 2026-04-29 · **Version:** 2.0 · **Sprache:** Deutsch
> **Verbindliche Referenz-Implementierung:** [`demo/dialog-mockup-themed.html`](./demo/dialog-mockup-themed.html)
>
> Alle Dialoge MÜSSEN visuell, strukturell und im Verhalten der Referenz-Implementierung entsprechen.
> Bei Unklarheiten in den Regeln gilt die Referenz-Implementierung als verbindlich.

---

## 1. Grundprinzipien (PFLICHT)

- **Standard zuerst:** Jeder neue Dialog basiert auf einem der drei Standard-Templates (`dialog_info_popup`, `dialog_panel_workbench`, `dialog_confirm_action`). Eigene Dialog-Strukturen sind VERBOTEN.
- **Erweiterungen nur additiv:** Erweiterungen zu einem Standard-Template sind nur mit fachlicher Begründung erlaubt. Sie dürfen die Pflichtstruktur NICHT verändern.
- **Stabile Bezeichner:** Jeder Dialog hat einen eindeutigen Bezeichner im Schema `dialog.<bereich>_<funktion>` (z. B. `dialog.measurement_profile_runtime`).
- **Konsistenz:** Gleiche Aufgaben sehen gleich aus. Visuelle Sonderlocken sind VERBOTEN.
- **Themefähig:** Alle Dialoge MÜSSEN mit allen Farbschemata (System, Hell, Dunkel, Dunkel Blau, Hoher Kontrast) ohne Anpassung funktionieren.
- **Referenz binden:** Die Datei `demo/dialog-mockup-themed.html` zeigt das verbindliche Erscheinungsbild aller Dialoge in allen Themes.

---

## 2. Pflichtstruktur (zwingend in dieser Reihenfolge)

Jeder Dialog MUSS exakt diese Struktur haben:

1. **Kopfbereich** mit Titelzeile und Fenster-Aktionen
2. **Beschreibungs-Sektion** (eine kurze Zeile)
3. **Aktionsleiste** mit Hilfe-Funktionen links und optionalen Tools rechts
4. **Optionale Toolbar** (nur bei funktionalen Controls/Filtern)
5. **Inhaltsbereich** (scrollbar bei Überlauf)
6. **Footer** mit Meta-Indicator links und Arbeits-Aktionen rechts

**Verbindliche HTML/CSS-Struktur** siehe `demo/dialog-mockup-themed.html` Sektionen `dialog-header`, `dialog-description`, `dialog-actionbar`, `dialog-toolbar`, `dialog-content`, `dialog-footer`.

Auch ohne Zugriff auf die HTML-Referenz MUSS die Struktur eindeutig umsetzbar sein:

| Bereich | Pflichtinhalt | Schutzregel |
|---|---|---|
| Kopfbereich | Links ein sichtbarer Fenstertitel, rechts Fenster-Aktionen in fester Reihenfolge | Fachliche Inhalte aus dem alten Dialogkopf duerfen nicht geloescht werden; sie werden nur dann verschoben, wenn sie eindeutig Titel oder Fensteraktion sind. |
| Beschreibungs-Sektion | Eine kurze, dezente Zeile direkt unter dem Kopfbereich | Bestehende fachliche Hilfetexte duerfen nicht geloescht werden; laengere Erklaerungen gehoeren in Inhalt, Info oder Handbuch. |
| Aktionsleiste | Links Info und Handbuch, rechts optionale technische Hilfsaktionen | Keine fachlichen Primaeraktionen in die Aktionsleiste verschieben, wenn sie zum Arbeitsfluss gehoeren. |
| Toolbar | Nur Filter, Suche, Sortierung, Ansicht oder andere funktionale Controls | Keine reinen Inhaltsbereiche als Toolbar markieren. |
| Inhaltsbereich | Alle fachlichen Dialoginhalte, bei Ueberlauf scrollbar | Kinder nur kapseln, nicht inhaltlich veraendern; Event-Handler und stabile Attribute muessen erhalten bleiben. |
| Footer | Links Meta-Indicator, rechts Arbeitsaktionen | Bestehende Speichern/Abbrechen/OK-Aktionen duerfen nur optisch eingeordnet, nicht ersetzt werden. |

Standardisierungscode darf bestehende Kinder NICHT pauschal ausblenden, entfernen, umbenennen oder umsortieren. Er darf nur eindeutig standardbezogene Elemente normalisieren: Titel, Fenster-Aktionen, Beschreibung, Aktionsleiste, Toolbar, Content-Container, Footer und Meta-Indicator. Alle funktionsabhaengigen Kindinhalte bleiben erhalten.

Picker-Sonderregel: Der Dialog, der nach einem erfolgreichen Pick angezeigt wird, folgt dem Minimalmodus in [`template-picker-rules.md`](./template-picker-rules.md). Diese Sonderregel gilt nur fuer den Pick-Ergebnisdialog, nicht fuer Picker/S-Picker selbst.

---

## 3. Globale Pflichtregeln

### 3.1 Bezeichner und Meta-Info

- Jeder Dialog hat einen eindeutigen Bezeichner (`dialog.<bereich>_<funktion>`).
- Jeder Dialog hat einen `data-ib-pickkey` und `data-ib-instancekey` (siehe Pickkey-Pflicht im Hauptregelwerk).
- Meta-Info wird im Footer links als dezenter Debug-Indicator angezeigt:
  - Visuell: Punkt mit Label `meta`, monospace, gedämpfte Farbe
  - Hover öffnet Tooltip mit Format: `pk: <pickkey> | tpl: <template> | dlg: <dialog-name>`
  - Ein dezenter Copy-Button neben dem Meta-String kopiert den vollständigen Meta-String
  - Der Copy-Button MUSS tastaturbedienbar sein, Kopierfeedback anzeigen und eigene stabile `data-ui`/`data-ib-pickkey` besitzen

### 3.2 Titelzeile

- Aussagekräftig, knapp, ohne Punkt am Ende.
- Wenn ein Dialog durch einen Button oder ein sichtbares UI-Element geoeffnet wird, MUSS der Fenstertitel bevorzugt aus dem lesbaren Text dieses Ausloesers gebildet werden.
- Technische Werte wie `id`, `data-ui`, `data-ib-pickkey` oder `data-dialog-trigger` duerfen NICHT als sichtbarer Fenstertitel erscheinen, solange ein lesbarer Ausloesertext, ein `aria-label` oder ein nicht-technischer `title` verfuegbar ist.
- Fallback-Reihenfolge: sichtbarer Ausloesertext → `aria-label` des Ausloesers → nicht-technischer `title` des Ausloesers → explizites `[data-dialog-title="1"]` → erste fachliche Ueberschrift → aus `data-dialog-name` abgeleiteter Fallback.
- Bei Confirm-Dialogen MIT Severity-Indicator-Icon links (Info/Warnung/Gefahr).
- Severity-Farben gemäß Token `--c-info`, `--c-warning`, `--c-danger`.

### 3.3 Beschreibungs-Sektion (eine kurze Zeile)

Direkt unter der Titelzeile. Die Beschreibung ist bewusst kompakt:

- **Zeile 1 (PFLICHT):** Aufgabe / Zweck des Dialogs in einem kurzen Satz oder Satzfragment, kleine Schrift, dezent unterhalb des Titels.

Laengere Funktionsbeschreibungen, Bedienhinweise und technische Erklaerungen gehoeren in den Inhaltsbereich, die Info-Funktion oder das Handbuch, nicht dauerhaft in den Dialogkopf.

Bekannte Dialoge MÜSSEN fachlich spezifische Kurzbeschreibungen erhalten. Generische Template-Beschreibungen sind nur als Fallback für unbekannte oder noch nicht inventarisierte Dialoge zulässig.

### 3.4 Hilfe-Aktionen (klare Funktionstrennung — PFLICHT)

In der Aktionsleiste ganz links, in dieser Reihenfolge:

1. **Info-Button (`ⓘ`)** — zeigt **strukturelle Meta-Information** des Dialogs:
   - Verwendetes Template
   - Pflicht- und Dialog-spezifische Felder
   - Eindeutiger Dialog-Bezeichner
   - Template-Beschreibung aus dieser Standard-Definition
   - Tastenkürzel: `Ctrl+I`

2. **Handbuch-Button (`📖`)** — öffnet **inhaltliche Dokumentation** zur Fachfunktion:
   - Verlinkt direkt zur passenden Passage in `./manual`
   - Öffnet im neuen Tab oder im integrierten Doc-Viewer
   - Tastenkürzel: `F1`

> **Klare Trennung:** Info = „Wie ist dieser Dialog gebaut?", Handbuch = „Was bedeutet die Funktion?"
> **VERBOTEN:** Info- und Handbuch-Inhalte zu vermischen.

### 3.5 Fenster-Aktionen (rechts oben — feste Reihenfolge)

1. **Minimieren / Restore** (`—` / `▢`)
2. **Maximieren / Restore** (`⛶`)
3. **Schließen** (`✕`) — IMMER als letztes, IMMER als Icon-Button

Ausnahme: `dialog_confirm_action` hat NUR den Schließen-Button. Minimieren und Maximieren sind dort verboten.

Fenster-Aktionen MUESSEN dem Standardkopf entsprechen:

- Rechts oben im Kopfbereich, nicht im Inhaltsbereich und nicht im Footer.
- Reine Icon-Buttons mit `type="button"`, `aria-label`, `title`, sichtbarem Fokuszustand und stabilem `data-ui`/`data-ib-pickkey`, wenn sie im Markup erzeugt werden.
- Reihenfolge darf nicht variieren: Minimieren/Restore, Maximieren/Restore, Schliessen.
- Schliessen bleibt immer der rechte aeusserste Button.
- Hover/Focus/Disabled-Zustaende muessen themetaugliche Tokens verwenden und duerfen keine hartcodierten Dialogfarben einfuehren.

### 3.6 Footer-Aktionen

- **Links:** Meta-Indicator (siehe 3.1).
- **Rechts:** Arbeits-Aktionen — sekundäre Aktionen links → primäre Aktion ganz rechts.
- **Visuelle Hervorhebung:** Primäre Aktion mit Akzentfarbe, sekundäre als Outline-Button.
- **Bei Confirm-Dialogen:** Primäre Aktion in `--c-danger` (rot) bei destruktiven Operationen.

### 3.7 Zustände (PFLICHT — vier Zustände)

Jeder Dialog MUSS diese Zustände sauber abbilden:

| Zustand | Verhalten |
|---|---|
| **Loading** | Skeleton oder Spinner mittig im Inhaltsbereich, Aktionsleiste deaktiviert |
| **Empty** | Zentriertes Icon + Erklärtext + ggf. Call-to-Action |
| **Error** | Akzentfarbe `--c-danger`, Fehlermeldung + Retry-Button + Details ausklappbar |
| **Success** | Akzentfarbe `--c-success`, Banner oben oder Toast |

### 3.8 Tastatur-Spezifikation (PFLICHT)

| Taste | Aktion |
|---|---|
| `Esc` | Schließt den Dialog (entspricht „Abbrechen") |
| `Enter` | Löst die primäre Aktion aus (außer in mehrzeiligen Eingabefeldern) |
| `Tab` / `Shift+Tab` | Navigiert vorwärts/rückwärts durch fokussierbare Elemente |
| `Ctrl+W` / `Cmd+W` | Schließt den Dialog |
| `F1` | Öffnet das Handbuch zur aktuellen Funktion |
| `Ctrl+I` | Öffnet die Info-Box des Dialogs |

### 3.9 Fokus-Management (PFLICHT)

- **Beim Öffnen:** Initial-Focus auf das primäre Eingabefeld oder die primäre Aktion.
- **Während des Lebens:** Focus-Trap innerhalb des Dialogs (Tab läuft nicht raus).
- **Beim Schließen:** Fokus zurück auf das Element, das den Dialog geöffnet hat.
- **Sichtbarer Fokus-Ring:** PFLICHT für alle interaktiven Elemente (Tastatur-Navigation).

### 3.10 Position, Größe, Persistenz

- **Position beim Öffnen:** Standardmäßig zentriert. Begrenzt auf den sichtbaren Viewport (linke obere und rechte untere Ecke immer sichtbar).
- **Resize:** Erlaubt für Info- und Arbeitsdialoge an der rechten unteren Ecke (`⤡`-Handle).
- **Maximieren:** Nur temporär für die aktuelle Öffnung. Beim nächsten Öffnen wieder Standardgröße.
- **Persistenz pro Dialog-Bezeichner:**
  - Position und Größe werden pro Dialog-Bezeichner persistent gespeichert (NICHT pro Session).
  - Reset über Doppelklick auf den Resize-Handle.
- **Außerhalb-Klick:**
  - Schließt unkritische Info-Dialoge.
  - Arbeits- und Confirm-Dialoge bleiben offen, um Datenverlust zu vermeiden.

### 3.11 S-Picker-Regel

- Sichtbare S-Picker-Buttons sind in Dialogen VERBOTEN.
- Der S-Picker-Shortcut (Default `Ctrl+S`, konfigurierbar) wirkt weiterhin kontextsensitiv auf den aktiven Dialog.

### 3.12 Logging (PFLICHT)

Jedes Öffnen, Schließen und jede Dialogaktion wird protokolliert.
**Pflichtfelder:** Seite · Dialog-Bezeichner · Trigger/Auslöser · Aktion/Button · Timestamp · Ergebnis (Erfolg/Fehler).

### 3.13 Theme-Kompatibilität (PFLICHT)

Alle Dialoge MÜSSEN folgende Farbschemata ohne Anpassung unterstützen:

| Schema | Beschreibung |
|---|---|
| **System** | Folgt `prefers-color-scheme` des Betriebssystems (Default) |
| **Hell** | Helle Oberfläche für Tageslicht |
| **Dunkel** | Klassisches dunkles Schema |
| **Dunkel Blau** | Dunkles Schema mit blauen Akzenten (Pool-Dashboard-Stil) |
| **Hoher Kontrast** | Maximaler Kontrast für Barrierefreiheit |

**Implementierungs-Pflichten:**
- Alle Farben über CSS-Custom-Properties (`var(--c-...)`).
- Theme-Wechsel via `data-theme`-Attribut am `<html>`-Element.
- System-Theme reagiert auf `prefers-color-scheme: dark`.
- Umschaltung wirkt sofort ohne Neustart.
- Themewechsel erfolgt NICHT im Dialog selbst, sondern in den globalen Einstellungen.

**Verbindliches Token-Set** siehe `demo/dialog-mockup-themed.html` Sektion `:root, [data-theme="..."]`. Dort sind alle 5 Themes mit allen Tokens vollständig definiert.

**VERBOTEN:** Hartcodierte Farben (`#xxx`, `rgb()`, `rgba()`) im Dialog-CSS. Alle Farben MÜSSEN über CSS-Custom-Properties referenziert werden.

---

## 4. Standard-Templates

### 4.1 `dialog_info_popup`

**Verwendung:** Query-/Info-/Diagnose-/Detaildialoge, Laufzeitdialoge, Referenzdetails, Hilfetexte.

**Pflicht:**
- Kopf · Titelzeile · Beschreibung · Info + Handbuch · Close · Meta-Footer · Scroll · Resize · Theme-Support · Tastatur-Bindings · alle 4 Zustände

**Optional:**
- Copy-Button · Inline-Details · kleine Toolbar · Sektions-Tabs

**Standardgröße:** inhaltsbasiert (`fit-content`) mit Viewport-Maximum. Manuell geänderte Größen werden profilabhängig pro Dialog-Bezeichner gespeichert.

**Referenz:** `demo/dialog-mockup-themed.html` → Bereich `<div class="dialog dialog-info-popup">` (`dialog.measurement_profile_runtime`).

---

### 4.2 `dialog_panel_workbench`

**Verwendung:** Logs, Wizards, Such-/Filterdialoge, Arbeitsdialoge mit mehreren Controls.

**Pflicht:**

- Kopf · Titelzeile · Beschreibung · Info + Handbuch · Close · Meta-Footer · Scroll · Resize · Theme-Support · Tastatur-Bindings · alle 4 Zustände · Footer-Aktionen rechts unten

**Optional:**

- Toolbar mit Filtern (Pflicht bei Such-/Filterdialogen)
- Copy · Inline-Details · Split-/Mehrbereichslayout · Tabs · Stepper für Wizards

**Standardgröße:** inhaltsbasiert (`fit-content`) mit Viewport-Maximum. Manuell geänderte Größen werden profilabhängig pro Dialog-Bezeichner gespeichert.

**Referenz:** `demo/dialog-mockup-themed.html` → Bereich `<div class="dialog dialog-panel-workbench">` (`dialog.analysis_log`).

---

### 4.3 `dialog_confirm_action`

**Verwendung:** Bestätigungsdialoge, Warnungen, sichere Freigaben.

**Pflicht:**

- Kopf · Titelzeile MIT Severity-Icon · Beschreibung · Info + Handbuch · Close · Meta-Footer · OK + Abbrechen · Theme-Support · Tastatur-Bindings · Severity-Indicator (Border-Akzent links)

**Optional:**

- Kompaktes Resize (NUR bei fachlichem Bedarf)
- Bestätigungs-Phrase bei destruktiven Aktionen (z. B. `LÖSCHEN` eingeben)
- Detail-Liste der Auswirkungen (Impact-List)

**Standardgröße:** inhaltsbasiert (`fit-content`) mit Viewport-Maximum; Confirm-Dialoge bleiben kompakt und ohne frei resizebare Arbeitsfläche.

**Severity-Klassen:**

- `is-info` — Border-Akzent in `--c-info`
- `is-warning` — Border-Akzent in `--c-warning`
- `is-danger` — Border-Akzent in `--c-danger`

**Pflicht bei destruktiven Aktionen:**

- `is-danger` Severity-Klasse
- Impact-Liste mit konkreten Zahlen (Datenpunkte, Zeitraum, abhängige Profile)
- Bestätigungs-Phrase als Schutz vor versehentlicher Auslösung
- Primäre Aktion in `--c-danger` (rot), bleibt deaktiviert bis Phrase korrekt eingegeben

**Referenz:** `demo/dialog-mockup-themed.html` → Bereich `<div class="dialog dialog-confirm-action is-danger">`.

---

### 4.4 Spezialisierung `dialog_panel_floating_workbench`

**Verwendung:** Kleine bewegliche Arbeitsdialoge / Floating Panels (z. B. Multi-Picker / Multi-Selection Bar).

**Pflicht:**

- Kopf bzw. Griffbereich · Schließen/Abbruch · beweglich/verschiebbar · visuell nahe an `dialog_panel_workbench` · Theme-Support

**Optional:**

- Picker · Meta-Footer (wenn inhaltlich sinnvoll)

**Aktueller Einsatz:** `picker_multi.panel_bar` als beweglicher Multi-Picker-Dialog.

---

## 5. Dialog-Inventar

| Bezeichner | Trigger | Template | Besonderheiten |

|---|---|---|---|
| `dialog.measurement_profile_runtime` | `dashboard_selection.btn_measurement_profile_runtime_info` | `dialog_info_popup` | Schrittliste, Inline-Details pro Schritt |
| `dialog.analysis_log` | Dashboard Analyse/Cache Logs | `dialog_panel_workbench` | Logfilter, Markieren, Wrap, Copy |
| `dialog.logs_record_start` | `logs_main.btn_record_start_header` | `dialog_panel_workbench` | Recorder-Startdialog mit Name, letzter Auswahl und Startaktion |
| `dialog.query_info` | Query-/Info-Popups via `InfluxBroPopup.show(...)` | `dialog_info_popup` | Query-/Text-/History-Inhalte |
| `dialog.analysis_strategy_help` | Hilfe im Strategiedialog | `dialog_info_popup` | JSON-Beispiele |
| `dialog.reference_detail` | Referenzdetails | `dialog_info_popup` | Detailansicht |
| `dialog.raw_outlier_params` | Raw Outlier Parameter | `dialog_panel_workbench` | Parameter-/Formdialog |
| `dialog.analysis_strategy` | Strategiedialog | `dialog_panel_workbench` | Chips, JSON, Strategieauswahl |
| `dialog.change_preview` | Change Preview | `dialog_panel_workbench` | Vorschau/Änderungsliste |
| `dialog.repair_wizard` | Repair Wizard | `dialog_panel_workbench` | Wizard-Ablauf, Stepper |
| `dialog.page_search` | Seitensuche | `dialog_panel_workbench` | Suche, Treffer, Picker |
| `dialog.settings_organizer` | Settings Organizer | `dialog_panel_workbench` | Arbeitsdialog |
| `dialog.jobs_timers_history` | Jobs Timer History | `dialog_panel_workbench` | Tabellen-/Historydialog |
| `dialog.dq_detail` | DQ Detail | `dialog_panel_workbench` | Detail-/Analysebereich |
| `dialog.export_target` | Export Ziel | `dialog_panel_workbench` | Formular-/Zielauswahl |
| `dialog.confirm_action` | Confirm-Dialoge | `dialog_confirm_action` | kompakt, Severity-Indicator |

---

## 6. Vollständigkeits-Checkliste (PFLICHT vor Fertigmeldung)

Vor jedem Commit eines neuen oder geänderten Dialogs MÜSSEN diese Punkte abgehakt sein:

- [ ] Eindeutiger Dialog-Bezeichner vergeben (`dialog.<bereich>_<funktion>`)
- [ ] Standard-Template gewählt (Erweiterung mit fachlicher Begründung dokumentiert)
- [ ] Visueller Abgleich mit `demo/dialog-mockup-themed.html` durchgeführt
- [ ] Titelzeile aussagekräftig
- [ ] Beschreibungs-Sektion mit genau einer kurzen Zeile
- [ ] Info-Button + Handbuch-Button vorhanden, klar getrennt
- [ ] Fenster-Aktionen rechts oben in korrekter Reihenfolge
- [ ] Meta-Indicator als dezenter Debug-Punkt links unten
- [ ] Footer-Aktionen rechts unten (bei Arbeitsdialogen)
- [ ] Alle 4 Zustände (Loading/Empty/Error/Success) abgebildet
- [ ] Tastatur-Bindings implementiert (`Esc`, `Enter`, `Tab`-Trap, `F1`, `Ctrl+I`, `Ctrl+W`)
- [ ] Initial-Focus und Focus-Return korrekt gesetzt
- [ ] Funktioniert in allen 5 Themes ohne Anpassung
- [ ] Keine hartcodierten Farben — alle über `var(--c-...)`
- [ ] Logging mit allen Pflichtfeldern aktiv
- [ ] Position/Größe werden pro Bezeichner persistiert
- [ ] `data-ib-pickkey` und `data-ib-instancekey` an allen relevanten Elementen

---

## 7. Verbindliche Referenz-Implementierung

**Datei:** `demo/dialog-mockup-themed.html`

Diese Datei ist die **autoritative visuelle und strukturelle Referenz** für alle Dialoge. Sie enthält:

- Vollständige CSS-Custom-Property-Tokens für alle 5 Themes
- Live-Beispiele für alle drei Standard-Templates (`info_popup`, `panel_workbench`, `confirm_action`)
- Implementierung aller Pflichtregeln (Tastatur, Fokus-Trap, Theme-Switch, Severity, Confirm-Phrase)
- Token-Namen wie `--c-bg`, `--c-text`, `--c-accent`, `--c-danger`, `--c-shadow-md` etc.

**Pflicht für OpenCode und alle Entwickler:**

- Vor Implementierung eines neuen Dialogs MUSS die Referenz-Datei geöffnet und visuell abgeglichen werden.
- Bei Widerspruch zwischen Regeltext und Referenz-Implementierung gilt die Referenz-Implementierung.
- Änderungen an der Referenz-Datei erfordern eine entsprechende Anpassung dieser Regeln und werden im Versionskopf vermerkt.

**Theme-Tokens dürfen NICHT umbenannt werden.** Neue Tokens dürfen ergänzt werden, müssen aber für alle 5 Themes definiert sein.
