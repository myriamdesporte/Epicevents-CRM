"""Read access to the collaborators."""

from sqlalchemy.orm import selectinload

from epicevents.models import User
from epicevents.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Queries about collaborators."""

    model = User

    # The role is loaded along with the collaborator
    default_options = (selectinload(User.role),)

    def get_by_email(self, email: str):
        """Return the collaborator having this email, or None."""
        query = self._select().where(User.email == email)
        return self.session.scalars(query).one_or_none()

    def get_by_employee_number(self, employee_number: str):
        """Return the collaborator having this employee number, or None."""
        query = self._select().where(User.employee_number == employee_number)
        return self.session.scalars(query).one_or_none()
