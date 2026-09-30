import { expect, Page } from '@playwright/test';

export async function signIn(page: Page, username = 'alice-dev', password = 'Valid-password-123!') {
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill(username);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('button', { name: new RegExp(username, 'i') })).toBeVisible();
}

export async function openRepository(page: Page, name = 'acme-docs') {
  await page.goto('/');
  const link = page.getByRole('link', { name, exact: true });
  if (await link.count()) await link.click();
  else await page.goto(`/alice-dev/${name}`);
  await expect(page.getByRole('heading', { name: new RegExp(name, 'i') })).toBeVisible();
}
