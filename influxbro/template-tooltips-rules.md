# Tooltips

Applies to all pages and interactive elements.

## Design Authority

- The HTML design references are authoritative and take precedence over this rules file.
- If this file conflicts with a referenced HTML design, implement the HTML design.
- Chip/UI info tooltips MUST follow `demo/chip-tooltip-professional.html`.
- Chart/data-point tooltips MUST follow `demo/chart-tooltip-professional.html`.

## Native/Generated Tooltip Baseline

- Tooltip line 1: a short description of the element/function (maximum about 2 short lines in total when rendered by the browser).
- Tooltip line 2: the stable element name in parentheses, e.g. `(dashboard_caching.btn_cache_pruefen)`.
- Prefer concise functional wording over long explanations.
- Tooltips must not be shown while `Picker` or `S-Picker` is active.
- If no explicit tooltip exists, derive a short tooltip from nearby label/help text.
- Do not use long prose paragraphs in native `title` tooltips.
- Detailed explanations still belong into info popups or professional tooltip bodies, not into native browser hover tooltips.

## Chip/UI Info Tooltip Design

Use `demo/chip-tooltip-professional.html` for chips, filter badges, analysis type chips and similar UI elements that explain a selectable function.

Required structure and behavior:

- Chip has a visible label, severity/status dot when applicable, and a dedicated info affordance when the chip itself has another primary action.
- Tooltip container uses a professional dark panel with arrow, header, body and footer.
- Header contains icon/severity visual, title and stable key/subtitle.
- Body contains concise description, meta rows and optional example block.
- Meta rows include contextually relevant values such as severity, source and active/status/count.
- Footer contains a documentation action and a visible `?` shortcut hint when documentation exists.
- Hover/focus shows the tooltip briefly; click/Enter/Space on the info affordance pins it so links are clickable.
- Escape or outside click closes a pinned tooltip.
- Touch opens the tooltip pinned directly.
- Use `role="tooltip"` and connect the owner element via `aria-describedby` when a stable tooltip element/id exists.
- Sanitize all dynamic text before injecting HTML.
- Keep tooltip inside the viewport and align the arrow to the triggering chip where possible.

## Chart/Data-Point Tooltip Design

Use `demo/chart-tooltip-professional.html` for graph hovers, chart points and time-series data point inspection.

Required structure and behavior:

- Tooltip is anchored to the nearest data point, not to arbitrary mouse text targets.
- Tooltip follows the data point with viewport/container clamping.
- Chart hover shows crosshair and highlighted data point marker when the graph implementation supports it.
- Tooltip container uses the chart design: dark gradient panel, top accent line, bottom arrow, compact rounded geometry.
- Header contains source name and bucket/measurement/field context.
- Main value block shows the value prominently with tabular numerals, unit and exact timestamp.
- Delta to previous point is shown with direction, color and icon/state when previous data is available.
- Range context shows min/average/max and current-position marker when the data window supports it.
- Sparkline context is shown when nearby data points are available.
- Tooltip hides when leaving the chart area or while `Picker`/`S-Picker` is active.
- Sanitize all dynamic text before injecting HTML.

## Picker Compatibility

- Picker and S-Picker always suppress visible tooltips.
- Dynamically generated visible tooltip triggers must keep stable `data-ui` and `data-ib-pickkey` values.
- Fallback tooltip text must never include user-entered values that could be secrets.
