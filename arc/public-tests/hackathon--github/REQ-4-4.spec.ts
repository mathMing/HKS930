import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-4-4: commit a file edit through the web editor and reopen the saved file', async ({ page }) => {
  const content = `Playwright edit ${Date.now()}`;
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Code', exact: true }).click();
  await page.getByRole('link', { name: 'README.md', exact: true }).click();
  await page.getByRole('button', { name: 'Edit' }).click();
  await page.getByRole('textbox', { name: 'File content' }).fill(content);
  await page.getByRole('textbox', { name: 'Commit message' }).fill('Update README from Playwright');
  await page.getByRole('button', { name: 'Commit changes' }).click();
  await expect(page.locator('pre')).toContainText(content);
  await page.reload(); await expect(page.locator('pre')).toContainText(content);
});
