from fastapi import Depends

from sqlalchemy.orm import Session

from app.db.session import get_session
from app.modules.accounts.store import UserStore
from app.modules.accounts.service import UserService

def get_user_store(session: Session = Depends(get_session)) -> UserStore:
    return UserStore(session)

def get_user_service(user_store: UserStore = Depends(get_user_store)) -> UserService:
    return UserService(user_store)
