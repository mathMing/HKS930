import { expect, test } from '@playwright/test';
import { signIn } from './support';

test('REQ-2-2-3: add an existing account directly as an organization member', async ({ page }) => {
  await signIn(page);
  await page.getByRole('button', { name: /alice-dev/i }).click();
  await page.getByRole('link', { name: 'Your organizations' }).click();
  await page.getByRole('link', { name: 'Acme Demo' }).click();
  await page.getByRole('link', { name: 'People', exact: true }).click();
  await page.getByRole('button', { name: 'Add member' }).click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill('bob-reviewer');
  await page.getByRole('combobox', { name: 'Role' }).selectOption({ label: 'Member' });
  await page.getByRole('button', { name: 'Add member' }).last().click();
  await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible();
  await expect(page.getByText('Member', { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible();
});
