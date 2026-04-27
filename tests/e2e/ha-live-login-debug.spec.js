const { test, expect } = require('@playwright/test');

function env(key) {
  const v = process.env[key];
  if (!v) throw new Error(`Missing env ${key}`);
  return v;
}

test('HA Live login debug (non-destructive)', async ({ page }) => {
  test.setTimeout(3 * 60 * 1000);
  const HA_URL = env('HA_URL');
  const USER = process.env.HA_USERNAME || '';
  const PASS = process.env.HA_PASSWORD || '';
  const HAS_2FA = String(process.env.HA_2FA || 'false').toLowerCase() === 'true';
  const TWO_FA_CODE = String(process.env.HA_2FA_CODE || '');

  async function maybeHandleTwoFactorAuth() {
    if (!HAS_2FA) return false;
    if (!/\/auth\//.test(String(page.url()))) return false;

    const twoFaText = page.getByText(/two-?factor|2fa|mfa|authenticat.*code|verification code|einmalpasswort|zwei-?faktor|verifizier/i);
    const looksLike2fa = await twoFaText.first().isVisible().catch(() => false);
    if (!looksLike2fa) return false;

    if (!TWO_FA_CODE) throw new Error('HA_2FA=true but HA_2FA_CODE is missing');

    const labeledBox = page.getByRole('textbox', {
      name: /authenticat.*code|verification code|one[- ]time|otp|code|einmalpasswort|verifizier/i,
    });
    if (await labeledBox.isVisible().catch(() => false)) {
      await labeledBox.fill(TWO_FA_CODE);
    } else {
      const preferred = page.locator(
        'input[name*="code" i]:visible, input[name*="otp" i]:visible, input[inputmode="numeric"]:visible, input[type="tel"]:visible, input[type="text"]:visible'
      );
      const preferredCount = await preferred.count().catch(() => 0);
      if (preferredCount >= 1) {
        await preferred.first().fill(TWO_FA_CODE);
      } else {
        const anyVisible = page.locator('input:visible');
        const n = await anyVisible.count().catch(() => 0);
        if (n !== 1) throw new Error(`2FA detected but could not uniquely locate code input (visible inputs=${n})`);
        await anyVisible.first().fill(TWO_FA_CODE);
      }
    }

    const submitBtn = page.getByRole('button', { name: /verify|submit|continue|next|confirm|anmelden|log in|weiter/i });
    if (await submitBtn.isVisible().catch(() => false)) {
      await submitBtn.click();
    } else {
      await page.keyboard.press('Enter');
    }
    await page.waitForTimeout(1500);
    return true;
  }

  await page.goto(HA_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);

  const loginBtn = page.getByRole('button', { name: /log in|anmelden/i });
  const userBox = page.getByRole('textbox', { name: /username|benutzername/i });
  const passBox = page.getByRole('textbox', { name: /password|passwort/i });

  const onLogin = await loginBtn.isVisible().catch(() => false);
  console.log('onLogin', onLogin, 'url', page.url());

  if (!onLogin) {
    // Already logged in.
    await page.goto(`${HA_URL}/hassio/dashboard`, { waitUntil: 'domcontentloaded' });
    console.log('already logged in, url', page.url());
    return;
  }

  await expect(userBox).toBeVisible({ timeout: 15_000 });
  await expect(passBox).toBeVisible({ timeout: 15_000 });
  await expect(loginBtn).toBeVisible({ timeout: 15_000 });

  if (!USER || !PASS) throw new Error('HA_USERNAME/HA_PASSWORD missing');
  await userBox.fill(USER);
  await passBox.fill(PASS);

  const uVal = await userBox.inputValue().catch(() => '<no-inputValue>');
  const pLen = (await passBox.inputValue().catch(() => '')).length;
  console.log('filled username length', String(uVal || '').length, 'password length', pLen);

  await loginBtn.click();
  await page.waitForTimeout(2000);
  console.log('after click url', page.url());

  const twoFaHandled = await maybeHandleTwoFactorAuth().catch((e) => {
    console.log('2fa_error', String(e && e.message ? e.message : e));
    return false;
  });
  console.log('twoFaHandled', twoFaHandled, 'url', page.url());

  const stillLogin = await loginBtn.isVisible().catch(() => false);
  console.log('stillLogin', stillLogin);

  if (stillLogin) {
    const err = await page.locator('ha-alert, .error, [role="alert"], .mdc-snackbar__label').first().textContent().catch(() => '');
    console.log('login_error', (err || '').trim());
  }
});
