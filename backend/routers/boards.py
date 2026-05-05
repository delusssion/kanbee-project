from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response

import storage
from auth_utils import get_current_user_id
from models.board import Board, BoardCreate, BoardRename

router = APIRouter(prefix='/boards', tags=['boards'])


@router.get('', response_model=List[Board])
def get_boards(user_id: str = Depends(get_current_user_id)):
    return storage.get_boards(user_id)


@router.get('/{board_id}', response_model=Board)
def get_board(board_id: str, user_id: str = Depends(get_current_user_id)):
    board = storage.get_board(board_id, user_id)
    if not board:
        raise HTTPException(404, 'Board not found')
    return board


@router.post('', response_model=Board, status_code=201)
def create_board(payload: BoardCreate, user_id: str = Depends(get_current_user_id)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(400, 'Board name must not be empty')
    return storage.create_board(user_id, name)


@router.patch('/{board_id}', response_model=Board)
def rename_board(board_id: str, payload: BoardRename, user_id: str = Depends(get_current_user_id)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(400, 'Board name must not be empty')
    board = storage.rename_board(board_id, user_id, name)
    if not board:
        raise HTTPException(404, 'Board not found')
    return board


@router.delete('/{board_id}', status_code=204)
def delete_board(board_id: str, user_id: str = Depends(get_current_user_id)):
    deleted = storage.delete_board(board_id, user_id)
    if not deleted:
        raise HTTPException(404, 'Board not found')
    return Response(status_code=204)
