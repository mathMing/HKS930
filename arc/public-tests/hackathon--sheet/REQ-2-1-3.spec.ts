import { expect, test } from '@playwright/test';

test('REQ-2-1-3: rename a worksheet and preserve its name after reload', async ({ page }) => {
  const name = `Research ${Date.now()}`;
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await page.getByRole('button', { name: 'Worksheet options for Sheet1' }).click();
  await page.getByRole('menuitem', { name: 'Rename' }).click();
  await expect(page.getByRole('dialog', { name: 'Rename worksheet' })).toBeVisible();
  await page.getByRole('textbox', { name: 'Worksheet name' }).fill(name);
  await page.getByRole('button', { name: 'Save', exact: true }).click();

  await expect(page.getByRole('tab', { name })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('tab', { name })).toBeVisible();
});

test('REQ-2-1-3: reject an empty worksheet name and keep the original tab', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await page.getByRole('button', { name: 'Worksheet options for Sheet1' }).click();
  await page.getByRole('menuitem', { name: 'Rename' }).click();
  await page.getByRole('textbox', { name: 'Worksheet name' }).fill('   ');
  await page.getByRole('button', { name: 'Save', exact: true }).click();

  await expect(page.getByText('Worksheet name cannot be empty', { exact: true })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Sheet1' })).toBeVisible();
});

test('REQ-2-1-3: reject a worksheet name already used in the same workbook', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await page.getByRole('button', { name: 'Add worksheet' }).click();
  await page.getByRole('tab', { name: 'Sheet1' }).click();
  await page.getByRole('button', { name: 'Worksheet options for Sheet1' }).click();
  await page.getByRole('menuitem', { name: 'Rename' }).click();
  await page.getByRole('textbox', { name: 'Worksheet name' }).fill('Sheet2');
  await page.getByRole('button', { name: 'Save', exact: true }).click();

  await expect(page.getByText('Worksheet name already exists', { exact: true })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Sheet1' })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Sheet2' })).toBeVisible();
});
