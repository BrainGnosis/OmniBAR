import { test, expect } from '@playwright/test';

test.describe('Document Extraction dashboard', () => {
  test('switches to the Math Reasoning dataset', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: 'Doc Extraction' }).click();

    const datasetSelect = page.getByLabel('Evaluation config');
    await datasetSelect.selectOption('math_reasoning');

    await expect(page.getByRole('heading', { name: 'Document Extraction Benchmarks' })).toBeVisible();
    await expect(page.getByText('Quadratic Explainer')).toBeVisible();
  });
});
