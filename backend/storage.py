import os
from contextlib import contextmanager
from typing import List, Optional
from uuid import uuid4

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool

from models.task import Task, TaskCreate, TaskUpdate

_pool: Optional[SimpleConnectionPool] = None

_COL = {'desc': 'description'}


def _get_pool() -> SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(1, 10, dsn=os.environ['DATABASE_URL'])
    return _pool


@contextmanager
def _conn():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def init_db():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            TEXT PRIMARY KEY,
                    username      TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id          TEXT PRIMARY KEY,
                    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title       TEXT NOT NULL,
                    description TEXT,
                    status      TEXT NOT NULL,
                    priority    TEXT NOT NULL,
                    due         TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id      TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    lang         TEXT NOT NULL DEFAULT 'en',
                    theme        TEXT NOT NULL DEFAULT 'dark',
                    default_view TEXT NOT NULL DEFAULT 'kanban'
                )
            """)


# ── Users ──────────────────────────────────────────────────────────

def create_user(username: str, password_hash: str) -> dict:
    user_id = uuid4().hex
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'INSERT INTO users (id, username, password_hash) VALUES (%s, %s, %s) RETURNING id, username',
                (user_id, username, password_hash),
            )
            return dict(cur.fetchone())


def get_user_by_username(username: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
            row = cur.fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT id, username FROM users WHERE id = %s', (user_id,))
            row = cur.fetchone()
    return dict(row) if row else None


# ── Sessions ───────────────────────────────────────────────────────

def create_session(session_id: str, user_id: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO sessions (session_id, user_id) VALUES (%s, %s)',
                (session_id, user_id),
            )


def get_session_user(session_id: str) -> Optional[str]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM sessions WHERE session_id = %s', (session_id,))
            row = cur.fetchone()
    return row[0] if row else None


def delete_session(session_id: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM sessions WHERE session_id = %s', (session_id,))


# ── Tasks ──────────────────────────────────────────────────────────

def _row_to_task(row: dict) -> Task:
    return Task(
        id=row['id'],
        title=row['title'],
        desc=row['description'],
        status=row['status'],
        priority=row['priority'],
        due=row['due'],
    )


def create_task(data: TaskCreate, user_id: str) -> Task:
    task_id = uuid4().hex
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO tasks (id, user_id, title, description, status, priority, due)
                   VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                (task_id, user_id, data.title, data.desc, data.status, data.priority, data.due),
            )
            return _row_to_task(cur.fetchone())


def get_all_tasks(user_id: str) -> List[Task]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM tasks WHERE user_id = %s ORDER BY id', (user_id,))
            return [_row_to_task(r) for r in cur.fetchall()]


def get_task(task_id: str, user_id: str) -> Optional[Task]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM tasks WHERE id = %s AND user_id = %s', (task_id, user_id))
            row = cur.fetchone()
    return _row_to_task(row) if row else None


def update_task(task_id: str, data: TaskUpdate, user_id: str) -> Optional[Task]:
    if hasattr(data, 'model_dump'):
        updates = data.model_dump(exclude_unset=True)
    else:
        updates = data.dict(exclude_unset=True)
    if not updates:
        return get_task(task_id, user_id)

    set_clause = ', '.join(f'{_COL.get(k, k)} = %s' for k in updates)
    values = list(updates.values()) + [task_id, user_id]

    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f'UPDATE tasks SET {set_clause} WHERE id = %s AND user_id = %s RETURNING *',
                values,
            )
            row = cur.fetchone()
    return _row_to_task(row) if row else None


def delete_task(task_id: str, user_id: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM tasks WHERE id = %s AND user_id = %s', (task_id, user_id))
            return cur.rowcount > 0


# ── User Settings ──────────────────────────────────────────────────

def get_or_create_user_settings(user_id: str) -> dict:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM user_settings WHERE user_id = %s', (user_id,))
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    'INSERT INTO user_settings (user_id) VALUES (%s) RETURNING *',
                    (user_id,),
                )
                row = cur.fetchone()
    return dict(row)


def update_user_settings(user_id: str, data: dict) -> dict:
    if not data:
        return get_or_create_user_settings(user_id)
    set_clause = ', '.join(f'{k} = %s' for k in data)
    values = list(data.values()) + [user_id]
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f'UPDATE user_settings SET {set_clause} WHERE user_id = %s RETURNING *',
                values,
            )
            row = cur.fetchone()
    return dict(row) if row else get_or_create_user_settings(user_id)


def get_user_by_id_full(user_id: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            row = cur.fetchone()
    return dict(row) if row else None


def update_password(user_id: str, password_hash: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE users SET password_hash = %s WHERE id = %s', (password_hash, user_id))
