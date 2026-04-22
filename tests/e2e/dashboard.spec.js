const { test, expect } = require('@playwright/test');

test.describe('Dashboard', () => {
  test('loads dashboard page', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/InfluxBro/);
  });

  test('desktop keeps main content visible across widths', async ({ page }) => {
    // Defensive: close any overlay dialog that could affect measurements.
    async function closePopup() {
      await page.evaluate(() => {
        try {
          const d = document.getElementById('influxbro_popup_root');
          if (d && d.open) {
            try { d.close(); } catch (e) {}
            try { d.style.display = 'none'; } catch (e) {}
          }
        } catch (e) {}
      });
    }

    for (const w of [1600, 1400, 1230, 1100, 1000]) {
      await page.setViewportSize({ width: w, height: 900 });
      await page.goto('/');
      await closePopup();

      const layout = await page.evaluate(() => {
        try {
          const main = document.querySelector('main.content');
          const nav = document.querySelector('nav.sidebar');
          const shell = document.querySelector('.shell');
          if (!main || !nav || !shell) return null;
          const mb = main.getBoundingClientRect();
          const nb = nav.getBoundingClientRect();
          const sb = shell.getBoundingClientRect();
          const st = getComputedStyle(shell);
          return {
            shellW: Math.round(sb.width),
            gridCols: String(st.gridTemplateColumns || ''),
            mainW: Math.round(mb.width),
            mainH: Math.round(mb.height),
            mainTop: Math.round(mb.top),
            navW: Math.round(nb.width),
            navH: Math.round(nb.height),
          };
        } catch (e) {
          return null;
        }
      });

      expect(layout, `layout missing at width=${w}`).not.toBeNull();
      expect(layout.shellW, `shell width at ${w}`).toBeGreaterThan(600);
      expect(layout.navW, `nav width at ${w}`).toBeGreaterThan(120);
      // Main area must be visible and non-trivial.
      expect(layout.mainW, `main width at ${w} (grid=${layout.gridCols})`).toBeGreaterThan(320);
      expect(layout.mainH, `main height at ${w}`).toBeGreaterThan(200);
      expect(layout.mainTop, `main top at ${w}`).toBeLessThan(360);
    }
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

    // Donate panel should be on the same row as the brand on iPhone.
    const donateLayout = await page.evaluate(() => {
      try {
        const brand = document.querySelector('.ib_pagecard .brand');
        const donate = document.querySelector('.ib_pagecard .branddonate');
        if (!brand || !donate) return null;
        const b = brand.getBoundingClientRect();
        const d = donate.getBoundingClientRect();
        return {
          brandTop: Math.round(b.top),
          brandLeft: Math.round(b.left),
          donateTop: Math.round(d.top),
          donateLeft: Math.round(d.left),
        };
      } catch (e) {
        return null;
      }
    });
    expect(donateLayout).not.toBeNull();
    expect(donateLayout.donateLeft).toBeGreaterThan(donateLayout.brandLeft);
    expect(Math.abs(donateLayout.donateTop - donateLayout.brandTop)).toBeLessThanOrEqual(20);

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
