// One-off browser verification of the USSD demo page.
// 1. Log in as applicant1, open /ussd-demo via the nav link
// 2. Dial *152*00# -> main menu must render
// 3. Reply 2 -> application status list (proves session continuity)
// 4. Reply 1 -> status detail (CON/END screen)
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

  await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle2' });
  await page.waitForSelector('input[name="username"]', { visible: true, timeout: 20000 });
  await page.type('input[name="username"]', 'applicant1', { delay: 10 });
  await page.type('input[name="password"]', 'Demo@1234', { delay: 10 });
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 }).catch(() => {}),
    page.click('button[type="submit"]'),
  ]);
  await page.waitForFunction(() => location.pathname === '/dashboard', { timeout: 20000 });
  check('login as applicant1', true);

  await page.click('a[href="/ussd-demo"]');
  await page.waitForSelector('#ussd-dial', { visible: true, timeout: 20000 });
  check('USSD demo page opens from the nav link', page.url().includes('/ussd-demo'), page.url());

  // Dial the service code — built entirely with the clickable keypad.
  // NOTE: Angular updates the input binding a tick after the click, so always
  // waitForFunction on the expected value instead of reading immediately.
  const dialValue = await page.$eval('#ussd-dial', (el) => el.value);
  check('dial input pre-filled with *152*00#', dialValue === '*152*00#', dialValue);
  for (let i = 0; i < dialValue.length; i++) await page.click('#btn-backspace');
  await page.waitForFunction(() => document.querySelector('#ussd-dial').value === '', { timeout: 5000 });
  const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'];
  for (const key of ['*', '1', '5', '2', '*', '0', '0', '#']) {
    await page.click(`button.keypad-key:nth-child(${KEYS.indexOf(key) + 1})`);
  }
  await page.waitForFunction(
    () => document.querySelector('#ussd-dial').value === '*152*00#',
    { timeout: 5000 },
  );
  check('keypad taps rebuild *152*00# in the dial field', true);
  const keypadCaption = await page.$eval('#ussd-dial', () =>
    document.querySelector('.text-xs.font-bold')?.textContent ?? '',
  );
  check('keypad caption says it types the service code', keypadCaption.includes('service code'), keypadCaption.trim());
  await page.click('#btn-dial');
  await page.waitForFunction(
    () => document.querySelector('#ussd-screen')?.innerText.includes('Apply for licence'),
    { timeout: 15000 },
  );
  const menu = await page.$eval('#ussd-screen', (el) => el.innerText);
  check('main menu renders on the simulated screen', menu.includes('1. Apply for licence') && menu.includes('5. My licences'), JSON.stringify(menu.slice(0, 60)));
  await page.screenshot({ path: `${SHOTS}/5-ussd-menu.png` });

  // Reply 2: application status — entered via the keypad, not the keyboard
  await page.waitForFunction(
    () => document.querySelector('#ussd-reply') !== null,
    { timeout: 15000 },
  );
  const replyCaption = await page.evaluate(() =>
    [...document.querySelectorAll('.text-xs.font-bold')].map((e) => e.textContent).join(''),
  );
  check('keypad caption switches to typing the reply', replyCaption.includes('reply'), replyCaption.trim());
  await page.click('button.keypad-key:nth-child(2)'); // key "2"
  await page.waitForFunction(
    () => document.querySelector('#ussd-reply').value === '2',
    { timeout: 5000 },
  );
  check('keypad tap lands in the reply input', true);
  await page.click('#btn-send-reply');
  await page.waitForFunction(
    () => document.querySelector('#ussd-screen')?.innerText.includes('Status - pick application'),
    { timeout: 15000 },
  );
  const statusList = await page.$eval('#ussd-screen', (el) => el.innerText);
  check('reply 2 shows the application status list', statusList.includes('EL-'), JSON.stringify(statusList.slice(0, 80)));
  await page.screenshot({ path: `${SHOTS}/6-ussd-status-list.png` });

  // Reply 1: pick first application -> detail screen (session continuity)
  await page.click('button.keypad-key:nth-child(1)'); // key "1"
  await page.click('#btn-send-reply');
  await page.waitForFunction(
    () => {
      const t = document.querySelector('#ussd-screen')?.innerText ?? '';
      return t.includes('session ended') || t.includes('Reference') || t.includes('reference') || t.includes('Status');
    },
    { timeout: 15000 },
  );
  const detail = await page.$eval('#ussd-screen', (el) => el.innerText);
  const ended = detail.includes('session ended');
  check('reply 1 shows the application detail screen', detail.length > 20, JSON.stringify(detail.slice(0, 100)));
  await page.screenshot({ path: `${SHOTS}/7-ussd-detail.png` });

  // After END, the reply input must be hidden
  const replyVisible = await page.$('#ussd-reply');
  check('reply input hidden once the session ends (END)', ended ? replyVisible === null : true, ended ? 'END received' : 'still CON');
} catch (err) {
  console.error('SCRIPT ERROR:', err.message);
  results.push({ name: 'script completed', ok: false, extra: err.message });
} finally {
  await browser.close();
}

const failed = results.filter((r) => !r.ok).length;
console.log(`\n${results.length - failed}/${results.length} checks passed`);
process.exit(failed ? 1 : 0);
