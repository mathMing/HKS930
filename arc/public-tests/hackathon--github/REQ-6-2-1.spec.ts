import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-6-2-1: filter the pull-request list by open status and restore the seeded result', async ({ page }) => {
  await openRepository(page); await page.getByRole('link', { name: 'Pull requests', exact: true }).click();
  await page.getByRole('link', { name: 'Open', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Improve onboarding', exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByRole('link', { name: 'Improve onboarding', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Improve onboarding', exact: true })).toBeVisible();
});
