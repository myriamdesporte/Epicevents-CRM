"""Read access to the roles."""

from epicevents.models import Role
from epicevents.repositories.base import BaseRepository


class RoleRepository(BaseRepository):
    """Queries about roles."""

    model = Role

    def get_by_name(self, name: str):
        """Return the role having this name, or None."""
        query = self._select().where(Role.name == name)
        return self.session.scalars(query).one_or_none()

    def names(self) -> set[str]:
        """Return every role name known to the database."""
        return {role.name for role in self.list_all()}
