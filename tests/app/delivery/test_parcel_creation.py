from decimal import Decimal
from http import HTTPStatus
from random import randint
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.src.delivery.entities import RegisterParcelDTO
from app.src.delivery.models import Parcel, ParcelType
from app.src.users.models import User
from app.src.users.services import UserService

URL = "/api/v1/delivery/parcels"


def get_parcel_dto(saved_parcel_type: ParcelType):
    return RegisterParcelDTO(
        weight=randint(1, 100),
        dollar_price=Decimal(randint(1, 100)),
        parcel_type_id=saved_parcel_type.id,
        name="test parcel",
    )


async def handle_response(test_app, parcel_dto, saved_parcel_type):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        return await ac.post(URL, json=parcel_dto.model_dump(mode="json"))


@pytest.mark.asyncio
async def test_parcel_create_unauthorized(
    test_app,
    saved_parcel_type: ParcelType,
):
    parcel_dto = get_parcel_dto(saved_parcel_type)

    response = await handle_response(test_app, parcel_dto, saved_parcel_type)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_parcel_create(
    test_app,
    test_user: User,
    saved_parcel_type: ParcelType,
):
    with patch.object(
        UserService,
        "get_user",
        new=AsyncMock(return_value=test_user),
    ):
        parcel_dto = get_parcel_dto(saved_parcel_type)
        response = await handle_response(
            test_app,
            parcel_dto,
            saved_parcel_type,
        )
        assert response.status_code == HTTPStatus.CREATED
    got_parcel = Parcel.model_validate(response.json())
    for field_name in ("dollar_price", "weight", "parcel_type_id"):
        getattr(got_parcel, field_name) == getattr(parcel_dto, field_name)