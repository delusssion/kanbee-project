from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

import storage

router = APIRouter(prefix='/settings', tags=['settings'])

SESSION_COOKIE = 'kanbee_session'


class SettingsUpdate(BaseModel):
    lang: Optional[str] = None
    theme: Optional[str] = None
    default_view: Optional[str] = None
    user_name: Optional[str] = None


def _ensure_session(response: Response, session_id: Optional[str]) -> str:
    if not session_id:
        session_id = uuid4().hex
        response.set_cookie(SESSION_COOKIE, session_id, samesite='lax', httponly=False)
    return session_id


@router.get('')
def get_settings(
    response: Response,
    kanbee_session: Optional[str] = Cookie(default=None),
):
    session_id = _ensure_session(response, kanbee_session)
    data = storage.get_or_create_settings(session_id)
    data.pop('session_id', None)
    return data


@router.patch('')
def patch_settings(
    payload: SettingsUpdate,
    response: Response,
    kanbee_session: Optional[str] = Cookie(default=None),
):
    session_id = _ensure_session(response, kanbee_session)
    updates = payload.model_dump(exclude_unset=True)
    data = storage.update_settings(session_id, updates)
    data.pop('session_id', None)
    return data
