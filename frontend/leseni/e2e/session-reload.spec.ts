import { expect, test } from '@playwright/test';

import { login } from './support/helpers';

/**
 * Hard reload (F5 / direct URL) must keep the logged-in session. Regression
 * tests for the SSR guard quirk: the server render could not see
 * sessionStorage and bounced authenticated pages to /login?returnUrl=…
 */
test.describe('Session survives hard reload', () => {
  test('applicant reloads /dashboard directly', async ({ page }) => {
    await login(page, 'applicant1', 'Demo@1234');
    // Hard navigation = fresh document request = goes through the server render
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('heading', { name: /Karibu/ })).toBeVisible();
  });

  test('admin reloads a staff page directly', async ({ page }) => {
    await login(page, 'admin', 'Demo@1234');
    await page.goto('/staff/admin', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/\/staff\/admin/);
  });

  test('deep link into a guarded page works when logged in', async ({ page }) => {
    await login(page, 'applicant1', 'Demo@1234');
    await page.goto('/ussd-demo', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/\/ussd-demo/);
    await expect(page.locator('#ussd-dial')).toBeVisible();
  });

  test('logged-out hard load of a guarded page still redirects to login', async ({ page }) => {
    // No login: fresh context
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/\/login\?returnUrl=/);
  });

  test('expired access token is silently refreshed (no logout)', async ({ page }) => {
    await login(page, 'applicant1', 'Demo@1234');

    // Corrupt the access token but keep the valid refresh token — simulates
    // the 2-hour access token expiry while the 7-day refresh is still valid.
    await page.evaluate(() => sessionStorage.setItem('leseni.access', 'expired-or-garbage'));

    // Reload: client boot fires API calls, gets 401s, silently refreshes
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('heading', { name: /Karibu/ })).toBeVisible();

    // The access token was rotated (no longer the corrupt value) and the
    // user stayed logged in instead of being bounced to /login.
    await expect
      .poll(() => page.evaluate(() => sessionStorage.getItem('leseni.access')), { timeout: 10_000 })
      .not.toBe('expired-or-garbage');
    await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
  });
});
