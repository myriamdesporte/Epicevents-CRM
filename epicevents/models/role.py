import enum
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epicevents.models.base import ModelBase

if TYPE_CHECKING:
    from epicevents.models.user import User


class RoleName(enum.StrEnum):
    """The rol names Epic Events works with, one per department."""

    SALES = "sales"
    SUPPORT = "support"
    MANAGEMENT = "management"


class Role(ModelBase):
    """A collaborator's role, matching one of the three departments."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True)

    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="role")

    def __repr__(self):
        return f"Role(id={self.id!r}, name={self.name!r}"
