import { test, expect } from '@playwright/test';
const API = process.env.API_URL || 'http://127.0.0.1:8001';
const UI  = process.env.UI_URL  || 'http://127.0.0.1:8001'; // fallback to API-served UI
const PLAN_PDF = process.env.PLAN_PDF || 'data/blueprints/LYNN-001.sample.pdf';

test.describe('R2.2.2 Story — UI flows on camera', () => {
  test('Upload → Takeoff → Estimate → Interactive (video)', async ({ page }) => {
    // Wait for page load
    await page.waitForLoadState('networkidle');

    // 1) Open UI with upload tab visible
    await page.goto(`${UI}/index_with_upload.html`, { waitUntil: 'load' });
    await expect(page.getByText(/Upload PDF Blueprint for AI Analysis/i)).toBeVisible();

    // More specific selectors
    await page.getByRole('button', { name: /^Select PDF$/i }).waitFor();
    await page.getByRole('button', { name: /^Select PDF$/i }).click();

    // Wait for file dialog
    const fileChooser = await page.waitForEvent('filechooser');
    await fileChooser.setFiles(PLAN_PDF);

    // Wait for upload feedback
    await page.waitForSelector('.file-info.show', { timeout: 10000 });

    // API calls with retry
    const takeoffResp = await page.request.post(`${API}/v1/takeoff`, {
      data: { project_id: 'LYNN-001', pdf_path: PLAN_PDF },
      timeout: 30000
    });
    expect(takeoffResp.ok()).toBeTruthy();
    const takeoff = await takeoffResp.json();
    expect(takeoff?.trades || takeoff?.quantities || takeoff?.items).toBeTruthy();

    // 4) Estimate with M01 body
    const estResp = await page.request.post(`${API}/v1/estimate`, {
      data: {
        project_id: 'LYNN-001',
        region: 'MA',
        quantities: takeoff,            // engine flattens/normalizes
        policy: 'schemas/pricing_policy.v0.yaml',
        unit_costs_csv: 'data/unit_costs.sample.csv',
        vendor_quotes_csv: ''
      },
      timeout: 30000
    });
    expect(estResp.ok()).toBeTruthy();
    const estimate = await estResp.json();
    expect(estimate?.totals || estimate?.grand_total || estimate?.trades).toBeTruthy();

    // 5) Interactive assess → qna (happy path)
    const assess = await page.request.post(`${API}/v1/interactive/assess`, {
      data: { project_id: 'LYNN-001', plan_features: {}, layout_meta: {} },
      timeout: 30000
    });
    expect(assess.ok()).toBeTruthy();
    const aBody = await assess.json();
    expect(aBody?.request_id).toBeTruthy();

    const qna = await page.request.post(`${API}/v1/interactive/qna`, {
      data: {
        project_id: 'LYNN-001',
        answers: [{ id: 'roofing.material', answer: 'Architectural shingles' }],
        plan_features: {}, layout_meta: {}
      },
      timeout: 30000
    });
    expect(qna.ok()).toBeTruthy();
    const qBody = await qna.json();
    expect(Array.isArray(qBody?.applied_overlays ?? [])).toBeTruthy();

    // 6) Pause briefly so the video isn't a still frame
    await page.waitForTimeout(1200);
  });
});
