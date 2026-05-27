import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app

VALID_PASSWORD = 'TestPa12!'


@pytest.fixture()
def client(monkeypatch):
    import storage

    state = {
        'users_by_email': {},
        'users_by_id': {},
        'sessions': {},
        'settings': {},
        'pw_history': {},
    }

    def create_user_with_email(email, password_hash):
        user_id = uuid4().hex
        base = email.split('@')[0]
        user = {'id': user_id, 'username': base, 'email': email, 'password_hash': password_hash}
        state['users_by_email'][email] = user
        state['users_by_id'][user_id] = user
        return {'id': user['id'], 'username': user['username'], 'email': user['email']}

    def get_user_by_email(email):
        return state['users_by_email'].get(email)

    def get_user_by_id(user_id):
        user = state['users_by_id'].get(user_id)
        if not user:
            return None
        return {'id': user['id'], 'username': user['username'], 'email': user['email']}

    def create_session(session_id, user_id):
        state['sessions'][session_id] = user_id

    def get_session_user(session_id):
        return state['sessions'].get(session_id)

    def add_password_history(user_id, pw_hash):
        state['pw_history'].setdefault(user_id, []).append(pw_hash)

    def get_password_history(user_id):
        return state['pw_history'].get(user_id, [])

    def get_or_create_user_settings(user_id):
        if user_id not in state['settings']:
            state['settings'][user_id] = {
                'lang': 'en',
                'theme': 'light',
                'default_view': 'kanban',
            }
        return state['settings'][user_id].copy()

    def update_user_settings(user_id, updates):
        settings = get_or_create_user_settings(user_id)
        settings.update(updates)
        state['settings'][user_id] = settings
        return settings.copy()

    monkeypatch.setattr(storage, 'init_db', lambda: None)
    monkeypatch.setattr(storage, 'create_user_with_email', create_user_with_email)
    monkeypatch.setattr(storage, 'get_user_by_email', get_user_by_email)
    monkeypatch.setattr(storage, 'get_user_by_id', get_user_by_id)
    monkeypatch.setattr(storage, 'create_session', create_session)
    monkeypatch.setattr(storage, 'get_session_user', get_session_user)
    monkeypatch.setattr(storage, 'add_password_history', add_password_history)
    monkeypatch.setattr(storage, 'get_password_history', get_password_history)
    monkeypatch.setattr(storage, 'get_or_create_user_settings', get_or_create_user_settings)
    monkeypatch.setattr(storage, 'update_user_settings', update_user_settings)

    with TestClient(app, base_url='https://testserver') as test_client:
        yield test_client


def auth(client, email='user@test.com', password=VALID_PASSWORD):
    client.post('/auth/register', json={'email': email, 'password': password})
    client.post('/auth/login', json={'email': email, 'password': password})


def test_get_settings_unauthorized(client):
    resp = client.get('/settings')
    assert resp.status_code == 401


def test_get_settings_defaults(client):
    auth(client)
    resp = client.get('/settings')
    assert resp.status_code == 200
    data = resp.json()
    assert data['lang'] == 'en'
    assert data['theme'] == 'light'
    assert data['default_view'] == 'kanban'
    assert 'user_id' not in data


def test_patch_settings_theme(client):
    auth(client)
    patch_resp = client.patch('/settings', json={'theme': 'dark'})
    assert patch_resp.status_code == 200
    assert patch_resp.json()['theme'] == 'dark'

    get_resp = client.get('/settings')
    assert get_resp.status_code == 200
    assert get_resp.json()['theme'] == 'dark'


def test_patch_unknown_field_ignored(client):
    auth(client)
    resp = client.patch('/settings', json={'unknown_field': 'ignored'})
    assert resp.status_code == 200
    data = resp.json()
    assert 'unknown_field' not in data
    assert data['theme'] == 'light'
    assert data['lang'] == 'en'
