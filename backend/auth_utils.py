from typing import Optional

from fastapi import Cookie, HTTPException

import storage


def get_current_user_id(kanbee_session: Optional[str] = Cookie(default=None)) -> str:
    if not kanbee_session:
        raise HTTPException(status_code=401, detail='Not authenticated')
    user_id = storage.get_session_user(kanbee_session)
    if not user_id:
        raise HTTPException(status_code=401, detail='Session expired')
    return user_id
