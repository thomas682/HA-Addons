const { test, expect } = require('@playwright/test');

const GAP_MS = 2500; // allow UI + async requests to settle

test.describe('Dashboard Analyse', () => {
  test('UI elements visible', async ({ page }) => {
    // Step 1: Navigate to dashboard
    await page.goto('/');
    await expect(page).toHaveTitle(/InfluxBro/);

    // Step 2: Open selection section
    const isOpen = await page.locator('#selection_details').evaluate(el => el.open);
    if (!isOpen) {
      await page.click('#selection_details summary');
    }
    await page.waitForTimeout(500);

    // Step 3: Verify input elements exist and are visible
    await expect(page.locator('#measurement_filter')).toBeVisible();
    await expect(page.locator('#field')).toBeVisible();
    await expect(page.locator('#entity_id')).toBeVisible();
    await expect(page.locator('#friendly_name')).toBeVisible();
    await expect(page.locator('#range')).toBeVisible();
    await expect(page.locator('#load')).toBeVisible();

    // Step 4: Select measurement
    await page.fill('#measurement_filter', 'Wh');
    await page.locator('#measurement_filter').press('Enter');
    await expect(page.locator('#measurement_filter')).toHaveValue('Wh');
    await page.waitForTimeout(GAP_MS);

    // Step 5: Select field
    await page.fill('#field', 'value');
    await page.locator('#field').press('Enter');
    await expect(page.locator('#field')).toHaveValue('value');
    await page.waitForTimeout(GAP_MS);

    // Step 6: Select entity
    await page.fill('#entity_id', 'sma_30581_energy_bezug_wh_hm2');
    await page.locator('#entity_id').press('Enter');
    await expect(page.locator('#entity_id')).toHaveValue('sma_30581_energy_bezug_wh_hm2');
    await page.waitForTimeout(GAP_MS);

    // Step 7: Select time range
    await page.selectOption('#range', 'all');
    await page.waitForTimeout(GAP_MS);

    console.log('Dashboard UI test passed');
  });

  test('analysis flow with InfluxDB', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/InfluxBro/);

    // Open selection section if closed
    const isOpen = await page.locator('#selection_details').evaluate(el => el.open);
    if (!isOpen) {
      await page.click('#selection_details summary');
      await page.waitForTimeout(500);
    }

    // Select source
    await page.fill('#measurement_filter', 'Wh');
    await page.locator('#measurement_filter').press('Enter');
    await page.waitForTimeout(1000);
    await page.fill('#field', 'value');
    await page.locator('#field').press('Enter');
    await page.waitForTimeout(1000);
    await page.fill('#entity_id', 'sma_30581_energy_bezug_wh_hm2');
    await page.locator('#entity_id').press('Enter');
    await page.waitForTimeout(1000);
    await page.selectOption('#range', 'all');

    await page.waitForTimeout(GAP_MS);

    // Click Analyse
    await page.click('#load');
    await page.waitForTimeout(15000);

    // Open Raw section
    const rawSection = page.locator('#raw_section');
    const rawIsOpen = await rawSection.evaluate(el => el.hasAttribute('open'));
    if (!rawIsOpen) {
      await page.click('#raw_section summary');
      await page.waitForTimeout(500);
    }

    // Check that the raw table container exists
    const rawTable = page.locator('#raw_box');
    await expect(rawTable).toBeVisible();

    // Check that the outlier overview box exists (may be hidden if no outliers)
    const outlierOverview = page.locator('#raw_outlier_overview_box');
    await expect(outlierOverview).toHaveCount(1);

    console.log('Analysis flow test passed');
  });

  test('field selection loads after measurement', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/InfluxBro/);

    // Open selection section if closed
    const isOpen = await page.locator('#selection_details').evaluate(el => el.open);
    if (!isOpen) {
      await page.click('#selection_details summary');
      await page.waitForTimeout(500);
    }

    // Initial field list should be empty
    const initialFieldCount = await page.locator('#field_list option').count();
    console.log('Initial field count:', initialFieldCount);

    // Select measurement
    await page.fill('#measurement_filter', 'Wh');
    await page.locator('#measurement_filter').press('Enter');
    await page.waitForTimeout(1500);

    // Field list should now have options
    const fieldCount = await page.locator('#field_list option').count();
    console.log('Field count after selecting Wh:', fieldCount);
    expect(fieldCount).toBeGreaterThan(0);

    // Select field
    await page.fill('#field', 'value');
    await page.locator('#field').press('Enter');
    await expect(page.locator('#field')).toHaveValue('value');

    await page.waitForTimeout(GAP_MS);

    console.log('Field selection test passed');
  });

  test('friendly_name filters by entity_id', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/InfluxBro/);

    // Open selection section if closed
    const isOpen = await page.locator('#selection_details').evaluate(el => el.open);
    if (!isOpen) {
      await page.click('#selection_details summary');
      await page.waitForTimeout(500);
    }

    // Select measurement and field first
    await page.fill('#measurement_filter', 'Wh');
    await page.locator('#measurement_filter').press('Enter');
    await page.waitForTimeout(1000);

    await page.fill('#field', 'value');
    await page.locator('#field').press('Enter');
    await page.waitForTimeout(1000);

    // Check friendly_name count before entity_id
    const initialFriendlyCount = await page.locator('#friendly_list option').count();
    console.log('Initial friendly_name count:', initialFriendlyCount);

    // Select entity_id
    await page.fill('#entity_id', 'sma_30581_energy_bezug_wh_hm2');
    await page.locator('#entity_id').press('Enter');
    await page.waitForTimeout(1500);

    await page.waitForTimeout(GAP_MS);

    // Friendly name should be filtered to 1
    const filteredFriendlyCount = await page.locator('#friendly_list option').count();
    console.log('Friendly_name count after entity_id:', filteredFriendlyCount);
    expect(filteredFriendlyCount).toBe(1);

    // Verify the value
    const friendlyValue = await page.locator('#friendly_list option').first().getAttribute('value');
    console.log('Filtered friendly_name:', friendlyValue);
    expect(friendlyValue).toContain('SMA_30581');

    console.log('Friendly name filtering test passed');
  });
});
