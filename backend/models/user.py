from pydantic import BaseModel


class UserRegister(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str


class RequestPasswordReset(BaseModel):
    email: str


class VerifyResetCode(BaseModel):
    email: str
    code: str


class ConfirmPasswordReset(BaseModel):
    email: str
    code: str
    new_password: str


class ChangePassword(BaseModel):
    current_password: str
    new_password: str
