from typing import Literal, Optional

from pydantic import BaseModel, validator

Status = Literal['todo', 'inprocess', 'done']
Priority = Literal['high', 'medium', 'low']


class Task(BaseModel):
    id: str
    title: str
    desc: Optional[str] = None
    status: Status
    priority: Priority
    due: Optional[str] = None

    @validator('desc', 'due', pre=True)
    def _empty_str_to_none(cls, value):
        if value == '':
            return None
        return value


class TaskCreate(BaseModel):
    title: str
    desc: Optional[str] = None
    status: Status = 'todo'
    priority: Priority = 'medium'
    due: Optional[str] = None

    @validator('desc', 'due', pre=True)
    def _empty_str_to_none(cls, value):
        if value == '':
            return None
        return value


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    desc: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    due: Optional[str] = None

    @validator('desc', 'due', pre=True)
    def _empty_str_to_none(cls, value):
        if value == '':
            return None
        return value
