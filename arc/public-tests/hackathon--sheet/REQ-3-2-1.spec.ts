import { expect, test } from '@playwright/test';

test('REQ-3-2-1: copy a selected cell range to another location', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  for (const [cell, value] of [['A1', 'alpha'], ['A2', 'beta']]) {
    await page.getByRole('gridcell', { name: cell }).click();
    const bar = page.getByRole('textbox', { name: 'Formula bar' }); await bar.fill(value); await bar.press('Enter');
  }
  const a1 = await page.getByRole('gridcell', { name: 'A1' }).boundingBox();
  const a2 = await page.getByRole('gridcell', { name: 'A2' }).boundingBox();
  expect(a1).not.toBeNull(); expect(a2).not.toBeNull();
  await page.mouse.move(a1!.x + 4, a1!.y + 4); await page.mouse.down();
  await page.mouse.move(a2!.x + 4, a2!.y + 4, { steps: 8 }); await page.mouse.up();
  await page.keyboard.press('Control+C');
  await page.getByRole('gridcell', { name: 'C1' }).click(); await page.keyboard.press('Control+V');
  await expect(page.getByRole('gridcell', { name: 'A1' })).toHaveText('alpha');
  await expect(page.getByRole('gridcell', { name: 'C1' })).toHaveText('alpha');
  await expect(page.getByRole('gridcell', { name: 'C2' })).toHaveText('beta');
  await page.reload(); await expect(page.getByRole('gridcell', { name: 'C2' })).toHaveText('beta');
});
