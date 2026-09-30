import { expect, test } from '@playwright/test';

test('REQ-4-2-2: show a stable formula error and recover after correction', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  const cell = page.getByRole('gridcell', { name: 'A1' }); const bar = page.getByRole('textbox', { name: 'Formula bar' });
  await cell.click(); await bar.fill('=1/0'); await bar.press('Enter');
  await expect(cell).toHaveText('#DIV/0!'); await cell.click(); await expect(bar).toHaveValue('=1/0');
  await page.reload(); await expect(page.getByRole('gridcell', { name: 'A1' })).toHaveText('#DIV/0!');
  await page.getByRole('gridcell', { name: 'A1' }).click(); await bar.fill('=6/2'); await bar.press('Enter');
  await expect(page.getByRole('gridcell', { name: 'A1' })).toHaveText('3');
});
