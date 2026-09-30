import { expect, test } from '@playwright/test';

test('REQ-1-2: cancel sign-out without ending the current session', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('alice-dev');
  await page.getByLabel('Password').fill('Valid-password-123!');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await page.getByRole('button', { name: 'Account menu' }).click();
  await page.getByRole('link', { name: 'Sign out' }).click();
  await expect(page.getByRole('dialog', { name: 'Sign out' })).toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByRole('button', { name: 'Account menu' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Sign in' })).toHaveCount(0);
});

test('REQ-1-2: confirm sign-out and require sign-in after refresh', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('alice-dev');
  await page.getByLabel('Password').fill('Valid-password-123!');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await page.getByRole('button', { name: 'Account menu' }).click();
  await page.getByRole('link', { name: 'Sign out' }).click();
  await page.getByRole('button', { name: 'Confirm sign out' }).click();
  await page.reload();
  await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible();
});
