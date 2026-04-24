from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

import storage
from auth_utils import get_current_user_id
from models.task import Task, TaskCreate, TaskUpdate

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.get('', response_model=List[Task])
def get_tasks(board_id: Optional[str] = Query(default=None), user_id: str = Depends(get_current_user_id)):
    return storage.get_all_tasks(user_id, board_id)


@router.post('', response_model=Task, status_code=201)
def create_task(payload: TaskCreate, user_id: str = Depends(get_current_user_id)):
    return storage.create_task(payload, user_id)


@router.get('/export', response_model=List[Task])
def export_tasks(user_id: str = Depends(get_current_user_id)):
    tasks = storage.get_all_tasks(user_id)
    return JSONResponse(
        content=jsonable_encoder(tasks),
        headers={'Content-Disposition': 'attachment; filename="kanbee-tasks.json"'},
    )


@router.post('/import', response_model=List[Task], status_code=201)
def import_tasks(payload: List[TaskCreate], user_id: str = Depends(get_current_user_id)):
    return [storage.create_task(task, user_id) for task in payload]


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
