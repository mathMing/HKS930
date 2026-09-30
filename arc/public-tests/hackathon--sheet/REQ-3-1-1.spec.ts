import { expect, test } from '@playwright/test';

test('REQ-3-1-1: edit a cell through the visible editor and persist it', async ({ page }) => {
  const value = `offline-edit-${Date.now()}`;
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await page.getByRole('gridcell', { name: 'D1' }).dblclick();
  const editor = page.getByRole('textbox', { name: 'Edit D1' });
  await editor.fill(value);
  await editor.press('Enter');
  await expect(page.getByRole('gridcell', { name: 'D1' })).toHaveText(value);
  await expect(page.getByRole('textbox', { name: 'Formula bar' })).toHaveValue(value);

  await page.reload();
  await expect(page.getByRole('gridcell', { name: 'D1' })).toHaveText(value);
});
