import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: 0,
  testDir: 'tests/e2e',
  outputDir: 'output/playwright-artifacts',
  reporter: [['html', { outputFolder: 'output/playwright-report', open: 'never' }], ['list']],
  use: {
    baseURL: 'http://127.0.0.1:8001',
    trace: 'on',
    video: 'on',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
