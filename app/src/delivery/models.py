from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from app.db import DatabaseSessionManager
from app.src.users.models import User


class ParcelType(SQLModel, table=True):
    __tablename__ = "parcel_types"
    id: UUID | None = Field(
        primary_key=True,
        default_factory=uuid4,
    )
    name: str = Field(unique=True)
    description: str = ""
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    parcels: list["Parcel"] = Relationship(  # noqa
        back_populates="parcel_type",
        cascade_delete=True,
    )


class Parcel(SQLModel, table=True):
    __tablename__ = "parcels"

    id: UUID | None = Field(
        primary_key=True,
        default_factory=uuid4,
    )
    name: str = ""
    weight: float = 0.0
    dollar_price: Decimal = Field(
        default=1,
        max_digits=10,
        decimal_places=2,
        ge=0,
    )

    delivery_price: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
        ge=0,
    )

    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    parcel_type_id: UUID | None = Field(
        default=None,
        foreign_key="parcel_types.id",
    )
    parcel_type: ParcelType | None = Relationship(
        back_populates="parcels",
    )
    request_id: UUID = Field(unique=True)  # idempotency key
    user_id: UUID | None = Field(
        default=None,
        foreign_key="user.id",  # Foreign key to User table
    )
    user: User | None = Relationship(
        back_populates="parcels",
    )


INIT_PARCELS_TYPES = (
    ParcelType(name="clothes", description="одежда"),
    ParcelType(name="electronics", description="электроника"),
    ParcelType(name="another", description="другое"),
)


async def init_parcel_types(session_manager: DatabaseSessionManager) -> None:
    async with session_manager.session() as session:
        async with session.begin():
            session.add_all(
                INIT_PARCELS_TYPES,
            )
        await session.commit()