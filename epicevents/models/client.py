from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epicevents.models.base import ModelBase

if TYPE_CHECKING:
    from epicevents.models.contract import Contract
    from epicevents.models.user import User


class Client(ModelBase):
    """A client company contact, followed by a one sales collaborator."""

    __tablename__ = "clients"

    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(30))
    company_name: Mapped[str] = mapped_column(String(150))

    # Foreign key: each client is assigned to one sales user
    sales_contact_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    sales_contact: Mapped["User"] = relationship(back_populates="managed_clients")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="client")

    def __repr__(self):
        return (
            f"Client(id={self.id!r}, full_name={self.full_name!r}, "
            f"company_name={self.company_name!r})"
        )
