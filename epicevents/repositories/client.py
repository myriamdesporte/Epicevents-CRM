"""Read access to the clients."""

from sqlalchemy.orm import selectinload

from epicevents.models import Client
from epicevents.repositories.base import BaseRepository


class ClientRepository(BaseRepository):
    """Queries about clients."""

    model = Client
    default_options = (selectinload(Client.sales_contact),)

    def list_for_sales_contact(self, user_id: int):
        """Return the clients a given sales collaborator is responsible for."""
        query = (
            self._select().where(Client.sales_contact_id == user_id).order_by(Client.id)
        )
        return list(self.session.scalars(query))
