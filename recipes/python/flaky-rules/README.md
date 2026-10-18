# flaky-rules (Python)

A flaky test passes and fails with the same code. These rules keep tests deterministic; the tests here show each way
to wait, and `tools/flaky_lint.py` finds the usual causes.

- Kind: rules · Tools: pytest-playwright `expect`, `expect_response`, `wait_for_function`; `tools/flaky_lint.py`
- Use for: every test you write, and every test that failed once and passed on a re-run.

## Rules
1. **Wait for the state, never for time.** No `time.sleep`, no `wait_for_timeout`. Use `expect(locator)...` (it
   retries), `page.expect_response(...)` around the action, or `page.wait_for_function(...)` for a script value.
2. **Every test makes its own data.** A fresh database per test (`app_url`), builders for records, no order between
   tests. A test that passes alone and fails in the suite is a bug in the test.
3. **No network.** Stub it (`network-stub`); serve the app on 127.0.0.1.
4. **No clock or randomness you don't control.** Pass the time and the seed in.
5. **Find by role and label**, not CSS classes or positions (`nth(3)`), which change with the layout.
6. **A re-run that passes is not a fix.** Find the race, fix the wait; never add retries to hide it.

## Copy
Copy, never retype: `recipes/python/flaky-rules/test_wait_for_state.py`.

## Run
`pytest recipes/python/flaky-rules -q` and `python3 tools/flaky_lint.py tests/`. A line that truly needs a wait says
why: `# flaky-lint: allow <reason>`.
