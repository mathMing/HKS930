import { expect, test, type Page } from '@playwright/test';
import { readFile } from 'node:fs/promises';

async function createBlankWorkbook(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'New blank workbook' }).click();
  await page.getByRole('button', { name: 'Create', exact: true }).click();
}

test('REQ-1-3-2: export the active worksheet as CSV without changing its visible values', async ({ page }) => {
  await createBlankWorkbook(page);
  const values = [
    ['Name', 'Note', 'Amount'],
    ['Alice', 'design, review', '12'],
    ['Bob', 'line one\nline two', '8'],
  ];
  for (let row = 0; row < values.length; row++) {
    for (let col = 0; col < values[row].length; col++) {
      const cell = `${String.fromCharCode(65 + col)}${row + 1}`;
      await page.getByRole('gridcell', { name: cell }).click();
      const formulaBar = page.getByRole('textbox', { name: 'Formula bar' });
      await formulaBar.fill(values[row][col]);
      await formulaBar.press('Enter');
    }
  }
  await page.getByRole('gridcell', { name: 'D1' }).click();
  await page.getByRole('textbox', { name: 'Formula bar' }).fill('Total');
  await page.getByRole('textbox', { name: 'Formula bar' }).press('Enter');
  await page.getByRole('gridcell', { name: 'D2' }).click();
  await page.getByRole('textbox', { name: 'Formula bar' }).fill('=SUM(C2:C3)');
  await page.getByRole('textbox', { name: 'Formula bar' }).press('Enter');
  await page.getByRole('gridcell', { name: 'D2' }).click();
  await expect(page.getByRole('gridcell', { name: 'D2' })).toHaveText('20');
  const formulaBar = page.getByRole('textbox', { name: 'Formula bar' });
  const formulaBefore = await formulaBar.inputValue();
  const before = await page.getByRole('gridcell', { name: 'B2' }).innerText();
  const downloadReady = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export CSV' }).click();
  const download = await downloadReady;
  expect(download.suggestedFilename()).toMatch(/\.csv$/i);
  const filePath = await download.path();
  expect(filePath).not.toBeNull();
  const csv = await readFile(filePath!, 'utf-8');
  expect(csv).toContain('"design, review"');
  expect(csv).toContain('12');
  expect(csv).toContain('20');
  expect(csv).not.toContain('=SUM');
  await expect(page.getByRole('gridcell', { name: 'B2' })).toHaveText(before);
  await expect(formulaBar).toHaveValue(formulaBefore);
  await page.reload();
  await expect(page.getByRole('gridcell', { name: 'C3' })).toHaveText('8');
});
