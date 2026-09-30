import { expect, test } from '@playwright/test';

test('REQ-5-2-1: create an issue and see it persisted in the repository', async ({ page }) => {
  const title = `Offline mirror issue ${Date.now()}`;
  const description = 'Created through the visible issue form for local mirror verification.';
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('alice-dev');
  await page.getByLabel('Password').fill('Valid-password-123!');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'acme-docs' }).click();
  await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await page.getByRole('link', { name: 'New issue' }).click();
  await page.getByLabel('Title').fill(title);
  await page.getByLabel('Description').fill(description);
  await page.getByRole('button', { name: 'Submit new issue' }).click();

  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
  await expect(page.getByText(description, { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await expect(page.getByRole('link', { name: title, exact: true })).toBeVisible();
  await page.getByRole('link', { name: title, exact: true }).click();
  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
});

test('REQ-5-2-1: reject a whitespace-only issue title without creating a record', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('alice-dev');
  await page.getByLabel('Password').fill('Valid-password-123!');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'acme-docs' }).click();
  await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await page.getByRole('link', { name: 'New issue' }).click();
  await page.getByLabel('Title').fill('   ');
  await page.getByRole('button', { name: 'Submit new issue' }).click();
  await expect(page.getByText('Title is required', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Submit new issue' })).toBeVisible();
});
