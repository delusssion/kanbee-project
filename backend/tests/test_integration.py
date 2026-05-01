import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app
from models.task import Task
from models.board import Board


@pytest.fixture()
def client(monkeypatch):
    import storage

    state = {
        'users': {},
        'users_by_id': {},
        'sessions': {},
        'tasks': {},
        'boards': {},
        'user_boards': {},
        'settings': {},
    }

    def create_user(username, password_hash):
        user = {'id': uuid4().hex, 'username': username, 'password_hash': password_hash}
        state['users'][username] = user
        state['users_by_id'][user['id']] = user
        return {'id': user['id'], 'username': user['username']}

    def get_user_by_username(username):
        return state['users'].get(username)

    def get_user_by_id(user_id):
        user = state['users_by_id'].get(user_id)
        if not user:
            return None
        return {'id': user['id'], 'username': user['username']}

    def create_session(session_id, user_id):
        state['sessions'][session_id] = user_id

    def get_session_user(session_id):
        return state['sessions'].get(session_id)

    def create_task(data, user_id):
        task = Task(id=uuid4().hex, **data.model_dump())
        state['tasks'][task.id] = {'owner': user_id, 'task': task}
        return task

    def get_all_tasks(user_id):
        return [item['task'] for item in state['tasks'].values() if item['owner'] == user_id]

    def get_task(task_id, user_id):
        item = state['tasks'].get(task_id)
        return item['task'] if item and item['owner'] == user_id else None

    def update_task(task_id, data, user_id):
        task = get_task(task_id, user_id)
        if not task:
            return None
        updates = data.model_dump(exclude_unset=True)
        task = task.model_copy(update=updates)
        state['tasks'][task_id] = {'owner': user_id, 'task': task}
        return task

    def delete_task(task_id, user_id):
        if not get_task(task_id, user_id):
            return False
        del state['tasks'][task_id]
        return True

    def get_boards(user_id):
        board_ids = state['user_boards'].get(user_id, [])
        return [state['boards'][bid]['board'] for bid in board_ids if bid in state['boards']]

    def create_board(user_id, name):
        position = len([b for b in state['boards'].values() if b['owner'] == user_id])
        board = Board(id=uuid4().hex, name=name, position=position)
        state['boards'][board.id] = {'owner': user_id, 'board': board}
        state['user_boards'].setdefault(user_id, []).append(board.id)
        return board

    def rename_board(board_id, user_id, name):
        entry = state['boards'].get(board_id)
        if not entry or entry['owner'] != user_id:
            return None
        board = entry['board']
        board = board.model_copy(update={'name': name})
        state['boards'][board_id]['board'] = board
        return board

    def delete_board(board_id, user_id):
        entry = state['boards'].get(board_id)
        if not entry or entry['owner'] != user_id:
            return False
        del state['boards'][board_id]
        state['user_boards'][user_id].remove(board_id)
        return True

    def get_or_create_user_settings(user_id):
        if user_id not in state['settings']:
            state['settings'][user_id] = {
                'lang': 'en',
                'theme': 'light',
                'default_view': 'board'
            }
        return state['settings'][user_id].copy()

    def update_user_settings(user_id, updates):
        settings = get_or_create_user_settings(user_id)
        settings.update(updates)
        state['settings'][user_id] = settings
        return settings.copy()

    monkeypatch.setattr(storage, 'init_db', lambda: None)
    monkeypatch.setattr(storage, 'create_user', create_user)
    monkeypatch.setattr(storage, 'get_user_by_username', get_user_by_username)
    monkeypatch.setattr(storage, 'get_user_by_id', get_user_by_id)
    monkeypatch.setattr(storage, 'create_session', create_session)
    monkeypatch.setattr(storage, 'get_session_user', get_session_user)
    monkeypatch.setattr(storage, 'create_task', create_task)
    monkeypatch.setattr(storage, 'get_all_tasks', get_all_tasks)
    monkeypatch.setattr(storage, 'get_task', get_task)
    monkeypatch.setattr(storage, 'update_task', update_task)
    monkeypatch.setattr(storage, 'delete_task', delete_task)
    monkeypatch.setattr(storage, 'get_boards', get_boards)
    monkeypatch.setattr(storage, 'create_board', create_board)
    monkeypatch.setattr(storage, 'rename_board', rename_board)
    monkeypatch.setattr(storage, 'delete_board', delete_board)
    monkeypatch.setattr(storage, 'get_or_create_user_settings', get_or_create_user_settings)
    monkeypatch.setattr(storage, 'update_user_settings', update_user_settings)

    with TestClient(app, base_url='https://testserver') as test_client:
        yield test_client


def test_register_login_and_task_crud_flow(client):
    credentials = {'username': 'tester01', 'password': 'Password1'}

    register = client.post('/auth/register', json=credentials)
    assert register.status_code == 200
    assert register.json()['username'] == credentials['username']
    assert 'httponly' in register.headers['set-cookie'].lower()

    login = client.post('/auth/login', json=credentials)
    assert login.status_code == 200
    assert 'httponly' in login.headers['set-cookie'].lower()

    created = client.post(
        '/tasks',
        json={
            'title': '  Sprint 3 task  ',
            'desc': 'Integration coverage',
            'status': 'todo',
            'priority': 'high',
        },
    )
    assert created.status_code == 201
    task = created.json()
    assert task['title'] == 'Sprint 3 task'
    assert task['status'] == 'todo'

    tasks = client.get('/tasks')
    assert tasks.status_code == 200
    assert [item['id'] for item in tasks.json()] == [task['id']]

    updated = client.patch(
        f"/tasks/{task['id']}",
        json={'title': 'Updated task', 'status': 'inprocess', 'priority': 'medium'},
    )
    assert updated.status_code == 200
    assert updated.json()['title'] == 'Updated task'
    assert updated.json()['status'] == 'inprocess'

    deleted = client.delete(f"/tasks/{task['id']}")
    assert deleted.status_code == 204
    assert client.get('/tasks').json() == []


def test_export_and_import_tasks(client):
    credentials = {'username': 'exporter', 'password': 'Password1'}
    assert client.post('/auth/register', json=credentials).status_code == 200

    imported = client.post(
        '/tasks/import',
        json=[
            {'title': 'Imported one', 'status': 'todo', 'priority': 'low'},
            {'title': 'Imported two', 'status': 'done', 'priority': 'high'},
        ],
    )
    assert imported.status_code == 201
    assert len(imported.json()) == 2

    exported = client.get('/tasks/export')
    assert exported.status_code == 200
    assert exported.headers['content-disposition'] == 'attachment; filename="kanbee-tasks.json"'
    assert [task['title'] for task in exported.json()] == ['Imported one', 'Imported two']


@pytest.mark.parametrize(
    'payload',
    [
        {'title': '   ', 'status': 'todo', 'priority': 'low'},
        {'title': 'Task', 'status': 'blocked', 'priority': 'low'},
        {'title': 'Task', 'status': 'todo', 'priority': 'urgent'},
    ],
)
def test_task_validation_rejects_invalid_payloads(client, payload):
    credentials = {'username': uuid4().hex[:8], 'password': 'Password1'}
    assert client.post('/auth/register', json=credentials).status_code == 200

    response = client.post('/tasks', json=payload)
    assert response.status_code == 422


def test_full_board_and_task_lifecycle(client):
    creds = {'username': 'boarduser', 'password': 'Passw1'}
    assert client.post('/auth/register', json=creds).status_code == 200
    assert client.post('/auth/login', json=creds).status_code == 200

    board_resp = client.post('/boards', json={'name': 'My Board'})
    assert board_resp.status_code == 201
    board = board_resp.json()
    assert board['name'] == 'My Board'

    task_resp = client.post(
        '/tasks',
        json={
            'title': 'Board task',
            'status': 'todo',
            'priority': 'high',
            'board_id': board['id']
        }
    )
    assert task_resp.status_code == 201
    task = task_resp.json()
    assert task['board_id'] == board['id']

    moved = client.patch(
        f"/tasks/{task['id']}",
        json={'status': 'inprocess'}
    )
    assert moved.status_code == 200
    assert moved.json()['status'] == 'inprocess'

    del_resp = client.delete(f"/tasks/{task['id']}")
    assert del_resp.status_code == 204

    board_del = client.delete(f"/boards/{board['id']}")
    assert board_del.status_code == 204

    boards = client.get('/boards')
    assert boards.status_code == 200
    assert len(boards.json()) == 0


def test_board_and_task_integration_flow(client):
    credentials = {'username': 'integrator', 'password': 'Password1'}
    assert client.post('/auth/register', json=credentials).status_code == 200

    board_res = client.post('/boards', json={'name': 'Project X'})
    assert board_res.status_code == 201
    board_id = board_res.json()['id']

    task_res = client.post(
        '/tasks',
        json={
            'title': 'Setup DB',
            'status': 'todo',
            'priority': 'high',
            'board_id': board_id
        }
    )
    assert task_res.status_code == 201
    assert task_res.json()['board_id'] == board_id

    updated_res = client.patch(
        f"/tasks/{task_res.json()['id']}",
        json={'board_id': None}
    )
    assert updated_res.status_code == 200
    assert updated_res.json()['board_id'] is None


def test_boards_isolation_between_users(client):
    client.post('/auth/register', json={'username': 'userA', 'password': 'Pass1'})
    client.post('/auth/login', json={'username': 'userA', 'password': 'Pass1'})
    board_resp = client.post('/boards', json={'name': 'A Board'})
    board_id = board_resp.json()['id']

    client.post('/auth/logout')

    client.post('/auth/register', json={'username': 'userB', 'password': 'Pass2'})
    client.post('/auth/login', json={'username': 'userB', 'password': 'Pass2'})

    get_resp = client.get(f'/boards/{board_id}')
    assert get_resp.status_code == 404

    boards = client.get('/boards')
    assert len(boards.json()) == 0


def test_settings_crud_flow(client):
    creds = {'username': 'setuser', 'password': 'Pass1'}
    client.post('/auth/register', json=creds)
    client.post('/auth/login', json=creds)

    settings = client.get('/settings')
    assert settings.status_code == 200
    data = settings.json()
    assert data['theme'] == 'light'
    assert data['lang'] == 'en'

    patch = client.patch('/settings', json={'theme': 'dark'})
    assert patch.status_code == 200
    assert patch.json()['theme'] == 'dark'

    updated = client.get('/settings')
    assert updated.json()['theme'] == 'dark'

    unknown = client.patch('/settings', json={'unknown_field': 'value'})
    assert unknown.status_code == 200
    assert 'unknown_field' not in unknown.json()
