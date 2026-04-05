import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logging_method_exception
from database.models import UsersOrm
from database.repositories.base import BaseRepository
from schemas.users import UserDTO, UserAuthDTO, UserCreateAuthDTO


class UsersRepository(
    BaseRepository[
        UsersOrm,
        UserCreateAuthDTO,
        UserDTO,
        uuid.UUID,
    ]):
    def __init__(self, _session: AsyncSession) -> None:
        super().__init__(
            _session,
            _model=UsersOrm, _add_dto=UserCreateAuthDTO, _dto=UserDTO
        )

    @logging_method_exception(SQLAlchemyError)
    async def get_with_password(self, id_value: uuid.UUID) -> UserAuthDTO | None:
        instance: UsersOrm | None = await self._session.get(UsersOrm, id_value)
        if instance and instance.deleted_at is not None:
            return None
        return UserAuthDTO.model_validate(instance, from_attributes=True) if instance else None

    @logging_method_exception(SQLAlchemyError)
    async def get_by_email_with_password(self, email: str) -> UserAuthDTO | None:
        query = (
            select(UsersOrm)
            .where(UsersOrm.email == email)
            .where(UsersOrm.deleted_at.is_(None))
        )
        result = await self._session.execute(query)
        instance: UsersOrm | None = result.scalar_one_or_none()
        return UserAuthDTO.model_validate(instance, from_attributes=True) if instance else None
