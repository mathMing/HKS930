import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-5-2-2: edit an issue title and description and keep both after reload', async ({ page }) => {
  const title = `Playwright title ${Date.now()}`; const description = 'Updated through the issue editor.';
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await page.getByRole('button', { name: 'Edit issue title' }).click();
  await page.getByRole('textbox', { name: 'Issue title' }).fill(title);
  await page.getByRole('button', { name: 'Save issue title' }).click();
  await page.getByRole('button', { name: 'Edit issue description' }).click();
  await page.getByRole('textbox', { name: 'Issue description' }).fill(description);
  await page.getByRole('button', { name: 'Save issue description' }).click();
  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
  await expect(page.getByText(description, { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
});
