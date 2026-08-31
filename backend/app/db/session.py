from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings

engine = create_async_engine(settings.database_url) # Instantiate async engine

SessionLocal = async_sessionmaker(bind=engine) # Instantiate the Async Session Maker

# Global/Shared dependency provider for database sessions
async def get_session():
    session = SessionLocal()

    try:
        yield session

    finally:
        await session.close() # Close the session no matter if the execution happened if failed
