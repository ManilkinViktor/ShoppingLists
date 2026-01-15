import datetime, uuid

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import UUID
from uuid_utils import uuid7

from src.utils.datetime_utils import utc_now



class TimestampMixin:
    __abstract__ = True

    created_at: Mapped[datetime.datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=utc_now,
        onupdate=utc_now
    )

class UUIDMixin:

    repr_attrs = ('id', )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7(),
    )

