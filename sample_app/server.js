// The sample app in JavaScript (node:http + node:sqlite): the same API as sample_app/app.py, serving
// sample_app/static. createApp({ dbPath }) builds a fresh app on its own database file; start() listens on port 0.
import { randomBytes } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';
import { validTitle } from './static/tasks.js';

const STATIC = fileURLToPath(new URL('./static/', import.meta.url));
export const TEST_USERS = { 'demo@example.com': 'test-password' };
export const TIP = 'Write the test first, watch it fail, then make it pass.';
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json' };

export { cleanTitle } from './static/tasks.js'; // recipe japanese-text

export function createApp({ dbPath, users = TEST_USERS }) {
  const sessions = new Map();
  const db = new DatabaseSync(dbPath);
  db.exec('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)');
  const taskJSON = (row) => ({ id: row.id, title: row.title, done: Boolean(row.done) });

  async function handle(request, response) {
    const url = new URL(request.url, 'http://local');
    const send = (status, body, headers = {}) => {
      response.writeHead(status, { ...(body === undefined ? {} : { 'content-type': 'application/json' }), ...headers });
      response.end(body === undefined ? undefined : JSON.stringify(body));
    };
    const session = /(?:^|;\s*)session=([^;]+)/.exec(request.headers.cookie ?? '')?.[1];
    const owner = sessions.get(session);
    let body = {};
    if (['POST', 'PATCH'].includes(request.method)) {
      let text = '';
      for await (const chunk of request) text += chunk;
      try { body = text ? JSON.parse(text) : {}; } catch { return send(400, { error: 'Send JSON.' }); }
    }
    const route = `${request.method} ${url.pathname}`;
    const taskId = Number(/^\/api\/tasks\/(\d+)$/.exec(url.pathname)?.[1]);

    if (route === 'POST /api/login') {
      if (users[body.email] !== body.password) return send(401, { error: 'Wrong email or password.' });
      const token = randomBytes(16).toString('base64url');
      sessions.set(token, body.email);
      return send(200, { email: body.email }, { 'set-cookie': `session=${token}; HttpOnly; SameSite=Lax; Path=/` });
    }
    if (route === 'POST /api/logout') {
      sessions.delete(session);
      return send(200, { ok: true }, { 'set-cookie': 'session=; Max-Age=0; Path=/' });
    }
    if (route === 'GET /api/tip') return send(200, { text: TIP });
    if (url.pathname.startsWith('/api/')) {
      if (!owner) return send(401, { error: 'Sign in first.' });
      if (route === 'GET /api/me') return send(200, { email: owner });
      if (route === 'GET /api/tasks') return send(200, db.prepare('SELECT * FROM tasks WHERE owner = ? ORDER BY id').all(owner).map(taskJSON));
      if (route === 'POST /api/tasks') {
        let title;
        try { title = validTitle(body.title); } catch (error) { return send(422, { error: error.message }); }
        const { lastInsertRowid } = db.prepare('INSERT INTO tasks (owner, title) VALUES (?, ?)').run(owner, title);
        return send(201, taskJSON(db.prepare('SELECT * FROM tasks WHERE id = ?').get(lastInsertRowid)));
      }
      if (taskId && request.method === 'PATCH') {
        db.prepare('UPDATE tasks SET done = ? WHERE id = ? AND owner = ?').run(body.done ? 1 : 0, taskId, owner);
        const row = db.prepare('SELECT * FROM tasks WHERE id = ? AND owner = ?').get(taskId, owner);
        return row ? send(200, taskJSON(row)) : send(404, { error: 'No such task.' });
      }
      if (taskId && request.method === 'DELETE') {
        const { changes } = db.prepare('DELETE FROM tasks WHERE id = ? AND owner = ?').run(taskId, owner);
        return changes ? send(204) : send(404, { error: 'No such task.' });
      }
      return send(404, { error: 'No such route.' });
    }
    const path = normalize(join(STATIC, url.pathname === '/' ? 'index.html' : url.pathname));
    if (!path.startsWith(STATIC)) return send(404, { error: 'Not found.' });
    try {
      const file = await readFile(path);
      response.writeHead(200, { 'content-type': TYPES[extname(path)] ?? 'application/octet-stream' });
      return response.end(file);
    } catch {
      return send(404, { error: 'Not found.' });
    }
  }

  const server = createServer((request, response) => {
    handle(request, response).catch((error) => {
      response.writeHead(500, { 'content-type': 'application/json' });
      response.end(JSON.stringify({ error: String(error) }));
    });
  });

  return {
    server,
    db,
    /** Listen on a free port on 127.0.0.1 and resolve with { url, close }. */
    start() {
      return new Promise((resolve) => {
        server.listen(0, '127.0.0.1', () => {
          const url = `http://127.0.0.1:${server.address().port}`;
          resolve({
            url,
            close: () => new Promise((done) => { server.closeAllConnections(); server.close(() => { db.close(); done(); }); }),
          });
        });
      });
    },
  };
}
