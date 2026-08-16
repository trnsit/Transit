from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url) # Instantiate engine

SessionLocal = sessionmaker(bind=engine) # Instantiate the Session Maker

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close() # Close the session no matter if the execution happened if failed
