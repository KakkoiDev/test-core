// A page object: one class per page, holding its locators and the actions a person takes there.
// Tests read like the journey; when the page changes, only this file changes. Roles and labels first, visible text
// next, data-testid only where nothing else fits. No assertions here: tests assert.
export class TasksPage {
  constructor(page, baseURL) {
    this.page = page;
    this.baseURL = baseURL;
    this.email = page.getByLabel('Email');
    this.password = page.getByLabel('Password');
    this.signInButton = page.getByRole('button', { name: 'Sign in' });
    this.signOutButton = page.getByRole('button', { name: 'Sign out' });
    this.newTask = page.getByLabel('New task');
    this.addButton = page.getByRole('button', { name: 'Add' });
    this.tasks = page.getByRole('list', { name: 'Tasks' });
    this.count = page.locator('#count');
    this.error = page.getByRole('alert');
  }

  async open() {
    await this.page.goto(this.baseURL);
    return this;
  }

  async signIn(email, password) {
    await this.email.fill(email);
    await this.password.fill(password);
    await this.signInButton.click();
  }

  async addTask(title) {
    await this.newTask.fill(title);
    await this.addButton.click();
  }

  task(title) {
    return this.tasks.getByRole('listitem').filter({ hasText: title });
  }

  async markDone(title) {
    await this.task(title).getByRole('checkbox').check();
  }

  async delete(title) {
    await this.task(title).getByRole('button', { name: 'Delete' }).click();
  }

  async signOut() {
    await this.signOutButton.click();
  }
}
