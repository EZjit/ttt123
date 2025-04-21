from decimal import Decimal
from random import choice, randint
from typing import Iterable
from uuid import uuid4

import pytest_asyncio
from faker import Faker
from sqlmodel import select

from app.src.delivery.models import Parcel, ParcelType


@pytest_asyncio.fixture
async def saved_parcel_type(db_session) -> ParcelType:
    results = await db_session.exec(
        select(ParcelType),
    )
    return results.first()


@pytest_asyncio.fixture
async def saved_parcel_types(db_session) -> Iterable[ParcelType]:
    results = await db_session.exec(
        select(ParcelType),
    )
    return results.all()


@pytest_asyncio.fixture
async def random_parcels_for_user(
    test_user,
    session_manager,
    saved_parcel_types,
    fake: Faker,
):
    parcel_types = list(saved_parcel_types)
    parcels = [
        Parcel(
            request_id=uuid4(),
            name=fake.word(),
            weight=randint(1, 100),
            delivery_price=Decimal(randint(1, 100)),
            parcel_type_id=choice(parcel_types).id,
            user_id=test_user.id,
            user=test_user,
        )
        for _ in range(randint(10, 30))
    ]
    async with session_manager.session() as session:
        async with session.begin():
            session.add_all(
                parcels,
            )
        await session.commit()
    yield parcels
    # clean
    async with session_manager.session() as session:
        async with session.begin():
            for parcel in parcels:
                await session.delete(
                    parcel,
                )
        await session.commit()