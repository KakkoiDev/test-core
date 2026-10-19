// functional/js without a browser: Gherkin (the same answers as Python, from tests/fixtures/gherkin-cases.json), the
// registry, the runner, the primitives for data, network, time, database and routes, and the vocabularies.
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { afterEach, beforeEach, describe, expect, test } from 'vitest';
import {
  AmbiguousStep, Registry, StepFailed, StepNotAtLevel, UnknownStep, compilePattern, loadScenarios, matchPattern, nearest,
  parseScenarios, runScenario, shape, similarity,
} from '../../functional/js/index.js';
import * as p from '../../functional/js/primitives.js';
import { steps as blockSteps, BLOCKS } from '../../functional/blocks/js/index.js';
import { steps as taskSteps } from '../../recipes/js/scenario-steps/task-steps.js';
import { createApp } from '../../sample_app/server.js';

const json = (path) => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));
const CASES = json('../fixtures/gherkin-cases.json');

const TASK = `## Scenarios

### US-7 Add two tasks
Given an empty list
When I add the task "Buy milk"
And I add the task "牛乳"
Then the list has 2 tasks

### Scenario: The old form
- Given an empty list
- Then the list has 0 tasks

## Notes
### Not a scenario
Given nothing
`;

function registry(log) {
  const steps = new Registry();
  steps.step('Given an empty list', (world) => { log.push('given'); world.tasks = []; }, { level: 'unit' });
  steps.step('When I add the task {title}', (world, { title }) => { log.push(title); world.tasks.push(title); }, { level: 'unit' });
  steps.step('Then the list has {n} tasks', (world, { n }) => {
    log.push(n);
    if (world.tasks.length !== n) throw new Error(`${world.tasks.length} tasks`);
  }, { level: 'unit' });
  return steps;
}

describe('gherkin', () => {
  test('headings with a story id, without one and with Scenario:', () => {
    const scenarios = parseScenarios(TASK, 't.md');
    expect(scenarios.map((s) => [s.id, s.title, s.name])).toEqual([
      ['US-7', 'Add two tasks', 'US-7 Add two tasks'], [null, 'The old form', 'The old form']]);
    expect(scenarios[0].steps.map((s) => s.full)).toEqual(['Given an empty list', 'When I add the task "Buy milk"',
      'When I add the task "牛乳"', 'Then the list has 2 tasks']);
    expect(scenarios[0].steps[2]).toMatchObject({ keyword: 'And', kind: 'When', line: 6 });
  });

  test.each(CASES.matches)('values of $step', ({ pattern, step, values }) => {
    expect(matchPattern(compilePattern(pattern), step)).toEqual(values);
  });

  test.each(CASES.nearest)('nearest to $step (as in Python)', ({ step, nearest: expected }) => {
    expect(nearest(step, CASES.patterns)).toEqual(expected);
  });

  test('patterns, shape and similarity', () => {
    expect(() => compilePattern('I add {x}')).toThrow('starts with Given');
    expect(() => compilePattern('When I move {x} to {x}')).toThrow('twice');
    expect(() => parseScenarios('## Scenarios\n### A\nAnd nothing\n')).toThrow('needs a Given');
    expect(shape('When I add the task "Buy milk"')).toBe('when i add the task {}');
    expect(similarity('When I add the task {t}', 'When I add the task "x"')).toBe(1);
  });
});

describe('registry', () => {
  test('one function per level, unknown steps get the nearest', () => {
    const steps = registry([]);
    steps.step('When I add the task {title}', () => 'e2e', { level: 'e2e' });
    expect(steps.find('When I add the task milk', 'e2e').definition.levels).toEqual(['e2e']);
    expect(() => steps.find('When I add task Buy milk', 'unit')).toThrow(UnknownStep);
    expect(() => steps.find('When I add task Buy milk', 'unit')).toThrow(/Nearest known steps:\n {2}- When I add the task \{title\}/);
    expect(() => steps.find('Given an empty list', 'e2e')).toThrow(StepNotAtLevel);
    expect(() => steps.step('Given an empty list', () => {}, { level: 'unit' })).toThrow('already registered at unit');
    expect(() => steps.step('Then x', () => {}, { level: 'browser' })).toThrow('level must be among');
    steps.step('Then the list has {n} {what}', () => {});
    expect(() => steps.find('Then the list has 2 tasks', 'unit')).toThrow(AmbiguousStep);
  });

  test('registries compose, and match their vocabulary', () => {
    const block = new Registry({ block: 'LogIn' });
    block.step('When I press Log In', () => {}, { level: 'e2e' });
    const both = new Registry(registry([]), block);
    expect(both.find('When I press Log In', 'e2e').definition.block).toBe('LogIn');
    const vocabulary = both.vocabulary('x');
    expect(vocabulary.steps.at(-1)).toEqual({ step: 'When I press Log In', levels: ['e2e'], block: 'LogIn' });
    expect(both.checkVocabulary(vocabulary)).toEqual([]);
    expect(both.checkVocabulary({ steps: [{ step: 'When I delete {x}' }] })).toContain("no function for the step 'When I delete {x}'");
  });

  test('the generated blocks and the task steps are their vocabularies', () => {
    expect(blockSteps.checkVocabulary(json('../../functional/blocks/vocabulary.json'))).toEqual([]);
    expect(taskSteps.checkVocabulary(json('../../recipes/shared/task-example.vocab.json'))).toEqual([]);
    expect(Object.keys(BLOCKS).sort()).toEqual(['BarChart', 'DataTable', 'EditForm', 'EmptyState', 'KpiTile', 'LogIn', 'SidePanel', 'Toasts']);
  });
});

describe('runner', () => {
  test('runs steps in order and resolves to the world', async () => {
    const log = [];
    const [scenario] = parseScenarios(TASK);
    const world = await runScenario(scenario, { level: 'unit', registry: registry(log), world: { extra: 1 } });
    expect(log).toEqual(['given', 'Buy milk', '牛乳', 2]);
    expect(world).toMatchObject({ level: 'unit', scenario: 'US-7 Add two tasks', extra: 1 });
  });

  test('an unknown step fails before the first step runs; a failing step names itself', async () => {
    const log = [];
    const [bad] = parseScenarios(TASK.replace('And I add the task "牛乳"', 'And I add task "牛乳"'), 't.md');
    await expect(runScenario(bad, { level: 'unit', registry: registry(log) })).rejects.toThrow(/t\.md:6: scenario "US-7 Add two tasks": unknown step/);
    expect(log).toEqual([]);
    const [wrong] = parseScenarios(TASK.replace('2 tasks', '3 tasks'), 't.md');
    await expect(runScenario(wrong, { level: 'unit', registry: registry([]) })).rejects.toThrow(StepFailed);
    await expect(runScenario(wrong, { level: 'unit', registry: registry([]) })).rejects.toThrow('step "Then the list has 3 tasks" failed: 2 tasks');
  });

  test('loadScenarios reads a file or a file URL and needs scenarios', () => {
    expect(loadScenarios(new URL('../../recipes/shared/task-example.md', import.meta.url)).map((s) => s.name))
      .toEqual(['Add a task', 'Delete a task', 'An empty title is not added']);
    const folder = mkdtempSync(join(tmpdir(), 'test-core-'));
    writeFileSync(join(folder, 't.md'), '# nothing\n');
    expect(() => loadScenarios(join(folder, 't.md'))).toThrow('no scenarios');
    rmSync(folder, { recursive: true, force: true });
  });
});

describe('primitives without a browser', () => {
  let folder;
  beforeEach(() => { folder = mkdtempSync(join(tmpdir(), 'test-core-')); });
  afterEach(() => rmSync(folder, { recursive: true, force: true }));

  test('builder', () => {
    const aTask = p.builder({ title: 'Task {n}', done: false, id: (n) => n * 10 });
    expect(aTask()).toEqual({ title: 'Task 1', done: false, id: 10 });
    expect(aTask({ done: true })).toEqual({ title: 'Task 2', done: true, id: 20 });
  });

  test('reading plain values', async () => {
    expect(await p.seenText('  1\n task ')).toBe('1 task');
    await p.expectText('3 tasks', 'tasks');
    await p.expectText('3 tasks', '3 tasks', { exact: true });
    await p.expectNoText('3 tasks', 'milk');
    await p.expectCount([1, 2], 2);
    await expect(p.expectText('3 tasks', 'milk')).rejects.toThrow('expected to see "milk"');
    await expect(p.expectCount([], 1)).rejects.toThrow('expected 1 item');
  });

  test('stubNetwork answers from the table and fails on anything else', async () => {
    const fetch = await p.stubNetwork({
      'GET /api/tip': { json: { text: 'Write the test first' } },
      'POST /api/tasks': () => ({ status: 201, json: { title: 'Buy milk' } }),
      '/api/broken': { status: 500, body: 'down' },
    });
    expect(await (await fetch('/api/tip')).json()).toEqual({ text: 'Write the test first' });
    expect((await fetch('/api/tasks', { method: 'POST' })).status).toBe(201);
    const broken = await fetch('/api/broken', { method: 'DELETE' });
    expect([broken.status, await broken.text()]).toEqual([500, 'down']);
    await expect(fetch('/api/other')).rejects.toThrow('no stub for GET http://stub.test/api/other');
    expect(p.routeMatches('POST /api/*', 'post', 'http://x/api/tasks')).toBe(true);
  });

  test('freezeTime', async () => {
    const clock = await p.freezeTime('2026-10-19T09:00:00');
    expect(clock.now().toISOString()).toBe('2026-10-19T09:00:00.000Z');
    expect(clock.advance(26 * 3600 * 1000).toISOString()).toBe('2026-10-20T11:00:00.000Z');
  });

  test('tempDatabase and httpClient against the app on port 0', async () => {
    const path = await p.tempDatabase(folder, 'CREATE TABLE notes (title TEXT);');
    const db = new DatabaseSync(path);
    expect(db.prepare('SELECT count(*) AS n FROM notes').get().n).toBe(0);
    db.close();
    await expect(p.tempDatabase(folder)).rejects.toThrow('exists');
    const app = await createApp({ dbPath: await p.tempDatabase(folder, '', 'app.sqlite3') }).start();
    try {
      const client = p.httpClient(app.url);
      expect((await client.get('/api/tasks')).status).toBe(401);
      expect((await client.post('/api/login', { email: 'demo@example.com', password: 'test-password' })).ok).toBe(true);
      expect((await client.post('/api/tasks', { title: ' Buy milk ' })).json.title).toBe('Buy milk');
      expect((await client.post('/api/tasks', { title: '' })).status).toBe(422);
    } finally {
      await app.close();
    }
  });

  test('describeControl', () => {
    expect(p.describeControl({ role: 'button', name: 'Log In' })).toBe('button "Log In"');
    expect(p.describeControl({ label: 'Email' })).toBe('field labelled "Email"');
  });
});
