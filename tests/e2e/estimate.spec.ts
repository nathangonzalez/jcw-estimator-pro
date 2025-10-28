/**
 * JCW Estimator Pro – Playwright E2E (NO-RUN SCAFFOLD)
 * DO NOT RUN in this phase. This is a synced artifact for later CI.
 * Rationale: UI has "AI Blueprint Analysis" + "Manual Entry" with IDs present in index.html.
 * Source: web/frontend/index.html. 
 * Cloud endpoints intentionally ignored in this stage.
 */

// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { test, expect } from '@playwright/test';

// Use skip to ensure no accidental execution.
test.describe.skip('Manual estimate smoke (scaffold only)', () => {
  const UI_BASE_URL = process.env.UI_BASE_URL || 'http://localhost:8000';
  const FRONTEND_ENTRY = process.env.FRONTEND_ENTRY || 'web/frontend/index.html';

  test('fills manual form and sees a non-zero total', async ({ page }) => {
    // Prefer http URL if served locally, otherwise open static file
    const target = process.env.USE_FILE === '1'
      ? `file://${process.cwd()}/${FRONTEND_ENTRY.replace(/\\/g, '/')}`
      : UI_BASE_URL;

    await page.goto(target);
    await page.getByRole('tab', { name: /Manual Entry/i }).click();

    await page.locator('#area').fill('5000');
    await page.locator('#projectType').selectOption('residential');
    await page.locator('#quality').selectOption('standard');
    await page.locator('#complexity').selectOption('moderate');
    await page.locator('#bedrooms').fill('0');
    await page.locator('#bathrooms').fill('0');

    await page.getByRole('button', { name: /Calculate Estimate/i }).click();

    // Wait for results section to show and assert non-zero totals
    const totalCost = page.locator('#totalCost');
    await expect(totalCost).toBeVisible();
    const text = await totalCost.innerText();
    expect(text).not.toMatch(/^\$?0(\.0+)?$/);
  });
});
