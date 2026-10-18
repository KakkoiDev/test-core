// Vitest runs unit and integration tests (*.test.js). End-to-end specs (*.spec.js) belong to Playwright.
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['recipes/js/**/*.test.js', 'sample_app/**/*.test.js', 'tests/**/*.test.js'],
    environment: 'node',
  },
});
