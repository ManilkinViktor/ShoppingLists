import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from schemas.users import UserDTO, UserAuthDTO
from database.models import UsersOrm
from database.repositories.base import BaseRepository

from core.logger import logging_method_exception

class UsersRepository(
    BaseRepository[
        UsersOrm,
        UserAuthDTO,
        UserDTO
    ]):
    def __init__(self, _session: AsyncSession):
        super().__init__(
            _session,
            _model=UsersOrm, _add_dto=UserAuthDTO, _dto=UserDTO
        )

    @logging_method_exception(SQLAlchemyError)
    async def get_with_password(self, id_value: uuid.UUID) -> UserAuthDTO | None:
        instance: UsersOrm | None = await self._session.get(UsersOrm, id_value)
        if instance:
            return UserAuthDTO.model_validate(instance, from_attributes=True)
        return None








