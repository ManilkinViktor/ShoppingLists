import datetime, uuid

from pydantic import BaseModel, field_validator, validator

from utils.datetime_utils import utc_now

class TimeStampMixinDTO(BaseModel):
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @field_validator('created_at', 'updated_at')
    @classmethod
    def validate_datetime(cls, v: datetime.datetime) -> datetime.datetime:
        v = cls.validate_utc_timezone(v)
        v = cls.validate_not_future_time(v)
        return v


    @classmethod
    def validate_utc_timezone(cls, v:datetime.datetime) -> datetime.datetime:
        if v.tzinfo is None:
            raise ValueError('datetime must have timezone')
        if v.tzinfo != datetime.UTC:
            v = v.astimezone(datetime.UTC)

        return  v


    @classmethod
    def validate_not_future_time(cls, v: datetime.datetime) -> datetime.datetime:
        if v > utc_now():
            raise ValueError('datetime cannot be future')
        return v




class UUIDMixinDTO(BaseModel):
    id: uuid.UUID
    _uuid_version = 7

    @field_validator('id')
    @classmethod
    def validate_uuid_version(cls, v: uuid.UUID) -> uuid.UUID:
        if  v.version != cls._uuid_version:
            raise ValueError(
                f'incorrect uuid version. \
                allowed: {cls._uuid_version}'
            )
        return v
