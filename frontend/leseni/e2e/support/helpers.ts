import { Page } from '@playwright/test';

let adminToken: string | null = null;
let applicantUserId: number | null = null;

/** Log in through the UI and wait for the redirect to the role's workspace. */
export async function login(page: Page, username: string, password: string): Promise<void> {
  await page.goto('/login');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/(dashboard|staff\/)/, { timeout: 20_000 });
}

/** Admin JWT for user-management API calls (cached per worker). */
async function adminAuth(request: import('@playwright/test').APIRequestContext): Promise<string> {
  if (adminToken) return adminToken;
  const res = await request.post('http://localhost:8000/api/auth/login/', {
    data: { username: 'admin', password: 'Demo@1234' },
  });
  if (!res.ok()) throw new Error(`Backend admin login failed: ${res.status()}`);
  const { access } = await res.json();
  adminToken = access;
  return access;
}

/**
 * Reset applicant1's NIDA number via the admin user-management API so the
 * banner tests always start from a known state (empty = seeded state).
 */
export async function resetApplicantNida(
  request: import('@playwright/test').APIRequestContext,
  nida: string,
): Promise<void> {
  const token = await adminAuth(request);
  if (applicantUserId === null) {
    const find = await request.get('http://localhost:8000/api/users/?search=applicant1', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!find.ok()) throw new Error(`User lookup failed: ${find.status()}`);
    const { results } = (await find.json()) as { results: { id: number; username: string }[] };
    const user = results.find((u) => u.username === 'applicant1');
    if (!user) throw new Error('applicant1 not found — is the demo data seeded?');
    applicantUserId = user.id;
  }
  const patch = await request.patch(`http://localhost:8000/api/users/${applicantUserId}/`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { nida_number: nida },
  });
  if (!patch.ok()) throw new Error(`NIDA reset failed: ${patch.status()} — ${await patch.text()}`);
  // Verify the write actually landed before the test proceeds.
  const check = await request.get('http://localhost:8000/api/auth/me/', {
    headers: { Authorization: `Bearer ${await adminAuthAsApplicant(request)}` },
  });
  if (check.ok()) {
    const me = (await check.json()) as { nida_number: string };
    if ((me.nida_number || '') !== nida) {
      throw new Error(`NIDA reset did not stick: expected ${nida!r}, got ${me.nida_number!r}`);
    }
  }
}

/** Login as applicant1 (for verifying the reset through /auth/me/). */
async function adminAuthAsApplicant(request: import('@playwright/test').APIRequestContext): Promise<string> {
  const res = await request.post('http://localhost:8000/api/auth/login/', {
    data: { username: 'applicant1', password: 'Demo@1234' },
  });
  if (!res.ok()) throw new Error(`applicant1 login failed: ${res.status()}`);
  const { access } = await res.json();
  return access;
}
