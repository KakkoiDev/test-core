// @playwright/test runs the end-to-end specs (*.spec.js). Each test starts its own app server (recipes/js/fixtures.js),
// so there is no webServer here and tests can run in parallel.
import { defineConfig } from '@playwright/test';

// macOS: without these two flags every test browser asks for a keychain (NOTES.md 1). Never remove them.
export const CHROMIUM_FLAGS = ['--use-mock-keychain', '--password-store=basic'];
const chrome = process.env.TEST_CORE_CHROME || process.env.PI_TEST_CHROME; // an existing Chromium: nothing downloads

export default defineConfig({
  testDir: 'recipes/js',
  testMatch: '**/*.spec.js',
  forbidOnly: true,
  retries: 0, // a flaky test is fixed, not retried (recipe flaky-rules)
  reporter: [['list'], ['junit', { outputFile: '.test-output/playwright-junit.xml' }]],
  outputDir: '.test-output/playwright',
  use: {
    browserName: 'chromium',
    headless: true,
    launchOptions: { args: CHROMIUM_FLAGS, ...(chrome ? { executablePath: chrome } : {}) },
    trace: 'retain-on-failure',
  },
});
