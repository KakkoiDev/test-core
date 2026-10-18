"""Test data builders: one function per kind of record, with good defaults and keyword overrides.

A test names only what it cares about: build_task(done=True). Everything else gets a valid, unique default, so
records never collide and a new required field is added in one place. Copy this file and add your own builders.
"""
from __future__ import annotations

import itertools

_ids = itertools.count(1)


def build_user(**overrides) -> dict:
    n = next(_ids)
    return {"email": f"user{n}@example.com", "password": "test-password", "name": f"Test User {n}", **overrides}


def build_task(**overrides) -> dict:
    n = next(_ids)
    return {"title": f"Task {n}", "done": False, **overrides}


def build_tasks(count: int, **overrides) -> list[dict]:
    return [build_task(**overrides) for _ in range(count)]
