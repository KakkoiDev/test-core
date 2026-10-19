// The sample app's task list as pure functions: what the unit level of a scenario runs against, and what the page
// (app.js) and the server (server.js) use. The same rules as sample_app/tasks.py. Every function returns a new list.

export const EN = { count_one: '1 task', count: '{n} tasks' };

/** Trim and compose (NFC) a title, so 'か' + U+3099 is stored as 'が' (recipe japanese-text). */
export const cleanTitle = (title) => String(title ?? '').normalize('NFC').trim();

/** The cleaned title, or an error when it is empty or longer than 200 characters. */
export function validTitle(title) {
  const clean = cleanTitle(title);
  if (!clean || clean.length > 200) throw new Error('A title has 1 to 200 characters.');
  return clean;
}

export const addTask = (tasks, title) => [...tasks, { title: validTitle(title), done: false }];
export const deleteTask = (tasks, title) => tasks.filter((task) => task.title !== title);

/** '1 task', '3 tasks' (or the texts of another language: the keys count_one and count). */
export const countText = (n, texts = EN) => (n === 1 ? texts.count_one : texts.count.replace('{n}', String(n)));
