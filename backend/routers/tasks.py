from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response

import storage
from auth_utils import get_current_user_id
from models.task import Task, TaskCreate, TaskUpdate

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.get('', response_model=List[Task])
def get_tasks(user_id: str = Depends(get_current_user_id)):
    return storage.get_all_tasks(user_id)


@router.post('', response_model=Task, status_code=201)
def create_task(payload: TaskCreate, user_id: str = Depends(get_current_user_id)):
    return storage.create_task(payload, user_id)


@router.patch('/{task_id}', response_model=Task)
def update_task(task_id: str, payload: TaskUpdate, user_id: str = Depends(get_current_user_id)):
    task = storage.update_task(task_id, payload, user_id)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    return task


@router.delete('/{task_id}', status_code=204)
def delete_task(task_id: str, user_id: str = Depends(get_current_user_id)):
    deleted = storage.delete_task(task_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Task not found')
    return Response(status_code=204)
