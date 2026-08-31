from fastapi import APIRouter, Depends, status, BackgroundTasks
from uuid import UUID

from app.modules.accounts.dependencies import get_current_user
from app.modules.accounts.models import User
from app.modules.scans.dependencies import get_scan_service
from app.modules.scans.service import ScanService
from app.modules.scans.schemas import ScanResponse

router = APIRouter(prefix='/scans', tags=['scans'])

@router.post('/repository/{repository_id}', response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan(
    repository_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    service: ScanService = Depends(get_scan_service)
):
    return await service.trigger_scan(user.id, repository_id, background_tasks)

@router.get('/{scan_id}', response_model=ScanResponse)
async def get_scan_details(
    scan_id: UUID,
    user: User = Depends(get_current_user),
    service: ScanService = Depends(get_scan_service)
):
    return await service.get_scan(user.id, scan_id)

@router.get('/repository/{repository_id}', response_model=list[ScanResponse])
async def list_scans_by_repository(
    repository_id: UUID,
    user: User = Depends(get_current_user),
    service: ScanService = Depends(get_scan_service)
):
    return await service.list_scans(user.id, repository_id)
