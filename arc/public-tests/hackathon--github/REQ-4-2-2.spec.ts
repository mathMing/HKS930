import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-4-2-2: open a commit diff and inspect the changed path', async ({ page }) => {
  await openRepository(page); await page.getByRole('link', { name: 'Commits' }).click();
  await page.getByRole('link', { name: /Document search flow/ }).click();
  await expect(page.getByText('Changed files', { exact: true })).toBeVisible();
  await expect(page.getByText('src/search.ts', { exact: true })).toBeVisible();
  await expect(page.getByText(/\+\d+/)).toBeVisible();
  await page.reload(); await expect(page.getByText('src/search.ts', { exact: true })).toBeVisible();
});
