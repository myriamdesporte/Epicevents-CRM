from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from epicevents.database import Base


def utc_now() -> datetime:
    """Return the current date and time in UTC."""
    return datetime.now(timezone.utc)


class ModelBase(Base):
    """Abstract parent holding columns shared by every model."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
