from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

import storage
from auth_utils import get_current_user_id

router = APIRouter(prefix='/settings', tags=['settings'])


class SettingsUpdate(BaseModel):
    lang: Optional[str] = None
    theme: Optional[str] = None
    default_view: Optional[str] = None


@router.get('')
def get_settings(user_id: str = Depends(get_current_user_id)):
    data = storage.get_or_create_user_settings(user_id)
    data.pop('user_id', None)
    return data


@router.patch('')
def patch_settings(payload: SettingsUpdate, user_id: str = Depends(get_current_user_id)):
    updates = payload.model_dump(exclude_unset=True)
    data = storage.update_user_settings(user_id, updates)
    data.pop('user_id', None)
    return data
