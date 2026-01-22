import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import EmailStr

from schemas.users import UserDTO, UserAuthDTO
from database.models import UsersOrm
from database.repositories.base import BaseRepository

class UsersRepository(
    BaseRepository[
        UsersOrm,
        UserAuthDTO,
        UserDTO
    ]):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session,
            _model=UsersOrm, _add_dto=UserAuthDTO, _dto=UserDTO
        )



    async def get_by_id(self, user_id: uuid.UUID, remove_hashed_password: bool = True) -> UserDTO | None:
        user: UsersOrm | None = await self.session.get(UsersOrm, user_id)
        if user is None:
            return None
        if remove_hashed_password:
            user: UserDTO = UserDTO.model_validate(user, from_attributes=True)
        else:
            user: UserAuthDTO = UserAuthDTO.model_validate(user, from_attributes=True)
        return user

    async def get_by_email(self, user_email: EmailStr, remove_hashed_password: bool = True) -> UserDTO | None:
        query = select(UsersOrm).filter_by(email=user_email)
        result = await self.session.execute(query)
        user: UsersOrm | None = result.scalars().one_or_none()
        if user is None:
            return None
        if remove_hashed_password:
            user: UserDTO = UserDTO.model_validate(result, from_attributes=True)
        else:
            user: UserAuthDTO = UserAuthDTO.model_validate(result, from_attributes=True)
        return user








