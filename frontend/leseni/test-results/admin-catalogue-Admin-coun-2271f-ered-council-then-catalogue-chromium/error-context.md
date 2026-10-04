# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-catalogue.spec.ts >> Admin council catalogue cascade >> region first (with counts), then filtered council, then catalogue
- Location: e2e/admin-catalogue.spec.ts:10:7

# Error details

```
Error: expect(received).toBeGreaterThan(expected)

Expected: > 0
Received:   0
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - link "e-Leseni System Admin" [ref=e6] [cursor=pointer]:
        - /url: /
        - generic [ref=e8]: e-Leseni
        - generic [ref=e9]: System Admin
      - navigation [ref=e10]:
        - link "My workspace" [ref=e11] [cursor=pointer]:
          - /url: /staff/admin
        - link "Users & Staff" [ref=e12] [cursor=pointer]:
          - /url: /staff/users
        - link "Dashboard" [ref=e13] [cursor=pointer]:
          - /url: /dashboard
        - link "Profile" [ref=e14] [cursor=pointer]:
          - /url: /profile
        - link "USSD demo" [ref=e15] [cursor=pointer]:
          - /url: /ussd-demo
        - button "Log out" [ref=e16] [cursor=pointer]
      - generic "Live updates connected" [ref=e17]: Live
  - main [ref=e19]:
    - generic [ref=e21]:
      - generic [ref=e22]:
        - generic [ref=e23]:
          - heading "Administration" [level=1] [ref=e24]
          - paragraph [ref=e25]: Every application across all LGAs — full workflow control.
        - generic [ref=e26]:
          - heading "eGA GovESB Integration Status" [level=2] [ref=e27]
          - generic [ref=e28]:
            - generic [ref=e29]: BRELA
            - generic [ref=e30]: TRA
            - generic [ref=e31]: GePG
            - generic [ref=e32]: NIDA
        - generic [ref=e33]:
          - generic [ref=e34]: SYSTEM ADMIN
          - link "My Profile" [ref=e35] [cursor=pointer]:
            - /url: /profile
          - link "Manage Users & Staff →" [ref=e36] [cursor=pointer]:
            - /url: /staff/users
          - link "Switch workspace" [ref=e37] [cursor=pointer]:
            - /url: /staff/review
      - generic [ref=e38]:
        - generic [ref=e39]:
          - button "Needs review (1)" [ref=e40]
          - button "Inspections (7)" [ref=e41]
          - button "Approvals (3)" [ref=e42]
          - button "Payments (1)" [ref=e43]
          - button "All (25)" [ref=e44]
        - generic [ref=e45]:
          - generic [ref=e46]: Activity
          - combobox "Activity" [ref=e47]:
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
      - generic [ref=e49]:
        - generic [ref=e50]:
          - generic [ref=e51]:
            - paragraph [ref=e52]: EL-GE-CHATO-ACT-NATURAL_RESOURCES-2026-00001
            - generic [ref=e53]: Submitted
            - generic [ref=e54]: Natural Resources & Mining
          - paragraph [ref=e55]:
            - text: Walkthrough Traders
            - generic [ref=e56]: verified
          - paragraph [ref=e57]:
            - text: "Natural Resources & Mining Licence — Chato · applicant: Neema Robert"
            - generic "NIDA on file" [ref=e58]: NIDA
          - paragraph [ref=e59]: “SDSDFDF”
          - link "Land/Plot Agreement" [ref=e61] [cursor=pointer]:
            - /url: http://localhost:8000/media/application_documents/2026/10/afyatrust.pdf
        - generic [ref=e62]:
          - button "Start review" [ref=e63]
          - button "→ Returned for correction" [ref=e64]
      - generic [ref=e66]:
        - generic [ref=e67]:
          - heading "Business activities" [level=2] [ref=e68]
          - paragraph [ref=e69]: The council's “kind of business” taxonomy — what this queue is filtered by and what applicants pick.
        - button "Manage activities" [ref=e71]
      - generic [ref=e72]:
        - generic [ref=e73]:
          - generic [ref=e74]:
            - heading "Council catalogue" [level=2] [ref=e75]
            - paragraph [ref=e76]: Your council's licences — the fees, validity and requirements applicants see. Each council keeps its own rules here.
          - generic [ref=e77]:
            - generic [ref=e78]:
              - generic [ref=e79]: Region
              - combobox "Region" [ref=e80]:
                - option "— choose a region —" [disabled] [selected]
                - option "Arusha (3)"
                - option "Dodoma (2)"
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
            - generic [ref=e81]:
              - generic [ref=e82]: Council
              - combobox "Council" [disabled] [ref=e83]:
                - option "choose a region first" [disabled]
                - option "Arusha"
                - option "Arusha City"
                - option "Arusha District"
                - option "Babati"
                - option "Babati District"
                - option "Babati Town"
                - option "Bagamoyo"
                - option "Bahi"
                - option "Bariadi"
                - option "Berega"
                - option "Biharamulo"
                - option "Buchosa"
                - option "Buhigwe"
                - option "Bukoba"
                - option "Bukoba District"
                - option "Bukoba Municipal"
                - option "Bukombe"
                - option "Bunda"
                - option "Busega"
                - option "Busokelo"
                - option "Butiama"
                - option "Chake Chake"
                - option "Chalinze"
                - option "Chamwino"
                - option "Chato"
            - button "Hide catalogue" [active] [ref=e84]
            - button "New licence type" [ref=e85]
        - generic [ref=e86]:
          - generic [ref=e88]:
            - generic [ref=e89]:
              - paragraph [ref=e90]:
                - text: Advertisements & Signage Licence
                - generic [ref=e91]: DSM01-ACT-ADVERTISING
                - generic [ref=e92]: BUSINESS
              - paragraph [ref=e93]: Fee TZS 120000.00 · 12 months · Advertisements & Signage
            - generic [ref=e94]:
              - button "Requirements (1)" [ref=e95]
              - button "Edit" [ref=e96]
          - generic [ref=e98]:
            - generic [ref=e99]:
              - paragraph [ref=e100]:
                - text: Business Licence
                - generic [ref=e101]: DSM01-BUS
                - generic [ref=e102]: BUSINESS
              - paragraph [ref=e103]: Fee TZS 50000.00 · 12 months · inspection required · General Trade & Shops
            - generic [ref=e104]:
              - button "Requirements (3)" [ref=e105]
              - button "Edit" [ref=e106]
          - generic [ref=e108]:
            - generic [ref=e109]:
              - paragraph [ref=e110]:
                - text: Driving Licence Renewal
                - generic [ref=e111]: DSM01-DRIVING_LICENCE_RENE
                - generic [ref=e112]: DRIVING
              - paragraph [ref=e113]: Fee TZS 70000.00 · 36 months
            - generic [ref=e114]:
              - button "Requirements (2)" [ref=e115]
              - button "Edit" [ref=e116]
          - generic [ref=e118]:
            - generic [ref=e119]:
              - paragraph [ref=e120]:
                - text: Entertainment & Events Licence
                - generic [ref=e121]: DSM01-ACT-ENTERTAINMENT
                - generic [ref=e122]: BUSINESS
              - paragraph [ref=e123]: Fee TZS 100000.00 · 12 months · inspection required · Entertainment & Events
            - generic [ref=e124]:
              - button "Requirements (2)" [ref=e125]
              - button "Edit" [ref=e126]
          - generic [ref=e128]:
            - generic [ref=e129]:
              - paragraph [ref=e130]:
                - text: Food & Beverages Licence
                - generic [ref=e131]: DSM01-ACT-FOOD
                - generic [ref=e132]: BUSINESS
              - paragraph [ref=e133]: Fee TZS 50000.00 · 12 months · inspection required · Food & Beverages
            - generic [ref=e134]:
              - button "Requirements (3)" [ref=e135]
              - button "Edit" [ref=e136]
          - generic [ref=e138]:
            - generic [ref=e139]:
              - paragraph [ref=e140]:
                - text: Food Handler
                - generic [ref=e141]: FH01
                - generic [ref=e142]: BUSINESS
              - paragraph [ref=e143]: Fee TZS 50000.00 · 12 months · inspection required
            - generic [ref=e144]:
              - button "Requirements (2)" [ref=e145]
              - button "Edit" [ref=e146]
          - generic [ref=e148]:
            - generic [ref=e149]:
              - paragraph [ref=e150]:
                - text: Food Vendor Licence
                - generic [ref=e151]: DSM01-FOOD_VENDOR_LICENCE
                - generic [ref=e152]: BUSINESS
              - paragraph [ref=e153]: Fee TZS 30000.00 · 12 months · inspection required · Food & Beverages
            - generic [ref=e154]:
              - button "Requirements (2)" [ref=e155]
              - button "Edit" [ref=e156]
          - generic [ref=e158]:
            - generic [ref=e159]:
              - paragraph [ref=e160]:
                - text: General Trade
                - generic [ref=e161]: GT01
                - generic [ref=e162]: BUSINESS
              - paragraph [ref=e163]: Fee TZS 30000.00 · 12 months
            - generic [ref=e164]:
              - button "Requirements (0)" [ref=e165]
              - button "Edit" [ref=e166]
          - generic [ref=e168]:
            - generic [ref=e169]:
              - paragraph [ref=e170]:
                - text: General Trade & Shops Licence
                - generic [ref=e171]: DSM01-ACT-GENERAL_TRADE
                - generic [ref=e172]: BUSINESS
              - paragraph [ref=e173]: Fee TZS 50000.00 · 12 months · General Trade & Shops
            - generic [ref=e174]:
              - button "Requirements (2)" [ref=e175]
              - button "Edit" [ref=e176]
          - generic [ref=e178]:
            - generic [ref=e179]:
              - paragraph [ref=e180]:
                - text: Health, Pharmacies & Sanitation Licence
                - generic [ref=e181]: DSM01-ACT-HEALTH
                - generic [ref=e182]: BUSINESS
              - paragraph [ref=e183]: Fee TZS 80000.00 · 12 months · inspection required · Health, Pharmacies & Sanitation
            - generic [ref=e184]:
              - button "Requirements (3)" [ref=e185]
              - button "Edit" [ref=e186]
          - generic [ref=e188]:
            - generic [ref=e189]:
              - paragraph [ref=e190]:
                - text: Hotels & Guest Houses Licence
                - generic [ref=e191]: DSM01-ACT-HOSPITALITY
                - generic [ref=e192]: BUSINESS
              - paragraph [ref=e193]: Fee TZS 200000.00 · 12 months · inspection required · Hotels & Guest Houses
            - generic [ref=e194]:
              - button "Requirements (3)" [ref=e195]
              - button "Edit" [ref=e196]
          - generic [ref=e198]:
            - generic [ref=e199]:
              - paragraph [ref=e200]:
                - text: Liquor, Bars & Nightclubs Licence
                - generic [ref=e201]: DSM01-ACT-LIQUOR
                - generic [ref=e202]: BUSINESS
              - paragraph [ref=e203]: Fee TZS 150000.00 · 12 months · inspection required · Liquor, Bars & Nightclubs
            - generic [ref=e204]:
              - button "Requirements (2)" [ref=e205]
              - button "Edit" [ref=e206]
          - generic [ref=e208]:
            - generic [ref=e209]:
              - paragraph [ref=e210]:
                - text: Livestock, Fisheries & Agriculture Licence
                - generic [ref=e211]: DSM01-ACT-LIVESTOCK
                - generic [ref=e212]: BUSINESS
              - paragraph [ref=e213]: Fee TZS 60000.00 · 12 months · inspection required · Livestock, Fisheries & Agriculture
            - generic [ref=e214]:
              - button "Requirements (2)" [ref=e215]
              - button "Edit" [ref=e216]
          - generic [ref=e218]:
            - generic [ref=e219]:
              - paragraph [ref=e220]:
                - text: Markets & Street Vending Licence
                - generic [ref=e221]: DSM01-ACT-MARKETS
                - generic [ref=e222]: BUSINESS
              - paragraph [ref=e223]: Fee TZS 20000.00 · 12 months · Markets & Street Vending
            - generic [ref=e224]:
              - button "Requirements (0)" [ref=e225]
              - button "Edit" [ref=e226]
          - generic [ref=e228]:
            - generic [ref=e229]:
              - paragraph [ref=e230]:
                - text: Natural Resources & Mining Licence
                - generic [ref=e231]: DSM01-ACT-NATURAL_RESOURCES
                - generic [ref=e232]: BUSINESS
              - paragraph [ref=e233]: Fee TZS 300000.00 · 12 months · inspection required · Natural Resources & Mining
            - generic [ref=e234]:
              - button "Requirements (3)" [ref=e235]
              - button "Edit" [ref=e236]
          - generic [ref=e238]:
            - generic [ref=e239]:
              - paragraph [ref=e240]:
                - text: New Driving Licence
                - generic [ref=e241]: DSM01-NEW_DRIVING_LICENCE
                - generic [ref=e242]: DRIVING
              - paragraph [ref=e243]: Fee TZS 120000.00 · 36 months
            - generic [ref=e244]:
              - button "Requirements (2)" [ref=e245]
              - button "Edit" [ref=e246]
          - generic [ref=e248]:
            - generic [ref=e249]:
              - paragraph [ref=e250]:
                - text: Small Industries & Workshops Licence
                - generic [ref=e251]: DSM01-ACT-INDUSTRY
                - generic [ref=e252]: BUSINESS
              - paragraph [ref=e253]: Fee TZS 70000.00 · 12 months · inspection required · Small Industries & Workshops
            - generic [ref=e254]:
              - button "Requirements (2)" [ref=e255]
              - button "Edit" [ref=e256]
          - generic [ref=e258]:
            - generic [ref=e259]:
              - paragraph [ref=e260]:
                - text: Transport & Logistics Licence
                - generic [ref=e261]: DSM01-ACT-TRANSPORT
                - generic [ref=e262]: BUSINESS
              - paragraph [ref=e263]: Fee TZS 100000.00 · 12 months · Transport & Logistics
            - generic [ref=e264]:
              - button "Requirements (2)" [ref=e265]
              - button "Edit" [ref=e266]
  - contentinfo [ref=e267]:
    - generic [ref=e269]:
      - generic [ref=e270]:
        - generic [ref=e271]: e-Leseni
        - paragraph [ref=e274]: The official online platform for business licensing across Tanzania's local government councils. Apply, pay, and receive your licence — all online.
        - generic [ref=e275]:
          - generic [ref=e276]:
            - generic [ref=e277]: "31"
            - generic [ref=e278]: Regions
          - generic [ref=e279]:
            - generic [ref=e280]: 200+
            - generic [ref=e281]: Councils
          - generic [ref=e282]:
            - generic [ref=e283]: 2900+
            - generic [ref=e284]: Wards
      - generic [ref=e285]:
        - heading "For Businesses" [level=4] [ref=e286]
        - navigation [ref=e287]:
          - link "Create an account" [ref=e288] [cursor=pointer]:
            - /url: /register
          - link "Log in to your account" [ref=e289] [cursor=pointer]:
            - /url: /login
          - link "Apply for a licence" [ref=e290] [cursor=pointer]:
            - /url: /apply
          - link "Manage my businesses" [ref=e291] [cursor=pointer]:
            - /url: /businesses
          - link "My dashboard" [ref=e292] [cursor=pointer]:
            - /url: /dashboard
          - link "My profile" [ref=e293] [cursor=pointer]:
            - /url: /profile
      - generic [ref=e294]:
        - heading "Services We Offer" [level=4] [ref=e295]
        - list [ref=e296]:
          - listitem [ref=e297]: BRELA business registration
          - listitem [ref=e299]: TRA TIN application
          - listitem [ref=e301]: LGA licence application
          - listitem [ref=e303]: Premises inspection scheduling
          - listitem [ref=e305]: GePG payment via control number
          - listitem [ref=e307]: QR-verifiable digital licences
      - generic [ref=e309]:
        - heading "Support & Contact" [level=4] [ref=e310]
        - list [ref=e311]:
          - listitem [ref=e312]:
            - text: "USSD access:"
            - strong [ref=e314]: "*152*00#"
          - listitem [ref=e315]: SMS status updates at every step
          - listitem [ref=e317]: Basic phone support (no smartphone needed)
        - link "Verify a licence →" [ref=e319] [cursor=pointer]:
          - /url: /verify
        - generic [ref=e320]: Live updates connected
    - generic [ref=e323]:
      - paragraph [ref=e324]: © 2026 e-Leseni. All rights reserved. Powered by LGA e-Services.
      - generic [ref=e325]:
        - link "Register" [ref=e326] [cursor=pointer]:
          - /url: /register
        - generic [ref=e327]: "|"
        - link "Log in" [ref=e328] [cursor=pointer]:
          - /url: /login
        - generic [ref=e329]: "|"
        - link "Apply" [ref=e330] [cursor=pointer]:
          - /url: /apply
        - generic [ref=e331]: "|"
        - link "Verify licence" [ref=e332] [cursor=pointer]:
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
  16 |     // Region select comes before the council select, and every region shows "(n)"
  17 |     const regionSelect = page.locator('select', { has: page.locator('option', { hasText: '— choose a region —' }) });
  18 |     const councilSelect = page.locator('select', { has: page.locator('option', { hasText: /choose a region first|— choose a council —/ }) });
  19 |     await expect(regionSelect).toBeVisible();
  20 |     await expect(councilSelect).toBeVisible();
  21 |     // Region must precede council in the DOM (raw handles, not Locators)
  22 |     await page.evaluate(() => {
  23 |       const texts = (s: HTMLSelectElement) => [...s.options].map((o) => (o.textContent ?? '').trim());
  24 |       const all = [...document.querySelectorAll('select')];
  25 |       const region = all.find((s) => texts(s).includes('— choose a region —'));
  26 |       const council = all.find((s) => texts(s).some((t) => t.includes('choose a region first') || t.includes('— choose a council —')));
  27 |       if (!region || !council || (region.compareDocumentPosition(council) & Node.DOCUMENT_POSITION_FOLLOWING) === 0) {
  28 |         throw new Error('region select is missing or is not before the council select');
  29 |       }
  30 |     });
  31 | 
  32 |     const regionOptions = regionSelect.locator('option');
  33 |     const regionTexts = (await regionOptions.allTextContents()).filter((t) => t && !t.includes('choose a region'));
> 34 |     expect(regionTexts.length).toBeGreaterThan(0);
     |                                ^ Error: expect(received).toBeGreaterThan(expected)
  35 |     for (const text of regionTexts) expect(text).toMatch(/\(\d+\)$/);
  36 | 
  37 |     // Council select is disabled with the "choose a region first" hint
  38 |     await expect(councilSelect).toBeDisabled();
  39 |     await expect(councilSelect.locator('option').first()).toHaveText(/choose a region first/);
  40 | 
  41 |     // Pick the first region: council select enables and is filtered to it
  42 |     const pickedRegion = regionTexts[0];
  43 |     const pickedCount = Number(pickedRegion.match(/\((\d+)\)$/)?.[1]);
  44 |     await regionSelect.selectOption(pickedRegion.replace(/\s*\(\d+\)$/, ''));
  45 |     await expect(councilSelect).toBeEnabled();
  46 | 
  47 |     const councilTexts = (await councilSelect.locator('option').allTextContents())
  48 |       .filter((t) => t && !t.includes('choose a council'));
  49 |     expect(councilTexts.length).toBe(pickedCount);
  50 | 
  51 |     // Pick the first council: the catalogue loads for it
  52 |     await councilSelect.selectOption({ index: 1 }); // index 0 is the placeholder
  53 |     await expect(
  54 |       page.getByText(/fee|validity|months|No licence types/i).first(),
  55 |     ).toBeVisible();
  56 | 
  57 |     // Switching the region resets the council selection
  58 |     const otherRegion = regionTexts.find((t) => t !== pickedRegion);
  59 |     if (otherRegion) {
  60 |       await regionSelect.selectOption(otherRegion.replace(/\s*\(\d+\)$/, ''));
  61 |       await expect(councilSelect).toHaveValue('');
  62 |       await expect(councilSelect.locator('option').first()).toHaveText(/choose a region first/);
  63 |     }
  64 |   });
  65 | });
  66 | 
```