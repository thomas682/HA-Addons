const { test, expect } = require('@playwright/test');

test.describe('Dashboard', () => {
  test('loads dashboard page', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/InfluxBro/);
  });

  test('settings buttons visible in section summaries', async ({ page }) => {
    await page.goto('/');
    const settingsBtns = page.locator('.ib_cfg_icon');
    await expect(settingsBtns).toHaveCount({ min: 1 });
  });

  test('raw outlier search bar exists', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#raw_search_bar')).toBeVisible();
  });

  test('graph reset button exists', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#graph_reset_time')).toBeVisible();
  });
});

test.describe('Settings Page', () => {
  test('loads settings page', async ({ page }) => {
    await page.goto('/config');
    await expect(page).toHaveTitle(/InfluxBro.*Einstellungen/);
  });

  test('back buttons visible in section summaries', async ({ page }) => {
    await page.goto('/config');
    const backBtns = page.locator('.ib_cfg_back_icon');
    await expect(backBtns).toHaveCount({ min: 1 });
  });
});
