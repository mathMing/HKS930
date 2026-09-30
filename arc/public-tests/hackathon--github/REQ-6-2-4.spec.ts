import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-6-2-4: create a draft pull request from a branch comparison', async ({ page }) => {
  const title = `Playwright draft ${Date.now()}`;
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Pull requests', exact: true }).click();
  await page.getByRole('link', { name: /Compare/ }).click();
  await page.getByRole('combobox', { name: 'base' }).selectOption({ label: 'main' });
  await page.getByRole('combobox', { name: 'compare' }).selectOption({ label: 'feature-search' });
  await page.getByRole('button', { name: 'Create draft pull request' }).click();
  await page.getByLabel('Title').fill(title);
  await page.getByRole('button', { name: 'Create draft pull request', exact: true }).click();
  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
  await expect(page.getByText('Draft', { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByText('Draft', { exact: true })).toBeVisible();
});
