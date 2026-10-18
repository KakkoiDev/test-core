// Recipe data-builders: the builders' own tests, and a builder used to arrange an integration test.
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { expect, test } from 'vitest';
import { createApp } from '../../../sample_app/server.js';
import { aTask, aUser, someTasks } from './builders.js';

test('defaults are valid and unique', () => {
  const [first, second] = [aTask(), aTask()];
  expect(first.done).toBe(false);
  expect(first.title).not.toBe(second.title);
});

test('overrides name only what the test cares about', () => {
  const task = aTask({ done: true });
  expect(task.done).toBe(true);
  expect(task.title).toMatch(/^Task /);
});

test('someTasks makes many', () => {
  expect(someTasks(3, { done: true }).map((task) => task.done)).toEqual([true, true, true]);
});

test('a builder arranges an integration test', async () => {
  const folder = mkdtempSync(join(tmpdir(), 'test-core-'));
  const user = aUser();
  const app = await createApp({ dbPath: join(folder, 'test.sqlite3'), users: { [user.email]: user.password } }).start();
  try {
    const login = await fetch(`${app.url}/api/login`, { method: 'POST', body: JSON.stringify({ email: user.email, password: user.password }) });
    const cookie = login.headers.get('set-cookie').split(';')[0];
    for (const task of someTasks(2)) {
      await fetch(`${app.url}/api/tasks`, { method: 'POST', headers: { cookie }, body: JSON.stringify({ title: task.title }) });
    }
    const listed = await (await fetch(`${app.url}/api/tasks`, { headers: { cookie } })).json();
    expect(listed).toHaveLength(2);
  } finally {
    await app.close();
    rmSync(folder, { recursive: true, force: true });
  }
});
