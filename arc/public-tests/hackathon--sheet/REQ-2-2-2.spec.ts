import { expect, test } from '@playwright/test';

test('REQ-2-2-2: insert and delete a column while keeping neighboring values', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  for (const [cell, value] of [['A1', 'Name'], ['B1', 'Score'], ['A2', 'Mina'], ['B2', '42']]) {
    await page.getByRole('gridcell', { name: cell }).click();
    const bar = page.getByRole('textbox', { name: 'Formula bar' });
    await bar.fill(value); await bar.press('Enter');
  }
  await page.getByRole('columnheader', { name: 'B' }).click({ button: 'right' });
  await page.getByRole('menuitem', { name: 'Insert 1 column left' }).click();
  await expect(page.getByRole('gridcell', { name: 'C2' })).toHaveText('42');
  await page.getByRole('columnheader', { name: 'B' }).click({ button: 'right' });
  await page.getByRole('menuitem', { name: 'Delete column' }).click();
  await expect(page.getByRole('gridcell', { name: 'B2' })).toHaveText('42');
  await page.reload();
  await expect(page.getByRole('gridcell', { name: 'B2' })).toHaveText('42');
});
