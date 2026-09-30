import { expect, test } from '@playwright/test';

test('REQ-3-1-2: paste a rectangular table and persist all cells', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await page.evaluate(() => navigator.clipboard.writeText('North\t12\nSouth\t18'));
  await page.getByRole('gridcell', { name: 'A1' }).click();
  await page.keyboard.press('Control+V');
  await expect(page.getByRole('gridcell', { name: 'A1' })).toHaveText('North');
  await expect(page.getByRole('gridcell', { name: 'B1' })).toHaveText('12');
  await expect(page.getByRole('gridcell', { name: 'A2' })).toHaveText('South');
  await expect(page.getByRole('gridcell', { name: 'B2' })).toHaveText('18');
  await page.reload();
  await expect(page.getByRole('gridcell', { name: 'B2' })).toHaveText('18');
});
