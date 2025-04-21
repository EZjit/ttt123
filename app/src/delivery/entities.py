from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.src.delivery.models import Parcel


class BackgroundCreationResponse(str, Enum):
    IN_PROGRESS = "in progress"


class GetParcelsFilterParams(BaseModel):
    offset: int = 0
    limit: int = 100
    page_type: UUID | None = None
    with_delivery_price: bool | None = None


class RegisterParcelDTO(BaseModel):
    # idempotency key, remove default value in prod
    request_id: UUID = Field(default_factory=uuid4)

    weight: float = Field(1, ge=0)
    dollar_price: Decimal = Field(Decimal(1), ge=0)
    parcel_type_id: UUID
    name: str = ""


class RegisterParcelWithUserDTO(RegisterParcelDTO):
    user_id: UUID


class GetParcelResponseDTO(BaseModel):
    id: UUID
    name: str
    weight: float
    dollar_price: str
    delivery_price: str
    parcel_type_name: str
    user_id: UUID | None


def convert_parcel_to_response_dto(parcel: Parcel) -> GetParcelResponseDTO:
    return GetParcelResponseDTO(
        id=parcel.id,
        name=parcel.name,
        weight=parcel.weight,
        dollar_price=f"{parcel.dollar_price} $",
        delivery_price=f"{parcel.delivery_price} руб."
        if parcel.delivery_price is not None
        else "Не рассчитано",
        parcel_type_name=parcel.parcel_type.name,
        user_id=parcel.user_id,
    )