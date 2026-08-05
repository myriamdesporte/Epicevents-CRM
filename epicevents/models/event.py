from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epicevents.models.base import ModelBase

if TYPE_CHECKING:
    from epicevents.models.contract import Contract
    from epicevents.models.user import User


class Event(ModelBase):
    """An event organized for a client, tied to a signed contract."""

    __tablename__ = "events"

    name: Mapped[str] = mapped_column(String(150))

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    location: Mapped[str] = mapped_column(String(255))
    attendees: Mapped[int] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Foreign key to the contract: one contract has at most one event
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), unique=True)

    # Foreign key to the support collaborator: optional (an event may have no support yet)
    support_contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    # Relationships
    contract: Mapped["Contract"] = relationship(back_populates="event")
    support_contact: Mapped[Optional["User"]] = relationship(
        back_populates="assigned_events"
    )

    def __repr__(self):
        return (
            f"Event(id={self.id!r}, name={self.name!r}, "
            f"contract_id={self.contract_id!r}"
        )
