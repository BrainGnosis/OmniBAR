import { expect, test } from '@playwright/test';

test.describe('OmniBrew:Prompt Review transparency surface', () => {
  const benchmarkPayload = [
    {
      id: 'bench-1',
      name: 'Reliability Snapshot',
      iterations: 5,
      successRate: 0.92,
      status: 'success',
      updatedAt: '2025-01-01T00:00:00.000Z',
      suite: 'demo-suite',
      latencySeconds: 1.23,
      tokensUsed: 456,
      costUsd: 0.0123,
      confidenceReported: 0.81,
      confidenceCalibrated: 0.86,
      history: [
        {
          timestamp: '2025-01-01T00:00:00.000Z',
          objective: 'exact_answer',
          result: true,
          expected: '42',
          actual: '42',
          latencySeconds: 1.18,
        },
      ],
    },
    {
      id: 'bench-2',
      name: 'Adversarial QA',
      iterations: 7,
      successRate: 0.58,
      status: 'failed',
      updatedAt: '2025-01-02T00:00:00.000Z',
      suite: 'stress-suite',
      latencySeconds: 3.45,
      tokensUsed: 789,
      costUsd: 0.0345,
      latestFailure: {
        objective: 'exact_answer',
        reason: 'Output drift',
        expected: 'true',
        actual: 'false',
      },
    },
  ];

  test('exposes latency, tokens, and JSON drill-downs', async ({ page }) => {
    await page.route('**/benchmarks', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(benchmarkPayload),
        });
        return;
      }
      await route.fallback();
    });

    await page.goto('/');
    await page.getByRole('button', { name: 'Benchmarks' }).click();

    await expect(page.getByText('Mock Mode')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Benchmark Library' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Latency (s)' })).toBeVisible();
    await expect(page.getByRole('cell', { name: '1.23' })).toBeVisible();
    await expect(page.getByRole('cell', { name: '0.0123' })).toBeVisible();

    const jsonInspector = page.getByRole('button', { name: 'Full benchmark snapshot (array)' });
    await expect(jsonInspector).toBeVisible();
    await expect(page.getByText('"tokensUsed": 456', { exact: false })).toBeVisible();

    const payloadSelector = page.getByLabel('JSON payload selector');
    await payloadSelector.selectOption('bench-2');
    await expect(page.getByRole('button', { name: 'Benchmark · Adversarial QA' })).toBeVisible();
    await expect(page.getByText('"tokensUsed": 789', { exact: false })).toBeVisible();
  });

  test('surfaces loading and error states when the snapshot fails', async ({ page }) => {
    await page.route('**/benchmarks', async (route) => {
      if (route.request().method() === 'GET') {
        await page.waitForTimeout(200);
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Snapshot unavailable' }),
        });
        return;
      }
      await route.fallback();
    });

    await page.goto('/');
    await page.getByRole('button', { name: 'Benchmarks' }).click();

    await expect(page.getByText('Loading benchmarks…')).toBeVisible();
    await expect(page.getByText('Snapshot unavailable')).toBeVisible();
  });
});
