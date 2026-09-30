import { expect, test } from '@playwright/test';

test('REQ-5-1-2: filter rows by a seeded value without deleting them', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  const rows = [
    ['Region', 'Sales', 'Status'],
    ['East', '1200', 'Open'],
    ['North', '800', 'Closed'],
    ['South', '700', 'Open'],
  ];
  for (let row = 0; row < rows.length; row++) {
    for (let col = 0; col < rows[row].length; col++) {
      const coordinate = `${String.fromCharCode(65 + col)}${row + 1}`;
      await page.getByRole('gridcell', { name: coordinate }).click();
      const formulaBar = page.getByRole('textbox', { name: 'Formula bar' });
      await formulaBar.fill(rows[row][col]);
      await formulaBar.press('Enter');
    }
  }
  await page.getByRole('button', { name: 'Data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Create filter' }).click();
  await page.getByRole('button', { name: 'Filter Region' }).click();
  await page.getByRole('button', { name: 'Clear selection' }).click();
  await page.getByRole('checkbox', { name: 'East', exact: true }).check();
  await page.getByRole('button', { name: 'Apply', exact: true }).click();

  await expect(page.getByRole('gridcell', { name: 'A2' })).toHaveText('East');
  await expect(page.getByText('North', { exact: true })).toBeHidden();
  await page.reload();
  await expect(page.getByText('North', { exact: true })).toBeHidden();
  await page.getByRole('button', { name: 'Filter Region' }).click();
  await page.getByRole('button', { name: 'Clear filter' }).click();
  await expect(page.getByText('North', { exact: true })).toBeVisible();
});
