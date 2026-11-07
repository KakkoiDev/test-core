// The sample app every e2e recipe tests: sign in, add, finish and delete tasks, a tip from the server,
// an offline banner and English/Japanese texts. Plain ES module, no build step.
import { countText } from './tasks.js';

const TEXTS = {
  en: await (await fetch('/messages/en.json')).json(),
  ja: await (await fetch('/messages/ja.json')).json(),
};

let language = 'en';
let tasks = [];
let email = null;
const $ = (selector) => document.querySelector(selector);
const t = (key, values = {}) => TEXTS[language][key].replace(/\{(\w+)\}/g, (_, name) => values[name]);
const count = (n) => countText(n, TEXTS[language]);

async function api(method, path, body) {
  const response = await fetch(path, {
    method,
    headers: body ? { 'content-type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  return { ok: response.ok, status: response.status, data };
}

function render() {
  document.documentElement.lang = language;
  for (const element of document.querySelectorAll('[data-text]')) element.textContent = t(element.dataset.text);
  $('#sign-in').hidden = Boolean(email);
  $('#tasks').hidden = !email;
  $('#who').textContent = email ? t('signedInAs', { email }) : '';
  $('#count').textContent = count(tasks.length);
  const list = $('#task-list');
  list.replaceChildren(...tasks.map((task) => {
    const row = $('#task-row').content.firstElementChild.cloneNode(true);
    row.querySelector('.task-title').textContent = task.title;
    row.querySelector('[data-text]').textContent = t('delete');
    const done = row.querySelector('.done');
    done.checked = task.done;
    done.addEventListener('change', () => toggle(task, done.checked));
    row.querySelector('.delete').addEventListener('click', () => remove(task));
    return row;
  }));
}

async function loadTasks() {
  const result = await api('GET', '/api/tasks');
  tasks = result.ok ? result.data : [];
}

async function loadTip() {
  try {
    const result = await api('GET', '/api/tip');
    $('#tip').textContent = result.ok && result.data?.text ? result.data.text : t('tipUnavailable');
  } catch {
    $('#tip').textContent = t('tipUnavailable');
  }
}

async function signedIn(address) {
  email = address;
  await loadTasks();
  render();
  loadTip();
}

async function toggle(task, done) {
  const result = await api('PATCH', `/api/tasks/${task.id}`, { done });
  if (result.ok) task.done = result.data.done;
  render();
}

async function remove(task) {
  const result = await api('DELETE', `/api/tasks/${task.id}`);
  if (result.ok) tasks = tasks.filter((other) => other.id !== task.id);
  render();
}

$('#sign-in-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const result = await api('POST', '/api/login', { email: form.get('email'), password: form.get('password') });
  $('#sign-in-error').hidden = result.ok;
  if (result.ok) await signedIn(result.data.email);
});

$('#sign-out').addEventListener('click', async () => {
  await api('POST', '/api/logout');
  email = null;
  tasks = [];
  render();
});

$('#new-task-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = $('#title');
  const result = await api('POST', '/api/tasks', { title: input.value });
  if (result.ok) {
    tasks.push(result.data);
    input.value = '';
  }
  render();
});

$('#language').addEventListener('click', () => {
  language = language === 'en' ? 'ja' : 'en';
  render();
});

// Full screen: the Fullscreen API where it exists, otherwise the board fills the window. The same element is
// shown either way (never a copy), so what is typed in it survives, and focus returns to the opening button.
const board = $('#board');
let opener = null;
function showView(view) {
  board.dataset.view = view;
  document.body.classList.toggle('full-window-open', view === 'full-window');
  $('#fullscreen').hidden = view !== 'inline';
  $('#exit-fullscreen').hidden = view === 'inline';
  if (view === 'inline') { opener?.focus(); opener = null; } else $('#exit-fullscreen').focus();
}
$('#fullscreen').addEventListener('click', async () => {
  opener = document.activeElement;
  if (document.fullscreenEnabled && board.requestFullscreen) {
    try { await board.requestFullscreen(); return; } catch { /* refused: fall back to the window */ }
  }
  showView('full-window');
});
$('#exit-fullscreen').addEventListener('click', () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else showView('inline');
});
document.addEventListener('fullscreenchange', () => showView(document.fullscreenElement === board ? 'fullscreen' : 'inline'));
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && board.dataset.view === 'full-window') showView('inline');
});

function showConnection() {
  $('#offline').hidden = navigator.onLine;
  $('#add').disabled = !navigator.onLine;
}
window.addEventListener('online', showConnection);
window.addEventListener('offline', showConnection);

showConnection();
const me = await api('GET', '/api/me');
if (me.ok) await signedIn(me.data.email);
else render();
document.body.dataset.ready = 'true';
