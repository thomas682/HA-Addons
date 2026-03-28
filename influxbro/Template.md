# InfluxBro UI Template (Masterdesign)

This file defines the standard look/behavior for GUI elements in this add-on.
When adding or changing UI elements, check this file first and align the page markup/CSS/JS accordingly.

Goal

- Keep tables and controls consistent across pages.
- Make global UI adjustments possible from one place ("master"), with explicit per-page overrides ("child").

## Section Titles (Info Icon)

Applies to all pages/sections that have a visible title (e.g. `details > summary`, cards, panels).

Required pattern

- Each section title gets an info icon next to it.
- Clicking the icon opens the global info popup (resizable, scrollbars, wrap toggle, copy).
- Text must be in German and should be detailed (describe purpose + controls + pitfalls).

Preferred markup

```html
<details open>
  <summary>
    <span class="ib_summary_row">
      <span>Auswahl</span>
      <button type="button" class="ib_info_icon"
        data-info-title="Auswahl"
        data-info-body="...sehr ausfuehrlicher Text...">i</button>
    </span>
  </summary>
  ...
</details>
```

Notes

- Use `type="button"` so it never submits forms.
- The click handler is global (see `_tooltips.html`) and stops propagation so the `details` does not toggle.

## Tables (Standard)

Applies to all list tables (Jobs, Cache, Timer Jobs, Backup, Restore, History, Dashboard lists).

### Structure

Preferred markup:

```html
<div class="table_wrap">
  <div class="table_title">Timer Jobs</div>
  <div class="table_head">
    <div class="tbl_actions">
      <!-- left-aligned controls (buttons/checkboxes/search) -->
    </div>
    <div class="muted">Optional hint / counters</div>
  </div>

  <div class="table_box" id="..._box">
    <table id="..." class="ib_tbl">
      <thead>...</thead>
      <tbody>...</tbody>
    </table>
  </div>
</div>
```

Notes

- Controls belong above the table and should be left-aligned.
- Prefer a dedicated `Liste aktualisieren` (reload) button in the table toolbar (above the list), not mixed into unrelated page action blocks.
- Use an icon-only refresh button for `Liste aktualisieren` (with `aria-label`).
- Use relative URLs (Ingress-friendly).
- Every table has a unique table title (Tabellenueberschrift) rendered above the table.
  - The title text must be unique within the page.
  - The title belongs to the table/list (not the page) and stays visible above the scroll area.
- The table including its controls is framed as one visual element.
  - The frame surrounds title + toolbar + scroll area (one cohesive block).

### Required features

- Column resize by dragging header borders.
  - Implemented via `InfluxBroTableCols.init('#table_id')`.
- Persistence: UI changes are saved automatically per list (per page + table id), and restored on next render.
  - Column widths (drag/auto-fit/window-fit)
  - Wrap toggle state
  - Per-column filter values
  - Table height (scroll area)
  - Sort state
  - Column visibility
- Button: `Spaltenbreite automatisch`
  - Calls `InfluxBroTableCols.autoFit('#table_id', {maxRows: ...})`.
- Button: `Fensterbreite`
  - Calls `InfluxBroTableCols.windowFit('#table_id')`.
  - Algorithm requirement:
    1) First set widths so that each column content is fully visible for the sampled rows.
    2) Measure the resulting full table width.
    3) Measure the visible area width (the container width that fits without horizontal scroll).
    4) Reduce each column width proportionally until the sum fits into the visible area.
- Toggle: `Umbruch` vs. `Abschneiden`
  - `Umbruch` enables multi-line cells.
  - Implemented via `InfluxBroTableWrap.setWrap('#table_id', true/false)`.
- Sticky header row (fixed while scrolling vertically inside the list box).
  - The header must not scroll away when the list scrolls in Y.
  - The scroll area height is adjustable and persisted (see Table height).
- Sorting: every column is sortable (client-side).
  - Click on the header toggles asc/desc.
  - Must be persisted per list.
  - If a column must not be sortable, mark the header with `data-nosort="1"`.
- Column visibility: columns can be shown/hidden.
  - Must be persisted per list.
  - Provide a column picker control (button near the table info icon).
- Optional: per-column filter row (Excel-like)
  - Toggle `Spaltenfilter`.
  - Implemented via `InfluxBroTableFilter.init('#table_id', {startHidden:true})`.
- Table height adjustable via a handle under the table.
  - Implemented via `InfluxBroTableHeight.attach(boxEl, 'unique_key')`.
  - Default visible area should be about 10 rows.
- Info icon (book) above the table.
  - Auto-injected when a table has an `id`.
  - Must be comprehensive and should contain:
    - Purpose (Sinn und Zweck) of this list
    - Column list with a precise description for each column
    - Action column(s): a detailed explanation for every action
  - Preferred: register a per-table spec via `window.InfluxBroTableInfoSpec[table_id]`.

Example (in the page template JS):

```js
window.InfluxBroTableInfoSpec = window.InfluxBroTableInfoSpec || {};
window.InfluxBroTableInfoSpec['timer_tbl'] = {
  purpose: 'Shows scheduled background jobs (timers) and their next/last run, plus manual controls.',
  columns: {
    'id': 'Stable timer id (used by the API).',
    'enabled': 'If false, the scheduler will not start this timer automatically.',
    'Modus': 'Current refresh mode and cadence (hours/daily).',
    'last run': 'Timestamp of the last finished run (persisted).',
    'next run': 'Computed next run timestamp based on settings.',
    'Kommentar': 'Short explanation of what this timer does.',
    'action': 'Manual controls for the timer job.'
  },
  actions: [
    'Modus: change refresh mode (hours/daily) and cadence.',
    'Start: start one due job immediately (best-effort pick).',
    'Abbruch: request cancellation of the currently running job (if any).'
  ]
};
```
- Row counters above the table.
  - Show row counts as `filtered / total`.
  - Must update when filters are applied.

### Recommended CSS

- Prefer `.ib_tbl` (truncate by default) and `.ib_wrap` (wrap mode).
- Keep font small for dense tables, but readable.
- Use a framed container for the whole list block (title + controls + table), e.g.:

```css
.table_wrap { border: 1px solid #ddd; border-radius: 12px; padding: 12px; }
.table_title { font-weight: 800; font-size: 14px; margin-bottom: 6px; }
.table_head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.table_box { border: 1px solid #eee; border-radius: 12px; overflow: auto; margin-top: 10px; }
```

## Master/Child override concept

Master

- This file defines the base behavior and appearance ("master") for element types.

Child overrides

- Individual pages may override:
  - default visible height
  - default wrap/filters state
  - additional buttons/actions
  - column widths and extra columns

Rule

- Overrides should be minimal and explicit.
- If the master changes, review and update derived pages accordingly.

## Other GUI elements (future)

Buttons

- Keep consistent sizing (e.g. `.btn_sm` / `.btn_xs`) and spacing.
- Place primary actions first, destructive actions last.

Modales Fenster / Query Fenster

- Query-/Info-Fenster muessen echte modale Fenster sein.
  - Sie duerfen sich nicht automatisch schliessen, nur weil ausserhalb des Fensters geklickt wurde.
  - Schliessen erfolgt explizit ueber `Schliessen` oder `Escape`.
- Das Fenster darf frei vergroessert werden.
  - Der Resize-Griff rechts unten muss die Breite bis nahe an die aktuelle Browserbreite erlauben.
  - Die Breite darf nur durch Viewport-/Padding-Grenzen begrenzt werden, nicht durch zu kleine fixe Maximalbreiten.
- Query-Fenster mit History muessen unter dem Hauptbereich `influxbro_popup_pre` einen eigenen History-Bereich besitzen.
  - Zwischen Query-Bereich und History-Bereich gibt es einen horizontalen Hoehen-Splitter.
  - Beide Bereiche muessen in der Hoehe anpassbar sein.
  - Die History darf nicht in einem separaten Popup aufgehen, wenn sie logisch Teil des Query-Fensters ist.
- Bevorzugte Struktur:
  - Kopfbereich
  - Steuer-/Aktionsbereich
  - Meta-Zeile
  - Query-Hauptbereich
  - Splitter
  - History-Bereich

Top/page title cards

- Dynamic title/page cards (for example `page.title.card`) must always return to the smallest height that still fully shows all currently visible controls.
- Do not feed a measured expanded runtime height back into the card's own persistent `min-height`.
- Separate:
  - a static minimum/base height
  - the live measured layout height used for page padding/offsets
- If content shrinks again (e.g. fewer wrapped controls, closed results, smaller zoom), the live height must shrink back as well.

Graphs

- Graph state and the last graph data should survive page navigation.
- Preferred approach: store a server-side pointer under `/data` that references an existing cache payload (no DB query on restore).
  - Dashboard example: write `/data/influxbro_dashboard_last.json` containing `cache_id` + selection metadata.
  - Restore policy: auto-restore only when the user has no active selection (e.g. entity_id/friendly_name empty) to avoid overwriting inputs.
  - On restore: load the cached payload from `/data` (e.g. `dash_cache/<cache_id>.data.json.gz`) and redraw the graph.
  - The UI still persists non-sensitive controls (checkboxes/selects) via the UI state store.

Checkboxes/selects/inputs

- Align vertically in toolbars.
- Prefer a label text that matches what the user expects (German UI).
- Checkbox size must stay consistent across pages and topbars.
  - Reuse the same visual scale as standard list/graph checkboxes such as `Dashboard: graph_markers`.
  - Preferred pattern: add class `row_sel` to the checkbox and avoid page-specific checkbox sizes unless there is a strong reason.

### Auswahlfeld (Master: Filter)

Use this pattern for filter/selection fields where the user can type freely, but still gets guided suggestions.

Required behavior

- Width
  - Auto width (default): as narrow as possible, but not wider than the average text width of the suggestion items.
  - Manual width: if auto width is disabled, use a fixed width from settings.
- Label row: above the field, left-aligned with the control, show `Name` and the item count `(n)`.
- Field height: just enough to display one line of text (no oversized 40px inputs).
- Short description: show a short, one-line explanation under the field.
- Detailed help: show a small `?` button before the short description. Clicking opens a popup with a detailed explanation.
- Persistence: the input value is persisted and restored via the UI state store.

Global settings (Einstellungen)

- `ui_sel_field_font_px`: font size inside the field
- `ui_sel_label_font_px`: font size of the label row (name + count)
- `ui_sel_desc_font_px`: font size of the short description
- `ui_sel_auto_width`: checkbox "Auto" (default true)
- `ui_sel_width_px`: manual width in px (used when Auto is off)
- When Auto is on: show the last computed width as the default value in the width input.

Preferred markup

```html
<div class="ib_sel" id="c_<name>">
  <label class="ib_sel_label">
    <span><Label text></span>
    <span id="cnt_<name>" class="muted"></span>
  </label>
  <div class="ib_sel_stack">
    <input id="<name>" list="<name>_list" placeholder="optional" />
    <datalist id="<name>_list"></datalist>
    <div class="ib_sel_desc">
      <button type="button" class="ib_sel_help" data-title="..." data-help="...">?</button>
      <div class="muted">Kurzer Text zur Erklaerung.</div>
    </div>
  </div>
</div>
```

### Auswahlfeld (Child: Zeiten)

This is a child of the filter selection field (inherits everything above) plus:

- The select provides the same interval options as used in Dashboard/Backup selection.
- If a range is selected, show the resolved start/stop timestamps in the label row (same line) after `(n)`.
- Width must be large enough so that `Name + (n) + range` fits in one line.
