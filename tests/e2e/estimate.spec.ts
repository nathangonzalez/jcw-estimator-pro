import { test, expect } from '@playwright/test';

test.describe('Estimator smoke (supervised scaffold)', () => {
  test('loads UI frame', async ({ page }) => {
    test.skip(true, 'Execution requires explicit approval.');
    await page.goto('http://localhost:3000/');
    await expect(page).toHaveTitle(/Estimator/i);
  });
});
