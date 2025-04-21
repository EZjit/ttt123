import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from app.config import Settings, get_settings
from app.db import DatabaseSessionManager
from app.di import get_container
from app.ioc import setup_container
from app.middleware import apply_middlewares
from app.routes import apply_routes, tags_metadata
from app.src.currency.service import ExchangeRateService
from app.src.delivery.models import init_parcel_types
from app.src.delivery.services.worker_service import BackgroundWorkerService

settings = get_settings()
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
)


async def init_db(container):
    session_manager = await container.get(DatabaseSessionManager)
    await session_manager.init_db()
    await init_parcel_types(session_manager=session_manager)


async def startup_events(settings: Settings, container):
    # Update usd rate in start
    container = get_container()
    # update usd on start
    exchange_service = await container.get(ExchangeRateService)
    await exchange_service.fetch_currency(currency="USD")

    if settings.init_db:
        # db init logic
        await init_db(container=container)


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = get_container()
    logger.info("App %s is starting", settings.title)

    await startup_events(settings, container)
    if not settings.testing_mode:
        # do not connect in testing
        background_worker_service = await container.get(BackgroundWorkerService)
        asyncio.create_task(background_worker_service.run())

    yield
    # graceful shutdown
    await background_worker_service.close()
    await app.state.dishka_container.close()
    logger.info("App %s closed", settings.title)


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(
        title=settings.title,
        lifespan=lifespan,
        version=settings.app_version,
        openapi_url=f"/api/v{settings.api_version}/openapi.json",
        openapi_tags=tags_metadata,
    )
    apply_routes(app=app)
    apply_middlewares(app=app, settings=settings)
    return app


def entry_point():
    app = create_app(settings)
    setup_container(
        context={
            Settings: settings,
            logging.Logger: logger,
        },
    )
    setup_dishka(get_container(), app)
    return app


if __name__ == "__main__":
    uvicorn.run(
        "__main__:entry_point",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        workers=settings.workers,
    )