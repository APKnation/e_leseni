import { expect, test } from '@playwright/test';

import { login, resetApplicantNida } from './support/helpers';

const DEMO_NIDA = '19991234567890123456';

test.describe('NIDA banner (citizen dashboard)', () => {
  test.use({ storageState: { cookies: [], origins: [] } }); // always start logged out

  test.beforeEach(async ({ request }) => {
    await resetApplicantNida(request, '');
  });

  test.afterAll(async ({ request }) => {
    // Leave the demo database in its seeded state (applicant1 has no NIDA).
    await resetApplicantNida(request, '');
  });

  test('applicant without NIDA sees the banner; adding one clears it', async ({ page }) => {
    await login(page, 'applicant1', 'Demo@1234');

    // Banner is visible with the warning text and CTA
    const banner = page.getByTestId('nida-banner');
    await expect(banner).toBeVisible();
    await expect(banner).toContainText('Your profile has no NIDA number');
    await expect(banner).toContainText('Add your NIDA number');

    // CTA deep-links to the profile edit tab
    await banner.getByRole('link', { name: /Add your NIDA number/ }).click();
    await expect(page).toHaveURL(/\/profile\?edit=1/);
    await expect(page.locator('#edit-nida')).toBeVisible();

    // Save a 20-digit NIDA number
    await page.fill('#edit-nida', DEMO_NIDA);
    await page.click('#btn-save-profile');
    await expect(page.getByText('Profile updated successfully.')).toBeVisible();

    // Back on the dashboard the banner is gone
    await page.click('a[href="/dashboard"]');
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(banner).toHaveCount(0);
  });

  test('staff never see the NIDA banner', async ({ page }) => {
    await login(page, 'officer1', 'Demo@1234');
    // Officer lands on their review workspace; the banner only exists on /dashboard
    await expect(page).toHaveURL(/\/staff\//);
    await page.goto('/dashboard');
    await expect(page.getByTestId('nida-banner')).toHaveCount(0);
  });
});
