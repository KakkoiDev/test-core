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

## Recipes

Each recipe exists in both languages: `recipes/python/<name>/` and `recipes/js/<name>/`, each with a card
(`README.md`), the copyable files and their own passing tests. `CATALOG.json` indexes them (name, language, kind,
purpose, English and Japanese keywords, files, the command that runs them).

| Name | Kind | What it shows |
|---|---|---|
| `unit-table` | unit | A pure function tested with a table of cases (`parametrize`, `test.each`) |
| `unit-nodeps` | unit | The same with no dependencies (`unittest`, `node --test`) |
| `integration-route-db` | integration | Real routes against a real database file in a temporary folder |
| `e2e-journey` | e2e | A person's whole journey in a real browser, through a page object |
| `fixtures` | fixtures | A test that starts signed in, with sample data |
| `data-builders` | fixtures | Test records from builders: valid unique defaults plus overrides |
| `network-stub` | e2e + unit | No network: `page.route` in the browser, `httpx.MockTransport` / stub `fetch` in code |
| `offline-phone` | e2e | Offline banner and disabled actions; phone viewport with touch |
| `japanese-text` | e2e + unit | Japanese names, IME-style input, NFC normalization, collation |
| `a11y-smoke` | e2e | Names, labels, alt, `lang`, one `h1`, tab order, duplicate ids; keyboard reach |
| `scenario-e2e` | e2e | Given/When/Then scenarios of a task, one e2e test each, named after the scenario |
| `flaky-rules` | rules | Wait for the state, never for time: the rules and each way to wait |

The recipes test `sample_app/`: one small task app (sign in, add, finish, delete, a tip from the server, offline banner,
English and Japanese) served by FastAPI (`sample_app/app.py`) and by `node:http` + `node:sqlite`
(`sample_app/server.js`) with the same API and the same page. Replace it with your app when you copy a recipe.

## Tools

```sh
python3 tools/catalog.py find "logged in"                 # or: find ログイン済み; list; show NAME --language js
python3 tools/catalog.py copy e2e-journey --language python --out tests/e2e
python3 tools/scenarios.py skeleton TASK.md --lang js     # one test per Given/When/Then scenario
python3 tools/scenarios.py check TASK.md --tests tests/e2e/task-12.spec.js --junit .test-output/playwright-junit.xml
python3 tools/e2e_coverage.py --pages 'app/templates/**/*.html' --tests 'tests/e2e/**/*' [--messages 'messages/*.json']
python3 tools/flaky_lint.py tests/
```

The tools need only Python 3.11+ (standard library). `e2e_coverage.py` lists every control of the pages (by role and
accessible name, label, `data-testid`), the tests that use each, the tests whose control is gone (always a failure:
remove the test knowingly) and the controls no test uses ("not verified"; a failure unless `--allow-untested`).

## Pinned versions

| Package | Version | Licence |
|---|---|---|
| pytest | 9.1.1 | MIT |
| pytest-playwright | 0.9.0 | Apache-2.0 |
| playwright (Python) | 1.56.0 | Apache-2.0 |
| fastapi | 0.142.2 | MIT |
| httpx | 0.28.1 | BSD-3-Clause |
| uvicorn | 0.53.0 | BSD-3-Clause |
| vitest | 5.0.3 | MIT |
| @playwright/test | 1.56.1 | Apache-2.0 |

Every transitive package is pinned too: `requirements.lock` (with hashes, resolved with `--exclude-newer 2026-10-05`)
and `package-lock.json`. Both Playwright versions use Chromium build 1194.

## Run locally

Prerequisites: Python 3.11+, Node.js 22.13+ (24 recommended; `node:sqlite`), an existing Chromium.

```sh
python3 -m venv .venv && .venv/bin/pip install --require-hashes -r requirements.lock
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci
export TEST_CORE_CHROME="$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1194/chrome-mac/headless_shell"
.venv/bin/python -m pytest          # tools, catalog and every Python recipe
npm test                            # Vitest, node --test and @playwright/test
```

`TEST_CORE_CHROME` (or `PI_TEST_CHROME`) points both languages at a Chromium already on the machine, so nothing is
downloaded. Without it, `npx playwright install chromium` provides one (CI does this, and only CI).

Tests are offline: the repository's `conftest.py` fails any Python connection to another machine, and the browser
fixtures abort any request that leaves 127.0.0.1.
