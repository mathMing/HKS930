import { expect, test } from '@playwright/test';
import { openRepository } from './support';

test('REQ-3-2-3: switch clone protocols and expose a repository clone value', async ({ page }) => {
  await openRepository(page);
  await page.getByRole('button', { name: 'Code', exact: true }).click();
  const clone = page.getByRole('textbox', { name: /clone/i });
  await expect(clone).toBeVisible();
  await expect(clone).toHaveValue(/acme-docs/);
  await page.getByRole('tab', { name: 'SSH' }).click();
  await expect(clone).toHaveValue(/^git@/);
  await page.getByRole('tab', { name: 'HTTPS' }).click();
  await expect(clone).toHaveValue(/^https?:/);
});
