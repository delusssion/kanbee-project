from typing import Optional
from uuid import uuid4

import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response

import storage
from auth_utils import get_current_user_id
from models.user import ChangePassword, ResetPassword, UserLogin, UserOut, UserRegister

router = APIRouter(prefix='/auth', tags=['auth'])

SESSION_COOKIE = 'kanbee_session'
MIN_USERNAME_LEN = 5
MIN_PASSWORD_LEN = 8


def _validate_username(username: str):
    if len(username) < MIN_USERNAME_LEN:
        raise HTTPException(400, f'Логин должен содержать минимум {MIN_USERNAME_LEN} символов')


def _validate_password(password: str):
    if len(password) < MIN_PASSWORD_LEN:
        raise HTTPException(400, f'Пароль должен содержать минимум {MIN_PASSWORD_LEN} символов')
    if not any(c.isalpha() for c in password):
        raise HTTPException(400, 'Пароль должен содержать хотя бы одну букву')
    if not any(c.isdigit() for c in password):
        raise HTTPException(400, 'Пароль должен содержать хотя бы одну цифру')


@router.post('/register', response_model=UserOut)
def register(payload: UserRegister, request: Request, response: Response):
    _validate_username(payload.username)
    _validate_password(payload.password)

    if storage.get_user_by_username(payload.username):
        raise HTTPException(400, 'Этот логин уже занят')

    password_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    user = storage.create_user(payload.username, password_hash)

    session_id = uuid4().hex
    storage.create_session(session_id, user['id'])
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        samesite='lax',
        httponly=True,
        secure=(request.url.scheme == 'https'),
    )

    return UserOut(id=user['id'], username=user['username'])


@router.post('/login', response_model=UserOut)
def login(payload: UserLogin, request: Request, response: Response):
    user = storage.get_user_by_username(payload.username)
    if not user or not bcrypt.checkpw(payload.password.encode(), user['password_hash'].encode()):
        raise HTTPException(401, 'Неверный логин или пароль')

    session_id = uuid4().hex
    storage.create_session(session_id, user['id'])
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        samesite='lax',
        httponly=True,
        secure=(request.url.scheme == 'https'),
    )

    return UserOut(id=user['id'], username=user['username'])


@router.post('/logout')
def logout(response: Response, kanbee_session: Optional[str] = Cookie(default=None)):
    if kanbee_session:
        storage.delete_session(kanbee_session)
    response.delete_cookie(SESSION_COOKIE)
    return {'ok': True}


@router.get('/me', response_model=UserOut)
def me(user_id: str = Depends(get_current_user_id)):
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(404)
    return UserOut(id=user['id'], username=user['username'])


@router.post('/reset-password')
def reset_password(payload: ResetPassword):
    user = storage.get_user_by_username(payload.username)
    if not user:
        raise HTTPException(400, 'Пользователь с таким логином не найден')
    _validate_password(payload.new_password)
    new_hash = bcrypt.hashpw(payload.new_password.encode(), bcrypt.gensalt()).decode()
    storage.update_password(user['id'], new_hash)
    return {'ok': True}


@router.post('/change-password')
def change_password(payload: ChangePassword, user_id: str = Depends(get_current_user_id)):
    user = storage.get_user_by_id_full(user_id)
    if not user or not bcrypt.checkpw(payload.current_password.encode(), user['password_hash'].encode()):
        raise HTTPException(400, 'Неверный текущий пароль')
    _validate_password(payload.new_password)
    new_hash = bcrypt.hashpw(payload.new_password.encode(), bcrypt.gensalt()).decode()
    storage.update_password(user_id, new_hash)
    return {'ok': True}
