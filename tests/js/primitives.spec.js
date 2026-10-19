// functional/js/primitives.js in a browser: find, act, read, stub the network, freeze time, loud missing controls.
import { expect, test } from '../../recipes/js/fixtures.js';
import * as p from '../../functional/js/primitives.js';

const FORM = `<form><label for="email">Email</label><input id="email" aria-describedby="email-help" aria-invalid="true">
<p id="email-help">Enter an email like name@example.com.</p>
<label><input type="checkbox" name="r"> Remember me</label>
<select aria-label="Subject"><option value="v">Vocabulary</option><option value="g">Grammar</option></select>
<button type="button" aria-busy="true" onclick="this.textContent='Saved'">Save</button>
<p data-testid="out" hidden>secret</p><canvas role="img" aria-label="Orders per day: Saturday is busiest"></canvas></form>`;

test('control finds by role, label, text, test id and css', async ({ page }) => {
  await page.setContent(FORM);
  expect(await (await p.control(page, { role: 'button', name: 'Save' })).count()).toBe(1);
  expect(await (await p.control(page, { label: 'Email' })).count()).toBe(1);
  expect(await (await p.control(page, { text: 'Remember me' })).count()).toBe(1);
  expect(await (await p.control(page, { testId: 'out' })).count()).toBe(1);
  expect(await (await p.control(page, { css: 'canvas' })).count()).toBe(1);
});

test('a missing control fails loudly', async ({ page }) => {
  await page.setContent(FORM);
  await expect(p.control(page, { role: 'button', name: 'Delete', block: 'Form', timeout: 200 }))
    .rejects.toThrow('Form: uses a control that no longer exists: button "Delete"');
  await expect(p.control(page, { label: 'Password', timeout: 200 })).rejects.toThrow(p.ControlMissing);
});

test('act and read', async ({ page }) => {
  await page.setContent(FORM);
  const email = await p.control(page, { label: 'Email' });
  await p.fill(email, 'aiko@example.com');
  await p.expectValue(email, 'aiko@example.com');
  const box = await p.control(page, { role: 'checkbox', name: 'Remember me' });
  await p.check(box);
  await p.expectChecked(box);
  await p.uncheck(box);
  await p.expectChecked(box, false);
  const subject = await p.control(page, { role: 'combobox', name: 'Subject' });
  await p.select(subject, 'Grammar');
  await p.expectValue(subject, 'g');
  await p.press(email, 'End');
  const save = await p.control(page, { role: 'button' });
  await p.expectAttribute(save, 'aria-busy', 'true');
  await p.click(save);
  await p.expectText(page, 'Saved');
  await p.expectText(save, 'Saved', { exact: true });
  await p.expectNoText(page, 'secret');
  await p.expectHidden(await p.control(page, { testId: 'out' }));
  await p.expectVisible(await p.control(page, { role: 'img' }));
  await p.expectName(await p.control(page, { role: 'img' }), 'Saturday is busiest');
  await p.expectDescription(email, 'name@example.com');
  await p.expectCount(page.getByRole('checkbox'), 1);
  expect(await p.seenText(save)).toBe('Saved');
});

test('stubNetwork in the page and freezeTime', async ({ page, appURL }) => {
  await p.stubNetwork({ 'GET /api/tip': { json: { text: 'A stubbed tip' } } }, { page });
  await p.freezeTime('2026-10-19T09:00:00', { page });
  await p.goto(page, appURL);
  expect(await page.evaluate(() => new Date().toISOString())).toBe('2026-10-19T09:00:00.000Z');
  expect(await page.evaluate(() => fetch('/api/tip').then((r) => r.json()))).toEqual({ text: 'A stubbed tip' });
  expect(await page.evaluate(() => fetch('/api/me').then((r) => r.status))).toBe(401);
});
