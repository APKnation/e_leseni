# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: nida-banner.spec.ts >> NIDA banner (citizen dashboard) >> applicant without NIDA sees the banner; adding one clears it
- Location: e2e/nida-banner.spec.ts:19:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByTestId('nida-banner')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByTestId('nida-banner') with timeout 5000ms
  - waiting for getByTestId('nida-banner')

```

```yaml
- banner:
  - link "e-Leseni Applicant":
    - /url: /
  - navigation:
    - link "Dashboard":
      - /url: /dashboard
    - link "My businesses":
      - /url: /businesses
    - link "Apply":
      - /url: /apply
    - link "Profile":
      - /url: /profile
    - link "USSD demo":
      - /url: /ussd-demo
    - button "Log out"
  - text: Live
- main:
  - heading "Karibu, Neema" [level=1]
  - paragraph: Your licence applications, payments and licences.
  - text: Applicant
  - link "My Profile":
    - /url: /profile
  - link "+ New application":
    - /url: /apply
  - heading "Active applications" [level=2]
  - text: "19"
  - heading "Awaiting payment" [level=2]
  - text: "0"
  - heading "Active licences" [level=2]
  - text: "0"
  - heading "Your licensing journey" [level=2]
  - paragraph: Before a council licence, every business needs BRELA registration and a TRA TIN — we handle both online.
  - list:
    - listitem: DONE Register your business with BRELA
    - listitem: DONE Get your TIN from TRA
    - listitem: DONE Get verified (TRA + BRELA check)
    - listitem: DONE Apply for your first LGA licence
    - listitem: Receive your licence
  - heading "Applications" [level=2]
  - paragraph: EL-GE-CHATO-ACT-NATURAL_RESOURCES-2026-00001
  - paragraph: Walkthrough Traders
  - paragraph: Natural Resources & Mining Licence — Chato
  - text: Submitted
  - button "Show timeline ▼"
  - paragraph: EL-DS-ILALA-FOOD_VENDOR_LICENCE-2026-00007
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Inspection scheduled
  - button "Show timeline ▼"
  - paragraph: EL-DS-ILALA-FOOD_VENDOR_LICENCE-2026-00006
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Draft
  - button "Show timeline ▼"
  - paragraph: EL-DS-ILALA-FOOD_VENDOR_LICENCE-2026-00005
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Inspected
  - button "Show timeline ▼"
  - paragraph: EL-IR-MAFINGA-BUS-2026-00001
  - paragraph: lia lia
  - paragraph: Business Licence — Mafinga
  - text: Draft
  - button "Show timeline ▼"
  - paragraph: EL-IR-MUFINDI-BUS-2026-00003
  - paragraph: lia lia
  - paragraph: Business Licence — Mufindi
  - text: Draft
  - button "Show timeline ▼"
  - paragraph: EL-IR-MUFINDI-BUS-2026-00002
  - paragraph: lia lia
  - paragraph: Business Licence — Mufindi
  - text: Draft
  - button "Show timeline ▼"
  - paragraph: EL-IR-MUFINDI-FOOD_VENDOR_LICENCE-2026-00003
  - paragraph: lia lia
  - paragraph: Food Vendor Licence — Mufindi
  - text: Draft
  - button "Show timeline ▼"
  - paragraph: EL-IR-MUFINDI-FOOD_VENDOR_LICENCE-2026-00002
  - paragraph: lia lia
  - paragraph: Food Vendor Licence — Mufindi
  - text: Inspection scheduled
  - button "Show timeline ▼"
  - paragraph: EL-IR-MUFINDI-FOOD_VENDOR_LICENCE-2026-00001
  - paragraph: lia lia
  - paragraph: Food Vendor Licence — Mufindi
  - text: Draft
  - button "Show timeline ▼"
  - paragraph: EL-DS-ILALA-FOOD_VENDOR_LICENCE-2026-00004
  - paragraph: Walkthrough Traders
  - paragraph: Food Vendor Licence — Ilala
  - text: Inspection scheduled
  - button "Show timeline ▼"
  - paragraph: EL-IR-MUFINDI-BUS-2026-00001
  - paragraph: lia lia
  - paragraph: Business Licence — Mufindi
  - text: Inspected
  - button "Show timeline ▼"
  - paragraph: EL-DS-ILALA-FOOD_VENDOR_LICENCE-2026-00003
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Rejected
  - button "Show timeline ▼"
  - paragraph: EL-DS-ILALA-FOOD_VENDOR_LICENCE-2026-00002
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Inspection scheduled
  - button "Show timeline ▼"
  - paragraph: EL-FOOD-ILALA-2026-00006
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Approved
  - button "Show timeline ▼"
  - paragraph: EL-FOOD-ILALA-2026-00005
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Approved
  - button "Show timeline ▼"
  - paragraph: EL-FOOD-ILALA-2026-00004
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Inspected
  - button "Show timeline ▼"
  - paragraph: EL-FOOD-ILALA-2026-00003
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Inspection scheduled
  - button "Show timeline ▼"
  - paragraph: EL-FOOD-ILALA-2026-00002
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Inspection scheduled
  - button "Show timeline ▼"
  - paragraph: EL-DS-ILALA-FOOD_VENDOR_LICENCE-2026-00001
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Rejected
  - button "Show timeline ▼"
  - paragraph: "Reason for rejection: Premises do not meet the food-handling bylaw; cold storage missing."
  - paragraph: EL-FOOD-ILALA-2026-00001
  - paragraph: Mama Neema Foods
  - paragraph: Food Vendor Licence — Ilala
  - text: Returned for correction
  - button "Show timeline ▼"
  - heading "Invoices & Payments" [level=2]
  - paragraph: No invoices yet.
  - heading "My businesses & activities" [level=2]
  - link "Manage businesses":
    - /url: /businesses
  - link "+ Apply for another activity":
    - /url: /apply
  - paragraph: apk
  - text: verified
  - paragraph: services
  - paragraph: "TIN: 991443074 · BRELA: 102681181"
  - paragraph: Walkthrough Traders
  - text: verified
  - paragraph: Retail · Kariakoo, Ilala
  - paragraph: "TIN: 123456789 · BRELA: 102345678"
  - paragraph: Walkthrough Shop
  - text: verified
  - paragraph: Retail
  - paragraph: "TIN: 123456789 · BRELA: 102345678"
  - paragraph: lia lia
  - text: unverified
  - paragraph: kilimo · Mninga, Mufindi
  - paragraph: "TIN: 121212 · BRELA: 121212"
  - paragraph: Mama Neema Foods
  - text: unverified
  - paragraph: Food & Beverage · Upanga, Ilala
  - paragraph: "TIN: 123456789 · BRELA: 100987654"
  - heading "Licences" [level=2]
  - paragraph: No licences issued yet.
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
  3  | import { login, resetApplicantNida } from './support/helpers';
  4  | 
  5  | const DEMO_NIDA = '19991234567890123456';
  6  | 
  7  | test.describe('NIDA banner (citizen dashboard)', () => {
  8  |   test.use({ storageState: { cookies: [], origins: [] } }); // always start logged out
  9  | 
  10 |   test.beforeEach(async ({ request }) => {
  11 |     await resetApplicantNida(request, '');
  12 |   });
  13 | 
  14 |   test.afterAll(async ({ request }) => {
  15 |     // Leave the demo database in its seeded state (applicant1 has no NIDA).
  16 |     await resetApplicantNida(request, '');
  17 |   });
  18 | 
  19 |   test('applicant without NIDA sees the banner; adding one clears it', async ({ page }) => {
  20 |     await login(page, 'applicant1', 'Demo@1234');
  21 | 
  22 |     // Banner is visible with the warning text and CTA
  23 |     const banner = page.getByTestId('nida-banner');
> 24 |     await expect(banner).toBeVisible();
     |                          ^ Error: expect(locator).toBeVisible() failed
  25 |     await expect(banner).toContainText('Your profile has no NIDA number');
  26 |     await expect(banner).toContainText('Add your NIDA number');
  27 | 
  28 |     // CTA deep-links to the profile edit tab
  29 |     await banner.getByRole('link', { name: /Add your NIDA number/ }).click();
  30 |     await expect(page).toHaveURL(/\/profile\?edit=1/);
  31 |     await expect(page.locator('#edit-nida')).toBeVisible();
  32 | 
  33 |     // Save a 20-digit NIDA number
  34 |     await page.fill('#edit-nida', DEMO_NIDA);
  35 |     await page.click('#btn-save-profile');
  36 |     await expect(page.getByText('Profile updated successfully.')).toBeVisible();
  37 | 
  38 |     // Back on the dashboard the banner is gone
  39 |     await page.click('a[href="/dashboard"]');
  40 |     await expect(page).toHaveURL(/\/dashboard/);
  41 |     await expect(banner).toHaveCount(0);
  42 |   });
  43 | 
  44 |   test('staff never see the NIDA banner', async ({ page }) => {
  45 |     await login(page, 'officer1', 'Demo@1234');
  46 |     // Officer lands on their review workspace; the banner only exists on /dashboard
  47 |     await expect(page).toHaveURL(/\/staff\//);
  48 |     await page.goto('/dashboard');
  49 |     await expect(page.getByTestId('nida-banner')).toHaveCount(0);
  50 |   });
  51 | });
  52 | 
```