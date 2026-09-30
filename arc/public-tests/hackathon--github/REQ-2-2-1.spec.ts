import { expect, test } from '@playwright/test';
import { signIn } from './support';

test('REQ-2-2-1: create an organization team and reopen its persisted page', async ({ page }) => {
  const team = `pw-team-${Date.now()}`;
  await signIn(page);
  await page.getByRole('button', { name: /alice-dev/i }).click();
  await page.getByRole('link', { name: 'Your organizations' }).click();
  await page.getByRole('link', { name: 'Acme Demo' }).click();
  await page.getByRole('link', { name: 'Teams', exact: true }).click();
  await page.getByRole('link', { name: 'New team' }).click();
  await page.getByLabel('Team name').fill(team);
  await page.getByRole('button', { name: 'Create team' }).click();
  await expect(page.getByRole('heading', { name: new RegExp(team) })).toBeVisible();
  await page.reload(); await expect(page.getByRole('heading', { name: new RegExp(team) })).toBeVisible();
});
