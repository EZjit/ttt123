from dataclasses import dataclass
from typing import Final
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import Settings
from app.src.users.models import User


class UserServiceError(HTTPException):
    pass


class NotAuthorizedError(UserServiceError):
    pass


USER_ID_KEY: Final[str] = "user_id"

TEST_USER_ID = UUID("76ebc6a6-a48f-4dee-a95f-db2c63ef62d3")


@dataclass
class UserService:
    db_session: AsyncSession
    settings: Settings

    async def get_user(self, session: dict) -> User:
        user_id = session.get(USER_ID_KEY)
        if not user_id:
            raise NotAuthorizedError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user session",
            )
        return await self.get_or_create(user_id=user_id)

    async def get_or_create(self, user_id: UUID) -> User:
        async with self.db_session as session:
            return await session.get(User, user_id) or await self.create_user(
                user_id=user_id,
                session=session,
            )

    async def create_user(self, user_id: UUID, session: AsyncSession) -> User:
        new_user = User(id=user_id)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user