import { expect, test } from '@playwright/test';

test('REQ-1-1-1: open the seeded workbook and restore it after refresh', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Q3 Sales' }).click();
  await expect(page.getByRole('tab', { name: 'Sheet1' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('grid', { name: 'Worksheet grid' })).toHaveAttribute('aria-multiselectable', 'true');
  await expect(page.getByRole('gridcell', { name: 'A1' })).toHaveText('Region');
  const workbookUrl = page.url();

  await page.reload();
  await expect(page.getByRole('heading', { name: 'Q3 Sales' })).toBeVisible();
  await expect(page.getByRole('gridcell', { name: 'A1' })).toHaveText('Region');
  expect(page.url()).toBe(workbookUrl);
});
