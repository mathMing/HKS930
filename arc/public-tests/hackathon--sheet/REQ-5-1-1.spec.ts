import { expect, test } from '@playwright/test';

test('REQ-5-1-1: sort selected rows by Sales and keep complete records together', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  const rows = [
    ['Region', 'Sales', 'Status'],
    ['North', '800', 'Closed'],
    ['East', '1200', 'Open'],
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
  const first = await page.getByRole('gridcell', { name: 'A1' }).boundingBox();
  const last = await page.getByRole('gridcell', { name: 'C4' }).boundingBox();
  expect(first).not.toBeNull();
  expect(last).not.toBeNull();
  await page.mouse.move(first!.x + first!.width / 2, first!.y + first!.height / 2);
  await page.mouse.down();
  await page.mouse.move(last!.x + last!.width / 2, last!.y + last!.height / 2, { steps: 12 });
  await page.mouse.up();

  await page.getByRole('button', { name: 'Data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Sort range' }).click();
  await expect(page.getByRole('dialog', { name: 'Sort range' })).toBeVisible();
  await page.getByRole('combobox', { name: 'Sort by' }).selectOption({ label: 'Sales' });
  await page.getByRole('combobox', { name: 'Order' }).selectOption({ label: 'Ascending' });
  await page.getByRole('checkbox', { name: 'Data has header row' }).check();
  await page.getByRole('button', { name: 'Sort', exact: true }).click();

  await expect(page.getByRole('gridcell', { name: 'A1' })).toHaveText('Region');
  await expect(page.getByRole('gridcell', { name: 'A2' })).toHaveText('South');
  await expect(page.getByRole('gridcell', { name: 'B2' })).toHaveText('700');
  await expect(page.getByRole('gridcell', { name: 'C2' })).toHaveText('Open');
  await page.reload();
  await expect(page.getByRole('gridcell', { name: 'A2' })).toHaveText('South');
});
