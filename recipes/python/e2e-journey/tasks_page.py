"""A page object: one class per page, holding its locators and the actions a person takes there.

Tests read like the journey ("sign in, add a task"); when the page changes, only this file changes. Locators use roles
and labels first, visible text next, data-testid only where nothing else fits. No assertions here: tests assert.
"""
from playwright.sync_api import Locator, Page


class TasksPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.email = page.get_by_label("Email")
        self.password = page.get_by_label("Password")
        self.sign_in_button = page.get_by_role("button", name="Sign in")
        self.sign_out_button = page.get_by_role("button", name="Sign out")
        self.new_task = page.get_by_label("New task")
        self.add_button = page.get_by_role("button", name="Add")
        self.tasks = page.get_by_role("list", name="Tasks")
        self.count = page.locator("#count")
        self.error = page.get_by_role("alert")

    def open(self) -> "TasksPage":
        self.page.goto(self.base_url)
        return self

    def sign_in(self, email: str, password: str) -> None:
        self.email.fill(email)
        self.password.fill(password)
        self.sign_in_button.click()

    def add_task(self, title: str) -> None:
        self.new_task.fill(title)
        self.add_button.click()

    def task(self, title: str) -> Locator:
        return self.tasks.get_by_role("listitem").filter(has_text=title)

    def mark_done(self, title: str) -> None:
        self.task(title).get_by_role("checkbox").check()

    def delete(self, title: str) -> None:
        self.task(title).get_by_role("button", name="Delete").click()

    def sign_out(self) -> None:
        self.sign_out_button.click()
