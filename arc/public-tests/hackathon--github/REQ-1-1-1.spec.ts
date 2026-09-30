import { expect, test } from '@playwright/test';

test('REQ-1-1-1: register a unique account and sign in with its verified email', async ({ page }) => {
  const suffix = `${Date.now()}`;
  const username = `pw-user-${suffix}`;
  const email = `${username}@example.test`;
  const password = 'Valid-password-123!';

  await page.goto('/');
  await page.getByRole('main').getByRole('link', { name: 'Sign in', exact: true }).click();
  await page.getByRole('link', { name: 'Create an account' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill(username);
  await page.getByRole('textbox', { name: 'Email' }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByLabel('Confirm password').fill(password);
  await page.getByRole('checkbox', { name: 'Agree to the terms' }).check();
  await page.getByRole('button', { name: 'Create account' }).click();

  await page.getByRole('textbox', { name: 'Username or email' }).fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByText(username).first()).toBeVisible();
  await page.reload();
  await expect(page.getByText(username).first()).toBeVisible();
});
