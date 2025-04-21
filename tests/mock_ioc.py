from typing import AsyncIterable

import fakeredis
from dishka import Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import Settings
from app.db import DatabaseSessionManager
from app.ioc import AppProvider
from app.src.users.services import UserService

# Have to change scope to Scope.APP


class MockConnectionProvider(AppProvider):
    @provide(scope=Scope.APP)
    def get_redis(self, settings: Settings) -> Redis:
        return fakeredis.FakeAsyncRedis(
            decode_responses=True,
            encoding="utf-8",
            version=7,
        )

    @provide(scope=Scope.APP)
    async def get_engine(self, settings: Settings) -> AsyncEngine:
        database_url = "sqlite+aiosqlite:///"

        return create_async_engine(database_url)

    @provide(scope=Scope.APP)
    async def db_session(
        self,
        session_manager: DatabaseSessionManager,
    ) -> AsyncIterable[AsyncSession]:
        async with session_manager.session() as session:
            yield session

    @provide(scope=Scope.APP)
    async def user_service(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> AsyncIterable[UserService]:
        yield UserService(db_session=db_session, settings=settings)