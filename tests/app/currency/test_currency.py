import json
from decimal import Decimal
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from dishka import AsyncContainer
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from app.src.currency.service import (
    CURRENCY_PREFIX,
    CBResponse,
    CurrencyResponse,
    ExchangeRateService,
)

CHECK_CURRENCY = "USD"

URL = f"/api/v1/currency/{CHECK_CURRENCY}"


@pytest.mark.anyio
async def test_currency(test_app, container: AsyncContainer):
    with open("./tests/app/currency/response.json") as file:
        mocked_response_json = json.load(file)
    file_cb_response: CBResponse = CBResponse.model_validate(
        mocked_response_json,
    )
    # check endpoint value

    with patch.object(
        ExchangeRateService,
        "fetch_cb",
        new=AsyncMock(return_value=mocked_response_json),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as ac:
            response = await ac.get(URL)
        assert response.status_code == HTTPStatus.OK
        got = CurrencyResponse.model_validate(response.json())
        assert (
            CurrencyResponse(
                currency_name=CHECK_CURRENCY,
                value=Decimal(file_cb_response.Valute[CHECK_CURRENCY].Value),
            )
            == got
        )
    # check cached value
    redis = await container.get(Redis)
    cached_value = await redis.get(f"{CURRENCY_PREFIX}{CHECK_CURRENCY}")
    assert Decimal(cached_value) == got.value