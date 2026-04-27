const { test, expect } = require('@playwright/test');

function env(key) {
  const v = process.env[key];
  if (!v) throw new Error(`Missing env ${key}`);
  return v;
}

test.describe('HA Live: InfluxBro Update + Version Check', () => {
  test('updates InfluxBro if version mismatches', async ({ page }) => {
    test.setTimeout(20 * 60 * 1000);

    const HA_URL = env('HA_URL');
    const USER = process.env.HA_USERNAME || '';
    const PASS = process.env.HA_PASSWORD || '';
    const EXPECT = env('INFLUXBRO_EXPECT_VERSION');
    const HAS_2FA = String(process.env.HA_2FA || 'false').toLowerCase() === 'true';

    if (HAS_2FA) throw new Error('Dieses Live-Update automatisiert kein 2FA (HA_2FA muss false sein)');

    async function neutralizeBrowserModInteractionGate() {
      // Some HA installs use browser_mod which blocks automation until a user interaction.
      // For this test, we remove/disable the overlay so clicks can proceed.
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

    async function liveVersion() {
      const r = await page.request.get('http://192.168.2.200:8099/api/info', { timeout: 5000 });
      const j = await r.json().catch(() => ({}));
      return String((j && j.version) || '');
    }

    async function clickSidebarSettings() {
      // Prefer scoping to sidebar to avoid picking up Settings content texts.
      const sidebar = page.locator('ha-sidebar, home-assistant').first();
      const settingsLink = sidebar.getByRole('link', { name: /^settings$|^einstellungen$/i }).first();
      const settingsText = sidebar.getByText(/^settings$|^einstellungen$/i).first();
      if (await settingsLink.isVisible().catch(() => false)) {
        await settingsLink.click();
      } else {
        await settingsText.click();
      }
      await waitFullyLoaded(60_000);
    }

    async function triggerCheckForUpdates() {
      // Primary path: 3-dots menu -> "NACH UPDATE SUCHEN".
      const menuCandidates = [
        page.locator('ha-icon-button[icon*="dots"], mwc-icon-button[icon*="dots"], button[aria-label*="more" i], button[aria-label*="menu" i]'),
        page.getByRole('button', { name: /more options|menu|mehr|optionen/i }),
      ];
      for (const c of menuCandidates) {
        const btn = c.first();
        if (!(await btn.isVisible().catch(() => false))) continue;
        await btn.click().catch(() => {});
        const item = page.getByRole('menuitem', { name: /nach update suchen|check for updates/i }).first();
        const itemText = page.getByText(/nach update suchen|check for updates/i).first();
        if (await item.isVisible().catch(() => false)) {
          await item.click();
          await waitFullyLoaded(60_000);
          return;
        }
        if (await itemText.isVisible().catch(() => false)) {
          await itemText.click();
          await waitFullyLoaded(60_000);
          return;
        }
        // Menu opened but no matching item; continue with fallback.
        await page.keyboard.press('Escape').catch(() => {});
      }

      // Fallback: many HA pages expose a refresh/reload icon instead of a menu.
      const refreshCandidates = [
        page.locator('ha-icon-button[icon*="refresh" i], mwc-icon-button[icon*="refresh" i]'),
        page.locator(
          'ha-icon-button[aria-label*="refresh" i], mwc-icon-button[aria-label*="refresh" i], button[aria-label*="refresh" i], ha-icon-button[aria-label*="reload" i], mwc-icon-button[aria-label*="reload" i], button[aria-label*="reload" i]'
        ),
        // Last-resort: on the Add-ons page this is typically the top-right icon.
        page.locator('app-toolbar ha-icon-button, app-toolbar mwc-icon-button, app-header ha-icon-button, app-header mwc-icon-button').last(),
      ];

      for (const c of refreshCandidates) {
        const btn = c.first ? c.first() : c;
        if (await btn.isVisible().catch(() => false)) {
          await btn.click().catch(() => {});
          await waitFullyLoaded(60_000);
          return;
        }
      }

      // Debug: print a small inventory of visible icon buttons.
      const inv = await page
        .locator('ha-icon-button:visible, mwc-icon-button:visible, button:visible')
        .evaluateAll((els) =>
          els
            .slice(0, 30)
            .map((e) => ({
              tag: e.tagName,
              ariaLabel: e.getAttribute('aria-label') || '',
              icon: e.getAttribute('icon') || '',
              title: e.getAttribute('title') || '',
              text: (e.textContent || '').trim().slice(0, 40),
            }))
        )
        .catch(() => []);
      console.log('visible_buttons_inventory', JSON.stringify(inv));

      // Absolute last resort: on the Add-ons list page, the only visible ha-icon-button is often the refresh action.
      const anyHaIconBtn = page.locator('ha-icon-button:visible').first();
      if (await anyHaIconBtn.isVisible().catch(() => false)) {
        await anyHaIconBtn.click().catch(() => {});
        await waitFullyLoaded(60_000);
        return;
      }

      throw new Error('Konnte weder "NACH UPDATE SUCHEN" noch Refresh ausloesen');
    }

    async function openInfluxBroAddonFromAddonsList() {
      const main = page.locator('home-assistant-main, home-assistant').first();
      const addonCard = main
        .locator('hassio-addon-card, ha-card, a, div')
        .filter({ hasText: /\bInfluxBro\b/i })
        .first();

      await addonCard.waitFor({ state: 'visible', timeout: 60_000 });
      await addonCard.click({ timeout: 60_000 });
      await waitFullyLoaded(60_000);
    }

    async function ensureOnAddonsList() {
      const isAddonsList = async () => {
        const headingText = page.getByText(/^add-ons$/i).first();
        const searchPlaceholder = page.getByPlaceholder(/search add-ons/i).first();
        return (await headingText.isVisible().catch(() => false)) || (await searchPlaceholder.isVisible().catch(() => false));
      };

      const candidates = [
        `${HA_URL}/hassio/dashboard`,
        `${HA_URL}/hassio/addons`,
        `${HA_URL}/hassio/store`,
        `${HA_URL}/hassio`,
      ];
      for (const u of candidates) {
        await page.goto(u, { waitUntil: 'domcontentloaded', timeout: 60_000 }).catch(() => {});
        await waitFullyLoaded(60_000);
        if (await isAddonsList()) return;
      }
      throw new Error(`Konnte die Add-ons Uebersicht nicht oeffnen (letzte url=${page.url()})`);
    }

    async function waitForUpdateInfluxBroPrompt(timeoutMs = 180_000) {
      const header = page.getByText(/update\s+influxbro/i).first();
      await header.waitFor({ state: 'visible', timeout: timeoutMs }).catch(() => {
        throw new Error('Update InfluxBro Prompt wurde nicht angezeigt');
      });

      // Best-effort: ensure the expected target version is mentioned somewhere.
      const expectEsc = String(EXPECT).replace(/\./g, '\\.');
      const target = page.getByText(new RegExp(expectEsc)).first();
      await target.waitFor({ state: 'visible', timeout: 60_000 }).catch(() => {});
    }

    async function clickUpdateButton() {
      const updateBtn = page.getByRole('button', { name: /^update$|^aktualisieren$/i });
      const n = await updateBtn.count().catch(() => 0);
      for (let i = 0; i < n; i++) {
        const b = updateBtn.nth(i);
        if (!(await b.isVisible().catch(() => false))) continue;
        if (await b.isDisabled().catch(() => false)) continue;
        await b.click();
        return;
      }
      throw new Error('Aktualisieren/Update Button nicht gefunden oder nicht klickbar');
    }

    async function readInstalledLatestLabels() {
      const text = await page.locator('body').innerText().catch(() => '');
      const installed = /(?:Installierte\s*Version|Installed\s*version)\s*[:\n]\s*([0-9]+\.[0-9]+\.[0-9]+)/i.exec(text || '');
      const latest = /(?:Neueste\s*Version|Latest\s*version)\s*[:\n]\s*([0-9]+\.[0-9]+\.[0-9]+)/i.exec(text || '');
      return {
        installed: installed ? String(installed[1] || '') : '',
        latest: latest ? String(latest[1] || '') : '',
      };
    }

    async function waitUntilUiShowsUpToDate(timeoutMs = 6 * 60 * 1000) {
      const deadline = Date.now() + timeoutMs;
      const updateBtn = page.getByRole('button', { name: /^update$|^aktualisieren$/i }).first();
      while (Date.now() < deadline) {
        const { installed, latest } = await readInstalledLatestLabels().catch(() => ({ installed: '', latest: '' }));
        const disabled = await updateBtn.isDisabled().catch(() => false);
        if (installed && latest && installed === latest && installed === EXPECT && disabled) return;
        await page.waitForTimeout(3000);
      }
      // Not all HA versions expose these labels; treat this as best-effort.
      console.log('ui_up_to_date_check_timeout');
    }

    async function closeUpdateDialog() {
      const dialog = page.locator('ha-dialog, mwc-dialog').first();
      const closeBtn = dialog.getByRole('button', { name: /close|schlie(ß|ss)en|schließen/i }).first();
      const closeIcon = dialog.locator('mwc-icon-button[icon*="close"], ha-icon-button[icon*="close"], button[aria-label*="close" i]').first();
      if (await closeBtn.isVisible().catch(() => false)) {
        await closeBtn.click();
      } else if (await closeIcon.isVisible().catch(() => false)) {
        await closeIcon.click();
      } else {
        // If this is not a modal dialog, fall back to Back.
        const backBtn = page.getByRole('button', { name: /back|zur(ü|ue)ck/i }).first();
        const backIcon = page.locator('ha-icon-button[icon*="arrow-left"], mwc-icon-button[icon*="arrow-left"]').first();
        if (await backBtn.isVisible().catch(() => false)) await backBtn.click().catch(() => {});
        else if (await backIcon.isVisible().catch(() => false)) await backIcon.click().catch(() => {});
        else await page.keyboard.press('Escape').catch(() => {});
      }
      await waitFullyLoaded(60_000);
    }

    async function updateFlowOnce() {
      await ensureLoggedIn();

      const before = await liveVersion().catch(() => '');
      if (before === EXPECT) return;

      // User flow: Settings -> 3 dots -> CHECK FOR UPDATES -> Update InfluxBro -> InfluxBro -> Update.
      await clickSidebarSettings();

      // Ensure we are in the Add-ons list (Settings -> Add-ons).
      await ensureOnAddonsList();

      await triggerCheckForUpdates();

      // Now open the InfluxBro add-on and wait until the update prompt appears.
      await openInfluxBroAddonFromAddonsList();
      await waitForUpdateInfluxBroPrompt(180_000);

      // If UI already indicates latest version, we're done.
      const ui0 = await readInstalledLatestLabels().catch(() => ({ installed: '', latest: '' }));
      if (ui0.installed && ui0.latest && ui0.installed === ui0.latest && ui0.installed === EXPECT) {
        await closeUpdateDialog();
        return;
      }

      await clickUpdateButton();

      // Wait until the exposed add-on port serves the expected version.
      const deadline = Date.now() + 12 * 60 * 1000;
      let last = '';
      while (Date.now() < deadline) {
        last = await liveVersion().catch(() => '');
        if (last === EXPECT) break;
        await page.waitForTimeout(5000);
      }
      expect(last).toBe(EXPECT);

      await waitUntilUiShowsUpToDate();
      await closeUpdateDialog();

      // Ensure the update prompt is gone; if not, wait 30 seconds and re-check.
      const updatePrompt = page.getByText(/update\s+influxbro/i).first();
      if (await updatePrompt.isVisible().catch(() => false)) {
        await page.waitForTimeout(30_000);
        await page.reload({ waitUntil: 'domcontentloaded' }).catch(() => {});
        await waitFullyLoaded(60_000);
      }
    }

    // Run flow; if still out-of-date, retry once.
    for (let attempt = 1; attempt <= 2; attempt++) {
      await updateFlowOnce();
      const v = await liveVersion().catch(() => '');
      if (v === EXPECT) return;
      if (attempt === 1) {
        console.log('retrying_update_flow');
      }
    }

    const finalV = await liveVersion().catch(() => '');
    throw new Error(`Live InfluxBro blieb veraltet (expected=${EXPECT}, got=${finalV || '<unknown>'})`);
  });
});
