import { expect, test } from '@playwright/test';

test('REQ-1-2-1: create a blank workbook and restore the active sheet', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();

  await expect(page.getByRole('tab', { name: 'Sheet1' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('gridcell', { name: 'A1' })).toHaveAttribute('aria-selected', 'true');
  await page.reload();
  await expect(page.getByRole('tab', { name: 'Sheet1' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('grid', { name: 'Worksheet grid' })).toBeVisible();
});
