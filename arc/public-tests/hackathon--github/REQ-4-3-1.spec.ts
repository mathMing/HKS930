import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-4-3-1: switch to a branch and see its branch-specific file', async ({ page }) => {
  await openRepository(page); await page.getByRole('link', { name: 'Code', exact: true }).click();
  await page.getByRole('button', { name: 'Branch main' }).click();
  const find = page.getByRole('textbox', { name: 'Find branch' }); await find.fill('feature-search');
  await page.getByRole('option', { name: 'feature-search', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Branch feature-search' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'main-only.md', exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByRole('button', { name: 'Branch feature-search' })).toBeVisible();
});
