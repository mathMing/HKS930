import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-4-2-1: inspect the repository commit history and its author metadata', async ({ page }) => {
  await openRepository(page); await page.getByRole('link', { name: 'Commits' }).click();
  await expect(page.getByText('Document search flow', { exact: true })).toBeVisible();
  await expect(page.getByText('alice-dev', { exact: true })).toBeVisible();
  await expect(page.getByText(/ago/).first()).toBeVisible();
  await page.reload(); await expect(page.getByText('Document search flow', { exact: true })).toBeVisible();
});
