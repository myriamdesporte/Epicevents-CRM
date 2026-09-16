"""Data access layer of the Epic Events CRM.

One repository per model, each owning the queries about it. This is the only
layer that talks to the database: the interface never queries it, and the
business rules go through these classes.
"""

from epicevents.repositories.client import ClientRepository
from epicevents.repositories.contract import ContractRepository
from epicevents.repositories.event import EventRepository
from epicevents.repositories.role import RoleRepository
from epicevents.repositories.user import UserRepository

__all__ = [
    "ClientRepository",
    "ContractRepository",
    "EventRepository",
    "RoleRepository",
    "UserRepository",
]
