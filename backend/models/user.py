from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class ResetPassword(BaseModel):
    username: str
    new_password: str
