const { test, expect } = require('@playwright/test');

test.describe('DQ + Rollup Smoke', () => {
  test('DQ page loads and debug API responds', async ({ page }) => {
    await page.goto('/dq');
    await expect(page.locator('main[data-ui="dq_page.main"]')).toHaveCount(1);

    // Ensure debug panel exists
    await expect(page.locator('#dbg_out')).toHaveCount(1);

    // Reload debug (best-effort) and ensure JSON is rendered
    await page.locator('#dbg_reload').click();
    await expect(page.locator('#dbg_out')).toContainText('"ok": true', { timeout: 15_000 });
  });

  test('Rollup page loads (even without Influx configured)', async ({ page }) => {
    await page.goto('/rollup');
    await expect(page.locator('main[data-ui="rollup_page.main"]')).toHaveCount(1);

    // Profiles select exists
    await expect(page.locator('#profile_id')).toHaveCount(1);

    // The page may show an error if Influx is not configured; assert no hard crash.
    await page.waitForTimeout(800);
    await expect(page.locator('body')).toContainText('Verdichtung');
  });
});
