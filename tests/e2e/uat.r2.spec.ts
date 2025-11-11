import { test, expect } from '@playwright/test';
import * as fs from 'fs';

test('UAT R2 - Health check', async ({ request }) => {
  const response = await request.get('/health');
  expect(response.status()).toBe(200);
});

test('UAT R2 - Estimate API', async ({ request }) => {
  const response = await request.post('/v1/estimate', {
    data: require('../../../data/quantities.sample.json')
  });
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty('estimate');
});

test('UAT R2 - Files exist', async () => {
  expect(fs.existsSync('output/LYNN_BURN_CURVE.csv')).toBe(true);
  expect(fs.existsSync('output/FINANCE_13W_FORECAST.csv')).toBe(true);
  expect(fs.existsSync('output/FINANCE_RUNWAY.md')).toBe(true);
});

test('UAT R2 Interactive - Assess endpoint', async ({ request }) => {
  const response = await request.post('/v1/plan/assess', {
    data: { project_id: 'test123', pdf_path: 'dummy.pdf' }
  });
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty('trades_inferred');
  expect(body).toHaveProperty('questions_ref');
});

test('UAT R2 Interactive - Estimate interactive mode', async ({ request }) => {
  const response = await request.post('/v1/estimate', {
    data: { mode: 'interactive', project_id: 'test123', region: 'default', quality: 'standard', complexity: 'normal' }
  });
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty('version', 'v0');
  expect(body).toHaveProperty('total_cost');
  expect(body).toHaveProperty('metadata');
  expect(body.metadata).toHaveProperty('interactive');
});
