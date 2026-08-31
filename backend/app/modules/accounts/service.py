from fastapi import HTTPException # An exception that FastAPI handles.

from app.modules.accounts.models import User
from app.modules.accounts.store import UserStore
from app.modules.accounts.schemas import UserCreate, UserResponse, Login
from app.security.password import hash_password, verify_password

class UserService:
    def __init__(self, user_store: UserStore):
        self.store = user_store

    # Make the method capable of receiving email, and getting the user object by the use of UserService
    async def authenticate(self, email) -> UserResponse:
        user = await self.store.authenticate(email)

        if not user:
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )

        return user

    async def login(self, login_data: Login) -> User:
        user = await self.store.authenticate(login_data.email)

        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail='Incorrect email or password'
            )

        return user

    async def create(self, user: UserCreate) -> User:
        if await self.store.authenticate(user.email):
            raise HTTPException(
                status_code=409,
                detail='User already exists'
            )

        password_hash = hash_password(user.password)

        return await self.store.create(
            email=user.email,
            password_hash=password_hash
        )
