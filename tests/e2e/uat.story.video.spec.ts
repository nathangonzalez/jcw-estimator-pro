import { test, expect } from '@playwright/test';
const API = process.env.API_URL || 'http://127.0.0.1:8001';
const UI  = process.env.UI_URL  || 'http://127.0.0.1:8001'; // fallback to API-served UI
const PLAN_PDF = process.env.PLAN_PDF || 'data/blueprints/LYNN-001.sample.pdf';

test.describe('R2.2.2 Story — UI flows on camera', () => {
  test('Upload → Takeoff → Estimate → Interactive (video)', async ({ page }) => {
    // 1) Open UI with upload tab visible
    await page.goto(`${UI}/index_with_upload.html`, { waitUntil: 'load' });
    await expect(page.getByText(/Upload PDF Blueprint for AI Analysis/i)).toBeVisible();

    // 2) Upload sample plan (shows drag/drop and progress on video)
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByRole('button', { name: /Select PDF/i }).click();
    const chooser = await fileChooserPromise;
    await chooser.setFiles(PLAN_PDF);
    await page.waitForTimeout(750); // give UI time to render

    // 3) Trigger takeoff via API (visible status text on UI if wired; else we still get page footage)
    const takeoffResp = await page.request.post(`${API}/v1/takeoff`, {
      data: { project_id: 'LYNN-001', pdf_path: PLAN_PDF }
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
      }
    });
    expect(estResp.ok()).toBeTruthy();
    const estimate = await estResp.json();
    expect(estimate?.totals || estimate?.grand_total || estimate?.trades).toBeTruthy();

    // 5) Interactive assess → qna (happy path)
    const assess = await page.request.post(`${API}/v1/interactive/assess`, {
      data: { project_id: 'LYNN-001', plan_features: {}, layout_meta: {} }
    });
    expect(assess.ok()).toBeTruthy();
    const aBody = await assess.json();
    expect(aBody?.request_id).toBeTruthy();

    const qna = await page.request.post(`${API}/v1/interactive/qna`, {
      data: {
        project_id: 'LYNN-001',
        answers: [{ id: 'roofing.material', answer: 'Architectural shingles' }],
        plan_features: {}, layout_meta: {}
      }
    });
    expect(qna.ok()).toBeTruthy();
    const qBody = await qna.json();
    expect(Array.isArray(qBody?.applied_overlays ?? [])).toBeTruthy();

    // 6) Pause briefly so the video isn't a still frame
    await page.waitForTimeout(1200);
  });
});
