import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-2-3: grant a team repository access and replace its role', async ({ page }) => {
  await signIn(page); await openRepository(page);
  await page.getByRole('link', { name: 'Settings', exact: true }).click();
  await page.getByRole('link', { name: 'Manage access' }).click();
  await page.getByRole('button', { name: 'Add people or teams' }).click();
  await page.getByRole('textbox', { name: 'Search' }).fill('engineering');
  await page.getByRole('option', { name: /engineering/i }).click();
  await page.getByRole('combobox', { name: 'Role' }).selectOption({ label: 'Write' });
  await page.getByRole('button', { name: 'Add', exact: true }).click();
  await expect(page.getByText('engineering', { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByText('engineering', { exact: true })).toBeVisible();
});
