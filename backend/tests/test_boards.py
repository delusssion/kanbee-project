import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app
from models.board import Board

VALID_PASSWORD = 'TestPa12!'


@pytest.fixture()
def client(monkeypatch):
    import storage

    state = {
        'users_by_email': {},
        'users_by_id': {},
        'sessions': {},
        'boards': {},
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

    def delete_session(session_id):
        state['sessions'].pop(session_id, None)

    def add_password_history(user_id, pw_hash):
        state['pw_history'].setdefault(user_id, []).append(pw_hash)

    def get_password_history(user_id):
        return state['pw_history'].get(user_id, [])

    def get_boards(user_id):
        return [item['board'] for item in state['boards'].values() if item['owner'] == user_id]

    def get_board(board_id, user_id):
        item = state['boards'].get(board_id)
        if item and item['owner'] == user_id:
            return item['board']
        return None

    def create_board(user_id, name):
        position = len([b for b in state['boards'].values() if b['owner'] == user_id])
        board = Board(id=uuid4().hex, name=name, position=position)
        state['boards'][board.id] = {'owner': user_id, 'board': board}
        return board

    def rename_board(board_id, user_id, name):
        item = state['boards'].get(board_id)
        if item and item['owner'] == user_id:
            board_copy = item['board'].model_copy(update={'name': name})
            state['boards'][board_id]['board'] = board_copy
            return board_copy
        return None

    def delete_board(board_id, user_id):
        item = state['boards'].get(board_id)
        if item and item['owner'] == user_id:
            del state['boards'][board_id]
            return True
        return False

    monkeypatch.setattr(storage, 'init_db', lambda: None)
    monkeypatch.setattr(storage, 'create_user_with_email', create_user_with_email)
    monkeypatch.setattr(storage, 'get_user_by_email', get_user_by_email)
    monkeypatch.setattr(storage, 'get_user_by_id', get_user_by_id)
    monkeypatch.setattr(storage, 'create_session', create_session)
    monkeypatch.setattr(storage, 'get_session_user', get_session_user)
    monkeypatch.setattr(storage, 'delete_session', delete_session)
    monkeypatch.setattr(storage, 'add_password_history', add_password_history)
    monkeypatch.setattr(storage, 'get_password_history', get_password_history)
    monkeypatch.setattr(storage, 'create_board', create_board)
    monkeypatch.setattr(storage, 'get_boards', get_boards)
    monkeypatch.setattr(storage, 'get_board', get_board)
    monkeypatch.setattr(storage, 'rename_board', rename_board)
    monkeypatch.setattr(storage, 'delete_board', delete_board)

    with TestClient(app, base_url='https://testserver') as test_client:
        yield test_client


def test_boards_crud_and_isolation(client):
    client.post('/auth/register', json={'email': 'user1@test.com', 'password': VALID_PASSWORD})
    board1 = client.post('/boards', json={'name': 'Dev Board'})
    assert board1.status_code == 201
    assert board1.json()['name'] == 'Dev Board'
    board1_id = board1.json()['id']

    boards = client.get('/boards')
    assert boards.status_code == 200
    assert len(boards.json()) == 1

    client.post('/auth/logout')

    client.post('/auth/register', json={'email': 'user2@test.com', 'password': VALID_PASSWORD})
    boards_user2 = client.get('/boards')
    assert boards_user2.json() == []

    client.post('/auth/logout')
    client.post('/auth/login', json={'email': 'user1@test.com', 'password': VALID_PASSWORD})

    renamed = client.patch(f'/boards/{board1_id}', json={'name': 'Production Board'})
    assert renamed.status_code == 200
    assert renamed.json()['name'] == 'Production Board'

    invalid_rename = client.patch(f'/boards/{board1_id}', json={'name': '   '})
    assert invalid_rename.status_code == 400

    deleted = client.delete(f'/boards/{board1_id}')
    assert deleted.status_code == 204
    assert client.get('/boards').json() == []


def test_create_board_returns_201(client):
    client.post('/auth/register', json={'email': 'creator@test.com', 'password': VALID_PASSWORD})
    resp = client.post('/boards', json={'name': 'Test Board'})
    assert resp.status_code == 201
    data = resp.json()
    assert data['name'] == 'Test Board'
    assert 'id' in data
    assert data['position'] == 0


def test_get_empty_boards(client):
    client.post('/auth/register', json={'email': 'empty@test.com', 'password': VALID_PASSWORD})
    resp = client.get('/boards')
    assert resp.status_code == 200
    assert resp.json() == []


def test_rename_nonexistent_board(client):
    client.post('/auth/register', json={'email': 'ghost@test.com', 'password': VALID_PASSWORD})
    resp = client.patch('/boards/fake-id', json={'name': 'New'})
    assert resp.status_code == 404


def test_delete_nonexistent_board(client):
    client.post('/auth/register', json={'email': 'deleter@test.com', 'password': VALID_PASSWORD})
    resp = client.delete('/boards/fake-id')
    assert resp.status_code == 404


def test_get_board_by_id(client):
    client.post('/auth/register', json={'email': 'getter@test.com', 'password': VALID_PASSWORD})
    created = client.post('/boards', json={'name': 'My Board'})
    board_id = created.json()['id']

    resp = client.get(f'/boards/{board_id}')
    assert resp.status_code == 200
    assert resp.json()['name'] == 'My Board'

    resp404 = client.get('/boards/nonexistent-id')
    assert resp404.status_code == 404
