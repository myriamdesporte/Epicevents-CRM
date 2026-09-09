"""Read access to the contracts."""

from sqlalchemy.orm import selectinload

from epicevents.models import Client, Contract
from epicevents.repositories.base import BaseRepository


class ContractRepository(BaseRepository):
    """Queries about contracts."""

    model = Contract

    # The client is loaded, and its sales contact along with it: a contract has
    # no sales contact of its own, it inherits the one of its client.
    default_options = (
        selectinload(Contract.client).selectinload(Client.sales_contact),
    )

    def list_unsigned(self):
        """Return the contracts not signed yet."""
        query = self._select().where(Contract.is_signed.is_(False))
        return list(self.session.scalars(query.order_by(Contract.id)))

    def list_not_fully_paid(self):
        """Return the contracts still owing money."""
        query = self._select().where(Contract.amount_due > 0)
        return list(self.session.scalars(query.order_by(Contract.id)))

    def list_for_sales_contact(self, user_id: int):
        """Return the contracts of the clients a collaborator is responsible for."""
        query = (
            self._select()
            .join(Client)
            .where(Client.sales_contact_id == user_id)
            .order_by(Contract.id)
        )
        return list(self.session.scalars(query))
