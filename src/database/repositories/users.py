import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from schemas.users import UserDTO, UserAuthDTO, UserCreateAuthDTO
from database.models import UsersOrm
from database.repositories.base import BaseRepository

from core.logger import logging_method_exception

class UsersRepository(
    BaseRepository[
        UsersOrm,
        UserCreateAuthDTO,
        UserDTO
    ]):
    def __init__(self, _session: AsyncSession):
        super().__init__(
            _session,
            _model=UsersOrm, _add_dto=UserCreateAuthDTO, _dto=UserDTO
        )

    @logging_method_exception(SQLAlchemyError)
    async def get_with_password(self, id_value: uuid.UUID) -> UserAuthDTO | None:
        instance: UsersOrm | None = await self._session.get(UsersOrm, id_value)
        return UserAuthDTO.model_validate(instance, from_attributes=True) if instance else None

    @logging_method_exception(SQLAlchemyError)
    async def get_by_email_with_password(self, email: str) -> UserAuthDTO | None:
        query = select(UsersOrm).where(UsersOrm.email == email)
        result = await self._session.execute(query)
        instance: UsersOrm | None = result.scalar_one_or_none()
        return UserAuthDTO.model_validate(instance, from_attributes=True) if instance else None





