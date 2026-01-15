import uuid
from typing import Annotated

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, UUID

from uuid_utils import uuid7

from src.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=True,
)

session_factory = async_sessionmaker(engine)


str_256 = Annotated[str, 256]


class Base(DeclarativeBase):

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7(),
    )



    cnt_repr_attrs = 1
    repr_attrs = tuple()

    def __repr__(self):
        attrs = []
        for idx, attr in enumerate(self.__table__.columns.keys()):
            if idx < self.cnt_repr_attrs or attr in self.repr_attrs:
                attrs.append(attr)

        return f'{self.__class__.__name__}({', '.join(f'{attr}={getattr(self, attr)}' for attr in attrs)})'

