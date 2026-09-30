import { expect, test } from '@playwright/test';

test('REQ-4-2-1: recalculate a dependent formula after its source changes', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  const bar = page.getByRole('textbox', { name: 'Formula bar' });
  for (const [cell, value] of [['A1', '3'], ['B1', '=A1*4'], ['C1', '=B1+1']]) {
    await page.getByRole('gridcell', { name: cell }).click(); await bar.fill(value); await bar.press('Enter');
  }
  await expect(page.getByRole('gridcell', { name: 'C1' })).toHaveText('13');
  await page.getByRole('gridcell', { name: 'A1' }).click(); await bar.fill('8'); await bar.press('Enter');
  await expect(page.getByRole('gridcell', { name: 'B1' })).toHaveText('32');
  await expect(page.getByRole('gridcell', { name: 'C1' })).toHaveText('33');
  await page.reload(); await expect(page.getByRole('gridcell', { name: 'C1' })).toHaveText('33');
});
