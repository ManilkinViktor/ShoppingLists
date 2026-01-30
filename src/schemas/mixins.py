import datetime, uuid
from typing import ClassVar

from pydantic import BaseModel, field_validator

from utils.datetime_utils import validate_utc_timezone, validate_not_future_time

class TimeStampMixinDTO(BaseModel):
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @field_validator('created_at', 'updated_at')
    @classmethod
    def validate_datetime(cls, v: datetime.datetime) -> datetime.datetime:
        v = validate_utc_timezone(v)
        v = validate_not_future_time(v)
        return v





class UUIDMixinDTO(BaseModel):
    id: uuid.UUID
    _uuid_version: ClassVar[int] = 7

    @field_validator('id')
    @classmethod
    def validate_uuid_version(cls, v: uuid.UUID | str) -> uuid.UUID:
        if isinstance(v, str):
            v = uuid.UUID(v)
        if  v.version != cls._uuid_version:
            raise ValueError(
                f'incorrect uuid version. allowed: {cls._uuid_version}'
            )
        return v

