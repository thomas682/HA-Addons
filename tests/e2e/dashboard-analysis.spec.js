const { test, expect } = require('@playwright/test');

test.describe('Dashboard Analyse', () => {
  test('complete analysis flow: select source, run analysis, check outliers', async ({ page }) => {
    // Step 1: Navigate to dashboard
    await page.goto('/');
    await expect(page).toHaveTitle(/InfluxBro/);

    // Step 2: Select measurement "Wh"
    await page.fill('#measurement', 'Wh');
    await page.locator('#measurement').press('Enter');
    await expect(page.locator('#measurement')).toHaveValue('Wh');

    // Wait for fields to load
    await page.waitForTimeout(1000);
    await expect(page.locator('#field_list option')).toHaveCount({ min: 1 });

    // Step 3: Select field "value"
    await page.fill('#field', 'value');
    await page.locator('#field').press('Enter');
    await expect(page.locator('#field')).toHaveValue('value');

    // Step 4: Select entity_id "sma_30581_energy_bezug_wh_hm2"
    await page.fill('#entity_id', 'sma_30581_energy_bezug_wh_hm2');
    await page.locator('#entity_id').press('Enter');
    await expect(page.locator('#entity_id')).toHaveValue('sma_30581_energy_bezug_wh_hm2');

    // Step 5: Wait for friendly_name to populate (should have 1 option)
    await page.waitForTimeout(1000);
    const friendlyCount = await page.locator('#friendly_name_list option').count();
    expect(friendlyCount).toBeGreaterThanOrEqual(1);

    // Step 6: Select time range "all"
    await page.selectOption('#range', 'all');

    // Step 7: Click Analyse button
    await page.click('#load');

    // Step 8: Wait for analysis to complete
    await page.waitForTimeout(5000);

    // Step 9: Check if outlier overview table has content or empty state
    const outlierBody = page.locator('#raw_outlier_body tr');
    const outlierCount = await outlierBody.count();

    if (outlierCount > 0) {
      const firstRow = outlierBody.first();
      await expect(firstRow).toBeVisible();
      console.log(`Found ${outlierCount} outlier rows`);
    } else {
      const emptyMsg = page.locator('#raw_outlier_body td');
      const text = await emptyMsg.first().textContent();
      console.log('No outliers found:', text);
    }

    // Step 10: Verify outlier row count display is visible
    await expect(page.locator('#raw_outlier_row_count')).toBeVisible();
  });
});
