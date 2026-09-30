import { expect, test } from '@playwright/test';

test('REQ-3-1-3: select exactly a rectangular range with accessible selection state', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  const grid = page.getByRole('grid', { name: 'Worksheet grid' });
  await expect(grid).toHaveAttribute('aria-multiselectable', 'true');
  const first = await page.getByRole('gridcell', { name: 'A1' }).boundingBox();
  const last = await page.getByRole('gridcell', { name: 'B2' }).boundingBox();
  expect(first).not.toBeNull(); expect(last).not.toBeNull();
  await page.mouse.move(first!.x + 5, first!.y + 5); await page.mouse.down();
  await page.mouse.move(last!.x + last!.width / 2, last!.y + last!.height / 2, { steps: 8 });
  await page.mouse.up();
  for (const cell of ['A1', 'B1', 'A2', 'B2'])
    await expect(page.getByRole('gridcell', { name: cell })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('gridcell', { name: 'C3' })).toHaveAttribute('aria-selected', 'false');
  await page.reload();
  for (const cell of ['A1', 'B1', 'A2', 'B2'])
    await expect(page.getByRole('gridcell', { name: cell })).toHaveAttribute('aria-selected', 'true');
});
