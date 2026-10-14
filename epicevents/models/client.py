"""The Client model."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epicevents.models.base import ModelBase
from epicevents.models.encrypted import EncryptedString

if TYPE_CHECKING:
    from epicevents.models.contract import Contract
    from epicevents.models.user import User


class Client(ModelBase):
    """A client company contact, followed by one sales collaborator."""

    __tablename__ = "clients"

    # Personal data, encrypted in the database; lengths checked by the validators
    full_name: Mapped[str] = mapped_column(EncryptedString)
    email: Mapped[str] = mapped_column(EncryptedString)
    phone: Mapped[str] = mapped_column(EncryptedString)
    company_name: Mapped[str] = mapped_column(EncryptedString)

    # Foreign key: each client is assigned to one sales user
    sales_contact_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    sales_contact: Mapped["User"] = relationship(back_populates="managed_clients")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="client")

    def __repr__(self) -> str:
        return (
            f"Client(id={self.id!r}, full_name={self.full_name!r}, "
            f"company_name={self.company_name!r})"
        )
