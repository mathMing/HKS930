import { expect, test } from '@playwright/test';

test('REQ-3-3: open the seeded public repository without signing in', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'acme-docs' }).click();
  await expect(page.getByRole('heading', { name: /alice-dev\/acme-docs/i })).toBeVisible();
  await expect(page.getByText('Public', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Code', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Issues', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Pull requests', exact: true })).toBeVisible();

  const repositoryUrl = page.url();
  await page.reload();
  await expect(page.getByRole('heading', { name: /alice-dev\/acme-docs/i })).toBeVisible();
  expect(page.url()).toBe(repositoryUrl);
});

test('REQ-3-3: do not reveal a private repository to an unauthenticated visitor', async ({ page }) => {
  await page.goto('/');
  await page.goto('/alice-dev/secret-research');
  await expect(page.getByRole('heading', { name: /alice-dev\/secret-research/i })).toHaveCount(0);
});
