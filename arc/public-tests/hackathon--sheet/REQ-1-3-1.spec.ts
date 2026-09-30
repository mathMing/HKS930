import { expect, test } from '@playwright/test';

test('REQ-1-3-1: import CSV in row order and retain the resulting workbook', async ({ page }) => {
  const filename = `Offline Import ${Date.now()}.csv`;
  await page.goto('/');
  await page.getByRole('button', { name: 'Import CSV' }).click();
  await page.getByLabel('CSV file').setInputFiles({
    name: filename,
    mimeType: 'text/csv',
    buffer: Buffer.from('Region,Sales\r\nEast,1200\r\nNorth,800\r\n', 'utf-8'),
  });
  await page.getByRole('button', { name: 'Confirm import' }).click();

  const workbookName = filename.replace(/\.csv$/i, '');
  await expect(page.getByRole('tab', { name: 'Sheet1' })).toBeVisible();
  await expect(page.getByRole('gridcell', { name: 'A1' })).toHaveText('Region');
  await expect(page.getByRole('gridcell', { name: 'B1' })).toHaveText('Sales');
  await expect(page.getByRole('gridcell', { name: 'A2' })).toHaveText('East');
  await page.reload();
  await expect(page.getByRole('heading', { name: workbookName, exact: true })).toBeVisible();
  await expect(page.getByRole('gridcell', { name: 'B3' })).toHaveText('800');
});

test('REQ-1-3-1: reject malformed CSV without creating a partial workbook', async ({ page }) => {
  const filename = `Malformed ${Date.now()}.csv`;
  await page.goto('/');
  await page.getByRole('button', { name: 'Import CSV' }).click();
  await page.getByLabel('CSV file').setInputFiles({
    name: filename,
    mimeType: 'text/csv',
    buffer: Buffer.from('Name,Note\r\nalice,"unclosed field\r\n', 'utf-8'),
  });
  await page.getByRole('button', { name: 'Confirm import' }).click();

  await expect(page.getByText('Invalid CSV file format. Import failed.', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: filename.replace(/\.csv$/i, ''), exact: true })).toHaveCount(0);
});
