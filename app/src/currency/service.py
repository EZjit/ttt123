import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from http import HTTPStatus

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from redis import Redis

logger = logging.getLogger(__name__)


class ExchangeRateError(HTTPException):
    pass


class CBCurrency(BaseModel):
    ID: str
    NumCode: str
    CharCode: str
    Nominal: int
    Name: str
    Value: Decimal
    Previous: Decimal


class CBResponse(BaseModel):
    Date: datetime
    PreviousURL: str
    Timestamp: str
    Valute: dict[str, CBCurrency]


class CurrencyResponse(BaseModel):
    currency_name: str
    value: Decimal


CURRENCY_PREFIX = "CB_VALUE_"
LOCK_PREFIX = "LOCKED_CB_"
BLOCKING_TIMEOUT = 3


@dataclass
class ExchangeRateService:
    redis: Redis
    cb_url = "https://www.cbr-xml-daily.ru/daily_json.js"

    async def fetch_currency(self, currency: str = "USD") -> CurrencyResponse:
        """Got currency"""
        currency = currency.upper()
        return CurrencyResponse(
            currency_name=currency,
            value=Decimal(await self.get_currency(currency=currency)),
        )

    async def get_currency(self, currency: str) -> str:
        if value := await self._load_cached_currency(
            currency=currency,
        ):
            return value
        # in prod better way is using redis lock but it conflicts with fakeredis
        async with asyncio.Lock():
            return await self._load_cached_currency(
                currency=currency,
            ) or await self.request_currency_from_cb(currency=currency)

    async def _load_cached_currency(self, currency: str) -> str | None:
        value = await self.redis.get(f"{CURRENCY_PREFIX}{currency}")
        if value:
            logger.debug("%s got value:%s from cache", currency, value)

        return value

    async def request_currency_from_cb(self, currency: str) -> Decimal:
        try:
            cb_response: CBResponse = await self.get_from_cb()
        except ValidationError as ex:
            raise ExchangeRateError(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=ex,
            ) from ex
        if currency not in cb_response.Valute:
            raise ExchangeRateError(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"{currency} not found in answer",
            )
        await self.save_to_cache(
            currency=cb_response.Valute[currency],
            cb_date=cb_response.Date,
        )
        return str(cb_response.Valute[currency].Value)

    async def save_to_cache(
        self,
        currency: CBCurrency,
        cb_date: datetime,
    ) -> None:
        # get cache seconds till the next day
        next_day_start = (cb_date + timedelta(days=1)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        seconds_to_next_day = int((next_day_start - cb_date).total_seconds())

        await self.redis.set(
            f"{CURRENCY_PREFIX}{currency.CharCode}",
            value=str(currency.Value),
            ex=seconds_to_next_day,
        )

    async def fetch_cb(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.cb_url, timeout=3)
                response.raise_for_status()
        except httpx.HTTPStatusError as ex:
            raise ExchangeRateError(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=ex,
            ) from ex
        return response.json()

    async def get_from_cb(self):
        try:
            cb_response: CBResponse = CBResponse.model_validate(
                await self.fetch_cb(),
            )
        except ValidationError as ex:
            raise ExchangeRateError(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=ex,
            ) from ex
        return cb_response