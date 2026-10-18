# integration-route-db (JavaScript)

Call the app's real routes against a real database file in a temporary folder.

- Kind: integration · Tools: Vitest, the app on port 0, `fetch`, `node:sqlite`
- Use for: an API route with its validation, its session and its database, without a browser.

## Copy
Copy, never retype: `recipes/js/integration-route-db/tasks-api.test.js`. It tests `sample_app/server.js`.

## Fill
1. Your app needs a factory that takes the database path and can listen on port 0:
   `createApp({ dbPath }).start() -> { url, close }`. (Express: `app.listen(0)`, then `server.address().port`.)
2. Keep `beforeEach` (temporary folder from `os.tmpdir()`, fresh database, start) and `afterEach` (close, remove).
3. One test per behaviour: Arrange (sign in, earlier requests), Act (one request), Assert (status, body, and the row
   in the database when the route writes).

## Run
`npx vitest run recipes/js/integration-route-db`

## Don't
- Don't share one server or database between tests; don't use a fixed port.
- Don't point a test at the developer's real database.
