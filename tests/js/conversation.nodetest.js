import assert from 'node:assert/strict';
import { test } from 'node:test';
import { runConversation } from '../../bench/conversation.mjs';

test('a follow-up receives the actual answer even if the earlier expectation failed', async () => {
  const snapshots = [];
  const steps = [
    ['Show a map', () => assert.fail('Wrong place')],
    ['Zoom in', (answer, prior) => assert.deepEqual([answer, prior], ['Closer view', ['A map']])],
  ];
  const result = await runConversation(steps, async history => {
    snapshots.push(history);
    return { answer: history.length === 1 ? 'A map' : 'Closer view', activity: [] };
  });
  assert.deepEqual(snapshots[1], [
    { role: 'user', text: 'Show a map' }, { role: 'assistant', text: 'A map' }, { role: 'user', text: 'Zoom in' },
  ]);
  assert.deepEqual(result.turns.map(turn => turn.status), ['fail', 'pass']);
  assert.equal(result.status, 'fail');
});

test('a missing answer stops follow-ups and retains diagnostics', async () => {
  let calls = 0;
  const result = await runConversation([['First', () => {}], ['Follow up', () => {}]], async () => {
    calls++;
    return { answer: '', activity: [{ type: 'provider-error' }] };
  });
  assert.equal(calls, 1);
  assert.equal(result.status, 'fail');
  assert.deepEqual(result.turns[0].activity, [{ type: 'provider-error' }]);
  assert.ok(result.turns[0].seconds >= 0);
});
