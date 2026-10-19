// Every generated test block passes its self-test against its App Block's demo markup (the fixture copy of Pi
// Workbench's kit/blocks), and a control removed from the markup fails loudly.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { expect, test } from '../../recipes/js/fixtures.js';
import { BLOCKS } from '../../functional/blocks/js/index.js';
import { selfTest } from '../../functional/blocks/selftest.js';
import { settings } from '../../functional/js/primitives.js';

const KIT = fileURLToPath(new URL('../fixtures/app-blocks/', import.meta.url));

for (const name of Object.keys(BLOCKS).sort()) {
  test(`the ${name} block passes its self-test`, async ({ page }) => {
    const world = await selfTest(page, BLOCKS[name], { kit: KIT });
    expect(world.level).toBe('e2e');
  });
}

test('a control removed from the markup fails loudly', async ({ page }) => {
  const block = BLOCKS.LogIn;
  const markup = readFileSync(join(KIT, block.DEMO[0]), 'utf8').replace('data-t="login.signup">Sign Up</a>', 'data-t="login.signup"></a>');
  expect(markup).not.toContain('Sign Up');
  const before = settings.timeout;
  settings.timeout = 300;
  try {
    await expect(selfTest(page, block, { markup })).rejects.toThrow('LogIn: uses a control that no longer exists: link "Sign Up"');
  } finally {
    settings.timeout = before;
  }
});
