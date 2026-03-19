from abc import ABC
from typing import Annotated, TYPE_CHECKING, TypeAlias

from pydantic import EmailStr, Field, model_validator, BaseModel

from core.constants import FieldConstraints
from schemas.mixins import UUIDMixinDTO, TimeStampMixinDTO

if TYPE_CHECKING:
    from schemas.workspace_members import WorkspaceMemberRelWorkspaceDTO


class UserBaseDTO(UUIDMixinDTO, ABC):
    name: str = Field(min_length=1, max_length=FieldConstraints.BASE_LEN)
    email: EmailStr


class UserDTO(UserBaseDTO, TimeStampMixinDTO):
    pass


password_field: TypeAlias = Annotated[
    str, Field(min_length=FieldConstraints.MIN_PASSWORD, max_length=FieldConstraints.BASE_LEN)]


class PasswordWithConfirm(BaseModel):
    password: password_field
    password_confirmation: password_field

    @model_validator(mode='after')
    def validate_password_confirmation(self) -> "PasswordWithConfirm":
        if self.password != self.password_confirmation:
            raise ValueError("The passwords don't match")
        return self


class UserCreateDTO(PasswordWithConfirm, UserBaseDTO):
    pass


class UserCreateAuthDTO(UserBaseDTO):
    hashed_password: str


class UserAuthDTO(UserDTO):
    hashed_password: str


class UserRelWorkspaceDTO(UserDTO):
    connected_workspaces: list['WorkspaceMemberRelWorkspaceDTO']
