import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-4-3-3: update the repository default branch using the confirmation flow', async ({ page }) => {
  await signIn(page); await openRepository(page);
  await page.getByRole('link', { name: 'Settings', exact: true }).click();
  await page.getByRole('link', { name: 'Branches', exact: true }).click();
  await page.getByRole('combobox', { name: 'Default branch' }).selectOption({ label: 'feature-search' });
  await page.getByRole('button', { name: 'Update' }).click();
  await page.getByRole('button', { name: 'Confirm' }).click();
  await page.goto('/alice-dev/acme-docs'); await page.getByRole('link', { name: 'Code', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Branch feature-search' })).toBeVisible();
});
