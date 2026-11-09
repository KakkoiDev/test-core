// End-to-end tests for bench/SCENARIOS.md: one test per scenario, named after its title. Each test runs a fresh
// consumer program in a temporary folder, so locks, signals and resume cross a real process boundary.
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtempSync, readFileSync, readdirSync, writeFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { createInterface } from 'node:readline';
import { describe, expect, test } from 'vitest';

const BENCH = resolve('bench/bench.mjs');

// The consumer: a plan built from a JSON config, and a task body whose behaviour the config chooses.
const CONSUMER = `
import { runBench, streakGate, rateGate } from ${JSON.stringify(BENCH)};
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
const config = JSON.parse(process.argv[2]);
let running = 0;
let started = 0;
let release;
const barrier = new Promise(done => { release = done; });
const groups = new Map();
const attempts = new Map();
const yieldTurn = () => new Promise(done => setImmediate(done));
const tasks = config.rate
  ? Object.keys(config.rate).map(id => ({ id }))
  : config.flat
    ? Array.from({ length: config.flat }, (_, i) => ({ id: 't' + i, ...(config.groups?.includes('t' + i) ? { group: 'local-model' } : {}) }))
    : Array.from({ length: config.rounds + 1 }, (_, r) => config.subjects.map(subject => ({ id: 'r' + (r + 1) + '-' + subject, round: r + 1, subject }))).flat();
try {
  const result = await runBench({
    dir: config.dir, revision: 'rev-test', resume: Boolean(config.resume), tasks,
    gate: config.rate ? rateGate({ threshold: 0.51 }) : config.flat ? undefined : streakGate({ required: config.rounds, regression: 1 }),
    concurrency: config.concurrency ?? 1, timeoutMs: config.timeoutMs, retries: config.retries,
    budget: config.capUsd ? { capUsd: config.capUsd, estimate: () => 1 } : undefined,
    exclusive: task => task.group,
    freeze: config.freeze, secrets: config.secrets, config: config.config,
    async run(task, { signal, taskDir }) {
      console.log('ran ' + task.id);
      if (config.block?.includes(task.id)) {
        // A real task holds a handle (a child process, a socket); this one holds an idle interval until aborted.
        const handle = setInterval(() => {}, 1 << 30);
        console.log('started ' + task.id);
        await new Promise((_, reject) => signal.addEventListener('abort', () => { clearInterval(handle); reject(new Error('aborted')); }, { once: true }));
      }
      if (config.rate) return { ok: true, outcome: config.rate[task.id] };
      attempts.set(task.id, (attempts.get(task.id) ?? 0) + 1);
      if (config.infraFailures?.[task.id] >= attempts.get(task.id)) return { ok: false, infra: true, error: 'HTTP 503' };
      running++;
      const group = task.group;
      const overlap = group ? (groups.get(group) ?? 0) > 0 : false;
      if (group) groups.set(group, (groups.get(group) ?? 0) + 1);
      const seen = running;
      // The first wave waits until config.barrier tasks run at once, so overlap is certain, not timing-dependent.
      if (running >= (config.barrier ?? Infinity)) release();
      if (started++ < (config.barrier ?? 0)) await barrier;
      for (let i = 0; i < 5; i++) await yieldTurn();
      running--;
      if (group) groups.set(group, groups.get(group) - 1);
      if (config.secretTask === task.id) writeFileSync(join(taskDir, 'reply.json'), JSON.stringify({ reply: config.secrets[0] }));
      if (config.fail?.includes(task.id)) return { ok: false, checks: { passed: 1, expected: 2 }, detail: 'synthetic failure' };
      return { ok: true, checks: { passed: 2, expected: 2 }, running: seen, overlap, ...(config.capUsd ? { costUsd: 1 } : {}) };
    },
  });
  console.log('RESULT ' + JSON.stringify(result));
  process.exitCode = result.exitCode;
} catch (error) {
  console.log('REFUSED ' + error.message);
  process.exitCode = 3;
}
`;

function workspace() {
  const root = mkdtempSync(join(tmpdir(), 'bench-'));
  writeFileSync(join(root, 'consumer.mjs'), CONSUMER);
  return root;
}

/** Start the consumer; `lines` collects its output, `waitFor(text)` resolves when a line contains the text. */
function start(root, config) {
  const child = spawn(process.execPath, [join(root, 'consumer.mjs'), JSON.stringify(config)], { cwd: root });
  const lines = [];
  const waiting = [];
  createInterface({ input: child.stdout }).on('line', line => {
    lines.push(line);
    for (const w of waiting.filter(w => line.includes(w.text))) w.resolve(line);
  });
  child.stderr.resume();
  // 'close' fires after the process exits and its output streams end, so every line has been read.
  const finished = once(child, 'close').then(([code, signal]) =>
    ({ code, signal, lines, result: JSON.parse(lines.find(l => l.startsWith('RESULT '))?.slice(7) ?? 'null') }));
  const waitFor = text => lines.find(l => l.includes(text)) ?? new Promise(done => waiting.push({ text, resolve: done }));
  return { child, lines, finished, waitFor };
}

const run = (root, config) => start(root, config).finished;
const json = path => JSON.parse(readFileSync(path, 'utf8'));
const ran = lines => lines.filter(l => l.startsWith('ran ')).map(l => l.slice(4));

describe('bench runner', () => {
  test('a streak run passes every round and the regression round', async () => {
    const root = workspace();
    const dir = join(root, 'report');

    const { code, result } = await run(root, { dir, rounds: 3, subjects: ['alpha', 'beta'] });

    expect(code).toBe(0);
    expect(result.state).toBe('stable-and-regression-passed');
    expect(result.summary.checks).toEqual({ passed: 16, expected: 16 });
    expect(result.summary.rounds.map(r => [r.round, r.regression, r.perfect])).toEqual([[1, false, true], [2, false, true], [3, false, true], [4, true, true]]);
    const records = readdirSync(join(dir, 'tasks')).filter(f => f.endsWith('.json')).map(f => json(join(dir, 'tasks', f)));
    expect(records).toHaveLength(8);
    for (const record of records) {
      expect(record.revision).toBe('rev-test');
      expect(typeof record.seconds).toBe('number');
      expect(record.ok).toBe(true);
    }
    expect(json(join(dir, 'state.json')).state).toBe('stable-and-regression-passed');
    expect(existsSync(join(dir, 'run.lock'))).toBe(false);
  });

  test('a failed round stops the run and keeps its reports', async () => {
    const root = workspace();
    const dir = join(root, 'report');

    const { code, result, lines } = await run(root, { dir, rounds: 3, subjects: ['alpha', 'beta'], fail: ['r2-beta'] });

    expect(code).toBe(1);
    expect(result.state).toBe('needs-investigation');
    expect(result.summary.failedRound).toBe(2);
    expect(ran(lines)).toEqual(['r1-alpha', 'r1-beta', 'r2-alpha', 'r2-beta']);
    const failed = json(join(dir, 'tasks', 'r2-beta.json'));
    expect(failed.ok).toBe(false);
    expect(failed.result.detail).toBe('synthetic failure');
    expect(typeof failed.seconds).toBe('number');
  });

  test('only one runner works in a report folder and a stale lock is reclaimed', async () => {
    const root = workspace();
    const dir = join(root, 'report');
    const first = start(root, { dir, rounds: 1, subjects: ['alpha'], block: ['r1-alpha'] });
    await first.waitFor('started r1-alpha');

    const second = await run(root, { dir, rounds: 1, subjects: ['alpha'], resume: true });
    first.child.kill('SIGKILL');
    await first.finished;
    const later = await run(root, { dir, rounds: 1, subjects: ['alpha'], resume: true });

    expect(second.code).toBe(3);
    expect(second.lines.join('\n')).toContain(`Run already active (PID ${first.child.pid})`);
    expect(ran(second.lines)).toEqual([]);
    expect(later.code).toBe(0);
    expect(later.result.state).toBe('stable-and-regression-passed');
  });

  test('an interrupted run resumes from its checkpoints without repeating finished tasks', async () => {
    const root = workspace();
    const dir = join(root, 'report');
    const first = start(root, { dir, rounds: 1, subjects: ['alpha', 'beta'], block: ['r1-beta'] });
    await first.waitFor('started r1-beta');

    first.child.kill('SIGINT');
    const interrupted = await first.finished;
    const unfinishedCheckpoint = existsSync(join(dir, 'tasks', 'r1-beta.json'));
    const resumed = await run(root, { dir, rounds: 1, subjects: ['alpha', 'beta'], resume: true });

    expect(interrupted.code).toBe(130);
    expect(interrupted.result.state).toBe('interrupted');
    expect(unfinishedCheckpoint).toBe(false);
    expect(ran(resumed.lines)).toEqual(['r1-beta', 'r2-alpha', 'r2-beta']);
    expect(resumed.result.state).toBe('stable-and-regression-passed');
  });

  test('a resume refuses when a frozen file changed', async () => {
    const root = workspace();
    const dir = join(root, 'report');
    writeFileSync(join(root, 'engine.js'), 'export const depth = 4;\n');
    const freeze = { root, files: ['engine.js'] };
    const first = start(root, { dir, rounds: 1, subjects: ['alpha'], block: ['r1-alpha'], freeze });
    await first.waitFor('started r1-alpha');
    first.child.kill('SIGINT');
    await first.finished;

    writeFileSync(join(root, 'engine.js'), 'export const depth = 5;\n');
    const resumed = await run(root, { dir, rounds: 1, subjects: ['alpha'], resume: true, freeze });

    expect(resumed.code).toBe(3);
    expect(resumed.lines.join('\n')).toContain('Frozen file changed: engine.js');
    expect(ran(resumed.lines)).toEqual([]);
  });

  test('a resume refuses when the list of frozen files changed', async () => {
    const root = workspace();
    const dir = join(root, 'report');
    writeFileSync(join(root, 'engine.js'), 'export const depth = 4;\n');
    writeFileSync(join(root, 'book.js'), 'export const openings = [];\n');
    const first = start(root, { dir, rounds: 1, subjects: ['alpha'], block: ['r1-alpha'], freeze: { root, files: ['engine.js'] } });
    await first.waitFor('started r1-alpha');
    first.child.kill('SIGINT');
    await first.finished;

    const resumed = await run(root, { dir, rounds: 1, subjects: ['alpha'], resume: true, freeze: { root, files: ['engine.js', 'book.js'] } });

    expect(resumed.code).toBe(3);
    expect(resumed.lines.join('\n')).toContain('Frozen file added: book.js');
    expect(ran(resumed.lines)).toEqual([]);
  });

  test('a resume refuses when the host config changed', async () => {
    const root = workspace();
    const dir = join(root, 'report');
    const first = start(root, { dir, rounds: 1, subjects: ['alpha'], block: ['r1-alpha'], config: { temperature: 0 } });
    await first.waitFor('started r1-alpha');
    first.child.kill('SIGINT');
    await first.finished;

    const resumed = await run(root, { dir, rounds: 1, subjects: ['alpha'], resume: true, config: { temperature: 0.7 } });

    expect(resumed.code).toBe(3);
    expect(resumed.lines.join('\n')).toContain('The config changed since the run started');
    expect(ran(resumed.lines)).toEqual([]);
  });

  test('a finished report folder is never reused', async () => {
    const root = workspace();
    const dir = join(root, 'report');
    await run(root, { dir, rounds: 1, subjects: ['alpha'] });
    const before = readFileSync(join(dir, 'state.json'), 'utf8');

    const fresh = await run(root, { dir, rounds: 1, subjects: ['alpha'] });
    const resumed = await run(root, { dir, rounds: 1, subjects: ['alpha'], resume: true });

    expect(fresh.code).toBe(3);
    expect(fresh.lines.join('\n')).toContain('already holds a run');
    expect(resumed.code).toBe(3);
    expect(resumed.lines.join('\n')).toContain('finished');
    expect(ran([...fresh.lines, ...resumed.lines])).toEqual([]);
    expect(readFileSync(join(dir, 'state.json'), 'utf8')).toBe(before);
  });

  test('a secret written into a report fails the run', async () => {
    const root = workspace();
    const dir = join(root, 'report');
    const secret = 'sk-synthetic-0123456789abcdef';

    const { code, result } = await run(root, { dir, rounds: 1, subjects: ['alpha'], secrets: [secret], secretTask: 'r1-alpha' });

    expect(code).toBe(2);
    expect(result.state).toBe('secret-leak');
    expect(result.summary.leaks).toEqual([{ file: 'tasks/r1-alpha/reply.json', secret: 0 }]);
    expect(readFileSync(join(dir, 'state.json'), 'utf8')).not.toContain(secret);
  });

  test('a win-rate run reports its score with a confidence interval', async () => {
    const root = workspace();
    const strong = Object.fromEntries(Array.from({ length: 200 }, (_, i) => ['g' + i, i < 150 ? 'win' : i < 170 ? 'draw' : 'loss']));
    const even = Object.fromEntries(Array.from({ length: 200 }, (_, i) => ['g' + i, i < 100 ? 'win' : 'loss']));

    const above = await run(root, { dir: join(root, 'strong'), rate: strong, concurrency: 4 });
    const unclear = await run(root, { dir: join(root, 'even'), rate: even, concurrency: 4 });

    expect(above.result.state).toBe('above-threshold');
    expect(above.code).toBe(0);
    expect(above.result.summary).toMatchObject({ games: 200, wins: 150, draws: 20, losses: 30, score: 0.8 });
    expect(above.result.summary.interval[0]).toBeGreaterThan(0.51);
    expect(above.result.summary.interval[0]).toBeLessThan(0.8);
    expect(unclear.result.state).toBe('inconclusive');
    expect(unclear.code).toBe(1);
    expect(unclear.result.summary.interval[0]).toBeLessThan(0.51);
    expect(unclear.result.summary.interval[1]).toBeGreaterThan(0.51);
  });

  test('a task that runs past its time limit is recorded as a timeout and the run goes on', async () => {
    const root = workspace();
    const dir = join(root, 'report');

    const { code, result, lines } = await run(root, { dir, flat: 3, block: ['t1'], timeoutMs: 1000 });

    expect(code).toBe(1);
    expect(result.state).toBe('needs-investigation');
    expect(result.summary.failed).toEqual(['t1']);
    expect(json(join(dir, 'tasks', 't1.json'))).toMatchObject({ ok: false, result: { ok: false, error: 'timeout' } });
    expect(ran(lines)).toEqual(['t0', 't1', 't2']);
  });

  test('an infrastructure failure is retried a bounded number of times before it counts', async () => {
    const root = workspace();
    const dir = join(root, 'report');

    const { code, result, lines } = await run(root, { dir, flat: 3, retries: 1, infraFailures: { t0: 1, t1: 2 } });

    expect(code).toBe(1);
    expect(result.state).toBe('needs-investigation');
    expect(result.summary.failed).toEqual(['t1']);
    expect(json(join(dir, 'tasks', 't0.json'))).toMatchObject({ ok: true, attempts: 2 });
    expect(json(join(dir, 'tasks', 't1.json'))).toMatchObject({ ok: false, attempts: 2, result: { infra: true, error: 'HTTP 503' } });
    expect(ran(lines)).toEqual(['t0', 't0', 't1', 't1', 't2']);
  });

  test('a run stops before a task that would pass the spending cap and resumes under a higher cap', async () => {
    const root = workspace();
    const dir = join(root, 'report');

    const capped = await run(root, { dir, flat: 4, capUsd: 2.5 });
    const state = json(join(dir, 'state.json'));
    const raised = await run(root, { dir, flat: 4, capUsd: 10, resume: true });

    expect(capped.code).toBe(1);
    expect(capped.result.state).toBe('budget-reached');
    expect(ran(capped.lines)).toEqual(['t0', 't1']);
    expect(state).toMatchObject({ state: 'budget-reached', spentUsd: 2, capUsd: 2.5 });
    expect(raised.result.state).toBe('complete');
    expect(ran(raised.lines)).toEqual(['t2', 't3']);
    expect(json(join(dir, 'state.json'))).toMatchObject({ spentUsd: 4, capUsd: 10 });
  });

  test('a run that reached its spending cap can still be interrupted while a task is in flight', async () => {
    const root = workspace();
    const dir = join(root, 'report');
    const first = start(root, { dir, flat: 3, concurrency: 2, block: ['t0'], capUsd: 1.5 });
    await first.waitFor('started t0');

    first.child.kill('SIGINT');
    const interrupted = await first.finished;

    expect(interrupted.code).toBe(130);
    expect(interrupted.result.state).toBe('interrupted');
    expect(ran(interrupted.lines)).toEqual(['t0']);
  });

  test('parallel tasks respect the limit and exclusive groups', async () => {
    const root = workspace();
    const dir = join(root, 'report');

    const { code, result } = await run(root, { dir, flat: 6, concurrency: 3, groups: ['t0', 't1'], barrier: 3 });

    const records = readdirSync(join(dir, 'tasks')).filter(f => f.endsWith('.json')).map(f => json(join(dir, 'tasks', f)));
    expect(code).toBe(0);
    expect(result.state).toBe('complete');
    expect(records).toHaveLength(6);
    expect(Math.max(...records.map(r => r.result.running))).toBe(3);
    expect(records.every(r => r.result.running <= 3)).toBe(true);
    expect(records.filter(r => ['t0', 't1'].includes(r.id)).every(r => r.result.overlap === false)).toBe(true);
  });
});
