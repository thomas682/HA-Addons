
# UI Picker / S-Picker (Pickkey + data-ui)

The UI Picker (Picker/S-Picker) identifies elements primarily by `data-ib-pickkey`.

`data-ui` remains required for consistency, but `data-ib-pickkey` is the canonical, chat-stable identifier.

Rules

- Every visible, support-relevant UI element MUST have a stable `data-ui`.
- Every visible UI element MUST be uniquely referenzierbar via `data-ib-pickkey`.
- For dynamically generated chips/buttons/dialogs/toolbars (created via JS/`innerHTML`), you MUST add BOTH `data-ui` and `data-ib-pickkey` at creation time.
  - Example pattern: `data-ui="cache_timeline.btn_oltype.counter"`.
- The pickkey naming MUST be globally unique and stable.
  - Preferred: `<page>.<section>.<element>.<role>` (lowercase, `.` separator).
  - Examples:
    - `topbar.settings_organizer.button`
    - `sidebar.nav.dashboard.link`
    - `dashboard.outliers.table`
    - `settings.connection.input.host`
- S-Picker output MUST use the canonical format:
  - `<PICK:<Page>|<pickkey>>`
- Fallback labeling (when no `data-ui`/`id` exists) should be informative but safe.
  - Current fallback format: `fallback:<css> | <short label snippet>`.
  - The snippet MUST NOT include input values (could be secrets); only static labels like `aria-label`, `name`, `placeholder`, or short `textContent`.
  - IMPORTANT: fallback is migration-only and must not be relied upon for support.

## Pick-Ergebnisdialog Minimalmodus

Diese Regel gilt nur fuer den Dialog, der nach einem erfolgreichen Pick angezeigt wird. Sie gilt NICHT fuer Picker/S-Picker selbst und NICHT fuer andere Dialoge.

Pflichtverhalten:

- Der Dialog zeigt ausschliesslich den gepickten Text und die Fensteraktionen `Minimieren`, `Maximieren` und `Schliessen`.
- Beim Oeffnen MUSS der gepickte Text automatisch in die Zwischenablage kopiert werden.
- Wenn das Kopieren fehlschlaegt, MUSS der Dialog eine kurze sichtbare Statusmeldung anzeigen.
- Der gepickte Text MUSS als Textinhalt gesetzt werden, niemals als unsanitized HTML.
- Der Dialog darf keine Toolbar, keine Doku-/Info-Leiste, keinen Meta-Footer und keine fachfremden Kinder enthalten.
- Fensteraktionen bleiben rechts oben und muessen tastaturbedienbar sein.
- Der Schliessen-Button schliesst nur den Pick-Ergebnisdialog und darf den Picker-Modus nicht erneut aktivieren.
- Der Minimaldialog braucht stabile `data-ui` und `data-ib-pickkey` fuer Root, Text und Fensteraktionen.
