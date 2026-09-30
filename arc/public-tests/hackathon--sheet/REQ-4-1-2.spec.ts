import { expect, test } from '@playwright/test';

test('REQ-4-1-2: copy a formula and adjust relative references at the destination', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  for (const [cell, value] of [['A1', '2'], ['A2', '5'], ['B1', '=A1*2']]) {
    await page.getByRole('gridcell', { name: cell }).click();
    const bar = page.getByRole('textbox', { name: 'Formula bar' }); await bar.fill(value); await bar.press('Enter');
  }
  await page.getByRole('gridcell', { name: 'B1' }).click(); await page.keyboard.press('Control+C');
  await page.getByRole('gridcell', { name: 'B2' }).click(); await page.keyboard.press('Control+V');
  await expect(page.getByRole('gridcell', { name: 'B2' })).toHaveText('10');
  await expect(page.getByRole('textbox', { name: 'Formula bar' })).toHaveValue('=A2*2');
  await page.reload(); await page.getByRole('gridcell', { name: 'B2' }).click();
  await expect(page.getByRole('textbox', { name: 'Formula bar' })).toHaveValue('=A2*2');
});
