"""Recipe data-builders: the builders' own tests, and a builder used to arrange an integration test."""
from fastapi.testclient import TestClient

from builders import build_task, build_tasks, build_user
from sample_app.app import create_app


def test_defaults_are_valid_and_unique():
    first, second = build_task(), build_task()

    assert first["done"] is False
    assert first["title"] != second["title"]


def test_overrides_name_only_what_the_test_cares_about():
    task = build_task(done=True)

    assert task["done"] is True
    assert task["title"].startswith("Task ")


def test_build_tasks_makes_many():
    assert [task["done"] for task in build_tasks(3, done=True)] == [True, True, True]


def test_a_builder_arranges_an_integration_test(tmp_path):
    user = build_user()
    app = create_app(tmp_path / "test.sqlite3", users={user["email"]: user["password"]})
    with TestClient(app) as client:
        client.post("/api/login", json={"email": user["email"], "password": user["password"]})
        for task in build_tasks(2):
            client.post("/api/tasks", json={"title": task["title"]})

        assert len(client.get("/api/tasks").json()) == 2
