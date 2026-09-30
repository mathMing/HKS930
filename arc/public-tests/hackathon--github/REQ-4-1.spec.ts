import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-4-1: browse a stored repository file and restore its content after reload', async ({ page }) => {
  await openRepository(page); await page.getByRole('link', { name: 'Code', exact: true }).click();
  await expect(page.getByRole('link', { name: 'README.md', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'README.md', exact: true }).click();
  await expect(page.getByText(/search/i).first()).toBeVisible();
  const content = await page.locator('pre').innerText();
  expect(content.trim().length).toBeGreaterThan(0);
  await page.reload(); await expect(page.locator('pre')).toHaveText(content);
});
