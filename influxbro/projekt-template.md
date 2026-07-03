# InfluxBro UI Template (Masterdesign)

This file defines the standard look/behavior for GUI elements in this add-on.
When adding or changing UI elements, check this file first and align the page markup/CSS/JS accordingly.

Goal

- Keep tables and controls consistent across pages.
- Make global UI adjustments possible from one place ("master"), with explicit per-page overrides ("child").

## Master/Child override concept

Master

- This file defines the base behavior and appearance ("master") for element types.

Child overrides

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
