from epicevents.database import Base, engine
from epicevents import models  # noqa: F401 - needed to register models on Base

Base.metadata.create_all(engine)
print("Tables created successfully.")
