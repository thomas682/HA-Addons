# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.js >> Dashboard >> settings buttons visible in section summaries
- Location: tests/e2e/dashboard.spec.js:9:3

# Error details

```
Error: locator._expect: expectedNumber: expected float, got object
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - banner "Topbar"
  - generic "page.title.card" [ref=e2]:
    - generic [ref=e3]:
      - generic [ref=e4]:
        - generic [ref=e5]: InfluxBro
        - generic [ref=e6]: by Thomas Schatz
        - generic [ref=e7]: "Aktiv: PC | Version: 1.12.197"
      - generic "nav.donate" [ref=e8]:
        - link "Donate with PayPal" [ref=e9] [cursor=pointer]:
          - /url: https://www.paypal.com/donate/?hosted_button_id=ZWZE3WM4NBUW6
          - img "Donate with PayPal" [ref=e10]
        - link "Buy me a coffee" [ref=e11] [cursor=pointer]:
          - /url: https://buymeacoffee.com/thomasschatz
          - img "Buy me a coffee" [ref=e12]
    - generic [ref=e13]:
      - generic "topbar.profile" [ref=e14]:
        - combobox "nav.profile.select" [ref=e15]:
          - option "MOBIL"
          - option "PC" [selected]
        - button "Anwenden" [ref=e16]
        - button "Speichern" [ref=e17]
        - button "Info" [ref=e18]
        - button "Picker" [ref=e19]
        - button "S-Picker" [ref=e20]
      - generic "topbar.zoom" [ref=e21]:
        - text: Zoom
        - button "Zoom out" [ref=e22]: "-"
        - text: 100%
        - button "Zoom in" [ref=e23]: +
      - generic [ref=e24]:
        - textbox "page.search" [ref=e25]:
          - /placeholder: Elemente auf dieser Seite suchen...
        - button "Feld leeren" [ref=e26] [cursor=pointer]:
          - img
      - button "Vorheriger Treffer" [ref=e27]: <
      - button "Naechster Treffer" [ref=e28]: ">"
      - button "Zu Einstellungen" [ref=e29]:
        - img [ref=e30]
      - button "Sucheinstellungen" [ref=e33]:
        - img [ref=e34]
      - button "Alle oeffnen" [ref=e37]:
        - img [ref=e38]
      - button "Alle schliessen" [ref=e40]:
        - img [ref=e41]
  - generic "errors.statusbar" [ref=e43]:
    - generic [ref=e44]: "Letzter Fehler:"
    - generic [ref=e45]: "Influx:"
    - 'generic "Influx Verbindung: OK" [ref=e46]': OK
    - button "Letzter Fehler" [ref=e47]
    - button "Fehlerdialog" [ref=e48]
    - button "Git Bugreport" [ref=e49]:
      - img [ref=e50]
      - text: Git Bugreport
  - generic [ref=e53]:
    - navigation "Navigation" [ref=e54]:
      - link "Dashboard" [ref=e55] [cursor=pointer]:
        - /url: ./
        - generic [ref=e56]: D
        - generic [ref=e57]: Dashboard
      - link "Statistik" [ref=e58] [cursor=pointer]:
        - /url: ./stats
        - generic [ref=e59]: T
        - generic [ref=e60]: Statistik
      - link "Datenqualitaet" [ref=e61] [cursor=pointer]:
        - /url: ./quality
        - generic [ref=e62]: Q
        - generic [ref=e63]: Datenqualitaet
      - link "Monitor" [ref=e64] [cursor=pointer]:
        - /url: ./monitor
        - generic [ref=e65]: O
        - generic [ref=e66]: Monitor
      - link "Backup" [ref=e67] [cursor=pointer]:
        - /url: ./backup
        - generic [ref=e68]: B
        - generic [ref=e69]: Backup
      - link "Restore" [ref=e70] [cursor=pointer]:
        - /url: ./restore
        - generic [ref=e71]: R
        - generic [ref=e72]: Restore
      - link "Kombinieren" [ref=e73] [cursor=pointer]:
        - /url: ./combine
        - generic [ref=e74]: C
        - generic [ref=e75]: Kombinieren
      - link "Export" [ref=e76] [cursor=pointer]:
        - /url: ./export
        - generic [ref=e77]: X
        - generic [ref=e78]: Export
      - link "Import" [ref=e79] [cursor=pointer]:
        - /url: ./import
        - generic [ref=e80]: M
        - generic [ref=e81]: Import
      - link "Logs" [ref=e82] [cursor=pointer]:
        - /url: ./logs
        - generic [ref=e83]: L
        - generic [ref=e84]: Logs
      - link "Jobs & Cache" [ref=e85] [cursor=pointer]:
        - /url: ./jobs
        - generic [ref=e86]: J
        - generic [ref=e87]: Jobs & Cache
      - link "History" [ref=e88] [cursor=pointer]:
        - /url: ./history
        - generic [ref=e89]: H
        - generic [ref=e90]: History
      - link "Diagnose" [ref=e91] [cursor=pointer]:
        - /url: ./dbinfo
        - generic [ref=e92]: I
        - generic [ref=e93]: Diagnose
      - link "Changelog" [ref=e94] [cursor=pointer]:
        - /url: ./info
        - generic [ref=e95]: i
        - generic [ref=e96]: Changelog
      - link "Handbuch" [ref=e97] [cursor=pointer]:
        - /url: ./manual
        - generic [ref=e98]: "?"
        - generic [ref=e99]: Handbuch
      - link "Profilverwaltung" [ref=e100] [cursor=pointer]:
        - /url: ./profiles
        - generic [ref=e101]: P
        - generic [ref=e102]: Profilverwaltung
      - link "Einstellungen" [ref=e103] [cursor=pointer]:
        - /url: ./config
        - generic [ref=e104]: S
        - generic [ref=e105]: Einstellungen
      - generic "nav.status" [ref=e106]:
        - generic [ref=e107]: Status
        - generic [ref=e108]:
          - button "Refresh" [ref=e109] [cursor=pointer]
          - generic [ref=e110]: Loescht abgeschlossene Eintraege.
        - generic "nav.sysinfo" [ref=e112]:
          - generic [ref=e113]: "Mem: 149.3 MB | Data: 15.2 MB | Disk: 16.14 GB / 40.63 GB | Load1: 0.01025390625 (CPU 4)"
    - main "dashboard.page" [ref=e114]:
      - heading "Dashboard" [level=2] [ref=e116]
      - generic "dashboard.backup_badge"
      - group "section.selection" [ref=e117]:
        - generic "▸ Auswahl Zu Einstellungen" [ref=e118] [cursor=pointer]:
          - text: ▸
          - generic [ref=e119]:
            - generic [ref=e120]: Auswahl
            - generic [ref=e121]:
              - button "Zu Einstellungen" [ref=e122]:
                - img [ref=e123]
              - button "Dieser Button (button.ib_info_icon)" [ref=e125]:
                - img [ref=e126]
        - option "Letzte 1h"
        - option "Letzte 6h"
        - option "Letzte 12h"
        - option "Letzte 24h" [selected]
        - option "Letzte 7 Tage"
        - option "Letzte 30 Tage"
        - option "Letzte 90 Tage"
        - option "Letztes Jahr"
        - option "Dieses Jahr"
        - option "Letzte 12 Monate"
        - option "Letzte 24 Monate"
        - option "Alle"
        - option "Benutzerdefiniert…"
      - group "section.graph" [ref=e129]:
        - generic "▸ Grafische Analyse Zu Einstellungen" [ref=e130] [cursor=pointer]:
          - text: ▸
          - generic [ref=e131]:
            - generic [ref=e132]: Grafische Analyse
            - generic [ref=e133]:
              - button "Zu Einstellungen" [ref=e134]:
                - img [ref=e135]
              - 'button "Dieser Button : Details (button.ib_info_icon)" [ref=e137]':
                - img [ref=e138]
        - option "Dynamisch" [selected]
        - option "Manuell"
      - group "section.raw" [ref=e141]:
        - generic "▸ Raw Daten Analyse Zu Einstellungen" [ref=e142] [cursor=pointer]:
          - text: ▸
          - generic [ref=e143]:
            - generic [ref=e144]: Raw Daten Analyse
            - generic [ref=e145]:
              - button "Zu Einstellungen" [ref=e146]:
                - img [ref=e147]
              - 'button "Dieser Button : Rows: 0 / 0 (button.ib_info_icon)" [ref=e149]':
                - img [ref=e150]
      - group "section.filterlist" [ref=e153]:
        - generic "▸ Bearbeitungsliste Zu Einstellungen" [ref=e154] [cursor=pointer]:
          - text: ▸
          - generic [ref=e155]:
            - generic [ref=e156]: Bearbeitungsliste
            - generic [ref=e157]:
              - button "Zu Einstellungen" [ref=e158]:
                - img [ref=e159]
              - 'button "Dieser Button : Rows: 0 / 0 (button.ib_info_icon)" [ref=e161]':
                - img [ref=e162]
        - option "Filter frei"
        - option "Counter Ausreisser" [selected]
        - option "nicht ansteigende Spruenge"
        - option "Grenzen"
        - option "Stoerphasensuche"
        - option "NULL Werte"
        - option "0-Werte"
        - option "alle werte"
        - option "alle" [selected]
        - option "primaer"
        - option "sekundaer"
```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  | 
  3  | test.describe('Dashboard', () => {
  4  |   test('loads dashboard page', async ({ page }) => {
  5  |     await page.goto('/');
  6  |     await expect(page).toHaveTitle(/InfluxBro/);
  7  |   });
  8  | 
  9  |   test('settings buttons visible in section summaries', async ({ page }) => {
  10 |     await page.goto('/');
  11 |     const settingsBtns = page.locator('.ib_cfg_icon');
> 12 |     await expect(settingsBtns).toHaveCount({ min: 1 });
     |                                ^ Error: locator._expect: expectedNumber: expected float, got object
  13 |   });
  14 | 
  15 |   test('raw outlier search bar exists', async ({ page }) => {
  16 |     await page.goto('/');
  17 |     await expect(page.locator('#raw_search_bar')).toBeVisible();
  18 |   });
  19 | 
  20 |   test('graph reset button exists', async ({ page }) => {
  21 |     await page.goto('/');
  22 |     await expect(page.locator('#graph_reset_time')).toBeVisible();
  23 |   });
  24 | });
  25 | 
  26 | test.describe('Settings Page', () => {
  27 |   test('loads settings page', async ({ page }) => {
  28 |     await page.goto('/config');
  29 |     await expect(page).toHaveTitle(/InfluxBro.*Einstellungen/);
  30 |   });
  31 | 
  32 |   test('back buttons visible in section summaries', async ({ page }) => {
  33 |     await page.goto('/config');
  34 |     const backBtns = page.locator('.ib_cfg_back_icon');
  35 |     await expect(backBtns).toHaveCount({ min: 1 });
  36 |   });
  37 | });
  38 | 
```