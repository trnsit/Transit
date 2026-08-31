from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.repositories.store import RepositoryStore
from app.modules.repositories.service import RepositoryService

def get_repository_store(session: AsyncSession = Depends(get_session)) -> RepositoryStore:
    return RepositoryStore(session)

def get_repository_service(store: RepositoryStore = Depends(get_repository_store)) -> RepositoryService:
    return RepositoryService(store)
