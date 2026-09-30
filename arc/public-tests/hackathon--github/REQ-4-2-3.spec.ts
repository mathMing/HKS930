import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-4-2-3: search code in the current repository and open a matching file', async ({ page }) => {
  await openRepository(page);
  const search = page.getByRole('searchbox', { name: 'Search' });
  await search.fill('search'); await search.press('Enter');
  await page.getByRole('link', { name: 'Code', exact: true }).click();
  await expect(page.getByRole('link', { name: 'src/search.ts', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'src/search.ts', exact: true }).click();
  await expect(page.getByText(/search/i).first()).toBeVisible();
  await expect(page.getByRole('searchbox', { name: 'Search' })).toHaveCount(0);
});
