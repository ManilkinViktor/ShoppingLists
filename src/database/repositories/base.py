from collections.abc import Collection
from typing import Generic, TypeVar, Type, Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect, select, or_, update, delete as sa_delete
from sqlalchemy.exc import SQLAlchemyError

from database.base import Base
from schemas.types import CreateDTO, DTO
from core.logger import LoggerMeta, logging_method_exception
from utils.datetime_utils import utc_now

ModelOrm = TypeVar('ModelOrm', bound=Base)


class BaseRepository(Generic[ModelOrm, CreateDTO, DTO], metaclass=LoggerMeta):
    def __init__(self, _session: AsyncSession,
                 _model: Type[ModelOrm], _add_dto: Type[CreateDTO], _dto: Type[DTO]):
        self._session = _session
        self._model = _model
        self._add_dto = _add_dto
        self._dto = _dto

    def _get_pk_filter(self, data: CreateDTO) -> dict:
        """Автоматически собирает фильтр по первичному ключу из DTO."""
        mapper = inspect(self._model)
        pk_columns = [c.key for c in mapper.primary_key]
        return {pk: getattr(data, pk, None) for pk in pk_columns if getattr(data, pk, None) is not None}

    def _get_single_pk_key(self) -> str:
        mapper = inspect(self._model)
        pk_columns = [c.key for c in mapper.primary_key]
        if len(pk_columns) != 1:
            raise NotImplementedError('Bulk operations support only models with a single primary key')
        return pk_columns[0]

    def _is_flush_deferred(self) -> bool:
        return bool(self._session.info.get('defer_flush'))

    async def _flush_if_needed(self) -> None:
        if not self._is_flush_deferred():
            await self._session.flush()

    @logging_method_exception(SQLAlchemyError)
    async def add(self, data: CreateDTO) -> DTO:
        pk_filter = self._get_pk_filter(data)
        instance = await self._session.get(self._model, pk_filter)

        if instance:
            if hasattr(instance, "deleted_at") and instance.deleted_at is not None:
                for key, value in data.model_dump(exclude=set(pk_filter.keys())).items():
                    setattr(instance, key, value)
                instance.deleted_at = None
        else:
            instance = self._model(**data.model_dump())
            self._session.add(instance)

        await self._session.flush()
        return self._dto.model_validate(instance, from_attributes=True)

    @logging_method_exception(SQLAlchemyError)
    async def add_deferred(self, data: CreateDTO) -> None:
        pk_filter = self._get_pk_filter(data)
        instance = await self._session.get(self._model, pk_filter)

        if instance:
            if hasattr(instance, "deleted_at") and instance.deleted_at is not None:
                for key, value in data.model_dump(exclude=set(pk_filter.keys())).items():
                    setattr(instance, key, value)
                instance.deleted_at = None
        else:
            instance = self._model(**data.model_dump())
            self._session.add(instance)

    @logging_method_exception(SQLAlchemyError)
    async def get(self, id_value: Any) -> DTO | None:
        instance = await self._session.get(self._model, id_value)
        if instance and getattr(instance, "deleted_at", None) is not None:
            return None
        return self._dto.model_validate(instance, from_attributes=True) if instance else None

    @logging_method_exception(SQLAlchemyError)
    async def get_by(self, **filters) -> DTO | None:
        query = select(self._model).filter_by(**filters)
        if hasattr(self._model, "deleted_at"):
            query = query.where(self._model.deleted_at.is_(None))
        result = await self._session.execute(query)
        instance: ModelOrm = result.scalar_one_or_none()
        return self._dto.model_validate(instance, from_attributes=True) if instance else None

    @logging_method_exception(SQLAlchemyError)
    async def get_by_filters_or(self, **filters_or) -> DTO | None:
        conditions = [getattr(self._model, key) == value for key, value in filters_or.items()]
        stmt = select(self._model).where(or_(*conditions))

        if hasattr(self._model, "deleted_at"):
            stmt = stmt.where(self._model.deleted_at.is_(None))

        result = await self._session.execute(stmt)
        instance: ModelOrm = result.scalar_one_or_none()
        return self._dto.model_validate(instance, from_attributes=True) if instance else None

    @logging_method_exception(SQLAlchemyError)
    async def get_all(self, **filters) -> list[DTO]:
        query = select(self._model)
        if hasattr(self._model, "deleted_at"):
            query = query.where(self._model.deleted_at.is_(None))
        if filters:
            conditions = []
            for key, value in filters.items():
                if not hasattr(self._model, key):
                    continue
                column = getattr(self._model, key)
                is_collection = (
                        isinstance(value, Collection)
                        and not isinstance(value, (str, bytes, bytearray, dict))
                )
                if is_collection:
                    if not value:
                        return []
                    conditions.append(column.in_(list(value)))
                else:
                    conditions.append(column == value)
            query = query.where(*conditions)
        result = await self._session.execute(query)
        instances = result.scalars().all()
        return [self._dto.model_validate(instance, from_attributes=True) for instance in instances]

    @logging_method_exception(SQLAlchemyError)
    async def _exists(self, get_instance: ModelOrm) -> bool:
        pk_values = inspect(get_instance).identity
        instance: ModelOrm = await self._session.get(self._model, pk_values)
        return bool(instance)

    @logging_method_exception(SQLAlchemyError)
    async def update(self, id_value: Any, **update_data) -> DTO | None:
        instance = await self._session.get(self._model, id_value)
        if instance and getattr(instance, "deleted_at", None) is None:
            for key, value in update_data.items():
                if value is not None and hasattr(instance, key):
                    setattr(instance, key, value)
            await self._flush_if_needed()
            return self._dto.model_validate(instance, from_attributes=True)
        return None

    @logging_method_exception(SQLAlchemyError)
    async def update_many(
        self,
        update_data_by_id: dict[Any, dict[str, Any]],
    ) -> int:
        if not update_data_by_id:
            return 0

        pk_key = self._get_single_pk_key()
        payloads: list[dict[str, Any]] = []

        for id_value, update_data in update_data_by_id.items():
            filtered_update_data = {
                key: value
                for key, value in update_data.items()
                if key != pk_key and value is not None and hasattr(self._model, key)
            }
            if not filtered_update_data:
                continue

            payloads.append({pk_key: id_value, **filtered_update_data})

        if not payloads:
            return 0

        stmt = update(self._model)
        if hasattr(self._model, 'deleted_at'):
            stmt = stmt.where(self._model.deleted_at.is_(None))
        await self._session.execute(stmt, payloads)
        await self._flush_if_needed()
        return len(payloads)

    @logging_method_exception(SQLAlchemyError)
    async def delete(self, id_value: Any) -> bool:
        instance = await self._session.get(self._model, id_value)
        if instance and getattr(instance, "deleted_at", None) is None:
            if hasattr(instance, "deleted_at"):
                instance.deleted_at = utc_now()
            else:
                await self._session.delete(instance)
            await self._flush_if_needed()
            return True
        return False

    @logging_method_exception(SQLAlchemyError)
    async def delete_many(self, id_values: Sequence[Any]) -> int:
        if not id_values:
            return 0

        pk_key = self._get_single_pk_key()
        pk_column = getattr(self._model, pk_key)
        ids = list(id_values)

        if hasattr(self._model, 'deleted_at'):
            deleted_at = utc_now()
            stmt = (
                update(self._model)
                .where(pk_column.in_(ids))
                .where(self._model.deleted_at.is_(None))
                .values(deleted_at=deleted_at)
            )
        else:
            stmt = sa_delete(self._model).where(pk_column.in_(ids))

        result = await self._session.execute(stmt)
        await self._flush_if_needed()
        return result.rowcount or 0
