import { expect, test } from '@playwright/test';

test('REQ-4-1-1: calculate a formula and preserve the expression after reload', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  const formula = '=SUM(A1:B1)+A1*2';
  await page.getByRole('gridcell', { name: 'A1' }).click();
  await page.getByRole('textbox', { name: 'Formula bar' }).fill('2');
  await page.getByRole('textbox', { name: 'Formula bar' }).press('Enter');
  await page.getByRole('gridcell', { name: 'B1' }).click();
  await page.getByRole('textbox', { name: 'Formula bar' }).fill('3');
  await page.getByRole('textbox', { name: 'Formula bar' }).press('Enter');
  await page.getByRole('gridcell', { name: 'C1' }).click();
  await page.getByRole('textbox', { name: 'Formula bar' }).fill(formula);
  await page.getByRole('textbox', { name: 'Formula bar' }).press('Enter');

  await expect(page.getByRole('gridcell', { name: 'C1' })).toHaveText('9');
  await page.getByRole('gridcell', { name: 'C1' }).click();
  await expect(page.getByRole('textbox', { name: 'Formula bar' })).toHaveValue(formula);
  await page.reload();
  await page.getByRole('gridcell', { name: 'C1' }).click();
  await expect(page.getByRole('gridcell', { name: 'C1' })).toHaveText('9');
  await expect(page.getByRole('textbox', { name: 'Formula bar' })).toHaveValue(formula);
});
