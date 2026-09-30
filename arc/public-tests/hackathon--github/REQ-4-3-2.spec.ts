import { expect, test } from '@playwright/test';
import { openRepository, signIn } from './support';

test('REQ-4-3-2: create a branch from the current revision and switch to it', async ({ page }) => {
  const branch = `pw-branch-${Date.now()}`;
  await signIn(page); await openRepository(page);
  await page.getByRole('link', { name: 'Code', exact: true }).click();
  await page.getByRole('button', { name: 'Branch main' }).click();
  await page.getByRole('textbox', { name: 'Find branch' }).fill(branch);
  const create = page.getByRole('option', { name: `Create branch: ${branch}` });
  await expect(create).toBeVisible(); await create.click();
  await expect(page.getByRole('button', { name: `Branch ${branch}` })).toBeVisible();
  await page.reload(); await expect(page.getByRole('button', { name: `Branch ${branch}` })).toBeVisible();
});
