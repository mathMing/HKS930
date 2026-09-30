import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-5-4: close and reopen an issue without losing its discussion', async ({ page }) => {
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await page.getByRole('button', { name: 'Close issue' }).click();
  await expect(page.getByText('Closed', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Reopen issue' }).click();
  await expect(page.getByText('Open', { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByRole('button', { name: 'Close issue' })).toBeVisible();
});
