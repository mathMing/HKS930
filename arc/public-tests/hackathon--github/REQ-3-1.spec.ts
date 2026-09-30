import { expect, test } from '@playwright/test';

test('REQ-3-1: search for a public repository and keep private results hidden', async ({ page }) => {
  await page.goto('/');
  const search = page.getByRole('searchbox', { name: 'Search' });
  await search.fill('acme-docs'); await search.press('Enter');
  await expect(page.getByRole('link', { name: 'acme-docs', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'acme-docs', exact: true }).click();
  await expect(page.getByRole('heading', { name: /acme-docs/i })).toBeVisible();
  await page.reload(); await expect(page.getByRole('heading', { name: /acme-docs/i })).toBeVisible();
  await page.goto('/'); await search.fill('secret-research'); await search.press('Enter');
  await expect(page.getByRole('link', { name: 'secret-research', exact: true })).toHaveCount(0);
});
