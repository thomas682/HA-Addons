# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.js >> Dashboard >> raw outlier search bar exists
- Location: tests/e2e/dashboard.spec.js:15:3

# Error details

```
Error: page.goto: net::ERR_ADDRESS_UNREACHABLE at http://192.168.2.200:8099/
Call log:
  - navigating to "http://192.168.2.200:8099/", waiting until "load"

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
  12 |     await expect(settingsBtns).toHaveCount({ min: 1 });
  13 |   });
  14 | 
  15 |   test('raw outlier search bar exists', async ({ page }) => {
> 16 |     await page.goto('/');
     |                ^ Error: page.goto: net::ERR_ADDRESS_UNREACHABLE at http://192.168.2.200:8099/
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