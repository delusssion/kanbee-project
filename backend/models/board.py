from pydantic import BaseModel


class Board(BaseModel):
    id: str
    name: str
    position: int


class BoardCreate(BaseModel):
    name: str


class BoardRename(BaseModel):
    name: str
