import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-5-3-3: assign an issue to an existing milestone', async ({ page }) => {
  await signIn(page); await openRepository(page); await page.getByRole('link', { name: 'Issues', exact: true }).click();
  await page.getByRole('link', { name: 'Improve onboarding', exact: true }).click();
  await page.getByRole('button', { name: /Milestone/ }).click();
  const milestone = page.getByRole('option').filter({ hasNotText: /No milestone/i }).first();
  await expect(milestone).toBeVisible(); const label = (await milestone.innerText()).trim();
  await milestone.click(); await expect(page.getByText(label, { exact: true })).toBeVisible();
  await page.reload(); await expect(page.getByText(label, { exact: true })).toBeVisible();
});
