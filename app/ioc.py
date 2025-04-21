import logging
from typing import AsyncIterable

from dishka import (
    AsyncContainer,
    Provider,
    Scope,
    from_context,
    make_async_container,
    provide,
)
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

import app.di
from app.config import Settings
from app.db import DatabaseSessionManager
from app.src.currency.service import ExchangeRateService
from app.src.delivery.services.parcel_publisher import PublisherService
from app.src.delivery.services.parcels_service import ParcelService
from app.src.delivery.services.worker_service import BackgroundWorkerService
from app.src.users.services import UserService

REDIS_HEALTH_CHECK_INTERVAL_S = 600


# app dependency logic
class AppProvider(Provider):
    settings = from_context(provides=Settings, scope=Scope.APP)
    logger = from_context(provides=logging.Logger, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_redis(self, settings: Settings) -> Redis:
        return Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            retry_on_timeout=True,
            retry_on_error=[RedisError],
            health_check_interval=REDIS_HEALTH_CHECK_INTERVAL_S,
            encoding="utf-8",
            decode_responses=True,
        )

    @provide(scope=Scope.APP)
    async def get_engine(self, settings: Settings) -> AsyncEngine:
        database_url = "mysql+aiomysql://{}:{}@{}/{}".format(
            settings.mysql_user,
            settings.mysql_password,
            settings.db_host,
            settings.mysql_database,
        )
        return create_async_engine(database_url)

    @provide(scope=Scope.APP)
    async def session_manager(
        self,
        engine: AsyncEngine,
        logger: logging.Logger,
    ) -> DatabaseSessionManager:
        return DatabaseSessionManager(engine=engine, logger=logger)

    @provide(scope=Scope.APP)
    async def background_worker_service(
        self,
        settings: Settings,
    ) -> AsyncIterable[BackgroundWorkerService]:
        yield BackgroundWorkerService(settings=settings)

    @provide(scope=Scope.APP)
    def exchange_service(self, redis: Redis) -> ExchangeRateService:
        return ExchangeRateService(redis=redis)

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

    @provide(scope=Scope.APP)
    async def parcel_service(
        self,
        db_session: AsyncSession,
        exchange_service: ExchangeRateService,
    ) -> AsyncIterable[ParcelService]:
        yield ParcelService(
            db_session=db_session,
            exchange_service=exchange_service,
        )

    @provide(scope=Scope.REQUEST)
    async def publisher_service(
        self,
        settings: Settings,
    ) -> AsyncIterable[PublisherService]:
        publisher_service = PublisherService(settings=settings)
        yield publisher_service
        await publisher_service.close()


def setup_container(
    context: dict | None = None,
) -> AsyncContainer:
    if app.di.container:
        return app.di.container
    app.di.container = make_async_container(
        AppProvider(),
        context=context,
    )
    return app.di.container