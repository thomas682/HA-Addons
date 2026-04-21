const { test, expect } = require('@playwright/test');

test.describe('Dashboard', () => {
  test('loads dashboard page', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/InfluxBro/);
  });

  test('topbar can be collapsed on iPhone', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');

    // Defensive: close any overlay dialog that could intercept taps.
    await page.evaluate(() => {
      try {
        const d = document.getElementById('influxbro_popup_root');
        if (d && d.open) {
          try { d.close(); } catch (e) {}
          try { d.style.display = 'none'; } catch (e) {}
        }
      } catch (e) {}
    });

    const toggle = page.locator('#ib_topbar_mobile_toggle');
    await expect(toggle).toBeVisible();

    const panel = page.locator('#ib_topbar_mobile_panel');
    await expect(panel).toBeHidden();

    await toggle.click();
    await expect(panel).toBeVisible();
  });

  test('restores cached dashboard panels after navigation', async ({ page }) => {
    const payload = {
      v: 1,
      at_ms: Date.now(),
      filters: {},
      range: '',
      start_local: '',
      stop_local: '',
      last_rows: [],
      last_query: '',
      outlier_active: false,
      outlier_rows: [],
      selected_keys: [],
      staged: [],
      analysis_cache_plan_choice: null,
      analysis_status_text: '',
      load_status_txt: 'Cache OK (restored)',
      load_status_time: 'Gesamt: 1ms',
      analysis_state: { status: 'done', measurement: 'm', field: 'f', types: [], currentChunk: 1, totalChunks: 1, totalFound: 0, timeRange: '', foundByType: {} },
      analysis_checklist_items: [{ label: 'Step A', status: 'ok' }],
      analysis_chunk_log: [],
      analysis_summary_html: '',
    };

    // Seed sessionStorage before any app scripts run.
    await page.addInitScript((p) => {
      try {
        const raw = JSON.stringify(p);
        const lastKey = 'influxbro_dash_cache_v1:last';
        sessionStorage.setItem(lastKey, raw);
        try {
          if (typeof _cacheKeyForCurrent === 'function') {
            const k = _cacheKeyForCurrent();
            if (k) sessionStorage.setItem(k, raw);
          }
        } catch (e) {}
      } catch (e) {}
    }, payload);

    await page.goto('/');

    // Ensure our seeded snapshot is present.
    const seeded = await page.evaluate(() => sessionStorage.getItem('influxbro_dash_cache_v1:last'));
    await expect(seeded || '').toContain('Cache OK (restored)');

    await expect(page.locator('#load_status_txt')).toContainText('Cache OK (restored)');
    await expect(page.locator('#analysis_checklist')).toContainText('Step A');

    // A stable graph control should still be present.
    await expect(page.locator('#graph_refresh')).toBeVisible();

    // Navigate away/back and ensure it is still present.
    await page.goto('/config');
    await page.goto('/');
    await expect(page.locator('#load_status_txt')).toContainText('Cache OK (restored)');
  });
});

test.describe('Settings Page', () => {
  test('loads settings page', async ({ page }) => {
    await page.goto('/config');
    await expect(page).toHaveTitle(/InfluxBro.*Einstellungen/);
  });
});
