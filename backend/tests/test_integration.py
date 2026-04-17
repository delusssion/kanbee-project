import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app
from models.task import Task


@pytest.fixture()
def client(monkeypatch):
    import storage

    state = {
        'users': {},
        'users_by_id': {},
        'sessions': {},
        'tasks': {},
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
