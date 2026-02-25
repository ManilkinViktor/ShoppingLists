from pydantic import BaseModel, EmailStr, Field

from core.constants import FieldConstraints
from schemas.users import PasswordWithConfirm, password_field


class UserLoginDTO(BaseModel):
    email: EmailStr
    password: password_field


class UserRegisterDTO(PasswordWithConfirm):
    name: str = Field(min_length=1, max_length=FieldConstraints.base_len)
    email: EmailStr


class TokenDTO(BaseModel):
    access_token: str
    token_type: str = 'bearer'
