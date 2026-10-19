"""The sample app's task list as pure functions: what the unit level of a scenario runs against.

The same rules as the routes (sample_app/app.py) and the page (sample_app/static/tasks.js). A list is a tuple of task
dicts; every function returns a new tuple and never changes the one it got.
"""
from __future__ import annotations

import unicodedata

EN = {"count_one": "1 task", "count": "{n} tasks"}


def clean_title(title: str) -> str:
    """Trim and compose (NFC) a title, so 'か' + U+3099 is stored as 'が' (recipe japanese-text)."""
    return unicodedata.normalize("NFC", title).strip()


def valid_title(title: str) -> str:
    """The cleaned title, or ValueError when it is empty or longer than 200 characters."""
    title = clean_title(title)
    if not title or len(title) > 200:
        raise ValueError("A title has 1 to 200 characters.")
    return title


def add_task(tasks: tuple, title: str) -> tuple:
    return (*tasks, {"title": valid_title(title), "done": False})


def delete_task(tasks: tuple, title: str) -> tuple:
    return tuple(task for task in tasks if task["title"] != title)


def count_text(n: int, texts: dict = EN) -> str:
    """'1 task', '3 tasks' (or the texts of another language: the keys count_one and count)."""
    return texts["count_one"] if n == 1 else texts["count"].replace("{n}", str(n))
