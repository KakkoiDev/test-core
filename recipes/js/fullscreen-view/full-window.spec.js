// Recipe fullscreen-view (fallback half): where the Fullscreen API is missing (iPhone Safari), the view fills the
// window instead. test.use() applies to this file: a phone with touch, and no Fullscreen API.
import { expect, test } from '../fixtures.js';

test.use({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => Object.defineProperty(Document.prototype, 'fullscreenEnabled', { get: () => false }));
});

test('without the Fullscreen API the view fills the window and Escape leaves it', async ({ signedInPage: page }) => {
  await page.getByLabel('New task').fill('Half-typed task');
  const board = page.locator('#board');
  const open = page.getByRole('button', { name: 'Full screen' });

  await open.tap();

  await expect(board).toHaveAttribute('data-view', 'full-window');
  const box = await board.boundingBox();
  expect(box).toMatchObject({ x: 0, y: 0, width: 390, height: 844 });
  expect(await page.evaluate(() => getComputedStyle(document.body).overflow)).toBe('hidden'); // the page behind is still
  const exit = page.getByRole('button', { name: 'Exit full screen' });
  await expect(exit).toBeFocused();
  expect((await exit.boundingBox()).height).toBeGreaterThanOrEqual(44);
  await page.keyboard.press('Escape');
  await expect(board).toHaveAttribute('data-view', 'inline');
  await expect(page.getByLabel('New task')).toHaveValue('Half-typed task');
  await expect(open).toBeFocused();
});
