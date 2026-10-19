"""The sample app in Python (FastAPI + sqlite3): the same API as sample_app/server.js, serving sample_app/static.

create_app(db_path) builds a fresh app on its own database file, so every test can have its own (recipe
integration-route-db). Test users are passed in; the default is one obvious test account.
"""
from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from sample_app.tasks import clean_title, valid_title  # noqa: F401  (clean_title: recipe japanese-text)

STATIC = Path(__file__).resolve().parent / "static"
TEST_USERS = {"demo@example.com": "test-password"}
TIP = "Write the test first, watch it fail, then make it pass."


class Login(BaseModel):
    email: str
    password: str


class NewTask(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    done: bool


def create_app(db_path: str | Path, users: dict[str, str] | None = None) -> FastAPI:
    users = TEST_USERS if users is None else users
    sessions: dict[str, str] = {}
    db = sqlite3.connect(db_path, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL,"
               " done INTEGER NOT NULL DEFAULT 0)")
    db.commit()
    app = FastAPI()

    def owner(session: str | None) -> str:
        if session not in sessions:
            raise HTTPException(401, "Sign in first.")
        return sessions[session]

    def task_json(row: sqlite3.Row) -> dict:
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

    @app.post("/api/login")
    def login(body: Login, response: Response):
        if users.get(body.email) != body.password:
            return JSONResponse({"error": "Wrong email or password."}, status_code=401)
        token = secrets.token_urlsafe(16)
        sessions[token] = body.email
        response.set_cookie("session", token, httponly=True, samesite="lax")
        return {"email": body.email}

    @app.post("/api/logout")
    def logout(response: Response, session: str | None = Cookie(None)):
        sessions.pop(session, None)
        response.delete_cookie("session")
        return {"ok": True}

    @app.get("/api/me")
    def me(session: str | None = Cookie(None)):
        return {"email": owner(session)}

    @app.get("/api/tasks")
    def list_tasks(session: str | None = Cookie(None)):
        rows = db.execute("SELECT * FROM tasks WHERE owner = ? ORDER BY id", (owner(session),)).fetchall()
        return [task_json(row) for row in rows]

    @app.post("/api/tasks", status_code=201)
    def add_task(body: NewTask, session: str | None = Cookie(None)):
        email = owner(session)
        try:
            title = valid_title(body.title)
        except ValueError as error:
            return JSONResponse({"error": str(error)}, status_code=422)
        cursor = db.execute("INSERT INTO tasks (owner, title) VALUES (?, ?)", (email, title))
        db.commit()
        return task_json(db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone())

    @app.patch("/api/tasks/{task_id}")
    def update_task(task_id: int, body: TaskUpdate, session: str | None = Cookie(None)):
        email = owner(session)
        db.execute("UPDATE tasks SET done = ? WHERE id = ? AND owner = ?", (int(body.done), task_id, email))
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id = ? AND owner = ?", (task_id, email)).fetchone()
        if row is None:
            raise HTTPException(404, "No such task.")
        return task_json(row)

    @app.delete("/api/tasks/{task_id}", status_code=204)
    def delete_task(task_id: int, session: str | None = Cookie(None)):
        cursor = db.execute("DELETE FROM tasks WHERE id = ? AND owner = ?", (task_id, owner(session)))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "No such task.")
        return Response(status_code=204)

    @app.get("/api/tip")
    def tip():
        return {"text": TIP}

    app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
    app.state.db = db
    return app
