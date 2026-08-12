from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epicevents.models.base import ModelBase
from epicevents.security import hash_password, verify_password

if TYPE_CHECKING:
    from epicevents.models.client import Client
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
    assigned_events: Mapped[list["Event"]] = relationship(
        back_populates="support_contact"
    )

    def set_password(self, password: str) -> None:
        """Hash a plaintext password and store the hash."""
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        """Tell whether the given plaintext password matches the stored hash."""
        return verify_password(self.password_hash, password)

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, employee_number={self.employee_number!r}, "
            f"email={self.email!r}, role_id={self.role_id!r})"
        )
