import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-6-3-1: read a public pull-request overview and commit list while signed out', async ({ page }) => {
  await openRepository(page); await page.getByRole('link', { name: 'Pull requests', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Improve onboarding', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Commits', exact: true }).click();
  await expect(page.getByRole('link', { name: /Document search flow/ })).toBeVisible();
  await page.reload(); await expect(page.getByRole('heading', { name: 'Improve onboarding', exact: true })).toBeVisible();
});
