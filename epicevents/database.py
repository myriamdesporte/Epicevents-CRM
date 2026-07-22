from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from epicevents.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Declarative base class from which all ORM models will inherit."""

    pass
