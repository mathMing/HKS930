import { expect, test, type Page } from '@playwright/test';

test('REQ-6-3-4: submit an approval review and retain the decision after reload', async ({ page }) => {
  await page.goto('/');
  // The requirement seeds bob-reviewer but does not specify that account's
  // password. This shared seeded password is provisional and needs confirmation.
  await page.getByRole('link', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('bob-reviewer');
  await page.getByLabel('Password').fill('Valid-password-123!');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'acme-docs' }).click();
  await page.getByRole('link', { name: 'Pull requests', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding' }).click();
  await page.getByRole('link', { name: 'Files changed' }).click();
  await page.getByRole('button', { name: 'Review changes' }).click();
  await page.getByRole('radio', { name: 'Approve' }).check();
  await page.getByRole('button', { name: 'Submit review' }).click();

  await expect(page.getByText('Approved', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText('Approved', { exact: true })).toBeVisible();
});
