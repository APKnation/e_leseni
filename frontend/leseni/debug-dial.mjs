// Debug: keypad-built dial then click Dial — dump the screen state.
import puppeteer from 'puppeteer-core';

const FRONTEND = 'http://localhost:4200';
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
  await page.click('a[href="/ussd-demo"]');
  await page.waitForSelector('#ussd-dial', { visible: true, timeout: 20000 });

  const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'];
  for (let i = 0; i < 8; i++) await page.click('#btn-backspace');
  for (const key of ['*', '1', '5', '2', '*', '0', '0', '#']) {
    await page.click(`button.keypad-key:nth-child(${KEYS.indexOf(key) + 1})`);
  }
  await page.waitForFunction(
    () => document.querySelector('#ussd-dial').value === '*152*00#',
    { timeout: 5000 },
  );
  console.log('dial field:', await page.$eval('#ussd-dial', (el) => el.value));
  await page.click('#btn-dial');

  for (const waitMs of [500, 1500, 3000, 6000]) {
    await new Promise((r) => setTimeout(r, waitMs));
    const state = await page.evaluate(() => ({
      screen: document.querySelector('#ussd-screen')?.innerText.slice(0, 150) ?? '(no screen)',
      errorBox: document.querySelector('.text-danger')?.textContent?.trim() ?? '(no error box)',
      replyInput: document.querySelector('#ussd-reply') !== null,
      dialDisabled: document.querySelector('#btn-dial')?.disabled ?? null,
      sessionActive: document.body.innerText.includes('session active'),
    }));
    console.log(`t+${waitMs}ms:`, JSON.stringify(state, null, 1));
  }
  await page.screenshot({ path: '.nida-verify/debug-dial.png' });
} catch (err) {
  console.error('DEBUG ERROR:', err.message);
} finally {
  await browser.close();
}
