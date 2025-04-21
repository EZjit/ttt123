from http import HTTPStatus

import pytest
from httpx import ASGITransport, AsyncClient

from app.src.delivery.models import INIT_PARCELS_TYPES, ParcelType

DEFAULT_TYPES_NUM = 3

URL = "/api/v1/delivery/parcels/types"


@pytest.mark.asyncio
async def test_parcels_types(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        response = await ac.get(URL)
    assert response.status_code == HTTPStatus.OK
    got = response.json()
    assert len(got) == len(INIT_PARCELS_TYPES)
    for item in response.json():
        assert ParcelType.model_validate(item).id