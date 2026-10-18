# test-core

**Every kind of test, already decided: pinned tools and copyable recipes for Python and JavaScript.**

A small local model should never wonder how to write a test. test-core picks the libraries, pins their versions and
gives one recipe per kind of test: a short card, a copyable file and the recipe's own passing test. The model picks a
recipe by name, copies it and fills it in; deterministic code runs the tests and checks them.

[Agent rules](AGENTS.md) · [Lessons already learned](NOTES.md) · [MIT licence](LICENSE)

## The chosen tools

| Language | Unit | Integration | End to end |
|---|---|---|---|
| Python | **pytest** | **pytest** + FastAPI `TestClient` (httpx) | **pytest-playwright** |
| JavaScript | **Vitest** | **Vitest** + a local server on port 0 | **@playwright/test** |

Why these:

- **pytest** reads plain `assert`, has fixtures and `parametrize` for table-driven tests, and still runs stdlib
  `unittest` files, so older projects keep working.
- **FastAPI `TestClient`** calls the app in the same process through httpx: no port, no server to stop.
- **Vitest** is fast and light on low-end machines, speaks native ES modules and has Jest's `expect` API.
- **Playwright** (both languages, one browser engine) finds elements by role and label, waits for state on its own,
  and can go offline, stub the network and emulate a phone.
- `node --test` and stdlib `unittest` stay readable and allowed for projects with no dependencies.

Every Chromium launch passes `--use-mock-keychain` and `--password-store=basic`. On macOS, without them, every test
browser asks for a keychain; read [NOTES.md](NOTES.md) before anything else that starts a browser.

## How a small model uses it

1. Read [AGENTS.md](AGENTS.md).
2. Find the recipe by name or keyword: `python3 tools/catalog.py find "logged in"` (English or Japanese keywords).
3. Read its card (`recipes/<language>/<name>/README.md`), copy its file into the project, rename and fill it.
4. Run the tests. A recipe is done when its test passed, and failed first when the change was missing.

Each planned task carries Given/When/Then scenarios; each scenario becomes one end-to-end test with the scenario's
title as the test's name (recipe `scenario-e2e`). The E2E rule: every control a person can use has at least one
end-to-end step that uses it, and `tools/e2e_coverage.py` fails when a control disappears while its test stays, or
when a control has no test.

## Status

This first commit holds the decisions and the lessons. The pinned dependencies, the recipes, `CATALOG.json`, the tools
and CI arrive in the recipes pull request.
