from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from app.db.session import get_session
from app.modules.accounts.models import User
from app.modules.accounts.store import UserStore
from app.modules.accounts.service import UserService
from app.security.jwt import decode_access_token

# OAuth2 scheme looking for token in 'Authorization: Bearer <token>' header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login') # Use standard url or register

def get_user_store(session: Session = Depends(get_session)) -> UserStore:
    return UserStore(session)

def get_user_service(user_store: UserStore = Depends(get_user_store)) -> UserService:
    return UserService(user_store)

async def get_current_user(token: str = Depends(oauth2_scheme), service: UserService = Depends(get_user_service)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    email: str = payload.get('sub')
    if email is None:
        raise credentials_exception
        
    user = await service.store.authenticate(email)
    if user is None:
        raise credentials_exception
        
    return user
