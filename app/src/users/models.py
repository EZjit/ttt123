from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    pass


class User(SQLModel, table=True):
    id: UUID | None = Field(
        primary_key=True,
        default_factory=uuid4,
    )
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    parcels: list["Parcel"] = Relationship(  # noqa
        back_populates="user",
        cascade_delete=True,
    )
