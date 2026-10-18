"""Recipe integration-route-db: call real routes against a real database in a temporary folder.

FastAPI's TestClient runs the app in this process through httpx: no port, no server to stop. Every test gets its own
database file from pytest's tmp_path, so tests never share state and can run in any order.
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from sample_app.app import create_app  # replace with your app factory: create_app(db_path) -> FastAPI


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.sqlite3"


@pytest.fixture
def client(db_path):
    with TestClient(create_app(db_path)) as client:
        yield client


@pytest.fixture
def signed_in(client):
    response = client.post("/api/login", json={"email": "demo@example.com", "password": "test-password"})
    assert response.status_code == 200
    return client  # the session cookie stays on this client


def test_adding_a_task_stores_it_in_the_database(signed_in, db_path):
    response = signed_in.post("/api/tasks", json={"title": "Buy milk"})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "title": "Buy milk", "done": False}
    rows = sqlite3.connect(db_path).execute("SELECT owner, title, done FROM tasks").fetchall()
    assert rows == [("demo@example.com", "Buy milk", 0)]


def test_tasks_are_listed_in_the_order_they_were_added(signed_in):
    for title in ["first", "second"]:
        signed_in.post("/api/tasks", json={"title": title})

    assert [task["title"] for task in signed_in.get("/api/tasks").json()] == ["first", "second"]


def test_an_empty_title_is_refused(signed_in):
    response = signed_in.post("/api/tasks", json={"title": "   "})

    assert response.status_code == 422
    assert signed_in.get("/api/tasks").json() == []


def test_without_signing_in_the_tasks_are_closed(client):
    assert client.get("/api/tasks").status_code == 401


def test_a_wrong_password_is_refused(client):
    response = client.post("/api/login", json={"email": "demo@example.com", "password": "wrong"})

    assert response.status_code == 401
    assert "session" not in response.cookies


def test_deleting_a_task_removes_it(signed_in):
    task = signed_in.post("/api/tasks", json={"title": "Buy milk"}).json()

    assert signed_in.delete(f"/api/tasks/{task['id']}").status_code == 204
    assert signed_in.get("/api/tasks").json() == []
    assert signed_in.delete(f"/api/tasks/{task['id']}").status_code == 404
