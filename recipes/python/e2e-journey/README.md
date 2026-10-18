# e2e-journey (Python)

A person's journey through the real app in a real browser, written through a page object.

- Kind: e2e · Tools: pytest-playwright, `live_server.py`, a page object
- Use for: every user-facing feature. Every control a person can use needs at least one e2e step (the E2E rule).

## Copy
Copy, never retype:
- `recipes/python/e2e-journey/tasks_page.py`: the page object; rename it after your page.
- `recipes/python/e2e-journey/test_task_journey.py`: the journey.
- `recipes/python/conftest.py` and `recipes/python/live_server.py`: the browser flags, the offline guard and `app_url`.

## Fill
1. Page object: one locator per control, by role and accessible name (`get_by_role("button", name="Add")`) or label
   (`get_by_label("Email")`); `get_by_test_id` only where no role or label fits. One method per action. No asserts.
2. Test: Arrange (open the page, sign in), Act (the person's steps), Assert with `expect(...)` after each step that
   changes the page. `expect` waits for the state; never add sleeps.
3. In `conftest.py`, change `create_app` to your app factory.

## Run
`TEST_CORE_CHROME=<path to chromium> pytest recipes/python/e2e-journey -q` (or let `playwright install chromium`
provide the browser in CI).

## Don't
- Don't select by CSS class or XPath; don't use `wait_for_timeout`.
- Don't share a server or a database between tests: `app_url` is fresh for each test.
