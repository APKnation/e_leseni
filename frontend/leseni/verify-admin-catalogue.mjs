// One-off browser verification of the admin region -> council catalogue cascade.
// 1. Log in as admin, open the staff workspace, show the Council catalogue
// 2. Assert the Region dropdown is listed BEFORE the council dropdown, with "(n)" counts
// 3. Assert the council select is disabled with "choose a region first" before a region is picked
// 4. Pick a region -> council select enables, shows only that region's councils
// 5. Pick a council -> catalogue list loads for it
// 6. Switch region -> council resets and catalogue clears
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

  // -- 1. Login as admin and reach the staff workspace ----------------------
  await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle2' });
  await page.waitForSelector('input[name="username"]', { visible: true, timeout: 20000 });
  await page.type('input[name="username"]', 'admin', { delay: 10 });
  await page.type('input[name="password"]', 'Demo@1234', { delay: 10 });
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 }).catch(() => {}),
    page.click('button[type="submit"]'),
  ]);
  await page.waitForFunction(
    () => location.pathname.startsWith('/staff/'),
    { timeout: 20000 },
  );
  check('login as admin lands on staff workspace', true, page.url());

  // -- 2. Open the Council catalogue ----------------------------------------
  const toggleXPath = '//button[contains(normalize-space(.), "Manage catalogue")]';
  await page.waitForSelector(`xpath/.${toggleXPath}`, { timeout: 20000 });
  const [toggleBtn] = await page.$x(toggleXPath);
  await toggleBtn.click();
  await page.waitForSelector('select', { timeout: 20000 });

  // Region select must exist for admins and come before the council select
  const selects = await page.$$('select');
  let regionHandle = null;
  let councilHandle = null;
  for (const sel of selects) {
    const options = await sel.$$eval('option', (os) => os.map((o) => o.textContent?.trim() ?? ''));
    if (options.some((t) => t.includes('choose a region'))) regionHandle = sel;
    if (options.some((t) => t.includes('choose a council') || t.includes('choose a region first'))) councilHandle = sel;
  }
  check('region dropdown present for admin', regionHandle !== null);
  check('council dropdown present for admin', councilHandle !== null);

  const orderOk = regionHandle && councilHandle
    ? await page.evaluate((a, b) => {
        const pos = (el) => el.compareDocumentPosition(el.ownerDocument.documentElement);
        return (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
      }, regionHandle, councilHandle)
    : false;
  check('region select appears BEFORE council select in the DOM', orderOk);

  // Region options carry "(n)" council counts
  const regionOptions = await regionHandle.$$eval('option', (os) =>
    os.map((o) => o.textContent?.trim() ?? '').filter((t) => t && !t.includes('choose a region')),
  );
  const allHaveCounts = regionOptions.length > 0 && regionOptions.every((t) => /\(\d+\)$/.test(t));
  check('every region option shows a council count "(n)"', allHaveCounts, JSON.stringify(regionOptions));
  await page.screenshot({ path: `${SHOTS}/9-admin-catalogue-region-first.png` });

  // -- 3. Council select disabled until a region is picked -------------------
  const councilDisabledBefore = await councilHandle.evaluate((el) => el.disabled);
  const councilLabelBefore = await councilHandle.$$eval('option', (os) => os[0]?.textContent?.trim() ?? '');
  check(
    'council select disabled with "choose a region first" hint',
    councilDisabledBefore && councilLabelBefore.includes('choose a region first'),
    councilLabelBefore,
  );

  // -- 4. Pick a region: council select enables, filtered, catalogue loads ---
  const regionToPick = regionOptions[0];
  const regionValue = regionToPick.replace(/\s*\(\d+\)$/, '');
  await regionHandle.select(regionValue);

  const councilDisabledAfter = await councilHandle.evaluate((el) => el.disabled);
  check('council select enables after picking a region', !councilDisabledAfter);

  await page.waitForFunction(
    () => {
      const sel = [...document.querySelectorAll('select')]
        .find((s) => [...s.options].some((o) => o.textContent?.includes('choose a council')));
      return sel ? sel.options.length > 1 : false;
    },
    { timeout: 10000 },
  );
  const councilOptions = await councilHandle.$$eval('option', (os) =>
    os.map((o) => o.textContent?.trim() ?? '').filter((t) => t && !t.includes('choose a council')),
  );
  check('council list filtered to the picked region', councilOptions.length > 0, JSON.stringify(councilOptions));

  // Count in the region label matches the number of councils offered
  const regionCount = Number(regionToPick.match(/\((\d+)\)$/)?.[1] ?? -1);
  check(
    'region label count matches councils offered',
    regionCount === councilOptions.length,
    `${regionToPick} -> ${councilOptions.length}`,
  );

  // Pick the first council
  const firstCouncilValue = await councilHandle.$$eval('option', (os) => {
    const opt = os.find((o) => !o.textContent?.includes('choose a council') && o.value);
    return opt ? opt.value : '';
  });
  await councilHandle.select(firstCouncilValue);

  // Catalogue list loads (either licence rows or an empty-catalogue message)
  await page.waitForFunction(
    () => document.body.innerText.includes('licence') || document.body.innerText.length > 1000,
    { timeout: 15000 },
  );
  const hasCatalogue = await page.evaluate(() => {
    const text = document.body.innerText;
    return text.includes('No licence types') || /fee|validity|months/i.test(text);
  });
  check('catalogue loads for the picked council', hasCatalogue);
  await page.screenshot({ path: `${SHOTS}/10-admin-catalogue-loaded.png`, fullPage: true });

  // -- 5. Switch region: council resets, catalogue clears ---------------------
  const otherRegion = regionOptions.find((t) => t !== regionToPick);
  if (otherRegion) {
    const otherValue = otherRegion.replace(/\s*\(\d+\)$/, '');
    await regionHandle.select(otherValue);
    await new Promise((r) => setTimeout(r, 800));
    const councilValueNow = await councilHandle.evaluate((el) => el.value);
    check(
      'switching region resets the council selection',
      councilValueNow === '' || councilValueNow === null,
      `council value="${councilValueNow}"`,
    );
    await page.screenshot({ path: `${SHOTS}/11-admin-catalogue-region-switch.png` });
  }
} catch (err) {
  console.error('SCRIPT ERROR:', err.message);
  results.push({ name: 'script completed', ok: false, extra: err.message });
} finally {
  await browser.close();
}

const failed = results.filter((r) => !r.ok).length;
console.log(`\n${results.length - failed}/${results.length} checks passed`);
process.exit(failed ? 1 : 0);
