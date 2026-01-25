from typing import Generic, TypeVar, Type, Any, List, Sequence
from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect, select
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

from database.base import Base
from core.logger import LoggerMeta, logging_method_exception

ModelOrm = TypeVar('ModelOrm', bound=Base)
AddDTO = TypeVar('AddDTO', bound=BaseModel)
DTO = TypeVar('DTO', bound=BaseModel)

class BaseRepository(Generic[ModelOrm, AddDTO, DTO], ABC, metaclass=LoggerMeta):
    def __init__(self, _session: AsyncSession,
                 _model: Type[ModelOrm], _add_dto: Type[AddDTO], _dto: Type[DTO]):
        self._session = _session
        self._model = _model
        self._add_dto = _add_dto
        self._dto = _dto

    @logging_method_exception(SQLAlchemyError)
    async def add(self, data: AddDTO) -> None:
        instance: ModelOrm = self._model(**data.model_dump())
        self._session.add(instance)

    @logging_method_exception(SQLAlchemyError)
    async def get(self, id_value: Any) -> DTO | None:
        instance: ModelOrm = await self._session.get(self._model, id_value)
        if instance:
            return self._dto.model_validate(instance, from_attributes=True)
        return None

    @logging_method_exception(SQLAlchemyError)
    async def get_by(self, **filters) -> DTO | None:
        query = select(self._model).filter_by(**filters)
        result = await self._session.execute(query)
        instance: ModelOrm = result.scalar_one_or_none()
        if instance:
            return self._dto.model_validate(instance, from_attributes=True)
        return None

    @logging_method_exception(SQLAlchemyError)
    async def get_all(self, **filters) -> List[DTO]:
        query = select(self._model).filter_by(**filters)
        result = await self._session.execute(query)
        instances: Sequence[ModelOrm] = result.scalars().all()
        return [self._dto.model_validate(instance, from_attributes=True)
                for instance in instances]

    @logging_method_exception(SQLAlchemyError)
    async def _exists(self, get_instance: ModelOrm) -> bool:
        pk_values = inspect(get_instance).identity
        instance: ModelOrm = await self._session.get(self._model, pk_values)
        if instance:
            return True
        return False

    @logging_method_exception(SQLAlchemyError)
    async def update(self, id_value: Any, data: DTO) -> bool:
        instance: ModelOrm = await self._session.get(self._model, id_value)
        if instance:
            for key, value in data.model_dump().items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            return True
        return False

    @logging_method_exception(SQLAlchemyError)
    async def delete(self, id_value: Any) -> bool:
        instance: ModelOrm = await self._session.get(self._model, id_value)
        if instance:
            await self._session.delete(instance)
            return True
        return False