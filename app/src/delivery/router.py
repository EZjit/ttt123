from typing import Annotated, Iterable, Sequence
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Path, Query, Request, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.src.delivery.entities import (
    BackgroundCreationResponse,
    GetParcelResponseDTO,
    GetParcelsFilterParams,
    RegisterParcelDTO,
    RegisterParcelWithUserDTO,
    convert_parcel_to_response_dto,
)
from app.src.delivery.models import Parcel, ParcelType
from app.src.delivery.services.parcel_publisher import PublisherService
from app.src.delivery.services.parcels_service import ParcelService
from app.src.users.models import User
from app.src.users.services import UserService

delivery_router = APIRouter(route_class=DishkaRoute)


@delivery_router.get(
    "/parcels",
    tags=["api"],
    response_model=Iterable[GetParcelResponseDTO],
)
async def get_parcels(
    request: Request,
    filter_query: Annotated[GetParcelsFilterParams, Query()],
    user_service: FromDishka[UserService],
    parcel_service: FromDishka[ParcelService],
) -> Iterable[GetParcelResponseDTO]:
    "Returns user parcels"
    user: User = await user_service.get_user(session=request.session)
    parcels: Iterable[Parcel] = await parcel_service.get_parcels(
        user=user,
        filter_query=filter_query,
    )

    return (convert_parcel_to_response_dto(parcel) for parcel in parcels)


@delivery_router.get(
    "/parcels/types",
    tags=["api"],
    response_model=Sequence[ParcelType],
)
async def get_parcels_types(
    db_session: FromDishka[AsyncSession],
) -> Sequence[ParcelType]:
    "Returns all parcels type"
    async with db_session as session:
        results = await session.exec(
            select(ParcelType).order_by(ParcelType.name),
        )
    return results.all()


@delivery_router.post(
    "/parcels",
    tags=["api"],
    status_code=status.HTTP_201_CREATED,
    response_model=Parcel,
)
async def register_parcel(
    request: Request,
    parcel_dto: RegisterParcelDTO,
    user_service: FromDishka[UserService],
    parcel_service: FromDishka[ParcelService],
) -> Parcel:
    "Returns parcel."
    user: User = await user_service.get_user(session=request.session)
    parcel: Parcel = await parcel_service.create_parcel(
        user=user,
        parcel_dto=parcel_dto,
    )
    return parcel


@delivery_router.post(
    "/parcels/background",
    tags=["api"],
    status_code=status.HTTP_201_CREATED,
    response_model=BackgroundCreationResponse,
)
async def register_parcel_with_mb(
    request: Request,
    parcel_dto: RegisterParcelDTO,
    user_service: FromDishka[UserService],
    publisher_service: FromDishka[PublisherService],
) -> BackgroundCreationResponse:
    "Returns simple object"
    user: User = await user_service.get_user(session=request.session)
    message: RegisterParcelWithUserDTO = RegisterParcelWithUserDTO(
        user_id=user.id,
        **parcel_dto.model_dump(),
    )
    await publisher_service.publish_message(message.model_dump_json())
    return BackgroundCreationResponse.IN_PROGRESS


@delivery_router.get(
    "/parcels/{parcel_id}",
    tags=["api"],
    response_model=GetParcelResponseDTO,
)
async def get_parcel(
    request: Request,
    parcel_id: Annotated[UUID, Path(title="Parcel id")],
    user_service: FromDishka[UserService],
    parcel_service: FromDishka[ParcelService],
) -> GetParcelResponseDTO:
    "Returns simple object"
    user: User = await user_service.get_user(session=request.session)
    parcel: Parcel | None = await parcel_service.get_parcel(
        user=user,
        parcel_id=parcel_id,
    )

    return convert_parcel_to_response_dto(parcel)