# integration-route-db (Python)

Call the app's real routes against a real database file in a temporary folder.

- Kind: integration · Tools: pytest, FastAPI `TestClient` (httpx), sqlite3
- Use for: an API route with its validation, its session and its database, without a browser.

## Copy
Copy, never retype: `recipes/python/integration-route-db/test_tasks_api.py`. It tests `sample_app/app.py`.

## Fill
1. Your app needs a factory that takes the database path: `create_app(db_path) -> FastAPI`. If it reads a global
   setting instead, override it in the `client` fixture (`app.dependency_overrides[get_db] = ...`).
2. Keep the fixtures: `db_path` (from `tmp_path`), `client`, `signed_in`.
3. One test per behaviour: Arrange (fixtures, earlier requests), Act (one request), Assert (status, body, and the row
   in the database when the route writes).

## Run
`pytest recipes/python/integration-route-db -q`

## Don't
- Don't share one database between tests, and don't point a test at the developer's real database.
- Don't start uvicorn for this: `TestClient` needs no port. A real server is for the browser (`e2e-journey`).
