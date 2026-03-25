from typing import Dict, List, Optional
from uuid import uuid4

from models.task import Task, TaskCreate, TaskUpdate

_tasks: Dict[str, Task] = {}


def create_task(data: TaskCreate) -> Task:
    task = Task(id=uuid4().hex, **data.dict())
    _tasks[task.id] = task
    return task


def get_all_tasks() -> List[Task]:
    return list(_tasks.values())


def get_task(task_id: str) -> Optional[Task]:
    return _tasks.get(task_id)


def update_task(task_id: str, data: TaskUpdate) -> Optional[Task]:
    existing = _tasks.get(task_id)
    if not existing:
        return None
    updated = existing.copy(update=data.dict(exclude_unset=True))
    _tasks[task_id] = updated
    return updated


def delete_task(task_id: str) -> bool:
    return _tasks.pop(task_id, None) is not None
