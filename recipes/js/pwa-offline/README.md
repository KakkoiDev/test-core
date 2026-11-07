# pwa-offline (JavaScript)

Check that an installable app (PWA) keeps working offline and that Chromium would install it.

- Kind: e2e · Tools: @playwright/test, `pwa/pwa.mjs` (`serviceWorkerControl`, `cacheContents`, `reloadOffline`,
  `installability`), `context.setOffline`, the DevTools protocol (`Page.getInstallabilityErrors`)
- Use for: a web app with a manifest and a service worker: an exported or generated app, a chat shell, any page that
  must open without a connection or be added to a home screen.

## Copy
Copy, never retype: `recipes/js/pwa-offline/pwa-offline.spec.js`. Import the helpers from `pwa/pwa.mjs` (pinned as
`test-core/pwa/pwa.mjs` in adopted repositories).

## Fill
- Control: `await serviceWorkerControl(page)` waits until a worker controls the page and returns its `scope` and
  `scriptURL`. Assert the scope is the app's own folder, not the origin's root.
- Cache: `await cacheContents(page)` lists every cache on the origin with its paths. Assert the exact list, so a file
  missing from the precache (or something that must never be cached, like an API) shows up.
- Offline: `await reloadOffline(page)` cuts the connection and reloads; expect `{ status: 200, fromServiceWorker: true }`,
  then use the app (a click that needs its script) to prove the cached files work.
- Install: launch **full Chromium** (`channel: 'chromium'`) with a **persistent profile**
  (`launchPersistentContext`), then `await installability(page)`; `errors: []` means installable. Check a page without
  a manifest reports `no-manifest`, so the check is not vacuous.

## Run
`npx playwright test recipes/js/pwa-offline`

## Don't
- Don't check installability in the headless shell: it reports every page installable (`installability` throws there).
- Don't use a fresh context for installability with full Chromium: it adds `in-incognito`.
- Don't stop the server to fake offline; cut the connection with `setOffline` (recipe offline-phone).
- Don't put two apps' service workers in nested scopes on one origin: give each app its own folder and its own
  manifest `id`.
