import { defineConfig, devices } from '@playwright/test';

/**
 * e-Leseni end-to-end tests (Playwright).
 *
 * Expects the dev stack to be reachable at baseURL (frontend :4200) with the
 * Django backend on :8000 and demo data seeded (seed_demo_data).
 * CI brings the stack up itself (see .github/workflows/ci.yml); locally
 * start it with npm start + the usual backend server before running.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // tests share seeded demo state (applicant1, USSD phone keys)
  workers: 1,
  timeout: 45_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['junit', { outputFile: 'test-results/junit.xml' }]] : 'list',
  use: {
    baseURL: 'http://localhost:4200',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
