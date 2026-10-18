// Recipe japanese-text (browser half): switch to Japanese, find controls by Japanese names, type Japanese.
import { expect, test } from '../fixtures.js';

test('the page switches to Japanese', async ({ signedInPage: page }) => {
  await page.getByRole('button', { name: '日本語' }).click();

  await expect(page.getByRole('heading', { level: 1 })).toHaveText('タスク');
  await expect(page.locator('html')).toHaveAttribute('lang', 'ja');
  await expect(page.getByRole('button', { name: 'English' })).toBeVisible();
});

test('a Japanese task is added and counted', async ({ signedInPage: page }) => {
  await page.getByRole('button', { name: '日本語' }).click();

  await page.getByLabel('新しいタスク').fill('牛乳を買う');
  await page.getByRole('button', { name: '追加' }).click();

  await expect(page.getByRole('listitem').filter({ hasText: '牛乳を買う' })).toBeVisible();
  await expect(page.locator('#count')).toHaveText('1 件のタスク');
});

test('decomposed input is stored composed', async ({ signedInPage: page, appURL }) => {
  await page.getByLabel('New task').fill('がっこう');
  await page.getByRole('button', { name: 'Add' }).click();
  await expect(page.locator('#count')).toHaveText('1 task');

  const [task] = await (await page.request.get(`${appURL}/api/tasks`)).json();

  expect(task.title).toBe('がっこう');
});
