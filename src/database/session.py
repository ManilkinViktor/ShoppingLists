from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=True,
)

session_factory = async_sessionmaker(engine)



