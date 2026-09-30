import { expect, test } from '@playwright/test';

test('REQ-2-2-1: insert a row above a record and persist the shifted data', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  for (const [cell, value] of [['A1', 'Name'], ['A2', 'Mina'], ['B2', '42']]) {
    await page.getByRole('gridcell', { name: cell }).click();
    const formulaBar = page.getByRole('textbox', { name: 'Formula bar' });
    await formulaBar.fill(value);
    await formulaBar.press('Enter');
  }

  await page.getByRole('rowheader', { name: '2' }).click({ button: 'right' });
  await page.getByRole('menuitem', { name: 'Insert 1 row above' }).click();
  await expect(page.getByRole('gridcell', { name: 'A3' })).toHaveText('Mina');
  await expect(page.getByRole('gridcell', { name: 'B3' })).toHaveText('42');
  await page.reload();
  await expect(page.getByRole('gridcell', { name: 'A3' })).toHaveText('Mina');
});

test('REQ-2-2-1: delete a row and shift the next record up without losing its values', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  for (const [cell, value] of [['A1', 'Name'], ['A2', 'Temporary'], ['A3', 'Mina'], ['B3', '42']]) {
    await page.getByRole('gridcell', { name: cell }).click();
    const formulaBar = page.getByRole('textbox', { name: 'Formula bar' });
    await formulaBar.fill(value);
    await formulaBar.press('Enter');
  }

  await page.getByRole('rowheader', { name: '2' }).click({ button: 'right' });
  await page.getByRole('menuitem', { name: 'Delete row' }).click();
  await expect(page.getByRole('gridcell', { name: 'A2' })).toHaveText('Mina');
  await expect(page.getByRole('gridcell', { name: 'B2' })).toHaveText('42');
  await page.reload();
  await expect(page.getByRole('gridcell', { name: 'A2' })).toHaveText('Mina');
});
