import { expect, test } from '@playwright/test';
import { signIn } from './support';

test('REQ-2-1-2: create an organization and retain its owner identity after reload', async ({ page }) => {
  const slug = `pw-org-${Date.now()}`;
  await signIn(page);
  await page.getByRole('button', { name: /alice-dev/i }).click();
  await page.getByRole('link', { name: 'Your organizations' }).click();
  await page.getByRole('link', { name: 'New organization' }).click();
  await page.getByLabel('Organization name').fill(slug);
  await page.getByLabel('Display name').fill(`Playwright ${slug}`);
  await page.getByRole('button', { name: 'Create organization' }).click();
  await expect(page.getByRole('heading', { name: new RegExp(slug) })).toBeVisible();
  await page.reload(); await expect(page.getByRole('heading', { name: new RegExp(slug) })).toBeVisible();
  await page.getByRole('button', { name: /alice-dev/i }).click();
  await page.getByRole('link', { name: 'Your organizations' }).click();
  await expect(page.getByRole('link', { name: slug, exact: true })).toBeVisible();
});
