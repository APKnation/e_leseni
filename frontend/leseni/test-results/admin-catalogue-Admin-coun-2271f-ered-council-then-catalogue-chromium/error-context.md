# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-catalogue.spec.ts >> Admin council catalogue cascade >> region first (with counts), then filtered council, then catalogue
- Location: e2e/admin-catalogue.spec.ts:10:7

# Error details

```
Error: expect(locator).toHaveText(expected) failed

Locator: locator('select').filter({ has: locator('option').filter({ hasText: /choose a region first|— choose a council —/ }) }).locator('option').first()
Expected pattern: /choose a region first/
Received string:  " — choose a council — "
Timeout: 5000ms

Call log:
  - Expect "toHaveText" locator('select').filter({ has: locator('option').filter({ hasText: /choose a region first|— choose a council —/ }) }).locator('option').first() with timeout 5000ms
  - waiting for locator('select').filter({ has: locator('option').filter({ hasText: /choose a region first|— choose a council —/ }) }).locator('option').first()
    14 × locator resolved to <option value="" disabled> — choose a council — </option>
       - unexpected value " — choose a council — "

```

```yaml
- banner:
  - link "e-Leseni System Admin":
    - /url: /
  - navigation:
    - link "My workspace":
      - /url: /staff/admin
    - link "Users & Staff":
      - /url: /staff/users
    - link "Dashboard":
      - /url: /dashboard
    - link "Profile":
      - /url: /profile
    - link "USSD demo":
      - /url: /ussd-demo
    - button "Log out"
  - text: Live
- main:
  - heading "Administration" [level=1]
  - paragraph: Every application across all LGAs — full workflow control.
  - heading "eGA GovESB Integration Status" [level=2]
  - text: BRELA TRA GePG NIDA SYSTEM ADMIN
  - link "My Profile":
    - /url: /profile
  - link "Manage Users & Staff →":
    - /url: /staff/users
  - link "Switch workspace":
    - /url: /staff/review
  - button "Needs review (1)"
  - button "Inspections (7)"
  - button "Approvals (3)"
  - button "Payments (1)"
  - button "All (25)"
  - text: Activity
  - combobox "Activity":
    - option "All activities" [selected]
    - option "Food & Beverages"
    - option "Liquor, Bars & Nightclubs"
    - option "Hotels & Guest Houses"
    - option "Entertainment & Events"
    - option "Transport & Logistics"
    - option "Health, Pharmacies & Sanitation"
    - option "Livestock, Fisheries & Agriculture"
    - option "Natural Resources & Mining"
    - option "Small Industries & Workshops"
    - option "Markets & Street Vending"
    - option "Advertisements & Signage"
    - option "General Trade & Shops"
  - paragraph: EL-GE-CHATO-ACT-NATURAL_RESOURCES-2026-00001
  - text: Submitted Natural Resources & Mining
  - paragraph: Walkthrough Traders verified
  - paragraph: "Natural Resources & Mining Licence — Chato · applicant: Neema Robert NIDA"
  - paragraph: “SDSDFDF”
  - link "Land/Plot Agreement":
    - /url: http://localhost:8000/media/application_documents/2026/10/afyatrust.pdf
  - button "Start review"
  - button "→ Returned for correction"
  - heading "Business activities" [level=2]
  - paragraph: The council's “kind of business” taxonomy — what this queue is filtered by and what applicants pick.
  - button "Manage activities"
  - heading "Council catalogue" [level=2]
  - paragraph: Your council's licences — the fees, validity and requirements applicants see. Each council keeps its own rules here.
  - text: Region
  - combobox "Region":
    - option "— choose a region —" [disabled]
    - option "Arusha (3)"
    - option "Dodoma (2)" [selected]
    - option "Geita (2)"
    - option "Kagera (4)"
    - option "Kigoma (1)"
    - option "Manyara (3)"
    - option "Mara (2)"
    - option "Mbeya (1)"
    - option "Mwanza (1)"
    - option "Pwani (3)"
    - option "Simiyu (2)"
    - option "Zanzibar - Pemba South (1)"
  - text: Council
  - combobox "Council":
    - option "— choose a council —" [disabled] [selected]
    - option "Bahi"
    - option "Chamwino"
  - button "Hide catalogue"
  - button "New licence type"
  - paragraph: Advertisements & Signage Licence AR-ARUSHA-ACT-ADVERTISING BUSINESS
  - paragraph: Fee TZS 120000.00 · 12 months · Advertisements & Signage
  - button "Requirements (1)"
  - button "Edit"
  - paragraph: Business Licence AR-ARUSHA-BUS BUSINESS
  - paragraph: Fee TZS 50000.00 · 12 months · inspection required · General Trade & Shops
  - button "Requirements (3)"
  - button "Edit"
  - paragraph: Driving Licence Renewal AR-ARUSHA-DRIVING_LICENCE_RENE DRIVING
  - paragraph: Fee TZS 70000.00 · 36 months
  - button "Requirements (2)"
  - button "Edit"
  - paragraph: Entertainment & Events Licence AR-ARUSHA-ACT-ENTERTAINMENT BUSINESS
  - paragraph: Fee TZS 100000.00 · 12 months · inspection required · Entertainment & Events
  - button "Requirements (2)"
  - button "Edit"
  - paragraph: Food & Beverages Licence AR-ARUSHA-ACT-FOOD BUSINESS
  - paragraph: Fee TZS 50000.00 · 12 months · inspection required · Food & Beverages
  - button "Requirements (3)"
  - button "Edit"
  - paragraph: Food Vendor Licence AR-ARUSHA-FOOD_VENDOR_LICENCE BUSINESS
  - paragraph: Fee TZS 30000.00 · 12 months · inspection required · Food & Beverages
  - button "Requirements (2)"
  - button "Edit"
  - paragraph: General Trade & Shops Licence AR-ARUSHA-ACT-GENERAL_TRADE BUSINESS
  - paragraph: Fee TZS 50000.00 · 12 months · General Trade & Shops
  - button "Requirements (2)"
  - button "Edit"
  - paragraph: Health, Pharmacies & Sanitation Licence AR-ARUSHA-ACT-HEALTH BUSINESS
  - paragraph: Fee TZS 80000.00 · 12 months · inspection required · Health, Pharmacies & Sanitation
  - button "Requirements (3)"
  - button "Edit"
  - paragraph: Hotels & Guest Houses Licence AR-ARUSHA-ACT-HOSPITALITY BUSINESS
  - paragraph: Fee TZS 200000.00 · 12 months · inspection required · Hotels & Guest Houses
  - button "Requirements (3)"
  - button "Edit"
  - paragraph: Liquor, Bars & Nightclubs Licence AR-ARUSHA-ACT-LIQUOR BUSINESS
  - paragraph: Fee TZS 150000.00 · 12 months · inspection required · Liquor, Bars & Nightclubs
  - button "Requirements (2)"
  - button "Edit"
  - paragraph: Livestock, Fisheries & Agriculture Licence AR-ARUSHA-ACT-LIVESTOCK BUSINESS
  - paragraph: Fee TZS 60000.00 · 12 months · inspection required · Livestock, Fisheries & Agriculture
  - button "Requirements (2)"
  - button "Edit"
  - paragraph: Markets & Street Vending Licence AR-ARUSHA-ACT-MARKETS BUSINESS
  - paragraph: Fee TZS 20000.00 · 12 months · Markets & Street Vending
  - button "Requirements (0)"
  - button "Edit"
  - paragraph: Natural Resources & Mining Licence AR-ARUSHA-ACT-NATURAL_RESOURCES BUSINESS
  - paragraph: Fee TZS 300000.00 · 12 months · inspection required · Natural Resources & Mining
  - button "Requirements (3)"
  - button "Edit"
  - paragraph: New Driving Licence AR-ARUSHA-NEW_DRIVING_LICENCE DRIVING
  - paragraph: Fee TZS 120000.00 · 36 months
  - button "Requirements (2)"
  - button "Edit"
  - paragraph: Small Industries & Workshops Licence AR-ARUSHA-ACT-INDUSTRY BUSINESS
  - paragraph: Fee TZS 70000.00 · 12 months · inspection required · Small Industries & Workshops
  - button "Requirements (2)"
  - button "Edit"
  - paragraph: Transport & Logistics Licence AR-ARUSHA-ACT-TRANSPORT BUSINESS
  - paragraph: Fee TZS 100000.00 · 12 months · Transport & Logistics
  - button "Requirements (2)"
  - button "Edit"
- contentinfo:
  - text: e-Leseni
  - paragraph: The official online platform for business licensing across Tanzania's local government councils. Apply, pay, and receive your licence — all online.
  - text: 31 Regions 200+ Councils 2900+ Wards
  - heading "For Businesses" [level=4]
  - navigation:
    - link "Create an account":
      - /url: /register
    - link "Log in to your account":
      - /url: /login
    - link "Apply for a licence":
      - /url: /apply
    - link "Manage my businesses":
      - /url: /businesses
    - link "My dashboard":
      - /url: /dashboard
    - link "My profile":
      - /url: /profile
  - heading "Services We Offer" [level=4]
  - list:
    - listitem: BRELA business registration
    - listitem: TRA TIN application
    - listitem: LGA licence application
    - listitem: Premises inspection scheduling
    - listitem: GePG payment via control number
    - listitem: QR-verifiable digital licences
  - heading "Support & Contact" [level=4]
  - list:
    - listitem:
      - text: "USSD access:"
      - strong: "*152*00#"
    - listitem: SMS status updates at every step
    - listitem: Basic phone support (no smartphone needed)
  - link "Verify a licence →":
    - /url: /verify
  - text: Live updates connected
  - paragraph: © 2026 e-Leseni. All rights reserved. Powered by LGA e-Services.
  - link "Register":
    - /url: /register
  - text: "|"
  - link "Log in":
    - /url: /login
  - text: "|"
  - link "Apply":
    - /url: /apply
  - text: "|"
  - link "Verify licence":
    - /url: /verify
```

# Test source

```ts
  1  | import { expect, test } from '@playwright/test';
  2  | 
  3  | import { login } from './support/helpers';
  4  | 
  5  | /**
  6  |  * Admin Council catalogue cascade: Region (with council counts) first, then
  7  |  * a filtered Council dropdown, then the catalogue list for that council.
  8  |  */
  9  | test.describe('Admin council catalogue cascade', () => {
  10 |   test('region first (with counts), then filtered council, then catalogue', async ({ page }) => {
  11 |     await login(page, 'admin', 'Demo@1234');
  12 |     await expect(page).toHaveURL(/\/staff\//);
  13 | 
  14 |     await page.getByRole('button', { name: 'Manage catalogue' }).click();
  15 | 
  16 |     // Wait for the region select to be populated (LGAs fetched on toggle)
  17 |     const regionSelect = page.locator('select', { has: page.locator('option', { hasText: '— choose a region —' }) });
  18 |     await expect(regionSelect.locator('option').filter({ hasText: /\(\d+\)$/ }).first()).toBeAttached({ timeout: 15_000 });
  19 | 
  20 |     // Region select comes before the council select, and every region shows "(n)"
  21 |     const councilSelect = page.locator('select', { has: page.locator('option', { hasText: /choose a region first|— choose a council —/ }) });
  22 |     await expect(regionSelect).toBeVisible();
  23 |     await expect(councilSelect).toBeVisible();
  24 |     // Region must precede council in the DOM (raw handles, not Locators)
  25 |     await page.evaluate(() => {
  26 |       const texts = (s: HTMLSelectElement) => [...s.options].map((o) => (o.textContent ?? '').trim());
  27 |       const all = [...document.querySelectorAll('select')];
  28 |       const region = all.find((s) => texts(s).includes('— choose a region —'));
  29 |       const council = all.find((s) => texts(s).some((t) => t.includes('choose a region first') || t.includes('— choose a council —')));
  30 |       if (!region || !council || (region.compareDocumentPosition(council) & Node.DOCUMENT_POSITION_FOLLOWING) === 0) {
  31 |         throw new Error('region select is missing or is not before the council select');
  32 |       }
  33 |     });
  34 | 
  35 |     const regionOptions = regionSelect.locator('option');
  36 |     const regionTexts = (await regionOptions.allTextContents()).filter((t) => t && !t.includes('choose a region'));
  37 |     expect(regionTexts.length).toBeGreaterThan(0);
  38 |     for (const text of regionTexts) expect(text).toMatch(/\(\d+\)$/);
  39 | 
  40 |     // Council select is disabled with the "choose a region first" hint
  41 |     await expect(councilSelect).toBeDisabled();
  42 |     await expect(councilSelect.locator('option').first()).toHaveText(/choose a region first/);
  43 | 
  44 |     // Pick the first region: council select enables and is filtered to it
  45 |     const pickedRegion = regionTexts[0];
  46 |     const pickedCount = Number(pickedRegion.match(/\((\d+)\)$/)?.[1]);
  47 |     await regionSelect.selectOption(pickedRegion.replace(/\s*\(\d+\)$/, ''));
  48 |     await expect(councilSelect).toBeEnabled();
  49 | 
  50 |     const councilTexts = (await councilSelect.locator('option').allTextContents())
  51 |       .filter((t) => t && !t.includes('choose a council'));
  52 |     expect(councilTexts.length).toBe(pickedCount);
  53 | 
  54 |     // Pick the first council: the catalogue loads for it
  55 |     await councilSelect.selectOption({ index: 1 }); // index 0 is the placeholder
  56 |     await expect(
  57 |       page.getByText(/fee|validity|months|No licence types/i).first(),
  58 |     ).toBeVisible();
  59 | 
  60 |     // Switching the region resets the council selection
  61 |     const otherRegion = regionTexts.find((t) => t !== pickedRegion);
  62 |     if (otherRegion) {
  63 |       await regionSelect.selectOption(otherRegion.replace(/\s*\(\d+\)$/, ''));
  64 |       await expect(councilSelect).toHaveValue('');
> 65 |       await expect(councilSelect.locator('option').first()).toHaveText(/choose a region first/);
     |                                                             ^ Error: expect(locator).toHaveText(expected) failed
  66 |     }
  67 |   });
  68 | });
  69 | 
```