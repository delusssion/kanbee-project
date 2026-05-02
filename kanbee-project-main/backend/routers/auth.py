import hashlib
import os
import re
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from typing import Optional
from uuid import uuid4

import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response

import storage
from auth_utils import get_current_user_id
from models.user import (ChangePassword, ConfirmPasswordReset, RequestPasswordReset,
                          UserLogin, UserOut, UserRegister, VerifyResetCode)

router = APIRouter(prefix='/auth', tags=['auth'])

SESSION_COOKIE = 'kanbee_session'
RESET_CODE_TTL_MINUTES = 15
RESET_RATE_LIMIT_SECONDS = 120
MAX_RESET_ATTEMPTS = 5

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'kanbee.service@gmail.com'
_SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def _validate_email(email: str):
    if not _EMAIL_RE.match(email):
        raise HTTPException(400, 'Некорректный email адрес')


def _validate_password(password: str):
    if len(password) <= 8:
        raise HTTPException(400, 'Пароль должен быть длиннее 8 символов')
    if not any(c.isalpha() for c in password):
        raise HTTPException(400, 'Пароль должен содержать хотя бы одну букву')
    if sum(1 for c in password if c.isdigit()) < 2:
        raise HTTPException(400, 'Пароль должен содержать минимум 2 цифры')
    if not any(not c.isalnum() for c in password):
        raise HTTPException(400, 'Пароль должен содержать минимум 1 специальный символ')


def _pw_history_hash(password: str, user_id: str) -> str:
    return hashlib.sha256(f'{password}:{user_id}'.encode()).hexdigest()


def _was_password_used(user_id: str, password: str) -> bool:
    return _pw_history_hash(password, user_id) in storage.get_password_history(user_id)


def _send_reset_email(to_email: str, code: str):
    if not _SMTP_PASSWORD:
        print(f'[DEV] Reset code for {to_email}: {code}')
        return
    msg = MIMEText(
        f'Ваш код для восстановления пароля KanBee: {code}\n\n'
        f'Код действителен {RESET_CODE_TTL_MINUTES} минут.\n'
        f'Если вы не запрашивали сброс пароля — проигнорируйте это письмо.',
        'plain', 'utf-8',
    )
    msg['Subject'] = 'KanBee — Код восстановления пароля'
    msg['From'] = f'KanBee <{SMTP_USER}>'
    msg['To'] = to_email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SMTP_USER, _SMTP_PASSWORD)
            smtp.sendmail(SMTP_USER, [to_email], msg.as_string())
    except Exception as exc:
        print(f'[EMAIL ERROR] {exc}')
        raise HTTPException(500, 'Не удалось отправить письмо. Попробуйте позже.')


@router.post('/register', response_model=UserOut)
def register(payload: UserRegister, request: Request, response: Response):
    _validate_email(payload.email)
    _validate_password(payload.password)

    if storage.get_user_by_email(payload.email):
        raise HTTPException(400, 'Этот email уже зарегистрирован')

    pw_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    user = storage.create_user_with_email(payload.email, pw_hash)
    storage.add_password_history(user['id'], _pw_history_hash(payload.password, user['id']))

    session_id = uuid4().hex
    storage.create_session(session_id, user['id'])
    response.set_cookie(
        SESSION_COOKIE, session_id, samesite='lax', httponly=True,
        secure=(request.url.scheme == 'https'),
    )
    return UserOut(id=user['id'], username=user['username'], email=user['email'])


@router.post('/login', response_model=UserOut)
def login(payload: UserLogin, request: Request, response: Response):
    user = storage.get_user_by_email(payload.email)
    if not user or not bcrypt.checkpw(payload.password.encode(), user['password_hash'].encode()):
        raise HTTPException(401, 'Неверный email или пароль')

    session_id = uuid4().hex
    storage.create_session(session_id, user['id'])
    response.set_cookie(
        SESSION_COOKIE, session_id, samesite='lax', httponly=True,
        secure=(request.url.scheme == 'https'),
    )
    return UserOut(id=user['id'], username=user['username'], email=user['email'])


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
    return UserOut(id=user['id'], username=user['username'], email=user.get('email') or '')


@router.post('/request-reset')
def request_reset(payload: RequestPasswordReset):
    _validate_email(payload.email)
    if storage.has_recent_reset_code(payload.email, RESET_RATE_LIMIT_SECONDS):
        raise HTTPException(429, 'Подождите 2 минуты перед повторной отправкой кода')
    user = storage.get_user_by_email(payload.email)
    if user:
        code = f'{secrets.randbelow(1_000_000):06d}'
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_CODE_TTL_MINUTES)
        code_id = storage.create_reset_code(payload.email, code, expires_at)
        try:
            _send_reset_email(payload.email, code)
        except HTTPException:
            storage.delete_reset_code(code_id)
            raise
    return {'ok': True}


@router.post('/verify-reset')
def verify_reset(payload: VerifyResetCode):
    code_row = storage.get_active_reset_code(payload.email)
    if not code_row:
        raise HTTPException(400, 'Неверный или истёкший код')
    if code_row['attempts'] >= MAX_RESET_ATTEMPTS:
        raise HTTPException(400, 'Превышено количество попыток. Запросите новый код')
    if code_row['code'] != payload.code:
        new_attempts = storage.increment_reset_attempts(code_row['id'])
        if new_attempts >= MAX_RESET_ATTEMPTS:
            storage.mark_reset_code_used(code_row['id'])
            raise HTTPException(400, 'Превышено количество попыток. Запросите новый код')
        raise HTTPException(400, 'Неверный или истёкший код')
    return {'ok': True}


@router.post('/confirm-reset')
def confirm_reset(payload: ConfirmPasswordReset):
    code_row = storage.get_active_reset_code(payload.email)
    if not code_row:
        raise HTTPException(400, 'Неверный или истёкший код')
    if code_row['attempts'] >= MAX_RESET_ATTEMPTS:
        raise HTTPException(400, 'Превышено количество попыток. Запросите новый код')
    if code_row['code'] != payload.code:
        new_attempts = storage.increment_reset_attempts(code_row['id'])
        if new_attempts >= MAX_RESET_ATTEMPTS:
            storage.mark_reset_code_used(code_row['id'])
            raise HTTPException(400, 'Превышено количество попыток. Запросите новый код')
        raise HTTPException(400, 'Неверный или истёкший код')

    user = storage.get_user_by_email(payload.email)
    if not user:
        raise HTTPException(400, 'Пользователь не найден')

    _validate_password(payload.new_password)

    if _was_password_used(user['id'], payload.new_password):
        raise HTTPException(400, 'Нельзя использовать пароль, который уже использовался ранее')

    new_hash = bcrypt.hashpw(payload.new_password.encode(), bcrypt.gensalt()).decode()
    storage.update_password(user['id'], new_hash)
    storage.add_password_history(user['id'], _pw_history_hash(payload.new_password, user['id']))
    storage.mark_reset_code_used(code_row['id'])
    return {'ok': True}


@router.post('/change-password')
def change_password(payload: ChangePassword, user_id: str = Depends(get_current_user_id)):
    user = storage.get_user_by_id_full(user_id)
    if not user or not bcrypt.checkpw(payload.current_password.encode(), user['password_hash'].encode()):
        raise HTTPException(400, 'Неверный текущий пароль')

    _validate_password(payload.new_password)

    if _was_password_used(user_id, payload.new_password):
        raise HTTPException(400, 'Нельзя использовать пароль, который уже использовался ранее')

    new_hash = bcrypt.hashpw(payload.new_password.encode(), bcrypt.gensalt()).decode()
    storage.update_password(user_id, new_hash)
    storage.add_password_history(user_id, _pw_history_hash(payload.new_password, user_id))
    return {'ok': True}
