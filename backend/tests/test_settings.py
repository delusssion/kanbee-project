import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app


@pytest.fixture()
def client(monkeypatch):
    import storage

    state = {
        'users': {},
        'users_by_id': {},
        'sessions': {},
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
    monkeypatch.setattr(storage, 'get_or_create_user_settings', get_or_create_user_settings)
    monkeypatch.setattr(storage, 'update_user_settings', update_user_settings)

    with TestClient(app, base_url='https://testserver') as test_client:
        yield test_client


def auth(client, username='user', password='Pass1'):
    client.post('/auth/register', json={'username': username, 'password': password})
    client.post('/auth/login', json={'username': username, 'password': password})


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
    assert data['default_view'] == 'board'
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
