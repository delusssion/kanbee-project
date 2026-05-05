import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
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
                CREATE TABLE IF NOT EXISTS boards (
                    id       TEXT PRIMARY KEY,
                    user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name     TEXT NOT NULL,
                    position INT  NOT NULL DEFAULT 0
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id          TEXT PRIMARY KEY,
                    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    board_id    TEXT REFERENCES boards(id) ON DELETE CASCADE,
                    title       TEXT NOT NULL,
                    description TEXT,
                    status      TEXT NOT NULL,
                    priority    TEXT NOT NULL,
                    due         TEXT
                )
            """)
            cur.execute("""
                ALTER TABLE tasks ADD COLUMN IF NOT EXISTS board_id TEXT REFERENCES boards(id) ON DELETE CASCADE
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id      TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    lang         TEXT NOT NULL DEFAULT 'en',
                    theme        TEXT NOT NULL DEFAULT 'dark',
                    default_view TEXT NOT NULL DEFAULT 'kanban'
                )
            """)
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT UNIQUE")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_codes (
                    id         TEXT PRIMARY KEY,
                    email      TEXT NOT NULL,
                    code       TEXT NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    used       BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS password_history (
                    id         TEXT PRIMARY KEY,
                    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    pw_hash    TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("""
                ALTER TABLE password_reset_codes ADD COLUMN IF NOT EXISTS
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """)
            cur.execute("""
                ALTER TABLE password_reset_codes ADD COLUMN IF NOT EXISTS
                    attempts INT NOT NULL DEFAULT 0
            """)
    _migrate_orphan_tasks()


def _migrate_orphan_tasks():
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT DISTINCT user_id FROM tasks WHERE board_id IS NULL")
            rows = cur.fetchall()
            for row in rows:
                uid = row['user_id']
                board_id = uuid4().hex
                cur.execute(
                    "INSERT INTO boards (id, user_id, name, position) VALUES (%s, %s, %s, 0)",
                    (board_id, uid, 'My Board'),
                )
                cur.execute(
                    "UPDATE tasks SET board_id = %s WHERE user_id = %s AND board_id IS NULL",
                    (board_id, uid),
                )


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
            cur.execute('SELECT id, username, email FROM users WHERE id = %s', (user_id,))
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


# ── Boards ─────────────────────────────────────────────────────────

def create_board(user_id: str, name: str) -> dict:
    board_id = uuid4().hex
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT COALESCE(MAX(position)+1, 0) AS pos FROM boards WHERE user_id = %s",
                (user_id,),
            )
            pos = cur.fetchone()['pos']
            cur.execute(
                "INSERT INTO boards (id, user_id, name, position) VALUES (%s, %s, %s, %s) RETURNING *",
                (board_id, user_id, name.strip(), pos),
            )
            return dict(cur.fetchone())


def get_boards(user_id: str) -> list:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM boards WHERE user_id = %s ORDER BY position, id",
                (user_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def get_board(board_id: str, user_id: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM boards WHERE id = %s AND user_id = %s",
                (board_id, user_id),
            )
            row = cur.fetchone()
    return dict(row) if row else None


def rename_board(board_id: str, user_id: str, name: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "UPDATE boards SET name = %s WHERE id = %s AND user_id = %s RETURNING *",
                (name.strip(), board_id, user_id),
            )
            row = cur.fetchone()
    return dict(row) if row else None


def delete_board(board_id: str, user_id: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM boards WHERE id = %s AND user_id = %s",
                (board_id, user_id),
            )
            return cur.rowcount > 0


# ── Tasks ──────────────────────────────────────────────────────────

def _row_to_task(row: dict) -> Task:
    return Task(
        id=row['id'],
        title=row['title'],
        desc=row['description'],
        status=row['status'],
        priority=row['priority'],
        due=row['due'],
        board_id=row.get('board_id'),
    )


def create_task(data: TaskCreate, user_id: str) -> Task:
    task_id = uuid4().hex
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO tasks (id, user_id, board_id, title, description, status, priority, due)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                (task_id, user_id, data.board_id, data.title, data.desc, data.status, data.priority, data.due),
            )
            return _row_to_task(cur.fetchone())


def get_all_tasks(user_id: str, board_id: Optional[str] = None) -> List[Task]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if board_id:
                cur.execute(
                    'SELECT * FROM tasks WHERE user_id = %s AND board_id = %s ORDER BY id',
                    (user_id, board_id),
                )
            else:
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


def update_username(user_id: str, username: str) -> dict:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'UPDATE users SET username = %s WHERE id = %s RETURNING id, username, email',
                (username, user_id),
            )
            row = cur.fetchone()
    return dict(row)


# ── Email auth ─────────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            row = cur.fetchone()
    return dict(row) if row else None


def create_user_with_email(email: str, password_hash: str) -> dict:
    user_id = uuid4().hex
    base = email.split('@')[0]
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT 1 FROM users WHERE username = %s', (base,))
            username = base if not cur.fetchone() else f'{base}_{user_id[:6]}'
            cur.execute(
                'INSERT INTO users (id, username, email, password_hash) VALUES (%s, %s, %s, %s)'
                ' RETURNING id, username, email',
                (user_id, username, email, password_hash),
            )
            return dict(cur.fetchone())


# ── Password reset codes ───────────────────────────────────────────

def create_reset_code(email: str, code: str, expires_at) -> str:
    code_id = uuid4().hex
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE password_reset_codes SET used = TRUE WHERE email = %s AND used = FALSE',
                (email,),
            )
            cur.execute(
                'INSERT INTO password_reset_codes (id, email, code, expires_at) VALUES (%s, %s, %s, %s)',
                (code_id, email, code, expires_at),
            )
    return code_id


def has_recent_reset_code(email: str, within_seconds: int) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT 1 FROM password_reset_codes WHERE email = %s AND created_at > %s LIMIT 1',
                (email, cutoff),
            )
            return cur.fetchone() is not None


def get_active_reset_code(email: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'SELECT * FROM password_reset_codes'
                ' WHERE email = %s AND used = FALSE AND expires_at > NOW()'
                ' ORDER BY created_at DESC LIMIT 1',
                (email,),
            )
            row = cur.fetchone()
    return dict(row) if row else None


def increment_reset_attempts(code_id: str) -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE password_reset_codes SET attempts = attempts + 1 WHERE id = %s RETURNING attempts',
                (code_id,),
            )
            row = cur.fetchone()
    return row[0] if row else 0


def delete_reset_code(code_id: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM password_reset_codes WHERE id = %s', (code_id,))


def mark_reset_code_used(code_id: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE password_reset_codes SET used = TRUE WHERE id = %s', (code_id,))


# ── Password history ───────────────────────────────────────────────

def add_password_history(user_id: str, pw_hash: str):
    history_id = uuid4().hex
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO password_history (id, user_id, pw_hash) VALUES (%s, %s, %s)',
                (history_id, user_id, pw_hash),
            )


def get_password_history(user_id: str) -> list:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT pw_hash FROM password_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 10',
                (user_id,),
            )
            return [row[0] for row in cur.fetchall()]
