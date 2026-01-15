import datetime

from sqlalchemy.orm import Mapped, mapped_column



def utc_now():
    return datetime.datetime.now(datetime.UTC)


class TimestampMixin:
    __abstract__ = True

    created_at: Mapped[datetime.datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=utc_now,
        onupdate=utc_now
    )

