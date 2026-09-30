import { expect, test } from '@playwright/test';

test('REQ-1-2-2: rename a workbook and preserve the new name after reload', async ({ page }) => {
  const name = `Quarterly Plan ${Date.now()}`;
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await page.getByRole('button', { name: 'Rename workbook' }).click();
  await page.getByRole('textbox', { name: 'Workbook name' }).fill(name);
  await page.getByRole('button', { name: 'Save', exact: true }).click();

  await expect(page.getByText(name, { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText(name, { exact: true })).toBeVisible();
});

test('REQ-1-2-2: reject an empty workbook name and retain the current name', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await page.getByRole('button', { name: 'Rename workbook' }).click();
  await page.getByRole('textbox', { name: 'Workbook name' }).fill('   ');
  await page.getByRole('button', { name: 'Save', exact: true }).click();

  await expect(page.getByText('Workbook name cannot be empty', { exact: true })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Sheet1' })).toBeVisible();
});
