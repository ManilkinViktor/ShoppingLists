from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


from src.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=True,
)

session_factory = async_sessionmaker(engine)


class FieldConstraints:
    base_len = 256
    description_len = 1024


class Base(DeclarativeBase):

    cnt_repr_attrs = 1
    repr_attrs = tuple()

    def __repr__(self):
        attrs = []
        for idx, attr in enumerate(self.__table__.columns.keys()):
            if idx < self.cnt_repr_attrs or attr in self.repr_attrs:
                attrs.append(attr)

        return f'<{self.__class__.__name__}({', '.join(f'{attr}={getattr(self, attr)}' for attr in attrs)})>'

