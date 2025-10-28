import { test, expect } from '@playwright/test';

const APP_URL = process.env.APP_URL ?? 'http://localhost:8000';
const PDF_PATH = 'C:\\Users\\natha\\OneDrive\\Aquisition Lab\\Deals\\JC Welton\\Post Day 1 Ops\\Estimating\\Lynn\\251020_291 SOD - Building Permit Set.pdf';

test('Manual estimate flow renders a total', async ({ page }) => {
  await page.goto(APP_URL, { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Project Input')).toBeVisible();

  await page.fill('#area', '5000');
  await page.selectOption('#quality', 'standard');
  await page.selectOption('#complexity', 'moderate');

  await page.getByRole('button', { name: /Calculate Estimate/i }).click();
  await expect(page.getByText(/Total Project Cost/i)).toBeVisible();
});
