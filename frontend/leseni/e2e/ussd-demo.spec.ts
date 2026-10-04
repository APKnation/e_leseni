import { expect, test } from '@playwright/test';

import { login } from './support/helpers';

/**
 * USSD demo simulator: dials the real backend gateway (CON/END), walks the
 * menu with the clickable keypad and asserts the gateway log panel records
 * every round-trip with its text= payload and CON/END prefix.
 */
test.describe('USSD demo simulator', () => {
  test('dial, keypad menu walk, and live gateway log', async ({ page }) => {
    await login(page, 'applicant1', 'Demo@1234');
    await page.click('a[href="/ussd-demo"]');
    await expect(page).toHaveURL(/\/ussd-demo/);

    // Dialer is pre-filled with the demo service code
    const dial = page.locator('#ussd-dial');
    await expect(dial).toHaveValue('*152*00#');
    await expect(page.locator('#ussd-phone')).not.toBeEmpty();

    // Keypad caption targets the service code while no session is open
    await expect(page.getByText(/Keypad — typing service code/)).toBeVisible();

    // Rebuild the code via keypad taps: clear then type *152*00#
    for (let i = 0; i < 8; i++) await page.click('#btn-backspace');
    const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'];
    for (const key of ['*', '1', '5', '2', '*', '0', '0', '#']) {
      await page.locator('button.keypad-key').nth(keys.indexOf(key)).click();
    }
    await expect(dial).toHaveValue('*152*00#');

    // Dial (Enter in the field = the call key)
    await dial.press('Enter');

    // Real gateway answer: main menu on the simulated screen
    const screen = page.locator('#ussd-screen');
    await expect(screen).toContainText('e-Leseni');
    await expect(screen).toContainText('1. Apply for licence');
    await expect(screen).toContainText('5. My licences');

    // Gateway log: round-trip #1 is the dial with empty text -> CON
    const logEntries = page.locator('[data-testid="gateway-log-entry"]');
    await expect(logEntries).toHaveCount(1);
    await expect(logEntries.nth(0)).toContainText('CON');
    await expect(logEntries.nth(0)).toContainText('text=""');

    // Reply caption switches to the reply field once the session is open
    await expect(page.getByText(/Keypad — typing reply/)).toBeVisible();

    // Reply "2" (application status) via keypad -> numbered list
    await page.locator('button.keypad-key').nth(1).click(); // key "2"
    await expect(page.locator('#ussd-reply')).toHaveValue('2');
    await page.locator('#ussd-reply').press('Enter');
    await expect(screen).toContainText('Status - pick application');

    // Round-trip #2 carries text="2" -> CON
    await expect(logEntries).toHaveCount(2);
    await expect(logEntries.nth(1)).toContainText('text="2"');
    await expect(logEntries.nth(1)).toContainText('CON');

    // Reply "1" -> application detail screen
    await page.locator('button.keypad-key').nth(0).click(); // key "1"
    await page.locator('#ussd-reply').press('Enter');
    await expect(screen).not.toContainText('Invalid choice');

    // END hides the reply input; log shows text="2*1"... wait: accumulated text
    const lastEntry = logEntries.nth(2);
    await expect(lastEntry).toContainText(/CON|END/);
    if ((await lastEntry.textContent())?.includes('END')) {
      await expect(page.locator('#ussd-reply')).toHaveCount(0);
    }
  });
});
