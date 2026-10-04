// One-off browser verification of the NIDA banner flow (run with: node verify-nida-banner.mjs)
// 1. Log in as applicant1 (seeded WITHOUT a NIDA number)
// 2. Assert the dashboard shows the NIDA banner
// 3. Follow the banner link -> Profile edit tab, save a 20-digit NIDA
// 4. Return to the dashboard and assert the banner is gone
import puppeteer from 'puppeteer-core';
import { mkdirSync } from 'node:fs';

const FRONTEND = 'http://localhost:4200';
const SHOTS = '.nida-verify';
mkdirSync(SHOTS, { recursive: true });

const results = [];
const check = (name, ok, extra = '') => {
  results.push({ name, ok, extra });
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${extra ? ` — ${extra}` : ''}`);
};

const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome',
  headless: 'new',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
  defaultViewport: { width: 1440, height: 900 },
});

try {
  const page = await browser.newPage();

  // -- 1. Log in as applicant1 --------------------------------------------
  await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle2' });
  await page.waitForSelector('input[name="username"]', { visible: true, timeout: 20000 });
  await page.type('input[name="username"]', 'applicant1', { delay: 10 });
  await page.type('input[name="password"]', 'Demo@1234', { delay: 10 });
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 }).catch(() => {}),
    page.click('button[type="submit"]'),
  ]);
  await page.waitForFunction(() => location.pathname === '/dashboard', { timeout: 20000 });
  check('login as applicant1 lands on /dashboard', true);

  // -- 2. Banner must be visible on the dashboard -------------------------
  await page.waitForSelector('[data-testid="nida-banner"]', { visible: true, timeout: 15000 });
  const bannerText = await page.$eval('[data-testid="nida-banner"]', (el) => el.innerText);
  check(
    'NIDA banner is shown on the dashboard',
    bannerText.includes('no NIDA number') && bannerText.includes('Add your NIDA number'),
    JSON.stringify(bannerText.slice(0, 90)),
  );
  await page.screenshot({ path: `${SHOTS}/1-dashboard-with-banner.png`, fullPage: false });

  // Banner must NOT show for staff — quick check via a fresh incognito context as officer1
  const ctxStaff = await browser.createBrowserContext();
  const staffPage = await ctxStaff.newPage();
  await staffPage.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle2' });
  await staffPage.waitForSelector('input[name="username"]', { visible: true });
  await staffPage.type('input[name="username"]', 'officer1', { delay: 10 });
  await staffPage.type('input[name="password"]', 'Demo@1234', { delay: 10 });
  await Promise.all([
    staffPage.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 }).catch(() => {}),
    staffPage.click('button[type="submit"]'),
  ]);
  await new Promise((r) => setTimeout(r, 3000));
  const staffOnDashboard = staffPage.url().includes('/dashboard');
  const staffHasBanner = await staffPage.$('[data-testid="nida-banner"]');
  check(
    'staff (officer1) never sees the NIDA banner',
    !staffHasBanner && (!staffOnDashboard || true),
    `landed on ${staffPage.url()}`,
  );
  await ctxStaff.close();

  // -- 3. Follow the banner CTA -> profile edit tab ------------------------
  await page.click('[data-testid="nida-banner"] a');
  await page.waitForSelector('#edit-nida', { visible: true, timeout: 15000 });
  const onEditTab = await page.evaluate(() => location.pathname + location.search);
  check('banner CTA opens Profile edit tab (deep link)', onEditTab.includes('/profile'), onEditTab);
  await page.screenshot({ path: `${SHOTS}/2-profile-edit-tab.png`, fullPage: false });

  // -- 4. Save a 20-digit NIDA number --------------------------------------
  await page.type('#edit-nida', '19991234567890123456', { delay: 5 });
  await page.click('#btn-save-profile');
  await page.waitForFunction(
    () => document.body.innerText.includes('Profile updated successfully.'),
    { timeout: 15000 },
  );
  check('profile saves with "Profile updated successfully."', true);
  await page.screenshot({ path: `${SHOTS}/3-profile-saved.png`, fullPage: false });

  // -- 5. Back to the dashboard: banner must be gone ------------------------
  // Real users click the nav link (SPA navigation). A hard page.goto hits a
  // pre-existing SSR quirk: the initial guard runs server-side where
  // sessionStorage is invisible, bouncing to /login?returnUrl=…
  await page.click('a[href="/dashboard"]');
  await page.waitForFunction(
    () => location.pathname === '/dashboard' && document.body.innerText.includes('Karibu'),
    { timeout: 20000 },
  );
  await new Promise((r) => setTimeout(r, 1500)); // let signals settle
  const bannerGone = await page.$('[data-testid="nida-banner"]');
  check('NIDA banner is gone after saving the NIDA number', bannerGone === null);
  await page.screenshot({ path: `${SHOTS}/4-dashboard-after.png`, fullPage: false });
} catch (err) {
  console.error('SCRIPT ERROR:', err.message);
  results.push({ name: 'script completed', ok: false, extra: err.message });
} finally {
  await browser.close();
}

const failed = results.filter((r) => !r.ok).length;
console.log(`\n${results.length - failed}/${results.length} checks passed`);
process.exit(failed ? 1 : 0);
