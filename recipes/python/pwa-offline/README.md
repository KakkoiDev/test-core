# pwa-offline (Python)

Check that an installable app (PWA) keeps working offline and that Chromium would install it.

- Kind: e2e · Tools: pytest-playwright, `pwa/pwa.py` (`service_worker_control`, `cache_contents`, `reload_offline`,
  `installability`), `context.set_offline`, the DevTools protocol (`Page.getInstallabilityErrors`)
- Use for: a web app with a manifest and a service worker: an exported or generated app, a chat shell, any page that
  must open without a connection or be added to a home screen.

## Copy
Copy, never retype: `recipes/python/pwa-offline/test_pwa_offline.py`. Import the helpers from `pwa/pwa.py` (pinned as
`test-core/pwa/pwa.py` in adopted repositories; put `test-core` on the path and `from pwa.pwa import ...`).

## Fill
- Control: `service_worker_control(page)` waits until a worker controls the page and returns its `scope` and
  `scriptURL`. Assert the scope is the app's own folder, not the origin's root.
- Cache: `cache_contents(page)` lists every cache on the origin with its paths. Assert the exact list, so a file
  missing from the precache (or something that must never be cached, like an API) shows up.
- Offline: `reload_offline(page)` cuts the connection and reloads; expect
  `{"status": 200, "from_service_worker": True}`, then use the app to prove the cached files work.
- Install: launch **full Chromium** (`channel="chromium"`) with a **persistent profile**
  (`launch_persistent_context`), then `installability(page)`; `errors == []` means installable. Check a page without a
  manifest reports `no-manifest`, so the check is not vacuous.

## Run
`pytest recipes/python/pwa-offline`

## Don't
- Don't check installability in the headless shell: it reports every page installable (`installability` raises there).
- Don't use a fresh context for installability with full Chromium: it adds `in-incognito`.
- Don't stop the server to fake offline; cut the connection with `set_offline` (recipe offline-phone).
- Don't put two apps' service workers in nested scopes on one origin: give each app its own folder and its own
  manifest `id`.
