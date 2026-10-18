// Recipe network-stub (browser half): page.route() answers the page's request with fixed data, or with an error.
import { expect, test } from '../fixtures.js';

test('the page shows the stubbed tip', async ({ signedInPage: page }) => {
  await page.route('**/api/tip', (route) => route.fulfill({ json: { text: 'Stubbed tip' } }));

  await page.reload();

  await expect(page.locator('#tip')).toHaveText('Stubbed tip');
});

test('the page survives a failing service', async ({ signedInPage: page }) => {
  await page.route('**/api/tip', (route) => route.fulfill({ status: 503, json: { error: 'down' } }));

  await page.reload();

  await expect(page.locator('#tip')).toHaveText('Tip unavailable.');
});
