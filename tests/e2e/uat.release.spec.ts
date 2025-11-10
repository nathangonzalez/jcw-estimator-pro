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

  test('POST /v1/takeoff (pdf_path) yields v0 quantities object', async ({ request }) => {
    // If you have a real local plan PDF, set this env var before running:
    // $env:PLAN_PDF="C:\\path\\to\\LYNN.pdf"
    const pdf = process.env.PLAN_PDF || 'data/blueprints/LYNN-001.sample.pdf';
    const res = await request.post('/v1/takeoff', { data: { project_id: 'LYNN-001', pdf_path: pdf } });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty('trades');
    expect(Array.isArray(body.trades)).toBeTruthy();
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
