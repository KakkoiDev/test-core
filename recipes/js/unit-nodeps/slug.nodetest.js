// Recipe unit-nodeps: node's built-in test runner, for a project that installs nothing.
// Run: node --test recipes/js/unit-nodeps/slug.nodetest.js
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { slugify } from './slug.js';

const cases = [
  ['Hello, World!', 'hello-world'],
  ['  spaces  around ', 'spaces-around'],
  ['Crème brûlée', 'creme-brulee'],
  ['', ''],
];

for (const [text, expected] of cases) {
  test(`slugify(${JSON.stringify(text)}) is ${JSON.stringify(expected)}`, () => {
    assert.equal(slugify(text), expected);
  });
}
