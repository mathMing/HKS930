import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-6-2-2: compare source and base branches before creating a pull request', async ({ page }) => {
  await openRepository(page); await page.getByRole('link', { name: 'Pull requests', exact: true }).click();
  await page.getByRole('link', { name: /Compare/ }).click();
  await page.getByRole('combobox', { name: 'base' }).selectOption({ label: 'main' });
  await page.getByRole('combobox', { name: 'compare' }).selectOption({ label: 'feature-search' });
  await expect(page.getByText('src/search.ts', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Create pull request' })).toBeVisible();
});
