from sqlalchemy import text
from epicevents.database import engine

with engine.connect() as conn:
    result = conn.execute(text("SELECT version(), current_user;"))
    version, user = result.one()
    print(f"Connecté : {version}")
    print(f"Utilisateur : {user}")
