"""functional/primitives.py without a browser: data, network, time, database, routes, and reading plain values."""
import sqlite3
from datetime import datetime, timezone

import pytest

from functional import primitives as p
from sample_app.app import create_app


def test_builder_gives_valid_unique_records_with_overrides():
    build_task = p.builder(title="Task {n}", done=False, id=lambda n: n * 10)
    assert build_task() == {"title": "Task 1", "done": False, "id": 10}
    assert build_task(done=True) == {"title": "Task 2", "done": True, "id": 20}
    assert p.builder(title="Task {n}")()["title"] == "Task 1"  # each builder counts on its own


def test_reading_plain_values_responses_and_collections():
    assert p.seen_text("  1\n task ") == "1 task"
    assert p.seen_text({"a": "牛乳"}) == '{"a": "牛乳"}'
    p.expect_text("3 tasks", "tasks")
    p.expect_text("3 tasks", "3 tasks", exact=True)
    p.expect_no_text("3 tasks", "milk")
    p.expect_count((1, 2), 2)
    with pytest.raises(AssertionError, match="expected to see 'milk'"):
        p.expect_text("3 tasks", "milk")
    with pytest.raises(AssertionError, match="expected 1 item"):
        p.expect_count([], 1)


def test_stub_network_answers_from_the_table_and_fails_on_anything_else():
    client = p.stub_network({"GET /api/tip": {"json": {"text": "Write the test first"}},
                             "POST /api/tasks": lambda request: {"status": 201, "json": {"title": "Buy milk"}},
                             "/api/broken": {"status": 500, "body": "down"}})
    assert client.get("/api/tip").json() == {"text": "Write the test first"}
    assert client.post("/api/tasks", json={"title": "Buy milk"}).status_code == 201
    response = client.delete("/api/broken")
    assert (response.status_code, p.seen_text(response)) == (500, "down")
    with pytest.raises(AssertionError, match="no stub for GET http://stub.test/api/other"):
        client.get("/api/other")
    with pytest.raises(AssertionError, match="no stub for DELETE"):
        client.delete("/api/tip")


def test_freeze_time_stops_and_moves_only_when_asked():
    clock = p.freeze_time("2026-10-19T09:00:00")
    assert clock.now() == clock() == datetime(2026, 10, 19, 9, tzinfo=timezone.utc)
    assert clock.advance(days=1, hours=2) == datetime(2026, 10, 20, 11, tzinfo=timezone.utc)
    assert clock.now().isoformat() == "2026-10-20T11:00:00+00:00"


def test_temp_database_is_fresh_with_its_schema(tmp_path):
    path = p.temp_database(tmp_path, "CREATE TABLE tasks (title TEXT);")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM tasks").fetchone() == (0,)
    with pytest.raises(FileExistsError):
        p.temp_database(tmp_path)


def test_http_client_calls_the_routes_in_process(tmp_path):
    client = p.http_client(create_app(p.temp_database(tmp_path)))
    assert client.get("/api/tasks").status_code == 401
    assert client.post("/api/login", json={"email": "demo@example.com", "password": "test-password"}).status_code == 200
    assert client.post("/api/tasks", json={"title": " Buy milk "}).json()["title"] == "Buy milk"
    assert client.post("/api/tasks", json={"title": ""}).status_code == 422


def test_describe_control():
    assert p.describe_control(role="button", name="Log In") == 'button "Log In"'
    assert p.describe_control(label="Email") == 'field labelled "Email"'
    assert p.describe_control(test_id="save") == "element [data-testid=save]"
    assert p.describe_control(css="#x") == "element #x"
