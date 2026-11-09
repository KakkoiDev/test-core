// End-to-end tests for the benchmark toolkit scenarios in bench/SCENARIOS.md (seeded prompts, report, freeze,
// launch, watch, stop). The commands run as separate processes, as a person or an agent would run them.
import { execFile, spawn } from 'node:child_process';
import { once } from 'node:events';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, watch, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { promisify } from 'node:util';
import { describe, expect, test } from 'vitest';
import { seeded } from '../../bench/seeded.mjs';

const CLI = resolve('bench/cli.mjs');
const BENCH = resolve('bench/bench.mjs');
const run = promisify(execFile);

async function cli(...args) {
  try {
    const { stdout, stderr } = await run(process.execPath, [CLI, ...args]);
    return { code: 0, stdout, stderr };
  } catch (error) {
    return { code: error.code, stdout: error.stdout, stderr: error.stderr };
  }
}

/** Resolve when `check()` is true, re-checking whenever something in `folder` changes. */
function waitForFolder(folder, check) {
  return new Promise((resolve, reject) => {
    const test = () => { try { if (check()) { watcher.close(); resolve(); } } catch (error) { watcher.close(); reject(error); } };
    const watcher = watch(folder, { recursive: true }, test);
    test();
  });
}

/** A consumer benchmark: three tasks per subject for two subjects; options choose a failure or a task that waits. */
function consumer(folder, { failCase, wait } = {}) {
  const script = join(folder, 'run-bench.mjs');
  writeFileSync(script, `
import { runBench, allGate } from ${JSON.stringify(BENCH)};
const tasks = ['alpha', 'beta'].flatMap(subject => [1, 2, 3].map(n => ({ id: subject + '-' + n, subject })));
const result = await runBench({
  dir: process.argv[2], revision: 'rev-toolkit', tasks, gate: allGate(),
  async run(task, { signal }) {
    if (${JSON.stringify(wait ?? null)} === task.id) {
      const handle = setInterval(() => {}, 1 << 30);
      console.log('waiting ' + task.id);
      await new Promise((_, reject) => signal.addEventListener('abort', () => { clearInterval(handle); reject(new Error('stopped')); }, { once: true }));
    }
    const failing = ${JSON.stringify(failCase ?? null)};
    const cases = ['first', 'second'].map((id, i) => ({ id, status: failing === task.id + '/' + id ? 'fail' : 'pass', seconds: i + 1,
      ...(failing === task.id + '/' + id ? { detail: 'synthetic failure in ' + task.id } : {}) }));
    console.log('ran ' + task.id);
    return { ok: cases.every(c => c.status === 'pass'), cases };
  },
});
console.log('done ' + result.state);
process.exitCode = result.exitCode;
`);
  return script;
}

describe('bench toolkit', () => {
  test('seeded prompts vary between keys and repeat for the same key', () => {
    const words = ['Apple', 'Banana', 'Mango', 'Pear', 'Grape', 'Kiwi'];
    const prompt = (round, subject) => {
      const choose = seeded('tally', round, subject);
      return `Count ${choose.pickDistinct(words, 3).join(', ')} with ${choose.pick(['buttons', 'keys'])}, start at ${choose.int(1, 9)}.`;
    };

    const first = Array.from({ length: 20 }, (_, round) => ['model-a', 'model-b'].map(subject => prompt(round, subject))).flat();
    const again = Array.from({ length: 20 }, (_, round) => ['model-a', 'model-b'].map(subject => prompt(round, subject))).flat();

    expect(again).toEqual(first);
    expect(new Set(first).size).toBeGreaterThan(30);
    for (const text of first) {
      const picked = text.slice(6, text.indexOf(' with')).split(', ');
      expect(new Set(picked).size).toBe(3);
    }
    expect(() => seeded('x').pickDistinct(words, 7)).toThrow(/needs 7/);
  });

  test('a report summarises each subject\'s cases, timings and failures', async () => {
    const root = mkdtempSync(join(tmpdir(), 'bench-report-'));
    const dir = join(root, 'run');
    await run(process.execPath, [consumer(root, { failCase: 'beta-2/second' }), dir]).catch(() => {});

    const text = await cli('report', dir);
    const json = JSON.parse((await cli('report', dir, '--json')).stdout);

    expect(text.code).toBe(0);
    expect(text.stdout).toContain('needs-investigation: 6/6 tasks');
    expect(text.stdout).toMatch(/alpha: 6\/6 cases · median 1\.5 s · slowest 2 s/);
    expect(text.stdout).toMatch(/beta: 5\/6 cases/);
    expect(text.stdout).toContain('FAIL beta-2 second: synthetic failure in beta-2');
    expect(json.state).toBe('needs-investigation');
    expect(json.subjects.find(s => s.subject === 'beta')).toMatchObject({ passed: 5, total: 6, failedTasks: 1,
      failures: [{ task: 'beta-2', case: 'second', detail: 'synthetic failure in beta-2' }] });
  });

  test('a flag before the run folder does not take the folder as its value', async () => {
    const root = mkdtempSync(join(tmpdir(), 'bench-flags-'));
    const dir = join(root, 'run');
    await run(process.execPath, [consumer(root), dir]);

    const reported = await cli('report', '--json', dir);
    const watched = await cli('watch', '--json', '--poll', '0.1', dir);

    expect(reported.code).toBe(0);
    expect(JSON.parse(reported.stdout)).toMatchObject({ state: 'complete', completed: 6 });
    expect(watched.code).toBe(0);
    expect(JSON.parse(watched.stdout)).toMatchObject({ state: 'complete', exitCode: 0 });
  });

  test('freezing copies one committed revision and refuses to overwrite', async () => {
    const root = mkdtempSync(join(tmpdir(), 'bench-freeze-'));
    const repo = join(root, 'repo');
    mkdirSync(join(repo, 'deps'), { recursive: true });
    writeFileSync(join(repo, 'app.js'), 'export const version = 1;\n');
    writeFileSync(join(repo, '.gitignore'), 'deps/\n');
    writeFileSync(join(repo, 'deps', 'lib.js'), 'export const dep = true;\n');
    const git = (...args) => run('git', ['-C', repo, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', ...args]);
    await git('init', '-q');
    await git('add', '-A');
    await git('commit', '-q', '-m', 'first');
    writeFileSync(join(repo, 'app.js'), 'export const version = 2; // uncommitted\n');
    const into = join(root, 'frozen');

    const first = await cli('freeze', '--repo', repo, '--revision', 'HEAD', '--into', into, '--copy', 'deps');
    const second = await cli('freeze', '--repo', repo, '--revision', 'HEAD', '--into', into);
    const unknown = await cli('freeze', '--repo', repo, '--revision', 'nope', '--into', join(root, 'other'));

    expect(first.code).toBe(0);
    expect(readFileSync(join(into, 'app.js'), 'utf8')).toBe('export const version = 1;\n');
    expect(readFileSync(join(into, 'deps', 'lib.js'), 'utf8')).toContain('dep = true');
    const frozen = JSON.parse(readFileSync(join(into, 'FROZEN.json'), 'utf8'));
    expect(frozen.revision).toMatch(/^[0-9a-f]{40}$/);
    expect(JSON.parse(first.stdout).revision).toBe(frozen.revision);
    expect(second.code).toBe(2);
    expect(second.stderr).toContain('already exists');
    expect(unknown.code).toBe(2);
    expect(unknown.stderr).toContain('Unknown revision: nope');
    expect(existsSync(join(root, 'other'))).toBe(false);
  });

  test('a detached run outlives its launcher and is watched to the end', async () => {
    const root = mkdtempSync(join(tmpdir(), 'bench-launch-'));
    const dir = join(root, 'run');
    const script = consumer(root);

    const launched = await cli('launch', '--folder', dir, '--label', 'test-core.bench.outlives', '--method', 'detached', '--cwd', root,
      '--', 'node', script, dir);
    const watched = await cli('watch', dir, '--poll', '0.1');

    expect(launched.code).toBe(0);
    expect(JSON.parse(launched.stdout)).toMatchObject({ method: 'detached', label: 'test-core.bench.outlives' });
    expect(watched.code).toBe(0);
    expect(watched.stdout).toContain('complete: 6/6 tasks');
    expect(readFileSync(join(dir, 'run.log'), 'utf8')).toContain('done complete');
  });

  test('a detached run can be stopped', async () => {
    const root = mkdtempSync(join(tmpdir(), 'bench-stop-'));
    const dir = join(root, 'run');
    const script = consumer(root, { wait: 'alpha-2' });
    await cli('launch', '--folder', dir, '--label', 'test-core.bench.stop', '--method', 'detached', '--cwd', root, '--', 'node', script, dir);
    await waitForFolder(dir, () => existsSync(join(dir, 'run.log')) && readFileSync(join(dir, 'run.log'), 'utf8').includes('waiting alpha-2'));

    const stopped = await cli('stop', dir);
    const watched = await cli('watch', dir, '--poll', '0.1');

    expect(stopped.code).toBe(0);
    expect(watched.code).toBe(130);
    expect(watched.stdout).toContain('interrupted');
    expect(existsSync(join(dir, 'run.lock'))).toBe(false);
  });

  // The launchd path exists only on macOS; the scenarios above use the portable detached path.
  test.skipIf(process.platform !== 'darwin')('on macOS a launchd job runs the benchmark and is removed by stop', async () => {
    const root = mkdtempSync(join(tmpdir(), 'bench-launchd-'));
    const dir = join(root, 'run');
    const label = `test-core.bench.launchd.${process.pid}`;
    const launched = await cli('launch', '--folder', dir, '--label', label, '--cwd', root, '--', 'node', consumer(root), dir);
    const watched = await cli('watch', dir, '--poll', '0.1');
    const stopped = await cli('stop', dir); // removes the finished job from launchd

    expect(JSON.parse(launched.stdout)).toMatchObject({ method: 'launchd', label });
    expect(watched.stdout).toContain('complete: 6/6 tasks');
    expect(stopped.code).toBe(0);
    const child = spawn('launchctl', ['print', `gui/${process.getuid()}/${label}`], { stdio: 'ignore' });
    const [code] = await once(child, 'close');
    expect(code).not.toBe(0);
  });
});
