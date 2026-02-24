from typing import Generic, TypeVar, Type, Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect, select, or_
from sqlalchemy.exc import SQLAlchemyError


from schemas.types import ModelOrm, AddDTO, DTO
from core.logger import LoggerMeta, logging_method_exception



class BaseRepository(Generic[ModelOrm, AddDTO, DTO], metaclass=LoggerMeta):
    def __init__(self, _session: AsyncSession,
                 _model: Type[ModelOrm], _add_dto: Type[AddDTO], _dto: Type[DTO]):
        self._session = _session
        self._model = _model
        self._add_dto = _add_dto
        self._dto = _dto

    @logging_method_exception(SQLAlchemyError)
    async def add(self, data: AddDTO) -> DTO:
        instance: ModelOrm = self._model(**data.model_dump())
        self._session.add(instance)
        await self._session.flush()
        return self._dto.model_validate(instance, from_attributes=True)

    @logging_method_exception(SQLAlchemyError)
    async def get(self, id_value: Any) -> DTO | None:
        instance: ModelOrm = await self._session.get(self._model, id_value)
        return self._dto.model_validate(instance, from_attributes=True) if instance else None

    @logging_method_exception(SQLAlchemyError)
    async def get_by(self, **filters) -> DTO | None:
        query = select(self._model).filter_by(**filters)
        result = await self._session.execute(query)
        instance: ModelOrm = result.scalar_one_or_none()
        return self._dto.model_validate(instance, from_attributes=True) if instance else None

    @logging_method_exception
    async def get_by_filters_or(self, **filters_or) -> DTO | None:
        conditions = [getattr(self._model, key) == value for key, value in filters_or.items()]
        stmt = select(self._model).where(or_(*conditions))
        result = await self._session.execute(stmt)
        instance: ModelOrm = result.scalar_one_or_none()
        return self._dto.model_validate(instance, from_attributes=True) if instance else None

    @logging_method_exception(SQLAlchemyError)
    async def get_all(self, **filters) -> list[DTO]:
        query = select(self._model).filter_by(**filters)
        result = await self._session.execute(query)
        instances: Sequence[ModelOrm] = result.scalars().all()
        return [self._dto.model_validate(instance, from_attributes=True)
                for instance in instances]

    @logging_method_exception(SQLAlchemyError)
    async def _exists(self, get_instance: ModelOrm) -> bool:
        pk_values = inspect(get_instance).identity
        instance: ModelOrm = await self._session.get(self._model, pk_values)
        return bool(instance)

    @logging_method_exception(SQLAlchemyError)
    async def update(self, id_value: Any, **update_data) -> DTO | None:
        instance: ModelOrm = await self._session.get(self._model, id_value)
        if instance:
            for key, value in update_data.items():
                if not(value is None) and hasattr(instance, key):
                    setattr(instance, key, value)
        return self._dto.model_validate(instance, from_attributes=True) if instance else None

    @logging_method_exception(SQLAlchemyError)
    async def delete(self, id_value: Any) -> bool:
        instance: ModelOrm = await self._session.get(self._model, id_value)
        if instance:
            await self._session.delete(instance)
        return bool(instance)
