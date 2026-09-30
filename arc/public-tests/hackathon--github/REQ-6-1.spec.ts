import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-6-1: configure a branch protection rule through repository settings', async ({ page }) => {
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Settings', exact: true }).click();
  await page.getByRole('link', { name: 'Branches', exact: true }).click();
  await page.getByRole('button', { name: /Add branch protection rule|Add rule/ }).click();
  await page.getByRole('textbox', { name: /Branch name pattern/ }).fill('feature-search');
  await page.getByRole('checkbox', { name: /Require a pull request before merging/ }).check();
  await page.getByRole('button', { name: /Save protection rule/ }).click();
  await expect(page.getByText('feature-search', { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByText('feature-search', { exact: true })).toBeVisible();
});
