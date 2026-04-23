# InfluxBro UI Template (Masterdesign)

This file defines the standard look/behavior for GUI elements in this add-on.
When adding or changing UI elements, check this file first and align the page markup/CSS/JS accordingly.

Goal

- Keep tables and controls consistent across pages.
- Make global UI adjustments possible from one place ("master"), with explicit per-page overrides ("child").

## Section Titles (Info Icon + Settings Button)

Applies to all pages/sections that have a visible title (e.g. `details > summary`, cards, panels).

Required pattern

- Each section title gets an info icon AND a settings button next to it.
- The settings button (gear icon) is inserted BEFORE the info icon.
- Visual order: `[Section Title] [⚙ Settings] [i Info]`
- Clicking the settings icon navigates to `./config` and (when possible) jumps to the most relevant setting for that section.
- Clicking the info icon opens the global info popup (resizable, scrollbars, wrap toggle, copy).
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

Settings button injection

- The settings button (`.ib_cfg_icon`) is auto-injected by a global script in `_topbar.html`.
- It runs on ALL pages that include `_topbar.html`.
- It finds every `summary .ib_summary_row .ib_info_icon` and inserts a `.ib_cfg_icon` button before it.
- The settings button is NOT injected on `config.html` (the settings page itself already has back buttons).

CSS

- `.ib_cfg_icon` is defined in `_topbar.html` (22x22px, circular, gear SVG icon).
- `.ib_info_icon` is defined in `_topbar.html` (22x22px, circular, "i" text).
- Both use `flex: 0 0 auto` so they don't shrink.

Notes

- Use `type="button"` so it never submits forms.
- The click handler is global (see `_tooltips.html`) and stops propagation so the `details` does not toggle.
- The settings button click handler is also global (in `_topbar.html`) and stops propagation.

## UI Picker / S-Picker (data-ui + Fallback)

The UI Picker (Picker/S-Picker) identifies elements primarily by `data-ui`.

Rules

- Every clickable UI control should have a stable `data-ui`.
- For dynamically generated chips/buttons (created via JS/`innerHTML`), you MUST add `data-ui` at creation time.
  - Example pattern: `data-ui="cache_timeline.btn_oltype.counter"`.
- Fallback labeling (when no `data-ui`/`id` exists) should be informative but safe.
  - Current fallback format: `fallback:<css> | <short label snippet>`.
  - The snippet MUST NOT include input values (could be secrets); only static labels like `aria-label`, `name`, `placeholder`, or short `textContent`.

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

## `data-ui` Naming

Applies to all interactive and inspectable GUI elements.

Required format

- Use `page_section.role_action`
- All parts must be lowercase and use `_`
- The name should make all three things obvious:
  - page/context
  - visual/functional section
  - role and action of the element

Preferred role prefixes

- `btn_` for buttons
- `input_` for text/number inputs
- `select_` for selects
- `chk_` for checkboxes
- `tbl_` for tables
- `panel_` for panels/containers
- `txt_` for text/status/info fields
- `dlg_` for dialogs
- `row_` for toolbar/action rows
- `handle_` for resize/split handles

Examples

- `dashboard_caching.btn_cache_pruefen`
- `dashboard_analysis.btn_analyse_mit_cache`
- `dashboard_outliers.tbl_ausreisser`
- `dashboard_raw.btn_query_test`
- `settings_yaml.btn_yaml_daten_einlesen`

Rules

- Prefer the visible button meaning over vague technical names.
- If the button text is the clearest description, use that text in normalized form.
- Avoid generic names like `section.raw`, `dashboard.actions`, `graph.refresh`.
- If a container and its button both need names, give them distinct roles, e.g.:
  - `dashboard_caching.btn_query_anzeigen`
  - `dashboard_caching.panel_query_details`

## Tooltips

Applies to all pages and interactive elements.

Required format

- Tooltip line 1: a short description of the element/function (maximum about 2 short lines in total when rendered by the browser)
- Tooltip line 2: the stable element name in parentheses, e.g. `(dashboard_caching.btn_cache_pruefen)`
- Prefer concise functional wording over long explanations
- Tooltips must not be shown while `Picker` or `S-Picker` is active

Rules

- Use the explicit tooltip definition from the template when present
- If no explicit tooltip exists, derive a short tooltip from nearby label/help text
- Do not use long prose paragraphs in native `title` tooltips
- Detailed explanations still belong into info popups, not into native hover tooltips

## Storage Policy (Global vs. Profile-based)

This policy applies to ALL pages and functions of the app, not only Dashboard.

### Global (server-side) state

Store server-side when the value changes the functional behavior or data scope of the app and should therefore be identical on iMac and iPhone.

Examples:

- source selection:
  - `measurement`
  - `field`
  - `measurement_filter`
  - `entity_id`
  - `friendly_name`
- time selection:
  - `range`
  - `start`
  - `stop`
- analysis-relevant values:
  - selected outlier types
  - effective analysis start value / oldest known point per series
  - analysis limits / functional thresholds
- other functional selections on Statistics / Logs / Import / Export / Backup / Restore / Monitor / Jobs / History

Rule:

- If a state changes what data is queried, filtered, analyzed, imported, exported, restored, or processed, it belongs to the global/server-side state.

### Profile-based (UI / optical) state

Store profile-based when the value only changes appearance, ergonomics, or layout and may intentionally differ between profiles like `PC` and `MOBIL`.

Examples:

- section open/closed state:
  - `analysis_open`
  - `selection_open`
  - `raw_open`
  - `graph_open`
  - `filterlist_open`
  - analogous `*_open` values on all pages
- table and layout state:
  - table heights
  - splitters / resize values
  - column widths
  - wrap / no-wrap
  - column visibility
  - window-fit / auto-width preferences
- display state:
  - font sizes
  - row heights / density
  - popup sizes
  - device-specific UI geometry

Rule:

- If a state changes only how the UI looks or feels, but not what data is processed, it belongs to the active UI profile.

### Do not mix both responsibilities

- Functional selection must not be restored from browser-only local state if a server-side/global source exists.
- UI profile state must not overwrite global functional selections.
- A page may combine both, but must keep them technically separate.

Recommended precedence:

1. Global functional state
2. Profile-based UI state
3. Temporary local/session-only helpers only when they are purely ephemeral

### App-wide Inventory (What belongs where)

This inventory applies to ALL pages/functions of the app.

#### Dashboard

Global / server-side:
- `measurement`
- `field`
- `measurement_filter`
- `entity_id`
- `friendly_name`
- `range`
- `start`
- `stop`
- selected outlier types
- persisted analysis start / oldest known point per series

Profile-based:
- `selection_open`
- `analysis_open`
- `raw_open`
- `graph_open`
- `filterlist_open`
- raw/outlier table heights
- raw/outlier resize values
- graph height / splitter values
- popup sizes / wrap / local display geometry

#### Statistics

Global / server-side:
- active source selection
- time range
- functional statistics filters
- selected stats mode / cache scope / job-related functional selections

Profile-based:
- section open/closed states
- table height
- wrap / column visibility / column widths
- local popup/dialog sizes

#### Logs

Global / server-side:
- functional filters that change what log data is queried

Profile-based:
- view/layout preferences
- table/list geometry
- open/closed states

#### Backup / Restore

Global / server-side:
- selected backup source/target
- restore selection
- functional operation parameters

Profile-based:
- table height
- popup/layout state
- section open/closed state

#### Import / Export / Combine

Global / server-side:
- source/target mapping
- time range
- transformation-relevant settings
- operation mode selections

Profile-based:
- table/dialog geometry
- open/closed sections
- wrap / visibility / sizing

#### Monitor / Jobs / History

Global / server-side:
- all functional monitor/job/history filters
- persisted jobs / history / pending state

Profile-based:
- list height
- open/closed states
- UI visibility / local layout only

#### Config / Profiles

Global / server-side:
- all real configuration values affecting runtime behavior

Profile-based:
- none of the functional config values themselves
- only visual representation / local configuration-page layout may be profile-based

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

## Logging Requirements

### Backend Logging (app.py)

Every API endpoint MUST log:

1. **Entry log** – when the endpoint is called, with key parameters
2. **Result log** – when the endpoint completes successfully, with result summary
3. **Error log** – when the endpoint fails, with error message and stacktrace (`exc_info=True`)

Standard pattern:

```python
@app.post("/api/example")
def api_example():
    body = request.get_json(force=True) or {}
    LOG.info("api.example called from=%s param1=%s param2=%s",
        request.remote_addr, body.get("param1",""), body.get("param2",""))
    t0 = time.monotonic()
    try:
        ...
        dur_ms = int((time.monotonic() - t0) * 1000)
        LOG.info("api.example done from=%s result=%s dur=%dms",
            request.remote_addr, result_summary, dur_ms)
        return jsonify({"ok": True, ...})
    except Exception as e:
        dur_ms = int((time.monotonic() - t0) * 1000)
        LOG.error("api.example error: %s dur=%dms", e, dur_ms, exc_info=True)
        return jsonify({"ok": False, "error": str(e)}), 500
```

Log format: `key=value` pairs, one line per log entry.

Required fields in entry logs:
- `from=` – client IP (`request.remote_addr`)
- Key parameters (measurement, field, entity_id, action type, etc.)

Required fields in result logs:
- `from=` – client IP
- Result summary (rows count, found count, success/failure)
- `dur=` – duration in milliseconds

### Client-Side Logging

Every page MUST:

1. **Report page view** on load via `POST ./api/page_view` with `{page: pathname}`
2. **Report UI actions** via `POST ./api/ui_event` for:
   - Button clicks (with `data-ui` attribute or element id)
   - Select changes (element id, new value)
   - Checkbox changes (element id, on/off)

Implementation: Global action reporter in `_topbar.html` that:
- Sends `page_view` on every page load
- Listens for `click` and `change` events on buttons, selects, checkboxes
- Throttles reports to 300ms to avoid flooding
- Uses `data-ui` attribute for consistent naming, falls back to element id

### What MUST Be Logged

| Category | Examples |
|---|---|
| Page views | Every page navigation/load |
| UI actions | Button clicks, select changes, checkbox toggles |
| API calls | All `/api/*` endpoint invocations |
| Config changes | Which fields were changed in `/api/config` POST |
| Errors | All exceptions with stacktrace |
| Duration | All API call durations in milliseconds |
