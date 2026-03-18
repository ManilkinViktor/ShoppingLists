import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=True,
    poolclass=NullPool,
)

session_factory = async_sessionmaker(engine)

