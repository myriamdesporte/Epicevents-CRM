"""Shared behavior of the repositories."""

from sqlalchemy import select


class BaseRepository:
    """Read access to one model."""

    # Set by each subclass.
    model = None

    # Relations to load along with the objects.
    default_options = ()

    def __init__(self, session):
        self.session = session

    def _select(self):
        """Return the base query for this model, related objects included."""
        return select(self.model).options(*self.default_options)

    def list_all(self):
        """Return every object, oldest first."""
        query = self._select().order_by(self.model.id)
        return list(self.session.scalars(query))

    def get(self, object_id):
        """Return one object by its id, or None when it doesn't exist."""
        query = self._select().where(self.model.id == object_id)
        return self.session.scalars(query).one_or_none()
