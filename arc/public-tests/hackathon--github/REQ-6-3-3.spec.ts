import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-6-3-3: add an inline comment to a changed code line and persist it', async ({ page }) => {
  const body = `Review note ${Date.now()}`;
  await signIn(page, 'bob-reviewer'); await openRepository(page);
  await page.getByRole('link', { name: 'Pull requests', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await page.getByRole('link', { name: 'Files changed', exact: true }).click();
  await page.getByRole('button', { name: 'Add comment' }).first().click();
  await page.getByLabel('Comment').fill(body);
  await page.getByRole('button', { name: 'Add single comment' }).click();
  await expect(page.getByText(body, { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByText(body, { exact: true })).toBeVisible();
});
