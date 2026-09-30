import { expect, test } from '@playwright/test';
import { signIn } from './support';

test('REQ-2-2-4: remove an organization member through the member action menu', async ({ page }) => {
  await signIn(page);
  await page.getByRole('button', { name: /alice-dev/i }).click();
  await page.getByRole('link', { name: 'Your organizations' }).click();
  await page.getByRole('link', { name: 'Acme Demo' }).click();
  await page.getByRole('link', { name: 'People', exact: true }).click();
  await page.getByRole('button', { name: 'Member menu bob-reviewer' }).click();
  await page.getByRole('menuitem', { name: 'Remove from organization' }).click();
  await page.getByRole('button', { name: 'Remove', exact: true }).click();
  await expect(page.getByText('bob-reviewer', { exact: true })).toHaveCount(0);
  await page.reload(); await expect(page.getByText('bob-reviewer', { exact: true })).toHaveCount(0);
});
