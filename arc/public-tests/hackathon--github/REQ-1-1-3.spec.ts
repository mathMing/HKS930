import { expect, test, type Page } from '@playwright/test';

async function createAccount(page: Page, username: string, email: string, password: string) {
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'Create an account' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill(username);
  await page.getByRole('textbox', { name: 'Email' }).fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByLabel('Confirm password').fill(password);
  await page.getByRole('checkbox', { name: 'Agree to the terms' }).check();
  await page.getByRole('button', { name: 'Create account' }).click();
}

test('REQ-1-1-3: recover a newly registered account and sign in only with the new password', async ({ page }) => {
  const suffix = `${Date.now()}`;
  const username = `pw-reset-${suffix}`;
  const email = `${username}@example.test`;
  const oldPassword = 'Valid-password-123!';
  const newPassword = 'Replacement-password-456!';

  await createAccount(page, username, email, oldPassword);
  await page.getByRole('link', { name: 'Forgot password' }).click();
  await page.getByRole('textbox', { name: 'Email' }).fill(email);
  await page.getByRole('button', { name: 'Send reset link' }).click();
  await expect(page.getByText('123456', { exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Verification code' }).fill('123456');
  await page.getByLabel('New password').fill(newPassword);
  await page.getByLabel('Confirm password').fill(newPassword);
  await page.getByRole('button', { name: 'Reset password' }).click();
  await expect(page.getByText('Password updated', { exact: true })).toBeVisible();

  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill(email);
  await page.getByLabel('Password').fill(oldPassword);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('button', { name: new RegExp(username, 'i') })).toHaveCount(0);
  await page.getByRole('textbox', { name: 'Username or email' }).fill(email);
  await page.getByLabel('Password').fill(newPassword);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('button', { name: new RegExp(username, 'i') })).toBeVisible();
});

test('REQ-1-1-3: reject a wrong code without changing the seeded account password', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'Forgot password' }).click();
  await page.getByRole('textbox', { name: 'Email' }).fill('alice.dev@example.test');
  await page.getByRole('button', { name: 'Send reset link' }).click();
  await expect(page.getByText('123456', { exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Verification code' }).fill('000000');
  await page.getByLabel('New password').fill('Replacement-password-456!');
  await page.getByLabel('Confirm password').fill('Replacement-password-456!');
  await page.getByRole('button', { name: 'Reset password' }).click();
  await expect(page.getByText('Verification code is invalid', { exact: true })).toBeVisible();

  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('alice-dev');
  await page.getByLabel('Password').fill('Valid-password-123!');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('button', { name: /alice-dev/i })).toBeVisible();
});
