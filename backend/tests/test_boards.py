import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app
from models.board import Board


@pytest.fixture()
def client(monkeypatch):
    import storage

    state = {
        'users': {},
        'users_by_id': {},
        'sessions': {},
        'boards': {},
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

    def get_boards(user_id):
        return [item['board'] for item in state['boards'].values() if item['owner'] == user_id]

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
    monkeypatch.setattr(storage, 'create_user', create_user)
    monkeypatch.setattr(storage, 'get_user_by_username', get_user_by_username)
    monkeypatch.setattr(storage, 'get_user_by_id', get_user_by_id)
    monkeypatch.setattr(storage, 'create_session', create_session)
    monkeypatch.setattr(storage, 'get_session_user', get_session_user)
    monkeypatch.setattr(storage, 'create_board', create_board)
    monkeypatch.setattr(storage, 'get_boards', get_boards)
    monkeypatch.setattr(storage, 'rename_board', rename_board)
    monkeypatch.setattr(storage, 'delete_board', delete_board)

    with TestClient(app, base_url='https://testserver') as test_client:
        yield test_client


def test_boards_crud_and_isolation(client):
    client.post('/auth/register', json={'username': 'user1', 'password': 'Pass1'})
    board1 = client.post('/boards', json={'name': 'Dev Board'})
    assert board1.status_code == 201
    assert board1.json()['name'] == 'Dev Board'
    board1_id = board1.json()['id']

    boards = client.get('/boards')
    assert boards.status_code == 200
    assert len(boards.json()) == 1

    client.post('/auth/logout')

    client.post('/auth/register', json={'username': 'user2', 'password': 'Pass2'})
    boards_user2 = client.get('/boards')
    assert boards_user2.json() == []

    client.post('/auth/logout')
    client.post('/auth/login', json={'username': 'user1', 'password': 'Pass1'})

    renamed = client.patch(f'/boards/{board1_id}', json={'name': 'Production Board'})
    assert renamed.status_code == 200
    assert renamed.json()['name'] == 'Production Board'

    invalid_rename = client.patch(f'/boards/{board1_id}', json={'name': '   '})
    assert invalid_rename.status_code == 400

    deleted = client.delete(f'/boards/{board1_id}')
    assert deleted.status_code == 204
    assert client.get('/boards').json() == []


def test_create_board_returns_201(client):
    client.post('/auth/register', json={'username': 'creator', 'password': 'Pass1'})
    resp = client.post('/boards', json={'name': 'Test Board'})
    assert resp.status_code == 201
    data = resp.json()
    assert data['name'] == 'Test Board'
    assert 'id' in data
    assert data['position'] == 0


def test_get_empty_boards(client):
    client.post('/auth/register', json={'username': 'empty', 'password': 'Pass1'})
    resp = client.get('/boards')
    assert resp.status_code == 200
    assert resp.json() == []


def test_rename_nonexistent_board(client):
    client.post('/auth/register', json={'username': 'ghost', 'password': 'Pass1'})
    resp = client.patch('/boards/fake-id', json={'name': 'New'})
    assert resp.status_code == 404


def test_delete_nonexistent_board(client):
    client.post('/auth/register', json={'username': 'deleter', 'password': 'Pass1'})
    resp = client.delete('/boards/fake-id')
    assert resp.status_code == 404
    
