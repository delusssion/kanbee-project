import os
from contextlib import contextmanager
from typing import List, Optional
from uuid import uuid4

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool

from models.task import Task, TaskCreate, TaskUpdate

_pool: Optional[SimpleConnectionPool] = None

# Map Pydantic field names → DB column names
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
                CREATE TABLE IF NOT EXISTS tasks (
                    id          TEXT PRIMARY KEY,
                    title       TEXT NOT NULL,
                    description TEXT,
                    status      TEXT NOT NULL,
                    priority    TEXT NOT NULL,
                    due         TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    session_id   TEXT PRIMARY KEY,
                    lang         TEXT NOT NULL DEFAULT 'en',
                    theme        TEXT NOT NULL DEFAULT 'light',
                    default_view TEXT NOT NULL DEFAULT 'kanban',
                    user_name    TEXT
                )
            """)


def _row_to_task(row: dict) -> Task:
    return Task(
        id=row['id'],
        title=row['title'],
        desc=row['description'],
        status=row['status'],
        priority=row['priority'],
        due=row['due'],
    )


def create_task(data: TaskCreate) -> Task:
    task_id = uuid4().hex
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO tasks (id, title, description, status, priority, due)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING *""",
                (task_id, data.title, data.desc, data.status, data.priority, data.due),
            )
            row = cur.fetchone()
    return _row_to_task(row)


def get_all_tasks() -> List[Task]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM tasks ORDER BY id')
            rows = cur.fetchall()
    return [_row_to_task(r) for r in rows]


def get_task(task_id: str) -> Optional[Task]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
            row = cur.fetchone()
    return _row_to_task(row) if row else None


def update_task(task_id: str, data: TaskUpdate) -> Optional[Task]:
    updates = data.dict(exclude_unset=True)
    if not updates:
        return get_task(task_id)

    set_clause = ', '.join(f'{_COL.get(k, k)} = %s' for k in updates)
    values = list(updates.values()) + [task_id]

    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f'UPDATE tasks SET {set_clause} WHERE id = %s RETURNING *',
                values,
            )
            row = cur.fetchone()
    return _row_to_task(row) if row else None


def delete_task(task_id: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
            return cur.rowcount > 0


# ── Settings ───────────────────────────────────────────────────────

def get_or_create_settings(session_id: str) -> dict:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM settings WHERE session_id = %s', (session_id,))
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    """INSERT INTO settings (session_id) VALUES (%s)
                       RETURNING *""",
                    (session_id,),
                )
                row = cur.fetchone()
    return dict(row)


def update_settings(session_id: str, data: dict) -> dict:
    if not data:
        return get_or_create_settings(session_id)
    set_clause = ', '.join(f'{k} = %s' for k in data)
    values = list(data.values()) + [session_id]
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f'UPDATE settings SET {set_clause} WHERE session_id = %s RETURNING *',
                values,
            )
            row = cur.fetchone()
    return dict(row) if row else get_or_create_settings(session_id)
