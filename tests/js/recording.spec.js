import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
const source = readFileSync(new URL('../../recording/recorder.mjs', import.meta.url), 'utf8');

test('a recording captures actions without typed text or secret fields and stops cleanly', async ({ page }) => {
  await page.route('http://127.0.0.1:19234/**', route => route.fulfill({ contentType: 'text/html', body: '<label>Note<input id="note"></label><label>Password<input type="password"></label><button>Save</button><p role="status"></p>' }));
  await page.goto('http://127.0.0.1:19234/');
  await page.evaluate(async code => {
    const module = await import(URL.createObjectURL(new Blob([code], { type: 'text/javascript' })));
    window.lines = [];
    window.recorder = module.installRecorder({ post: async lines => window.lines.push(...lines) });
    document.querySelector('button').onclick = () => { document.querySelector('[role=status]').textContent = 'Saved'; };
  }, source);
  await page.getByLabel('Note', { exact: true }).fill('private project words');
  await page.getByLabel('Password', { exact: true }).fill('secret-password');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Saved');
  const lines = await page.evaluate(async () => { await window.recorder.flush(); return window.lines; });
  expect(lines.some(line => line.type === 'click')).toBe(true);
  expect(lines.filter(line => line.type === 'change')).toHaveLength(1);
  expect(lines.find(line => line.type === 'change').value).toEqual({ redacted: true, length: 21 });
  expect(JSON.stringify(lines)).not.toMatch(/private|secret|password|Note|Save/);
  await page.evaluate(() => window.recorder.stop());
  await page.getByLabel('Note', { exact: true }).fill('later');
  expect(await page.evaluate(() => window.lines.length)).toBe(lines.length);
});

test('recording off and failed delivery do not break the application or retain typed values', async ({ page }) => {
  await page.setContent('<input aria-label="Note"><button>Save</button>');
  await page.evaluate(async code => {
    const module = await import(URL.createObjectURL(new Blob([code], { type: 'text/javascript' })));
    window.calls = 0;
    window.recorder = module.installRecorder({ enabled: false, post: async () => { window.calls++; throw Error('offline'); } });
  }, source);
  await page.getByLabel('Note').fill('not recorded');
  expect(await page.evaluate(() => window.calls)).toBe(0);
  await page.evaluate(() => window.recorder.setEnabled(true));
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await page.evaluate(() => window.recorder.flush());
  expect(await page.evaluate(() => window.calls)).toBeGreaterThan(0);
  await expect(page.getByRole('button', { name: 'Save', exact: true })).toBeEnabled();
  await page.evaluate(() => window.recorder.stop());
});

test('slow delivery keeps only the bounded recent steps and disabling drops pending steps', async ({ page }) => {
  await page.setContent('<button>Save</button>');
  await page.evaluate(async code => {
    const module = await import(URL.createObjectURL(new Blob([code], { type: 'text/javascript' })));
    window.batches = [];
    window.recorder = module.installRecorder({ maxSteps: 3, post: steps => {
      window.batches.push(steps);
      return new Promise(resolve => { window.release = resolve; });
    } });
    document.querySelector('button').click();
  }, source);
  await expect.poll(() => page.evaluate(() => window.batches.length)).toBe(1);
  await page.evaluate(() => { for (let i = 0; i < 30; i++) document.querySelector('button').click(); });
  await page.evaluate(() => window.release());
  await expect.poll(() => page.evaluate(() => window.batches.length)).toBe(2);
  expect(await page.evaluate(() => window.batches[1].length)).toBe(3);
  await page.evaluate(async () => {
    document.querySelector('button').click();
    window.recorder.setEnabled(false);
    window.release();
    await window.recorder.flush();
    window.recorder.stop();
  });
  expect(await page.evaluate(() => window.batches.length)).toBe(2);
});
