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

### Required features

- Column resize by dragging header borders.
  - Implemented via `InfluxBroTableCols.init('#table_id')`.
- Button: `Spaltenbreite automatisch`
  - Calls `InfluxBroTableCols.autoFit('#table_id', {maxRows: ...})`.
- Button: `Fensterbreite`
  - Calls `InfluxBroTableCols.windowFit('#table_id')`.
- Toggle: `Umbruch` vs. `Abschneiden`
  - `Umbruch` enables multi-line cells.
  - Implemented via `InfluxBroTableWrap.setWrap('#table_id', true/false)`.
- Sticky header row.
- Optional: per-column filter row (Excel-like)
  - Toggle `Spaltenfilter`.
  - Implemented via `InfluxBroTableFilter.init('#table_id', {startHidden:true})`.
- Table height adjustable via a handle under the table.
  - Implemented via `InfluxBroTableHeight.attach(boxEl, 'unique_key')`.
  - Default visible area should be about 10 rows.
- Info icon (book) above the table.
  - Auto-injected when a table has an `id`.
  - Shows generic table help + column list.

### Recommended CSS

- Prefer `.ib_tbl` (truncate by default) and `.ib_wrap` (wrap mode).
- Keep font small for dense tables, but readable.

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
