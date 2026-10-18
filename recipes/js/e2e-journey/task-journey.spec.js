// Recipe e2e-journey: a person's whole journey through the real app in a real browser, through a page object.
// Fixtures (../fixtures.js): appURL = the app on a free port with a fresh database. expect() waits on its own.
import { expect, test } from '../fixtures.js';
import { TasksPage } from './tasks-page.js';

test('a person signs in, adds, finishes and deletes a task', async ({ page, appURL }) => {
  const tasks = await new TasksPage(page, appURL).open();

  await tasks.signIn('demo@example.com', 'test-password');
  await expect(page.getByText('Signed in as demo@example.com')).toBeVisible();

  await tasks.addTask('Buy milk');
  await expect(tasks.task('Buy milk')).toBeVisible();
  await expect(tasks.count).toHaveText('1 task');

  await tasks.markDone('Buy milk');
  await expect(tasks.task('Buy milk').getByRole('checkbox')).toBeChecked();

  await tasks.delete('Buy milk');
  await expect(tasks.task('Buy milk')).toHaveCount(0);
  await expect(tasks.count).toHaveText('0 tasks');

  await tasks.signOut();
  await expect(tasks.signInButton).toBeVisible();
});

test('a wrong password shows an error', async ({ page, appURL }) => {
  const tasks = await new TasksPage(page, appURL).open();

  await tasks.signIn('demo@example.com', 'wrong-password');

  await expect(tasks.error).toHaveText('Wrong email or password.');
  await expect(tasks.newTask).toBeHidden();
});

test('a finished task stays finished after a reload', async ({ page, appURL }) => {
  const tasks = await new TasksPage(page, appURL).open();
  await tasks.signIn('demo@example.com', 'test-password');
  await tasks.addTask('Buy milk');
  await tasks.markDone('Buy milk');
  await expect(tasks.task('Buy milk').getByRole('checkbox')).toBeChecked();

  await page.reload();

  await expect(tasks.task('Buy milk').getByRole('checkbox')).toBeChecked();
});
