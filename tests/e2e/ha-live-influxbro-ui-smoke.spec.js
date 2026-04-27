const { test, expect } = require('@playwright/test');

function env(key) {
  const v = process.env[key];
  if (!v) throw new Error(`Missing env ${key}`);
  return v;
}

test.describe('HA Live: InfluxBro UI Smoke', () => {
  test('loads UI pages and API info', async ({ page }) => {
    test.setTimeout(8 * 60 * 1000);

    const HA_URL = env('HA_URL');
    const USER = process.env.HA_USERNAME || '';
    const PASS = process.env.HA_PASSWORD || '';
    const EXPECT = env('INFLUXBRO_EXPECT_VERSION');
    const HAS_2FA = String(process.env.HA_2FA || 'false').toLowerCase() === 'true';
    if (HAS_2FA) throw new Error('Dieser Smoke-Test unterstuetzt kein 2FA (HA_2FA muss false sein)');

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
      await page.goto(HA_URL, { waitUntil: 'domcontentloaded', timeout: 60_000 });
      await waitFullyLoaded(60_000);

      const loginBtn = page.getByRole('button', { name: /log in|anmelden/i });
      const userBox = page.getByRole('textbox', { name: /username|benutzername/i });
      const passBox = page.getByRole('textbox', { name: /password|passwort/i });

      if (await loginBtn.isVisible().catch(() => false)) {
        if (!USER || !PASS) throw new Error('HA_USERNAME/HA_PASSWORD required for UI login');
        await expect(userBox).toBeVisible({ timeout: 20_000 });
        await expect(passBox).toBeVisible({ timeout: 20_000 });
        await userBox.fill(USER);
        await passBox.fill(PASS);
        await loginBtn.click();
        await page.waitForTimeout(1200);
        await expect(page).not.toHaveURL(/\/auth\//, { timeout: 90_000 });
        await waitFullyLoaded(60_000);
      }
    }

    async function openInfluxBroPanel() {
      // Preferred: click the left sidebar panel entry "InfluxBro".
      await page.goto(`${HA_URL}/lovelace/0`, { waitUntil: 'domcontentloaded', timeout: 60_000 }).catch(() => {});
      await waitFullyLoaded(60_000);

      const sidebar = page.locator('ha-sidebar, home-assistant').first();
      const influxLink = sidebar.getByRole('link', { name: /^influxbro$/i }).first();
      const influxText = sidebar.getByText(/^influxbro$/i).first();

      if (await influxLink.isVisible().catch(() => false)) {
        await influxLink.click();
      } else {
        await influxText.click();
      }
      await waitFullyLoaded(60_000);

      // If sidebar click didn't work (e.g. collapsed sidebar), try discovering direct panel URL.
      if (!/_[Ii]nfluxbro/.test(String(new URL(page.url()).pathname || ''))) {
        const href = await page
          .locator('a[href*="_influxbro"]')
          .first()
          .getAttribute('href')
          .catch(() => '');
        if (href) {
          const u = href.startsWith('http') ? href : `${HA_URL}${href.startsWith('/') ? '' : '/'}${href}`;
          await page.goto(u, { waitUntil: 'domcontentloaded', timeout: 60_000 }).catch(() => {});
          await waitFullyLoaded(60_000);
        }
      }

      await expect(page).toHaveURL(/_[Ii]nfluxbro/, { timeout: 60_000 });
    }

    function findInfluxFrameByUrl() {
      const frames = page.frames();
      const main = page.mainFrame();
      const urls = frames.map((f) => String(f.url ? f.url() : ''));
      console.log('frame_urls', urls.join(' | '));

      return (
        frames.find((f) => f !== main && /hassio_ingress|hassio-ingress|ingress/i.test(String(f.url() || '')))
        || frames.find((f) => f !== main && /influxbro/i.test(String(f.url() || '')))
        || frames.find((f) => f !== main && /api\/hassio_ingress\//i.test(String(f.url() || '')))
        || null
      );
    }

    async function resolveInfluxContext() {
      // In HA panels, the actual app UI is often rendered in an iframe (ingress).
      // We detect this by checking for the InfluxBro-side nav labels.

      const pageHasNav = await page.getByText(/Datenqualit(ae|ä)t/i).first().isVisible().catch(() => false);
      if (pageHasNav) return { kind: 'page' };

      const iframeCount = await page.locator('iframe').count().catch(() => 0);
      for (let i = 0; i < Math.min(iframeCount, 6); i++) {
        const fl = page.frameLocator('iframe').nth(i);
        const hasNav = await fl.getByText(/Datenqualit(ae|ä)t/i).first().isVisible().catch(() => false);
        if (hasNav) {
          return { kind: 'iframe', frameLocator: fl, frame: findInfluxFrameByUrl() };
        }
      }

      // Fallback: if we see any iframe, assume first is the panel content.
      if (iframeCount > 0) {
        return { kind: 'iframe', frameLocator: page.frameLocator('iframe').first(), frame: findInfluxFrameByUrl() };
      }

      return { kind: 'page' };
    }

    async function clickNav(ctx, labelRe) {
      // Click a nav item by its visible label. Prefer clickable elements.
      const scope = ctx.kind === 'iframe' ? ctx.frameLocator : page;
      const clickable = scope.locator('a, button, [role="button"], [role="link"], summary').filter({ hasText: labelRe }).first();
      if (await clickable.isVisible().catch(() => false)) {
        await clickable.click();
        await page.waitForTimeout(400);
        return;
      }

      const byRoleLink = scope.getByRole('link', { name: labelRe }).first();
      if (await byRoleLink.isVisible().catch(() => false)) {
        await byRoleLink.click();
        await page.waitForTimeout(400);
        return;
      }

      const byRoleBtn = scope.getByRole('button', { name: labelRe }).first();
      if (await byRoleBtn.isVisible().catch(() => false)) {
        await byRoleBtn.click();
        await page.waitForTimeout(400);
        return;
      }

      // Last resort.
      await scope.getByText(labelRe).first().click();
      await page.waitForTimeout(400);
    }

    await ensureLoggedIn();
    await openInfluxBroPanel();

    const ctx = await resolveInfluxContext();
    const scope = ctx.kind === 'iframe' ? ctx.frameLocator : page;

    // Basic presence.
    await expect(scope.getByText(/InfluxBro/i).first()).toBeVisible({ timeout: 60_000 });

    // Smoke: ensure key nav items exist.
    await expect(scope.getByText(/Datenqualit(ae|ä)t/i).first()).toBeVisible({ timeout: 60_000 });
    await expect(scope.getByText(/Verdichtung/i).first()).toBeVisible({ timeout: 60_000 });

    await clickNav(ctx, /Datenqualit(ae|ä)t/i);
    await expect(scope.getByText(/Datenqualit(ae|ä)t/i).first()).toBeVisible({ timeout: 60_000 });

    await clickNav(ctx, /Verdichtung/i);
    await expect(scope.getByText(/Verdichtung/i).first()).toBeVisible({ timeout: 60_000 });

    // Same-origin API check from inside the panel.
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

    // Additional endpoint smoke (host port).
    const r = await page.request.get('http://192.168.2.200:8099/api/dq/debug');
    expect(r.status()).toBe(200);
  });
});
