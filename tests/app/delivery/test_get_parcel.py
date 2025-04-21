from http import HTTPStatus
from random import choice
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.src.delivery.entities import GetParcelResponseDTO
from app.src.delivery.models import Parcel
from app.src.users.models import User
from app.src.users.services import UserService

URL = "/api/v1/delivery/parcels"


async def handle_request(test_app, parcel_id):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        return await ac.get(f"{URL}/{parcel_id}")


@pytest.mark.asyncio
async def test_get_parcel_unauthorized(
    test_app,
    random_parcels_for_user: list[Parcel],
):
    random_parcel: Parcel = choice(random_parcels_for_user)
    response = await handle_request(
        test_app=test_app,
        parcel_id=str(random_parcel.id),
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_parcel_authorized(
    test_app,
    random_parcels_for_user: list[Parcel],
    test_user: User,
):
    random_parcel: Parcel = choice(random_parcels_for_user)
    with patch.object(
        UserService,
        "get_user",
        new=AsyncMock(return_value=test_user),
    ):
        response = await handle_request(
            test_app=test_app,
            parcel_id=str(random_parcel.id),
        )
    assert response.status_code == HTTPStatus.OK
    parcel_dto: GetParcelResponseDTO = GetParcelResponseDTO.model_validate(
        response.json(),
    )
    assert parcel_dto.id == random_parcel.id