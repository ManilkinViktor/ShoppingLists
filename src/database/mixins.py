import datetime, uuid

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import UUID, TIMESTAMP


from uuid_utils import uuid7

from utils.datetime_utils import utc_now



class TimestampMixin:
    __abstract__ = True

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=None,
    )

class UUIDMixin:
    __abstract__ = True

    repr_attrs = ('id', )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )
