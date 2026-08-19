from fastapi import APIRouter, Depends

from pydantic import EmailStr

from app.modules.accounts.dependencies import get_user_service
from app.modules.accounts.service import UserService
from app.modules.accounts.schemas import UserCreate, UserResponse

router = APIRouter()

@router.get('/users/{email}', response_model=UserResponse)
# Pass the get_user_service function as the dependency
async def get_user(email: EmailStr, service: UserService = Depends(get_user_service)): # The Depends function represents the function as the dependency for FastAPI to manage its lifecycle.
    return await service.authenticate(email)

@router.post('/register', response_model=UserResponse)
async def create_user(user: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.create(user)
