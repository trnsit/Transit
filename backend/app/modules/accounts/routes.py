from fastapi import APIRouter, Depends

from app.security.jwt import create_access_token
from app.modules.accounts.dependencies import get_user_service, get_current_user
from app.modules.accounts.schemas import UserCreate, UserResponse, Token, Login
from app.modules.accounts.service import UserService

router = APIRouter(tags=['accounts'])

@router.post('/register', response_model=UserResponse)
# Pass the get_user_service function as the dependency
async def create_user(user: UserCreate, service: UserService = Depends(get_user_service)):  # The Depends function represents the function as the dependency for FastAPI to manage its lifecycle.
    return await service.create(user)

@router.post('/login', response_model=Token)
async def login(login_data: Login, service: UserService = Depends(get_user_service)):
    user = await service.login(login_data)
    access_token = create_access_token(data={'sub': user.email})

    return {'access_token': access_token, 'token_type': 'bearer'}

@router.get('/users/me', response_model=UserResponse)
async def profile(current_user = Depends(get_current_user)):
    return current_user
