import { expect, test } from '@playwright/test';

test('REQ-3-2-2: undo and redo a cell edit through the toolbar', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  const cell = page.getByRole('gridcell', { name: 'A1' });
  await cell.click(); const bar = page.getByRole('textbox', { name: 'Formula bar' });
  await bar.fill('before'); await bar.press('Enter');
  await cell.click(); await bar.fill('after'); await bar.press('Enter');
  await page.getByRole('button', { name: 'Undo' }).click(); await expect(cell).toHaveText('before');
  await page.getByRole('button', { name: 'Redo' }).click(); await expect(cell).toHaveText('after');
  await page.reload(); await expect(page.getByRole('gridcell', { name: 'A1' })).toHaveText('after');
});
