import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-5-2-3: add an issue discussion comment and persist its author and body', async ({ page }) => {
  const comment = `Playwright discussion ${Date.now()}`;
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await page.getByLabel('Comment').fill(comment);
  await page.getByRole('button', { name: 'Comment', exact: true }).click();
  const article = page.getByRole('article').filter({ hasText: comment });
  await expect(article).toContainText(comment); await expect(article).toContainText('alice-dev');
  await page.reload(); await expect(page.getByRole('article').filter({ hasText: comment })).toBeVisible();
});
