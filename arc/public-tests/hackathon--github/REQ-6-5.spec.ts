import { expect, test } from '@playwright/test';

test('REQ-6-5: merge an eligible pull request and persist its merged state', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('alice-dev');
  await page.getByLabel('Password').fill('Valid-password-123!');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'acme-docs' }).click();
  await page.getByRole('link', { name: 'Pull requests', exact: true }).click();
  await page.getByRole('link', { name: 'Fix search' }).click();
  await page.getByRole('button', { name: 'Merge pull request' }).click();
  await page.getByRole('button', { name: 'Confirm merge' }).click();

  await expect(page.getByText('Merged', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText('Merged', { exact: true })).toBeVisible();
});
