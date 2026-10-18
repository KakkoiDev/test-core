# network-stub (JavaScript)

Tests never reach the network. Answer the request where it is made: in the browser with `page.route`, in code with a
stub `fetch`.

- Kind: e2e and unit · Tools: @playwright/test `page.route`, Vitest `vi.fn` / `vi.stubGlobal`
- Use for: a third-party API, a slow service, an error state (503, network down) you cannot cause for real.

## Copy
Copy, never retype: `recipes/js/network-stub/network-stub.spec.js` (browser) and `recipes/js/network-stub/tips.test.js`
(code; to see it run, `tips.js`).

## Fill
- Browser: `await page.route('**/api/tip', (route) => route.fulfill({ json: {...} }))` before the page makes the
  request (route first, then `goto` or `reload`). Errors: `route.fulfill({ status: 503 })`.
- Code: pass `fetch` in and give the test `vi.fn(async () => Response.json({...}))`; check calls with
  `toHaveBeenCalledWith`. For code that calls the global, `vi.stubGlobal('fetch', ...)` and
  `vi.unstubAllGlobals()` after each test.

## Run
`npx vitest run recipes/js/network-stub` and `npx playwright test recipes/js/network-stub`

## Guard
The `context` fixture in `recipes/js/fixtures.js` aborts any browser request that leaves 127.0.0.1, so a forgotten
stub fails loudly.
