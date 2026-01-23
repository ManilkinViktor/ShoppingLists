from sqlalchemy.ext.asyncio import AsyncSession



from schemas.users import UserDTO, UserAuthDTO
from database.models import UsersOrm
from database.repositories.base import BaseRepository

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









