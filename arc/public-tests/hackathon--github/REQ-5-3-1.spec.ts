import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-5-3-1: assign an eligible participant to an issue and persist it', async ({ page }) => {
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await page.getByRole('button', { name: /Assignees/ }).click();
  const search = page.getByRole('textbox', { name: /Search/ }); await search.fill('bob-reviewer');
  await page.getByRole('checkbox', { name: 'bob-reviewer' }).check();
  await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByText('bob-reviewer', { exact: true })).toBeVisible();
});
