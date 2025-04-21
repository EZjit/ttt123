import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Iterable
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.src.currency.service import ExchangeRateService
from app.src.delivery.entities import GetParcelsFilterParams, RegisterParcelDTO
from app.src.delivery.models import Parcel

if TYPE_CHECKING:
    from app.src.users.models import User


class ParcelServiceError(HTTPException):
    pass


logger = logging.getLogger(__name__)


@dataclass
class ParcelService:
    db_session: AsyncSession
    exchange_service: ExchangeRateService

    async def get_parcel(
        self,
        user: "User",
        parcel_id=UUID,
    ) -> "Parcel":
        async with self.db_session as session:
            statement = (
                select(Parcel)
                .options(joinedload(Parcel.parcel_type))
                .where(Parcel.user_id == user.id, Parcel.id == parcel_id)
            )
            results = await session.exec(
                statement,
            )
            parcel = results.first()
        if not parcel:
            raise ParcelServiceError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not found",
            )
        return parcel

    async def get_parcels(
        self,
        user: "User",
        filter_query: GetParcelsFilterParams,
    ) -> Iterable["Parcel"]:
        async with self.db_session as session:
            statement = (
                select(Parcel)
                .options(joinedload(Parcel.parcel_type))
                .where(Parcel.user_id == user.id)
            )
            statement = self.apply_filters(statement, filter_query)
            results = await session.exec(
                statement.offset(filter_query.offset).limit(filter_query.limit),
            )
        parcels = results.all()

        return parcels

    def apply_filters(self, statement, filter_query: GetParcelsFilterParams):
        if filter_query.page_type:
            statement = statement.where(
                Parcel.parcel_type_id == filter_query.page_type,
            )
        if filter_query.with_delivery_price is not None:
            statement = (
                statement.where(
                    Parcel.delivery_price is None,
                )
                if filter_query.with_delivery_price is False
                else statement.where(
                    Parcel.delivery_price is not None,
                )
            )
        return statement

    async def create_parcel(
        self,
        user: "User",
        parcel_dto: RegisterParcelDTO,
    ) -> Parcel:
        async with self.db_session as session:
            return await self.check_create_request(
                parcel_dto.request_id,
                session=session,
            ) or await self.add_new_parcel(user, parcel_dto, session)

    async def calculate_delivery(self, parcel: Parcel) -> Decimal:
        usd_price = Decimal(
            await self.exchange_service.get_currency("USD"),
        )
        delivery_price = (
            parcel.dollar_price * Decimal(0.01)
            + Decimal(parcel.weight) * Decimal(0.5)
        ) * usd_price
        return delivery_price

    async def add_new_parcel(
        self,
        user: "User",
        parcel_dto: RegisterParcelDTO,
        session: AsyncSession,
    ) -> Parcel:
        new_parcel = Parcel(
            user=user,
            **parcel_dto.model_dump(),
        )
        new_parcel.delivery_price = await self.calculate_delivery(new_parcel)
        session.add(new_parcel)

        try:
            await session.commit()
        except SQLAlchemyError as ex:
            logger.error(ex)
            raise ParcelServiceError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Couldn't add parcel",
            ) from ex
        await session.refresh(new_parcel)
        return new_parcel

    async def check_create_request(
        self,
        request_id: UUID,
        session: AsyncSession,
    ) -> Parcel | None:
        result = await session.exec(
            select(Parcel).where(Parcel.request_id == request_id),
        )
        if parcel := result.first():
            logger.info("%s request checked, found saved entity", request_id)
            return parcel