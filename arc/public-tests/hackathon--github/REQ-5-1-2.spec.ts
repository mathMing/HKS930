import { expect, test } from '@playwright/test';

test('REQ-5-1-2: open a seeded issue and restore its discussion after refresh', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'acme-docs' }).click();
  await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding' }).click();

  await expect(page.getByRole('heading', { name: 'Improve onboarding', exact: true })).toBeVisible();
  await expect(page.getByText('Open', { exact: true })).toBeVisible();
  await expect(page.getByText('Describe the onboarding improvement.', { exact: true })).toBeVisible();
  const detailUrl = page.url();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Improve onboarding', exact: true })).toBeVisible();
  expect(page.url()).toBe(detailUrl);
});
