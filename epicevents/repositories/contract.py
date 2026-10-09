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

    def list_filtered(
        self,
        *,
        unsigned: bool = False,
        unpaid: bool = False,
        sales_contact_id: int | None = None,
    ):
        """Return the contracts matching all the given criteria, oldest first.
        With no criterion, every contract is returned.
        """
        query = self._select()

        if unsigned:
            query = query.where(Contract.is_signed.is_(False))
        if unpaid:
            query = query.where(Contract.amount_due > 0)
        if sales_contact_id is not None:
            query = query.join(Contract.client).where(
                Client.sales_contact_id == sales_contact_id
            )

        return list(self.session.scalars(query.order_by(Contract.id)))
