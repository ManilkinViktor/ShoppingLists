import sys
import uuid
from pathlib import Path

import pytest
from uuid_utils import uuid7

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from conftest import session_factory
from database.repositories.users import UsersRepository
from schemas.users import UserCreateAuthDTO


@pytest.mark.asyncio
async def test_users_repository_password_methods_hide_soft_deleted_users() -> None:
    user_id = uuid.UUID(str(uuid7()))
    email = f"soft-delete-user-{user_id}@example.com"

    try:
        async with session_factory() as session:
            repository = UsersRepository(session)
            await repository.add(
                UserCreateAuthDTO(
                    id=user_id,
                    name="soft-delete-user",
                    email=email,
                    hashed_password="hashed",
                )
            )
            await session.commit()

        async with session_factory() as session:
            repository = UsersRepository(session)
            deleted = await repository.delete(user_id)
            await session.commit()
            assert deleted is True

        async with session_factory() as session:
            repository = UsersRepository(session)
            assert await repository.get_with_password(user_id) is None
            assert await repository.get_by_email_with_password(email) is None
    finally:
        async with session_factory() as session:
            repository = UsersRepository(session)
            await repository.delete(user_id)
            await session.commit()
