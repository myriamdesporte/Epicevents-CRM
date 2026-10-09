"""Read access to the events."""

from sqlalchemy.orm import selectinload

from epicevents.models import Contract, Event
from epicevents.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    """Queries about events."""

    model = Event

    default_options = (
        selectinload(Event.support_contact),
        selectinload(Event.contract).selectinload(Contract.client),
    )

    def list_filtered(
        self, *, no_support: bool = False, support_contact_id: int | None = None
    ):
        """Return the events matching all the given criteria, oldest first.
        With no criterion, every event is returned.
        """
        query = self._select()

        if no_support:
            query = query.where(Event.support_contact_id.is_(None))
        if support_contact_id is not None:
            query = query.where(Event.support_contact_id == support_contact_id)

        return list(self.session.scalars(query.order_by(Event.id)))
