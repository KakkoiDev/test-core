// Recipe pwa-offline: an installable app keeps working offline. Checks: its service worker takes control with the
// app's own scope, CacheStorage holds exactly the app's files, a reload with the network cut is served by the worker
// and still works, and full Chromium reports the app installable (and a page without a manifest not).
import { cacheContents, installability, reloadOffline, serviceWorkerControl } from '../../../pwa/pwa.mjs';
import { CHROMIUM_FLAGS } from '../../../playwright.config.js';
import { expect, test } from '../fixtures.js';

const APP = '/pwa/index.html';

test('the service worker takes control of its own scope and caches the app', async ({ page, appURL }) => {
  await page.goto(appURL + APP);

  const registration = await serviceWorkerControl(page);

  expect(registration.scope).toBe(`${appURL}/pwa/`);
  expect(registration.scriptURL).toBe(`${appURL}/pwa/sw.js`);
  expect(await cacheContents(page)).toEqual({
    'tally-v1': ['/pwa/app.js', '/pwa/icon-192.png', '/pwa/icon-512.png', '/pwa/index.html', '/pwa/manifest.webmanifest'],
  });
});

test('an offline reload is served by the service worker and the app still works', async ({ page, appURL }) => {
  await page.goto(appURL + APP);
  await serviceWorkerControl(page);

  const reload = await reloadOffline(page);

  expect(reload).toEqual({ status: 200, fromServiceWorker: true });
  await expect(page.getByRole('heading', { name: 'Tally' })).toBeVisible();
  await page.getByRole('button', { name: 'Add one' }).click(); // app.js came from the cache too
  await expect(page.locator('#count')).toHaveText('1');
});

test('Chromium reports the app installable, and a page without a manifest not', async ({ playwright, appURL }, testInfo) => {
  // Full Chromium (the headless shell says "installable" to everything) on a persistent profile (a fresh context
  // would add "in-incognito").
  const context = await playwright.chromium.launchPersistentContext(testInfo.outputPath('profile'),
    { ...testInfo.project.use.launchOptions, args: CHROMIUM_FLAGS, channel: 'chromium' });
  try {
    const page = context.pages()[0] ?? await context.newPage();
    await page.goto(appURL + APP);
    await serviceWorkerControl(page);

    const app = await installability(page);
    await page.goto(appURL + '/');
    const plain = await installability(page);

    expect(app).toEqual({ errors: [], manifestURL: `${appURL}/pwa/manifest.webmanifest`, manifestErrors: [] });
    expect(plain.errors).toContain('no-manifest');
  } finally {
    await context.close();
  }
});

test('the installability check refuses the headless shell instead of passing', async ({ page, appURL }) => {
  await page.goto(appURL + '/');

  const check = installability(page);

  await expect(check).rejects.toThrow(/headless shell/);
});
