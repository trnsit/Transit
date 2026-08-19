from fastapi import HTTPException # An exception that FastAPI handles.

from app.models.user import User
from app.stores.user import UserStore
from app.schemas.user import UserCreate, UserResponse
from app.security.password import hash_password, verify_password

class UserService:
    def __init__(self, user_store: UserStore):
        self.store = user_store

    # Make the method capable of receiving email, and getting the user object by the use of UserService
    async def get_by_email(self, email) -> UserResponse:
        user = await self.store.get_by_email(email)

        if not user:
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )

        return user

    async def create(self, user: UserCreate) -> User:
        if await self.store.get_by_email(user.email):
            raise HTTPException(
                status_code=409,
                detail='User already exists'
            )

        password_hash = hash_password(user.password)

        return await self.store.create(
            email=user.email,
            password_hash=password_hash
        )
