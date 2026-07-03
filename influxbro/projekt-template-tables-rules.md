
# Tables (Standard)

Applies to all list tables (Jobs, Cache, Timer Jobs, Backup, Restore, History, Dashboard lists).

## Structure

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
- Tabellen mit vielen Aktionen sollten zwei Leisten trennen:
  - Standard Actions: allgemeine Tabellensteuerung (Refresh, Abbruch, Breiten, Wrap, Filter)
  - Customer Actions: tabellen- oder domänenspezifische Aktionen darunter
- Wenn Status-/Infotext für eine Tabelle gebraucht wird, soll dieser in einem eigenen kleinen Panel/Kartenblock unter der Standard-Action-Leiste stehen, nicht inline zwischen Buttons.
- Prefer a dedicated `Liste aktualisieren` (reload) button in the table toolbar (above the list), not mixed into unrelated page action blocks.
- Use an icon-only refresh button for `Liste aktualisieren` (with `aria-label`).
- Use relative URLs (Ingress-friendly).
- Every table has a unique table title (Tabellenueberschrift) rendered above the table.
  - The title text must be unique within the page.
  - The title belongs to the table/list (not the page) and stays visible above the scroll area.
- The table including its controls is framed as one visual element.
  - The frame surrounds title + toolbar + scroll area (one cohesive block).

## Required features

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
  - Dies ist der Standardzustand fuer Tabellen ohne gespeicherte Spaltenbreiten.
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
  - Header colors are global and configurable:
    - Background: `ui_table_header_bg`
    - Text: `ui_table_header_fg`
    - Pages should use CSS vars `--ib-table-head-bg` / `--ib-table-head-fg` (defined in `_topbar.html`).
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
    - A short introduction that explains the function and content of the table so a user immediately understands what this table is for
    - Column list with a precise description for each column
    - Action column(s): a detailed explanation for every action
    - All applicable toolbar actions/buttons/checkboxes/filter toggles/window-fit controls for this table; no table-specific control may be omitted
  - The table title line (`.table_title`) and the table action/title header (`.table_head`) must remain fixed above the scroll area and must not scroll away with the table content.
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

## Recommended CSS

- Prefer `.ib_tbl` (truncate by default) and `.ib_wrap` (wrap mode).
- Keep font small for dense tables, but readable.
- Use a framed container for the whole list block (title + controls + table), e.g.:

```css
.table_wrap { border: 1px solid #ddd; border-radius: 12px; padding: 12px; }
.table_title { font-weight: 800; font-size: 14px; margin-bottom: 6px; }
.table_head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.table_box { border: 1px solid #eee; border-radius: 12px; overflow: auto; margin-top: 10px; }
```
