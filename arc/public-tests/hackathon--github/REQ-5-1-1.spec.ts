import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-5-1-1: filter open and closed issues without changing their records', async ({ page }) => {
  await openRepository(page); await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await page.getByRole('link', { name: 'Open', exact: true }).click();
  const search = page.getByRole('searchbox', { name: 'Search issues' });
  await search.fill('Improve onboarding');
  await expect(page.getByRole('link', { name: 'Improve onboarding', exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByRole('link', { name: 'Improve onboarding', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Closed', exact: true }).click();
  await search.fill('Legacy welcome text');
  await expect(page.getByRole('link', { name: 'Legacy welcome text', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Improve onboarding', exact: true })).toHaveCount(0);
});
