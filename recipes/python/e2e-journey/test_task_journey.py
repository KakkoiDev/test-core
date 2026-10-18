"""Recipe e2e-journey: a person's whole journey through the real app in a real browser, through a page object.

Fixtures (recipes/python/conftest.py): `page` from pytest-playwright, `app_url` = the app on a free port with a fresh
database. Every expect() waits for the state on its own: no sleeps.
"""
from playwright.sync_api import expect

from tasks_page import TasksPage


def test_a_person_signs_in_adds_finishes_and_deletes_a_task(page, app_url):
    tasks = TasksPage(page, app_url).open()

    tasks.sign_in("demo@example.com", "test-password")
    expect(page.get_by_text("Signed in as demo@example.com")).to_be_visible()

    tasks.add_task("Buy milk")
    expect(tasks.task("Buy milk")).to_be_visible()
    expect(tasks.count).to_have_text("1 task")

    tasks.mark_done("Buy milk")
    expect(tasks.task("Buy milk").get_by_role("checkbox")).to_be_checked()

    tasks.delete("Buy milk")
    expect(tasks.task("Buy milk")).to_have_count(0)
    expect(tasks.count).to_have_text("0 tasks")

    tasks.sign_out()
    expect(tasks.sign_in_button).to_be_visible()


def test_a_wrong_password_shows_an_error(page, app_url):
    tasks = TasksPage(page, app_url).open()

    tasks.sign_in("demo@example.com", "wrong-password")

    expect(tasks.error).to_have_text("Wrong email or password.")
    expect(tasks.new_task).to_be_hidden()


def test_a_finished_task_stays_finished_after_a_reload(page, app_url):
    tasks = TasksPage(page, app_url).open()
    tasks.sign_in("demo@example.com", "test-password")
    tasks.add_task("Buy milk")
    tasks.mark_done("Buy milk")
    expect(tasks.task("Buy milk").get_by_role("checkbox")).to_be_checked()

    page.reload()

    expect(tasks.task("Buy milk").get_by_role("checkbox")).to_be_checked()
