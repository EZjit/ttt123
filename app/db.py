import contextlib
import logging
from dataclasses import dataclass, field
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    async_sessionmaker,
)
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


class DBError(Exception):
    pass


@dataclass
class DatabaseSessionManager:
    engine: AsyncEngine
    logger: logging.Logger
    sessionmaker: async_sessionmaker = field(init=False)

    def __post_init__(self):
        self.sessionmaker = async_sessionmaker(
            autocommit=False,
            bind=self.engine,
            expire_on_commit=False,
            # strange behavior for sqlmodel
            class_=AsyncSession,
        )

    async def close(self):
        await self.engine.dispose()

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        async with self.engine.begin() as connection:
            try:
                yield connection
            except Exception as ex:
                await connection.rollback()
                raise DBError(ex) from ex

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        session = self.sessionmaker()
        try:
            yield session
        except Exception as ex:
            await session.rollback()
            raise DBError(ex) from ex
        finally:
            await session.close()

    async def init_db(self, *, drop: bool = True):
        self.logger.warning("Init db called")
        async with self.engine.begin() as conn:
            if drop:
                await self.drop_all(conn)
            await self.create_all(conn)

    async def create_all(self, connection: AsyncConnection):
        await connection.run_sync(SQLModel.metadata.create_all)

    async def drop_all(self, connection: AsyncConnection):
        await connection.run_sync(SQLModel.metadata.drop_all)