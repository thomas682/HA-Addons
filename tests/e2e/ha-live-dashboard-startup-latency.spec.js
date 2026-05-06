const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');

function env(key) {
  const v = process.env[key];
  if (!v) throw new Error(`Missing env ${key}`);
  return v;
}

test.describe('HA Live: Dashboard startup latency', () => {
  test('measures dashboard startup until visible GUI', async ({ page }, testInfo) => {
    test.setTimeout(8 * 60 * 1000);

    const HA_URL = env('HA_URL');
    const USER = process.env.HA_USERNAME || '';
    const PASS = process.env.HA_PASSWORD || '';
    const EXPECT = env('INFLUXBRO_EXPECT_VERSION');
    const HAS_2FA = String(process.env.HA_2FA || 'false').toLowerCase() === 'true';
    if (HAS_2FA) throw new Error('Dieser Live-Test unterstuetzt kein 2FA (HA_2FA muss false sein)');

    const requestRows = [];
    const visibleSteps = [];
    const tSuite0 = Date.now();

    function rememberStep(label) {
      visibleSteps.push({ at_ms: Date.now() - tSuite0, label: String(label) });
    }

    page.on('requestfinished', async (req) => {
      const url = String(req.url() || '');
      if (!/hassio_ingress|_influxbro|\/api\//i.test(url)) return;
      try {
        const res = await req.response();
        requestRows.push({
          at_ms: Date.now() - tSuite0,
          method: req.method(),
          url,
          status: res ? res.status() : 0,
        });
      } catch {}
    });

    async function neutralizeBrowserModInteractionGate() {
      await page
        .addStyleTag({
          content:
            '.browser-mod-require-interaction{display:none !important; pointer-events:none !important; visibility:hidden !important;}',
        })
        .catch(() => {});
      await page
        .evaluate(() => {
          for (const el of document.querySelectorAll('.browser-mod-require-interaction')) {
            try {
              el.remove();
            } catch {}
          }
        })
        .catch(() => {});
    }

    async function waitFullyLoaded(timeoutMs = 60_000) {
      await page.waitForSelector('home-assistant', { timeout: timeoutMs }).catch(() => {});
      await page.waitForTimeout(800);
      await neutralizeBrowserModInteractionGate();
    }

    async function ensureLoggedIn() {
      rememberStep('goto_home_assistant');
      await page.goto(HA_URL, { waitUntil: 'domcontentloaded', timeout: 60_000 });
      await waitFullyLoaded(60_000);

      const loginBtn = page.getByRole('button', { name: /log in|anmelden/i });
      const userBox = page.getByRole('textbox', { name: /username|benutzername/i });
      const passBox = page.getByRole('textbox', { name: /password|passwort/i });

      if (await loginBtn.isVisible().catch(() => false)) {
        if (!USER || !PASS) throw new Error('HA_USERNAME/HA_PASSWORD required for UI login');
        rememberStep('login_required');
        await expect(userBox).toBeVisible({ timeout: 20_000 });
        await expect(passBox).toBeVisible({ timeout: 20_000 });
        await userBox.fill(USER);
        await passBox.fill(PASS);
        await loginBtn.click();
        await page.waitForTimeout(1200);
        await expect(page).not.toHaveURL(/\/auth\//, { timeout: 90_000 });
        await waitFullyLoaded(60_000);
        rememberStep('login_completed');
      } else {
        rememberStep('login_not_required');
      }
    }

    async function openInfluxBroPanel() {
      rememberStep('goto_lovelace');
      await page.goto(`${HA_URL}/lovelace/0`, { waitUntil: 'domcontentloaded', timeout: 60_000 }).catch(() => {});
      await waitFullyLoaded(60_000);

      const sidebar = page.locator('ha-sidebar, home-assistant').first();
      const influxLink = sidebar.getByRole('link', { name: /^influxbro$/i }).first();
      const influxText = sidebar.getByText(/^influxbro$/i).first();

      rememberStep('open_influxbro_sidebar');
      if (await influxLink.isVisible().catch(() => false)) {
        await influxLink.click();
      } else {
        await influxText.click();
      }
      await waitFullyLoaded(60_000);

      if (!/_[Ii]nfluxbro/.test(String(new URL(page.url()).pathname || ''))) {
        const href = await page.locator('a[href*="_influxbro"]').first().getAttribute('href').catch(() => '');
        if (href) {
          const u = href.startsWith('http') ? href : `${HA_URL}${href.startsWith('/') ? '' : '/'}${href}`;
          rememberStep('fallback_open_influxbro_url');
          await page.goto(u, { waitUntil: 'domcontentloaded', timeout: 60_000 }).catch(() => {});
          await waitFullyLoaded(60_000);
        }
      }

      await expect(page).toHaveURL(/_[Ii]nfluxbro/, { timeout: 60_000 });
      rememberStep('influxbro_panel_opened');
    }

    function findInfluxFrameByUrl() {
      const frames = page.frames();
      const main = page.mainFrame();
      return (
        frames.find((f) => f !== main && /hassio_ingress|hassio-ingress|ingress/i.test(String(f.url() || '')))
        || frames.find((f) => f !== main && /influxbro/i.test(String(f.url() || '')))
        || frames.find((f) => f !== main && /api\/hassio_ingress\//i.test(String(f.url() || '')))
        || null
      );
    }

    async function resolveInfluxContext() {
      const pageHasMain = await page.locator('main[data-ui="dashboard_page.main"]').first().isVisible().catch(() => false);
      if (pageHasMain) return { kind: 'page' };

      const iframeCount = await page.locator('iframe').count().catch(() => 0);
      for (let i = 0; i < Math.min(iframeCount, 6); i++) {
        const fl = page.frameLocator('iframe').nth(i);
        const hasMain = await fl.locator('main[data-ui="dashboard_page.main"]').first().isVisible().catch(() => false);
        if (hasMain) {
          return { kind: 'iframe', frameLocator: fl, frame: findInfluxFrameByUrl() };
        }
      }

      if (iframeCount > 0) {
        return { kind: 'iframe', frameLocator: page.frameLocator('iframe').first(), frame: findInfluxFrameByUrl() };
      }
      return { kind: 'page' };
    }

    async function measureVisibleDashboard() {
      const t0 = Date.now();
      const ctx = await resolveInfluxContext();
      const scope = ctx.kind === 'iframe' ? ctx.frameLocator : page;

      rememberStep(`context_${ctx.kind}`);
      await expect(scope.locator('main[data-ui="dashboard_page.main"]').first()).toBeVisible({ timeout: 60_000 });
      rememberStep('dashboard_main_visible');
      await expect(scope.locator('[data-ui="dashboard_selection.section_root"]').first()).toBeVisible({ timeout: 60_000 });
      rememberStep('dashboard_selection_visible');
      await expect(scope.getByText(/InfluxBro/i).first()).toBeVisible({ timeout: 60_000 });
      rememberStep('dashboard_brand_visible');

      const liveVer =
        ctx.kind === 'iframe' && ctx.frame
          ? await ctx.frame.evaluate(async () => {
              const r = await fetch('./api/info');
              const j = await r.json().catch(() => ({}));
              return String((j && j.version) || '');
            })
          : await page.evaluate(async () => {
              const r = await fetch('./api/info');
              const j = await r.json().catch(() => ({}));
              return String((j && j.version) || '');
            });
      expect(liveVer).toBe(EXPECT);
      rememberStep('api_info_verified');

      return {
        latency_ms: Date.now() - t0,
        context: ctx.kind,
      };
    }

    await ensureLoggedIn();
    await openInfluxBroPanel();
    const result = await measureVisibleDashboard();

    const visibleAt = (visibleSteps.find((x) => x.label === 'dashboard_main_visible') || {}).at_ms || 0;
    const sidebarAt = (visibleSteps.find((x) => x.label === 'open_influxbro_sidebar') || {}).at_ms || 0;
    const panelAt = (visibleSteps.find((x) => x.label === 'influxbro_panel_opened') || {}).at_ms || 0;

    const trimmedRequests = requestRows
      .filter((row) => row.at_ms <= visibleAt)
      .slice(0, 25)
      .map((row) => ({
        at_ms: row.at_ms,
        method: row.method,
        status: row.status,
        path: row.url.replace(/^https?:\/\/[^/]+/i, ''),
      }));

    const payload = {
      context: result.context,
      latency_ms: result.latency_ms,
      sidebar_open_to_visible_ms: sidebarAt && visibleAt ? Math.max(0, visibleAt - sidebarAt) : 0,
      panel_route_to_visible_ms: panelAt && visibleAt ? Math.max(0, visibleAt - panelAt) : 0,
      steps: visibleSteps,
      requests: trimmedRequests,
    };
    console.log('dashboard_startup_latency', JSON.stringify(payload));

    const outFile = testInfo.outputPath('dashboard-startup-latency.json');
    fs.mkdirSync(path.dirname(outFile), { recursive: true });
    fs.writeFileSync(outFile, JSON.stringify(payload, null, 2));
  });
});
