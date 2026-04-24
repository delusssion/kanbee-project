from typing import Literal, Optional

from pydantic import BaseModel, field_validator

Status = Literal['todo', 'inprocess', 'done']
Priority = Literal['high', 'medium', 'low']


class Task(BaseModel):
    id: str
    title: str
    desc: Optional[str] = None
    status: Status
    priority: Priority
    due: Optional[str] = None
    board_id: Optional[str] = None

    @field_validator('desc', 'due', mode='before')
    @classmethod
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
    board_id: Optional[str] = None

    @field_validator('title')
    @classmethod
    def _title_must_not_be_blank(cls, value):
        title = value.strip()
        if not title:
            raise ValueError('Title must not be empty')
        return title

    @field_validator('desc', 'due', mode='before')
    @classmethod
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

    @field_validator('title')
    @classmethod
    def _title_must_not_be_blank(cls, value):
        if value is None:
            return value
        title = value.strip()
        if not title:
            raise ValueError('Title must not be empty')
        return title

    @field_validator('desc', 'due', mode='before')
    @classmethod
    def _empty_str_to_none(cls, value):
        if value == '':
            return None
        return value
