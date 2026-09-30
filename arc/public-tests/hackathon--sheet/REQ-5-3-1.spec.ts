import { expect, test } from '@playwright/test';

test('REQ-5-3-1: create a pivot summary and refresh it after source data changes', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  const rows = [['Region', 'Sales'], ['North', '10'], ['South', '20']];
  const bar = page.getByRole('textbox', { name: 'Formula bar' });
  for (let r = 0; r < rows.length; r++) for (let c = 0; c < rows[r].length; c++) {
    const cell = `${String.fromCharCode(65 + c)}${r + 1}`;
    await page.getByRole('gridcell', { name: cell }).click(); await bar.fill(rows[r][c]); await bar.press('Enter');
  }
  const first = await page.getByRole('gridcell', { name: 'A1' }).boundingBox();
  const last = await page.getByRole('gridcell', { name: 'B3' }).boundingBox();
  expect(first).not.toBeNull(); expect(last).not.toBeNull();
  await page.mouse.move(first!.x + 4, first!.y + 4); await page.mouse.down();
  await page.mouse.move(last!.x + 4, last!.y + 4, { steps: 8 }); await page.mouse.up();
  await page.getByRole('button', { name: 'Data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Create pivot table' }).click();
  await page.getByRole('dialog', { name: 'Create pivot table' }).getByRole('button', { name: 'Create' }).click();
  const editor = page.getByRole('region', { name: 'Pivot table editor' });
  await editor.getByRole('combobox', { name: 'Rows' }).selectOption({ label: 'Region' });
  await editor.getByRole('combobox', { name: 'Values' }).selectOption({ label: 'Sales' });
  await editor.getByRole('combobox', { name: 'Summarize by' }).selectOption({ label: 'SUM' });
  await editor.getByRole('button', { name: 'Apply' }).click();
  await expect(page.getByRole('tab', { name: 'Pivot1' })).toBeVisible();
  await expect(page.getByRole('gridcell', { name: 'B4' })).toHaveText('30');
  await page.getByRole('button', { name: 'Refresh pivot table' }).click();
  await expect(page.getByRole('gridcell', { name: 'B4' })).toHaveText('30');
});
