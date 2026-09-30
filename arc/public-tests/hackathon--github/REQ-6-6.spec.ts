import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-6-6: close and reopen a pull request without merging it', async ({ page }) => {
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Pull requests', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await page.getByRole('button', { name: 'Close pull request' }).click();
  await expect(page.getByText('Closed', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Reopen pull request' }).click();
  await expect(page.getByText('Open', { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByRole('button', { name: 'Close pull request' })).toBeVisible();
});
