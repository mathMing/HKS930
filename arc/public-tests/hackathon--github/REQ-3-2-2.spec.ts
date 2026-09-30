import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-3-2-2: fork a public repository and retain its source relationship', async ({ page }) => {
  const name = `pw-fork-${Date.now()}`;
  await signIn(page); await openRepository(page);
  await page.getByRole('button', { name: 'Fork' }).click();
  await page.getByLabel('Repository name').fill(name);
  await page.getByRole('button', { name: 'Create fork' }).click();
  await expect(page.getByRole('heading', { name: new RegExp(name) })).toBeVisible();
  await expect(page.getByText(/Forked from.*acme-docs/i)).toBeVisible();
  await page.reload(); await expect(page.getByText(/Forked from.*acme-docs/i)).toBeVisible();
});
