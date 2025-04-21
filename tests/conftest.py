import logging

import pytest
import pytest_asyncio
from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import setup_dishka
from faker import Faker
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel.ext.asyncio.session import AsyncSession

import app.di
from app import main
from app.config import Settings, get_settings
from app.db import DatabaseSessionManager
from app.src.users.models import User
from app.src.users.services import TEST_USER_ID, UserService
from tests.mock_ioc import MockConnectionProvider

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def fake():
    return Faker()


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def container(settings: Settings):
    app.di.container = make_async_container(
        MockConnectionProvider(),
        context={
            Settings: settings,
            logging.Logger: logging.getLogger(__name__),
        },
    )
    yield app.di.container


@pytest.fixture(scope="session")
def test_app(container: AsyncContainer, settings: Settings):
    app = main.create_app(settings)
    setup_dishka(container, app)

    yield app


@pytest_asyncio.fixture(autouse=True, scope="session")
async def db(container: AsyncContainer):
    await main.init_db(container=container)

    yield


@pytest_asyncio.fixture
async def session_manager(container: AsyncContainer):
    yield await container.get(DatabaseSessionManager)


@pytest_asyncio.fixture
async def db_session(container: AsyncContainer):
    yield await container.get(AsyncSession)


@pytest_asyncio.fixture
async def user_service(container: AsyncContainer):
    yield await container.get(UserService)


@pytest_asyncio.fixture
async def test_user(user_service: UserService) -> User:
    user = await user_service.get_or_create(user_id=TEST_USER_ID)
    return user


@pytest.fixture
def test_client(test_app: FastAPI):
    yield TestClient(test_app)