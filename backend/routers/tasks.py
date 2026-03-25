from typing import List

from fastapi import APIRouter, HTTPException, Response

import storage
from models.task import Task, TaskCreate, TaskUpdate

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.get('', response_model=List[Task])
def get_tasks():
    return storage.get_all_tasks()


@router.post('', response_model=Task, status_code=201)
def create_task(payload: TaskCreate):
    return storage.create_task(payload)


@router.patch('/{task_id}', response_model=Task)
def update_task(task_id: str, payload: TaskUpdate):
    task = storage.update_task(task_id, payload)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    return task


@router.delete('/{task_id}', status_code=204)
def delete_task(task_id: str):
    deleted = storage.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Task not found')
    return Response(status_code=204)
