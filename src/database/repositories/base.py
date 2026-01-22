import uuid
from typing import Generic, TypeVar, Type
from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession

from database.base import Base
from schemas.mixins import UUIDMixinDTO

ModelOrm = TypeVar('ModelOrm', bound=Base)
AddDTO = TypeVar('AddDTO', bound=UUIDMixinDTO)
DTO = TypeVar('DTO', bound=UUIDMixinDTO)

class BaseRepository(Generic[ModelOrm, AddDTO, DTO], ABC):

    def __init__(self, session: AsyncSession,
                 _model: Type[ModelOrm], _add_dto: Type[AddDTO], _dto: Type[DTO]):
        self.session = session
        self._model = _model
        self._add_dto = _add_dto
        self._dto = _dto

    async def add(self, data: AddDTO) -> None:
        instance: ModelOrm = self._model(**data.model_dump())
        self.session.add(instance)

    async def get_by_id(self, id_: uuid.UUID) -> DTO | None:
        instance: ModelOrm | None = await self.session.get(self._model, id_)
        if instance:
            instance: DTO = self._dto.model_validate(instance, from_attributes=True)
        return instance

    async def update(self, new_data: DTO) -> bool:
        instance: ModelOrm | None = await self.session.get(self._model, new_data.id)
        if instance:
            for key, value in new_data.model_dump().items():
                setattr(instance, key, value)
            await self.session.merge(instance)
            return True
        return False

    async def delete(self, id_):
        instance: ModelOrm | None = await self.session.get(self._model, id_)
        if instance:
            await self.session.delete(instance)
            return True
        return False