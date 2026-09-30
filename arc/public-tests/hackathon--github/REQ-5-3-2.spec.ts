import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-5-3-2: apply a repository label to an issue and retain the relationship', async ({ page }) => {
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await page.getByRole('button', { name: /Labels/ }).click();
  await page.getByRole('option', { name: 'documentation', exact: true }).click();
  await expect(page.getByText('documentation', { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByText('documentation', { exact: true })).toBeVisible();
});
