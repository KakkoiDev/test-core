// Recipe fullscreen-view (native half): a part of the page goes full screen with the Fullscreen API and comes back
// unchanged. Checks: the same element went full screen (not a copy), Exit is visible and focused, the state survives,
// and focus returns to the button that opened it.
import { expect, test } from '../fixtures.js';

const fullscreenId = (page) => page.evaluate(() => document.fullscreenElement?.id ?? null);

test('full screen keeps the view and its state, and Exit returns focus', async ({ signedInPage: page }) => {
  await page.getByLabel('New task').fill('Half-typed task');
  const board = page.locator('#board');
  await board.evaluate((element) => { element.dataset.probe = 'same-node'; }); // a re-created view would lose this
  const open = page.getByRole('button', { name: 'Full screen' });

  await open.click();

  await expect.poll(() => fullscreenId(page)).toBe('board');
  const exit = page.getByRole('button', { name: 'Exit full screen' });
  await expect(exit).toBeFocused();
  await exit.click();
  await expect.poll(() => fullscreenId(page)).toBe(null);
  await expect(board).toHaveAttribute('data-view', 'inline');
  await expect(board).toHaveAttribute('data-probe', 'same-node');
  await expect(page.getByLabel('New task')).toHaveValue('Half-typed task');
  await expect(open).toBeFocused();
});
