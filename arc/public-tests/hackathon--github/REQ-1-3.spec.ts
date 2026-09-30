import { expect, test } from '@playwright/test';
import { signIn } from './support';

test('REQ-1-3: change the signed-in account password and verify the old credential stops working', async ({ page }) => {
  await signIn(page);
  await page.getByRole('button', { name: /alice-dev/i }).click();
  await page.getByRole('link', { name: 'Settings' }).click();
  await page.getByRole('link', { name: 'Password and authentication' }).click();
  await page.getByLabel('Current password').fill('Valid-password-123!');
  await page.getByLabel('New password').fill('New-password-456!');
  await page.getByLabel('Confirm password').fill('New-password-456!');
  await page.getByRole('button', { name: 'Update password' }).click();
  await expect(page.getByText('Password updated', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: /alice-dev/i }).click();
  await page.getByRole('menuitem', { name: 'Sign out' }).click();
  await signIn(page, 'alice-dev', 'New-password-456!');
  await page.getByRole('button', { name: /alice-dev/i }).click();
  await page.getByRole('menuitem', { name: 'Sign out' }).click();
  await page.goto('/'); await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('alice-dev');
  await page.getByLabel('Password').fill('Valid-password-123!');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('button', { name: /alice-dev/i })).toHaveCount(0);
});
