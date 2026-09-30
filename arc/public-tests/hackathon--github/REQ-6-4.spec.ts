import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-6-4: request a pull-request reviewer and remove the request', async ({ page }) => {
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Pull requests', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await page.getByRole('button', { name: 'Reviewers' }).click();
  await page.getByRole('textbox', { name: 'Search' }).fill('bob-reviewer');
  await page.getByRole('option', { name: 'bob-reviewer', exact: true }).click();
  await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Remove bob-reviewer' }).click();
  await expect(page.getByText('bob-reviewer', { exact: true })).toHaveCount(0);
  await page.reload(); await expect(page.getByText('bob-reviewer', { exact: true })).toHaveCount(0);
});
