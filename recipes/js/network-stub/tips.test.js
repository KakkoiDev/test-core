// Recipe network-stub (code half): answer fetch with a stub. Pass it in, or replace the global for one test.
import { afterEach, expect, test, vi } from 'vitest';
import { fetchTip } from './tips.js';

afterEach(() => vi.unstubAllGlobals());

test('code reads the stubbed response', async () => {
  const stub = vi.fn(async () => Response.json({ text: 'Drink water' }));

  expect(await fetchTip(stub)).toBe('Drink water');
  expect(stub).toHaveBeenCalledWith('https://tips.example.com/today');
});

test('code falls back when the service fails', async () => {
  expect(await fetchTip(async () => new Response('', { status: 500 }))).toBe('Tip unavailable.');
});

test('code falls back when the network is down', async () => {
  expect(await fetchTip(async () => { throw new TypeError('fetch failed'); })).toBe('Tip unavailable.');
});

test('a global stub works for code that calls fetch directly', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => Response.json({ text: 'From the global stub' })));

  expect(await fetchTip()).toBe('From the global stub');
});
