# Section Titles (Info Icon + Settings Button)

Applies to all pages/sections that have a visible title (e.g. `details > summary`, cards, panels).

Required pattern

- Each section title gets an info icon AND a settings button next to it.
- The settings button (gear icon) is inserted BEFORE the info icon.
- Visual order: `[Section Title] [⚙ Settings] [i Info]`
- Clicking the settings icon navigates to `./config` and passes a `settings_ref` context so the settings page filters to the most relevant parameters for that section.
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
- It scans `main.content details > summary .ib_summary_row`, inserts a `.ib_cfg_icon` button for known sections, and places it before the info icon when one exists.
- The settings button is NOT injected on `config.html` (the settings page itself already has back buttons).

CSS

- `.ib_cfg_icon` is defined in `_topbar.html` (22x22px, circular, gear SVG icon).
- `.ib_info_icon` is defined in `_topbar.html` (22x22px, circular, "i" text).
- Both use `flex: 0 0 auto` so they don't shrink.

Notes

- Use `type="button"` so it never submits forms.
- The click handler is global (see `_tooltips.html`) and stops propagation so the `details` does not toggle.
- The settings button click handler is also global (in `_topbar.html`) and stops propagation.
- The settings page must show a visible context-filter chip with a clear action when opened with `settings_ref`.
