import { expect, test } from '@playwright/test';

test('REQ-5-2-1: apply a dropdown validation rule and reject an invalid value', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await page.getByRole('gridcell', { name: 'A1' }).click();
  await page.getByRole('button', { name: 'Data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Data validation' }).click();
  const dialog = page.getByRole('dialog', { name: 'Data validation' });
  await dialog.getByRole('combobox', { name: 'Rule type' }).selectOption({ label: 'Dropdown' });
  await dialog.getByRole('textbox', { name: 'Allowed values' }).fill(' Red, Blue ');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await page.getByRole('gridcell', { name: 'A1' }).click();
  await page.getByRole('textbox', { name: 'Formula bar' }).fill('Green');
  await page.getByRole('textbox', { name: 'Formula bar' }).press('Enter');
  await expect(page.getByText(/Please select one of the following values/)).toBeVisible();
  await expect(page.getByRole('gridcell', { name: 'A1' })).toBeEmpty();
});
