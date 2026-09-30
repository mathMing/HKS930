import { expect, test } from '@playwright/test';

test('REQ-1-1-2: sign in, retain the browser session after refresh', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('alice-dev');
  await page.getByLabel('Password').fill('Valid-password-123!');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByRole('button', { name: /alice-dev/i })).toBeVisible();
  const workspaceUrl = page.url();
  await page.reload();
  await expect(page.getByRole('button', { name: /alice-dev/i })).toBeVisible();
  expect(page.url()).toBe(workspaceUrl);
});

test('REQ-1-1-2: reject an incorrect password without authenticating', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('alice-dev');
  await page.getByLabel('Password').fill('incorrect-password');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByRole('button', { name: /alice-dev/i })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible();
});
