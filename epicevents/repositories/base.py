"""Shared behavior of the repositories."""

from sqlalchemy import select


class BaseRepository:
    """Read and write access to one model."""

    # Set by each subclass.
    model = None

    # Relations to load along with the objects.
    default_options = ()

    # Columns update() refuses to touch
    protected_fields = frozenset({"id", "created_at", "updated_at"})

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

    def add(self, **fields):
        """Create an object from the given fields, save it, and return it."""
        created = self.model(**fields)
        self.session.add(created)
        self.session.commit()
        return created

    def update(self, obj, **changes):
        """Apply the given changes to an object, save it, and return it."""
        allowed = set(self.model.__table__.columns.keys()) - self.protected_fields
        refused = set(changes) - allowed

        if refused:
            raise ValueError(
                f"{self.model.__name__} cannot be updated with: "
                f"{', '.join(sorted(refused))}."
            )

        for field, value in changes.items():
            setattr(obj, field, value)

        self.session.commit()
        return obj

    def delete(self, obj) -> None:
        """Remove an object from the database."""
        self.session.delete(obj)
        self.session.commit()
