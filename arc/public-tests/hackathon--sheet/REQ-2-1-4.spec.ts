import { expect, test } from '@playwright/test';

test('REQ-2-1-4: prevent deleting the only worksheet in a workbook', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await page.getByRole('button', { name: 'Worksheet options for Sheet1' }).click();
  await page.getByRole('menuitem', { name: 'Delete' }).click();

  await expect(page.getByText('A workbook must contain at least one worksheet', { exact: true })).toBeVisible();
  await expect(page.getByRole('dialog', { name: 'Delete worksheet' })).toHaveCount(0);
  await expect(page.getByRole('tab', { name: 'Sheet1' })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('tab', { name: 'Sheet1' })).toBeVisible();
});
