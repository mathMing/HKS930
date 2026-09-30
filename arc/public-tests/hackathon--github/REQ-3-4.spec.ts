import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-3-4: change repository visibility as its owner and retain the setting', async ({ page }) => {
  await signIn(page); await openRepository(page);
  await page.getByRole('link', { name: 'Settings', exact: true }).click();
  await page.getByRole('link', { name: 'General', exact: true }).click();
  await page.getByRole('button', { name: /Change visibility/i }).click();
  await page.getByRole('button', { name: /Make private/i }).click();
  await page.getByRole('textbox', { name: /repository name/i }).fill('acme-docs');
  await page.getByRole('button', { name: /I understand, change repository visibility/i }).click();
  await expect(page.getByText('Private', { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByText('Private', { exact: true })).toBeVisible();
});
