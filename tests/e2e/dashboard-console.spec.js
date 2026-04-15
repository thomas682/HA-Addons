const { test, expect } = require('@playwright/test');

test.describe('Dashboard Console', () => {
  test('dashboard loads without critical console or page errors', async ({ page }) => {
    const errors = [];

    page.on('console', (msg) => {
      const text = msg.text();
      if (/SyntaxError|already been declared|Unexpected end of input|Unexpected token/i.test(text)) {
        errors.push(`console:${text}`);
      }
    });

    page.on('pageerror', (err) => {
      const text = String(err && err.message ? err.message : err);
      if (/SyntaxError|already been declared|Unexpected end of input|Unexpected token/i.test(text)) {
        errors.push(`pageerror:${text}`);
      }
    });

    await page.goto('/');
    await expect(page.locator('main[data-ui="dashboard_page.main"]')).toHaveCount(1);
    await page.waitForTimeout(1500);

    expect(errors).toEqual([]);
  });
});
