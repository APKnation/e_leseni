import { expect, test } from '@playwright/test';

import { login } from './support/helpers';

/**
 * Admin Council catalogue cascade: Region (with council counts) first, then
 * a filtered Council dropdown, then the catalogue list for that council.
 */
test.describe('Admin council catalogue cascade', () => {
  test('region first (with counts), then filtered council, then catalogue', async ({ page }) => {
    await login(page, 'admin', 'Demo@1234');
    await expect(page).toHaveURL(/\/staff\//);

    await page.getByRole('button', { name: 'Manage catalogue' }).click();

    // Wait for the region select to be populated (LGAs fetched on toggle)
    const regionSelect = page.locator('select', { has: page.locator('option', { hasText: '— choose a region —' }) });
    await expect(regionSelect.locator('option').filter({ hasText: /\(\d+\)$/ }).first()).toBeAttached({ timeout: 15_000 });

    // Region select comes before the council select, and every region shows "(n)"
    const councilSelect = page.locator('select', { has: page.locator('option', { hasText: /choose a region first|— choose a council —/ }) });
    await expect(regionSelect).toBeVisible();
    await expect(councilSelect).toBeVisible();
    // Region must precede council in the DOM (raw handles, not Locators)
    await page.evaluate(() => {
      const texts = (s: HTMLSelectElement) => [...s.options].map((o) => (o.textContent ?? '').trim());
      const all = [...document.querySelectorAll('select')];
      const region = all.find((s) => texts(s).includes('— choose a region —'));
      const council = all.find((s) => texts(s).some((t) => t.includes('choose a region first') || t.includes('— choose a council —')));
      if (!region || !council || (region.compareDocumentPosition(council) & Node.DOCUMENT_POSITION_FOLLOWING) === 0) {
        throw new Error('region select is missing or is not before the council select');
      }
    });

    const regionOptions = regionSelect.locator('option');
    const regionTexts = (await regionOptions.allTextContents()).filter((t) => t && !t.includes('choose a region'));
    expect(regionTexts.length).toBeGreaterThan(0);
    for (const text of regionTexts) expect(text).toMatch(/\(\d+\)$/);

    // Council select is disabled with the "choose a region first" hint
    await expect(councilSelect).toBeDisabled();
    await expect(councilSelect.locator('option').first()).toHaveText(/choose a region first/);

    // Pick the first region: council select enables and is filtered to it
    const pickedRegion = regionTexts[0];
    const pickedCount = Number(pickedRegion.match(/\((\d+)\)$/)?.[1]);
    await regionSelect.selectOption(pickedRegion.replace(/\s*\(\d+\)$/, ''));
    await expect(councilSelect).toBeEnabled();

    const councilTexts = (await councilSelect.locator('option').allTextContents())
      .filter((t) => t && !t.includes('choose a council'));
    expect(councilTexts.length).toBe(pickedCount);

    // Pick the first council: the catalogue loads for it
    await councilSelect.selectOption({ index: 1 }); // index 0 is the placeholder
    await expect(
      page.getByText(/fee|validity|months|No licence types/i).first(),
    ).toBeVisible();

    // Switching the region resets the council selection; the placeholder now
    // reflects that a (new) region is picked: "— choose a council —"
    const otherRegion = regionTexts.find((t) => t !== pickedRegion);
    if (otherRegion) {
      await regionSelect.selectOption(otherRegion.replace(/\s*\(\d+\)$/, ''));
      await expect(councilSelect).toHaveValue('');
      await expect(councilSelect.locator('option').first()).toHaveText(/— choose a council —/);
      const newCouncilTexts = (await councilSelect.locator('option').allTextContents())
        .filter((t) => t && !t.includes('choose a council'));
      expect(newCouncilTexts.length).toBe(Number(otherRegion.match(/\((\d+)\)$/)?.[1]));
    }
  });
});
