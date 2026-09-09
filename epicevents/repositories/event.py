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

    def list_without_support(self):
        """Return the events with no support collaborator assigned yet."""
        query = self._select().where(Event.support_contact_id.is_(None))
        return list(self.session.scalars(query.order_by(Event.id)))

    def list_for_support_contact(self, user_id: int):
        """Return the events assigned to a given support collaborator."""
        query = (
            self._select().where(Event.support_contact_id == user_id).order_by(Event.id)
        )
        return list(self.session.scalars(query))

    def list_filtered(
        self, *, no_support: bool = False, support_contact_id: int | None = None
    ):
        """Return the events matching all the given criteria at once."""
        query = self._select()

        if no_support:
            query = query.where(Event.support_contact_id.is_(None))
        if support_contact_id is not None:
            query = query.where(Event.support_contact_id == support_contact_id)

        return list(self.session.scalars(query))
