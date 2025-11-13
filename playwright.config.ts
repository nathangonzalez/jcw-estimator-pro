import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: 0,
  testDir: 'tests/e2e',
  outputDir: 'output/playwright-artifacts',
  reporter: [
    ['html', { outputFolder: 'output/playwright-report', open: 'never' }],
    ['json', { outputFile: 'output/uat-report.json' }],
    ['list']
  ],
  use: {
    baseURL: 'http://127.0.0.1:8001',
    trace: 'on-first-retry',
    video: 'on',
    screenshot: 'on',
    actionTimeout: 15000,
    navigationTimeout: 30000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
