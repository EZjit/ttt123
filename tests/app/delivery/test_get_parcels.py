from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.src.delivery.entities import GetParcelResponseDTO
from app.src.delivery.models import Parcel
from app.src.users.models import User
from app.src.users.services import UserService

URL = "/api/v1/delivery/parcels"


async def handle_request(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        return await ac.get(URL)


@pytest.mark.asyncio
async def test_get_parcels_unauthorized(
    test_app,
    random_parcels_for_user: list[Parcel],
):
    response = await handle_request(test_app=test_app)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_parcels_authorized(
    test_app,
    random_parcels_for_user: list[Parcel],
    test_user: User,
):
    with patch.object(
        UserService,
        "get_user",
        new=AsyncMock(return_value=test_user),
    ):
        response = await handle_request(test_app=test_app)
    assert response.status_code == HTTPStatus.OK
    got_parcels = response.json()

    assert len(got_parcels) == len(random_parcels_for_user)
    for parcel in got_parcels:
        # Check valid results
        GetParcelResponseDTO.model_validate(parcel)