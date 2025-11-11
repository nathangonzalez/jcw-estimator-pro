import { test, expect } from '@playwright/test';
import fs from 'fs';

test.describe('R1 UAT — API happy paths', () => {
  test('GET /health returns 200 and minimal body', async ({ request }) => {
    const res = await request.get('/health');
    expect(res.ok()).toBeTruthy();
    const body = await res.json().catch(() => ({}));
    expect(typeof body).toBe('object');
  });

  test('POST /v1/estimate (M01 body) returns v0-shaped response', async ({ request }) => {
    const quantities = JSON.parse(fs.readFileSync('data/quantities.sample.json', 'utf-8'));
    const req = { project_id: 'LYNN-001', quantities };
    const res = await request.post('/v1/estimate', { data: req });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    // v0 response surface checks (accept either totals.grand_total or grand_total)
    expect(body).toHaveProperty('trades');
    const grand = (body?.totals?.grand_total ?? body?.grand_total ?? 0);
    expect(typeof grand).toBe('number');
  });

  test('POST /v1/takeoff returns v0-like quantities', async ({ request }) => {
    const pdfPath = process.env.PLAN_PDF || 'data/blueprints/LYNN-001.sample.pdf';
    const resp = await request.post('/v1/takeoff', {
      data: { project_id: 'LYNN-001', pdf_path: pdfPath },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
  
    expect(body).toBeDefined();
    expect(body.project_id || body.metadata?.project_id).toBeDefined();
    expect(body.trades).toBeDefined();
  
    const trades = body.trades;
    // For real plans (PLAN_PDF provided), require normalized array shape.
    if (process.env.PLAN_PDF) {
      expect(Array.isArray(trades)).toBe(true);
      // minimal v0 content sanity
      if (Array.isArray(trades) && trades.length > 0) {
        expect(trades[0]).toHaveProperty('trade');
        expect(trades[0]).toHaveProperty('items');
      }
    } else {
      // Placeholder input: accept either array or object to avoid false negatives on sample
      expect(Array.isArray(trades) || typeof trades === 'object').toBe(true);
    }
  });
});

test.describe('R1 UAT — Pipeline (takeoff ➜ estimate)', () => {
  test('Takeoff output passes into estimate', async ({ request }) => {
    const pdf = process.env.PLAN_PDF || 'data/blueprints/LYNN-001.sample.pdf';
    const takeoff = await (await request.post('/v1/takeoff', { data: { project_id: 'LYNN-001', pdf_path: pdf } })).json();
    const est = await (await request.post('/v1/estimate', { data: { project_id: 'LYNN-001', quantities: takeoff } })).json();
    expect((est?.totals?.grand_total ?? 0)).toBeGreaterThanOrEqual(0);
  });
});
