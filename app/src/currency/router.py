from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Path

from app.src.currency.service import CurrencyResponse, ExchangeRateService

currency_router = APIRouter()


@currency_router.get(
    "/{currency}",
    tags=["api"],
    response_model=CurrencyResponse,
)
@inject
async def get_currency(
    currency: Annotated[str, Path(title="Currency")],
    service: FromDishka[ExchangeRateService],
) -> CurrencyResponse:
    "Returns currency value."

    return await service.fetch_currency(currency=currency.upper())