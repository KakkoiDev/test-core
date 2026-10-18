// Recipe integration-route-db: call real routes against a real database in a temporary folder.
// Each test starts the app on port 0 with its own database file, and stops it after: no shared state, any order.
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { afterEach, beforeEach, expect, test } from 'vitest';
import { createApp } from '../../../sample_app/server.js'; // replace with your app's factory

let folder, dbPath, app;

beforeEach(async () => {
  folder = mkdtempSync(join(tmpdir(), 'test-core-'));
  dbPath = join(folder, 'test.sqlite3');
  app = await createApp({ dbPath }).start();
});

afterEach(async () => {
  await app.close();
  rmSync(folder, { recursive: true, force: true });
});

/** A tiny client that keeps the session cookie, like a browser. */
function client() {
  let cookie = '';
  return async (method, path, body) => {
    const response = await fetch(app.url + path, {
      method,
      headers: { cookie, ...(body ? { 'content-type': 'application/json' } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    cookie = response.headers.get('set-cookie')?.split(';')[0] ?? cookie;
    return { status: response.status, body: response.status === 204 ? null : await response.json() };
  };
}

async function signedIn() {
  const call = client();
  expect((await call('POST', '/api/login', { email: 'demo@example.com', password: 'test-password' })).status).toBe(200);
  return call;
}

test('adding a task stores it in the database', async () => {
  const call = await signedIn();

  const response = await call('POST', '/api/tasks', { title: 'Buy milk' });

  expect(response).toEqual({ status: 201, body: { id: 1, title: 'Buy milk', done: false } });
  const db = new DatabaseSync(dbPath);
  expect(db.prepare('SELECT owner, title, done FROM tasks').all()).toEqual([{ owner: 'demo@example.com', title: 'Buy milk', done: 0 }]);
  db.close();
});

test('tasks are listed in the order they were added', async () => {
  const call = await signedIn();
  for (const title of ['first', 'second']) await call('POST', '/api/tasks', { title });

  const { body } = await call('GET', '/api/tasks');

  expect(body.map((task) => task.title)).toEqual(['first', 'second']);
});

test('an empty title is refused', async () => {
  const call = await signedIn();

  expect((await call('POST', '/api/tasks', { title: '   ' })).status).toBe(422);
  expect((await call('GET', '/api/tasks')).body).toEqual([]);
});

test('without signing in the tasks are closed', async () => {
  expect((await client()('GET', '/api/tasks')).status).toBe(401);
});

test('a wrong password is refused', async () => {
  expect((await client()('POST', '/api/login', { email: 'demo@example.com', password: 'wrong' })).status).toBe(401);
});

test('deleting a task removes it', async () => {
  const call = await signedIn();
  const { body: task } = await call('POST', '/api/tasks', { title: 'Buy milk' });

  expect((await call('DELETE', `/api/tasks/${task.id}`)).status).toBe(204);
  expect((await call('GET', '/api/tasks')).body).toEqual([]);
  expect((await call('DELETE', `/api/tasks/${task.id}`)).status).toBe(404);
});
