# InfluxBro UI Template (Masterdesign)

This file defines the standard look/behavior for GUI elements in this add-on.
When adding or changing UI elements, check this file first and align the page markup/CSS/JS accordingly.

Goal

- Keep tables and controls consistent across pages.
- Make global UI adjustments possible from one place ("master"), with explicit per-page overrides ("child").

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

Checkboxes/selects/inputs

- Align vertically in toolbars.
- Prefer a label text that matches what the user expects (German UI).
