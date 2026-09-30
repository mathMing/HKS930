import { expect, test } from '@playwright/test';
import { signIn } from './support';

test('REQ-2-2-2: add and remove a direct team member with persisted membership', async ({ page }) => {
  await signIn(page);
  await page.getByRole('button', { name: /alice-dev/i }).click();
  await page.getByRole('link', { name: 'Your organizations' }).click();
  await page.getByRole('link', { name: 'Acme Demo' }).click();
  await page.getByRole('link', { name: 'Teams', exact: true }).click();
  await page.getByRole('link').filter({ hasText: 'engineering' }).first().click();
  await page.getByRole('link', { name: 'Members', exact: true }).click();
  await page.getByRole('button', { name: 'Add member' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('bob-reviewer');
  await page.getByRole('button', { name: 'Add member' }).last().click();
  await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Remove bob-reviewer' }).click();
  await expect(page.getByText('bob-reviewer', { exact: true })).toHaveCount(0);
  await page.reload(); await expect(page.getByText('bob-reviewer', { exact: true })).toHaveCount(0);
});
