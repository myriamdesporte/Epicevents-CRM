from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epicevents.models.base import ModelBase

if TYPE_CHECKING:
    from epicevents.models.client import Client
    from epicevents.models.event import Event
    from epicevents.models.user import User


class Contract(ModelBase):
    """A contract between Epic Events and a client."""

    __tablename__ = "contracts"

    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    amount_due: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    is_signed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Foreign keys
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    sales_contact_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="contracts")
    sales_contact: Mapped["User"] = relationship(back_populates="managed_contracts")

    event: Mapped[Optional["Event"]] = relationship(back_populates="contract")

    def __repr__(self):
        return (
            f"Contract(id={self.id!r}, client_id={self.client_id!r}, "
            f"total_amount={self.total_amount!r}, is_signed={self.is_signed!r}"
        )
