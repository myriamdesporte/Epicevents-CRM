import enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String,
    Enum,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epicevents.database import Base


class Department(enum.Enum):
    """The three departments at Epic Events (a collaborator's role)."""

    SALES = "sales"
    SUPPORT = "support"
    MANAGEMENT = "management"


class User(Base):
    """An Epic Event collaborator, attached to a department."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    department: Mapped[Department] = mapped_column(Enum(Department))

    # Relationships
    clients: Mapped[list["Client"]] = relationship(back_populates="sales_contact")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="sales_contact")
    events: Mapped[list["Event"]] = relationship(back_populates="support_contact")

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, email={self.email!r}, "
            f"department={self.department.value!r})"
        )


class Client(Base):
    """A client company contact, managed by a sales collaborator."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(30))
    company_name: Mapped[str] = mapped_column(String(150))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Foreign key: each client is assigned to one sales user
    sales_contact_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    # Relationships
    sales_contact: Mapped["User"] = relationship(back_populates="clients")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="client")

    def __repr__(self):
        return (
            f"Client(id={self.id!r}, full_name={self.full_name!r}, "
            f"company_name={self.company_name!r})"
        )


class Contract(Base):
    """A contract between Epic Events and a client."""

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)

    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    amount_due: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_signed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Foreign keys
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    sales_contact_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="contracts")
    sales_contact: Mapped["User"] = relationship(back_populates="contracts")
    event: Mapped[Optional["Event"]] = relationship(back_populates="contract")

    def __repr__(self):
        return (
            f"Contract(id={self.id!r}, client_id={self.client_id!r}, "
            f"sales_contact_id={self.sales_contact_id!r}, is_signed={self.is_signed!r}"
        )


class Event(Base):
    """An event organized for a client, tied to a signed contract."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    location: Mapped[str] = mapped_column(String(255))
    attendees: Mapped[int] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Foreign key to the contract: one contract has at most one event
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), unique=True)

    # Foreign key to the support user: optional (an event may have no support yet)
    support_contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    # Relationships
    contract: Mapped["Contract"] = relationship(back_populates="event")
    support_contact: Mapped["User"] = relationship(back_populates="events")

    def __repr__(self):
        return (
            f"Event(id={self.id!r}, name={self.name!r}, "
            f"contract_id={self.contract_id!r}"
        )
