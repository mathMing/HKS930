import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-6-3-2: inspect a pull request changed-file diff and aggregate summary', async ({ page }) => {
  await openRepository(page); await page.getByRole('link', { name: 'Pull requests', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await page.getByRole('link', { name: 'Files changed', exact: true }).click();
  await expect(page.getByText('src/search.ts', { exact: true })).toBeVisible();
  await expect(page.getByText(/\+\d+.*-\d+/)).toBeVisible();
  await page.reload(); await expect(page.getByText('src/search.ts', { exact: true })).toBeVisible();
});
