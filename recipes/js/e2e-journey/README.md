# e2e-journey (JavaScript)

A person's journey through the real app in a real browser, written through a page object.

- Kind: e2e · Tools: @playwright/test, a page object, `recipes/js/fixtures.js`
- Use for: every user-facing feature. Every control a person can use needs at least one e2e step (the E2E rule).

## Copy
Copy, never retype:
- `recipes/js/e2e-journey/tasks-page.js`: the page object; rename it after your page.
- `recipes/js/e2e-journey/task-journey.spec.js`: the journey.
- `recipes/js/fixtures.js` and `playwright.config.js`: `appURL`, the offline guard and the browser flags.

## Fill
1. Page object: one locator per control, by role and accessible name (`getByRole('button', { name: 'Add' })`) or
   label (`getByLabel('Email')`); `getByTestId` only where no role or label fits. One async method per action.
2. Test: Arrange (open, sign in), Act (the person's steps), Assert with `await expect(...)` after each step that
   changes the page. `expect` waits for the state; never `waitForTimeout`.
3. In `fixtures.js`, change `createApp` to your app's start function (it must listen on port 0).

## Run
`TEST_CORE_CHROME=<path to chromium> npx playwright test recipes/js/e2e-journey` (CI installs the browser with
`npx playwright install --with-deps chromium`).

## Don't
- Don't select by CSS class or XPath; don't share a server or database between tests.
