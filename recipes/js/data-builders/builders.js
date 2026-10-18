// Test data builders: one function per kind of record, with good defaults and overrides.
// A test names only what it cares about: aTask({ done: true }). Defaults are valid and unique (a counter, not random).
let next = 1;

export const aUser = (overrides = {}) => {
  const n = next++;
  return { email: `user${n}@example.com`, password: 'test-password', name: `Test User ${n}`, ...overrides };
};

export const aTask = (overrides = {}) => {
  const n = next++;
  return { title: `Task ${n}`, done: false, ...overrides };
};

export const someTasks = (count, overrides = {}) => Array.from({ length: count }, () => aTask(overrides));
