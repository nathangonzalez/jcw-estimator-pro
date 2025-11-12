import { test, expect } from '@playwright/test';
import * as fs from 'fs';

test('UAT Interactive - Health check', async ({ request }) => {
  const response = await request.get('/health');
  expect(response.status()).toBe(200);
});

test('UAT Interactive - Assess endpoint with PDF', async ({ request }) => {
  // Create a minimal test PDF (base64 encoded)
  const testPdfB64 = Buffer.from('%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(roof shingle window vinyl) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF').toString('base64');

  const response = await request.post('/v1/interactive/assess', {
    data: {
      project_id: 'uat-interactive-test-001',
      pdf_base64: testPdfB64
    }
  });

  expect(response.status()).toBe(200);
  const body = await response.json();

  // Validate response structure
  expect(body).toHaveProperty('project_id', 'uat-interactive-test-001');
  expect(body).toHaveProperty('coverage_score');
  expect(body.coverage_score).toBeGreaterThanOrEqual(0);
  expect(body.coverage_score).toBeLessThanOrEqual(1);
  expect(body).toHaveProperty('trades_inferred');
  expect(Array.isArray(body.trades_inferred)).toBe(true);
  expect(body).toHaveProperty('questions_ref');
  expect(body.questions_ref).toContain('output/uat-interactive-test-001/QUESTIONS.json');

  // Check that output files were created
  expect(fs.existsSync('output/uat-interactive-test-001/QUESTIONS.json')).toBe(true);
  expect(fs.existsSync('output/uat-interactive-test-001/ASSESS_RESPONSE.json')).toBe(true);
});

test('UAT Interactive - QnA endpoint processes answers', async ({ request }) => {
  // First create questions via assess
  const testPdfB64 = Buffer.from('%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(foundation slab window aluminum) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF').toString('base64');

  await request.post('/v1/interactive/assess', {
    data: {
      project_id: 'uat-qna-test-001',
      pdf_base64: testPdfB64
    }
  });

  // Now test QnA with answers
  const qnaResponse = await request.post('/v1/interactive/qna', {
    data: {
      project_id: 'uat-qna-test-001',
      answers: [
        { id: 'uat-qna-test-001_roofing_material_0', key: 'shingle' },
        { id: 'uat-qna-test-001_foundation_type_1', key: 'slab' }
      ]
    }
  });

  expect(qnaResponse.status()).toBe(200);
  const qnaBody = await qnaResponse.json();

  expect(qnaBody).toHaveProperty('project_id', 'uat-qna-test-001');
  expect(qnaBody).toHaveProperty('answered');
  expect(qnaBody).toHaveProperty('next_questions');
  expect(qnaBody).toHaveProperty('completion_status');
  expect(qnaBody).toHaveProperty('total_answered');
  expect(qnaBody).toHaveProperty('total_questions');

  // Should have processed the answers
  expect(qnaBody.answered).toHaveLength(2);
  expect(qnaBody.total_answered).toBe(2);

  // Check answer structure
  for (const answer of qnaBody.answered) {
    expect(answer).toHaveProperty('id');
    expect(answer).toHaveProperty('question');
    expect(answer).toHaveProperty('answer');
    expect(answer).toHaveProperty('severity');
  }

  // Check that QNA response was saved
  expect(fs.existsSync('output/uat-qna-test-001/QNA_RESPONSE.json')).toBe(true);
});

test('UAT Interactive - Assess validation errors', async ({ request }) => {
  // Test missing project_id
  const response1 = await request.post('/v1/interactive/assess', {
    data: { pdf_base64: 'dummy' }
  });
  expect(response1.status()).toBe(422);

  // Test missing PDF
  const response2 = await request.post('/v1/interactive/assess', {
    data: { project_id: 'test' }
  });
  expect(response2.status()).toBe(422);
});

test('UAT Interactive - Assess endpoint happy-path with request_id', async ({ request }) => {
  const testPdfB64 = Buffer.from('%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(roof shingle window vinyl) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF').toString('base64');

  const response = await request.post('/v1/interactive/assess', {
    data: {
      project_id: 'uat-assess-request-id-test',
      pdf_base64: testPdfB64
    }
  });

  expect(response.status()).toBe(200);
  const body = await response.json();

  // Should include request_id in response
  expect(body).toHaveProperty('request_id');
  expect(typeof body.request_id).toBe('string');
  expect(body.request_id.length).toBeGreaterThan(0);
});

test('UAT Interactive - QnA endpoint with empty questions returns 422', async ({ request }) => {
  const response = await request.post('/v1/interactive/qna', {
    data: {
      project_id: 'uat-empty-answers-test',
      answers: []  // Empty array
    }
  });

  expect(response.status()).toBe(422);
  const body = await response.json();

  expect(body).toHaveProperty('error', 'VALIDATION');
  expect(body).toHaveProperty('detail', 'answers array cannot be empty');
  expect(body).toHaveProperty('request_id');
});

test('UAT Interactive - QnA endpoint with well-formed payload returns 200', async ({ request }) => {
  // First create questions via assess
  const testPdfB64 = Buffer.from('%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(foundation slab window aluminum) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF').toString('base64');

  await request.post('/v1/interactive/assess', {
    data: {
      project_id: 'uat-qna-well-formed-test',
      pdf_base64: testPdfB64
    }
  });

  // Now test QnA with well-formed answers
  const qnaResponse = await request.post('/v1/interactive/qna', {
    data: {
      project_id: 'uat-qna-well-formed-test',
      answers: [
        { id: 'uat-qna-well-formed-test_generic_quality_0', key: 'standard' }
      ]
    }
  });

  expect(qnaResponse.status()).toBe(200);
  const qnaBody = await qnaResponse.json();

  expect(qnaBody).toHaveProperty('request_id');
  expect(qnaBody).toHaveProperty('project_id', 'uat-qna-well-formed-test');
  expect(qnaBody).toHaveProperty('answered');
  expect(qnaBody).toHaveProperty('next_questions');
  expect(qnaBody).toHaveProperty('completion_status');
  expect(qnaBody).toHaveProperty('total_answered');
  expect(qnaBody).toHaveProperty('total_questions');

  // Should have applied_overlays or empty array
  expect(qnaBody).toHaveProperty('applied_overlays');
  expect(Array.isArray(qnaBody.applied_overlays)).toBe(true);
});

test('UAT Interactive - QnA validation errors', async ({ request }) => {
  // Test missing project_id
  const response1 = await request.post('/v1/interactive/qna', {
    data: { answers: [] }
  });
  expect(response1.status()).toBe(422);

  // Test missing QUESTIONS.json
  const response2 = await request.post('/v1/interactive/qna', {
    data: {
      project_id: 'nonexistent-project',
      answers: [{ id: 'test', key: 'value' }]
    }
  });
  expect(response2.status()).toBe(422);
});

test('UAT Interactive - Question generation determinism', async ({ request }) => {
  // Create same assess request twice
  const testPdfB64 = Buffer.from('%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(hvac electrical plumbing finishes) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF').toString('base64');

  const response1 = await request.post('/v1/interactive/assess', {
    data: {
      project_id: 'determinism-test',
      pdf_base64: testPdfB64
    }
  });

  const response2 = await request.post('/v1/interactive/assess', {
    data: {
      project_id: 'determinism-test',
      pdf_base64: testPdfB64
    }
  });

  expect(response1.status()).toBe(200);
  expect(response2.status()).toBe(200);

  const body1 = await response1.json();
  const body2 = await response2.json();

  // Should generate same results for same input
  expect(body1.questions_ref).toBe(body2.questions_ref);
  expect(body1.coverage_score).toBe(body2.coverage_score);
  expect(body1.trades_inferred.length).toBe(body2.trades_inferred.length);
});

test('UAT Interactive - Files cleanup', async () => {
  // Clean up test files
  const testDirs = [
    'output/uat-interactive-test-001',
    'output/uat-qna-test-001',
    'output/determinism-test'
  ];

  for (const dir of testDirs) {
    if (fs.existsSync(dir)) {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  }
});
