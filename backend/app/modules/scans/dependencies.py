from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.scans.store import ScanStore
from app.modules.scans.service import ScanService
from app.modules.repositories.dependencies import get_repository_store
from app.modules.repositories.store import RepositoryStore

def get_scan_store(session: AsyncSession = Depends(get_session)) -> ScanStore:
    return ScanStore(session)

def get_scan_service(
    scan_store: ScanStore = Depends(get_scan_store),
    repo_store: RepositoryStore = Depends(get_repository_store)
) -> ScanService:
    return ScanService(scan_store, repo_store)
