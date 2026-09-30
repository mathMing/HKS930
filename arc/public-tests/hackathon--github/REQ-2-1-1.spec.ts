import { expect, test } from '@playwright/test';
import { signIn } from './support';

test('REQ-2-1-1: filter an organization repository list and open a visible result', async ({ page }) => {
  await signIn(page);
  await page.getByRole('button', { name: /alice-dev/i }).click();
  await page.getByRole('link', { name: 'Your organizations' }).click();
  await page.getByRole('link', { name: 'Acme Demo' }).click();
  await page.getByRole('link', { name: 'Repositories', exact: true }).click();
  const filter = page.getByRole('textbox', { name: 'Find a repository' });
  await filter.fill('acme-docs');
  const publicRepo = page.getByRole('link', { name: 'acme-docs', exact: true });
  await expect(publicRepo).toBeVisible(); await publicRepo.click();
  await expect(page.getByRole('heading', { name: /acme-docs/i })).toBeVisible();
  await page.goBack();
  await expect(page.getByRole('link', { name: 'acme-docs', exact: true })).toBeVisible();
});
