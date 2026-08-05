from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epicevents.models.base import ModelBase

if TYPE_CHECKING:
    from epicevents.models.client import Client
    from epicevents.models.contract import Contract
    from epicevents.models.event import Event
    from epicevents.models.role import Role


class User(ModelBase):
    """An Epic Events collaborator, identified by an employee number."""

    __tablename__ = "users"

    employee_number: Mapped[str] = mapped_column(String(20), unique=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    # Foreign key
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))

    # Relationships
    role: Mapped["Role"] = relationship(back_populates="users")
    managed_clients: Mapped[list["Client"]] = relationship(
        back_populates="sales_contact"
    )
    managed_contracts: Mapped[list["Contract"]] = relationship(
        back_populates="sales_contact"
    )
    assigned_events: Mapped[list["Event"]] = relationship(
        back_populates="support_contact"
    )

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, employee_number={self.employee_number!r}, "
            f"email={self.email!r}, role_id={self.role_id!r})"
        )
