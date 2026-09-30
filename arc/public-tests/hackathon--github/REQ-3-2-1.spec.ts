import { expect, test } from '@playwright/test';
import { signIn } from './support';

test('REQ-3-2-1: create an initialized private repository in the signed-in namespace', async ({ page }) => {
  const name = `pw-repo-${Date.now()}`;
  await signIn(page); await page.getByRole('link', { name: 'New repository' }).click();
  await page.getByLabel('Repository name').fill(name);
  await page.getByLabel('Description').fill('Repository created by Playwright');
  await page.getByRole('radio', { name: 'Private' }).check();
  await page.getByRole('checkbox', { name: 'Add a README file' }).check();
  await page.getByRole('button', { name: 'Create repository' }).click();
  await expect(page.getByRole('heading', { name: new RegExp(name) })).toBeVisible();
  await expect(page.getByText('Private', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'README.md' })).toBeVisible();
  await page.reload(); await expect(page.getByRole('heading', { name: new RegExp(name) })).toBeVisible();
});
