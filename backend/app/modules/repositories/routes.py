from uuid import UUID

from fastapi import Depends, APIRouter, status

from app.modules.accounts.dependencies import get_current_user
from app.modules.repositories.dependencies import get_repository_service
from app.modules.repositories.schemas import RepositoryCreate, RepositoryUpdate, RepositoryResponse
from app.modules.repositories.service import RepositoryService
from app.modules.accounts.models import User

router = APIRouter(prefix='/repositories', tags=['repositories'])

@router.get('/{repository_id}', response_model=RepositoryResponse)
async def get_repository_by_id(repository_id: UUID, user: User = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.get_by_id(user.id, repository_id)

@router.get('', response_model=list[RepositoryResponse])
async def list_repository_by_user(user: User = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.list_by_user(user.id)

@router.post('', response_model=RepositoryResponse)
async def create_repository(data: RepositoryCreate, user: User = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.create(user.id, data)

@router.patch('/{repository_id}', response_model=RepositoryResponse)
async def update_repository(data: RepositoryUpdate, repository_id: UUID, user: User = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.update(user.id, repository_id, data)

@router.delete('/{repository_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(repository_id: UUID, user: User = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.delete(user.id, repository_id)

@router.get('/github/remote', response_model=list[RepositoryCreate])
async def list_remote_github_repositories(user: User = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.list_github_repositories(user.id)
