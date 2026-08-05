"""Create the database tables."""

from sqlalchemy import select

from epicevents.database import Base, engine, Session
from epicevents.models import Role, RoleName


def create_tables() -> None:
    """Create every table declared on Base that does not exist yet."""
    Base.metadata.create_all(engine)
    print("Tables created successfully.")


def seed_roles() -> None:
    """Insert the three Epic Events roles, skipping those already present."""
    with Session() as session:
        existing = set(session.scalars(select(Role.name)))
        for role_name in RoleName:
            if role_name not in existing:
                session.add(Role(name=role_name))
                print(f"Role '{role_name}‘ created.")
        session.commit()


if __name__ == "__main__":
    create_tables()
    seed_roles()
