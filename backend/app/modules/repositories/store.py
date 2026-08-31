from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.modules.repositories.schemas import RepositoryCreate, RepositoryUpdate
from app.modules.repositories.models import Repository
from app.modules.accounts.models import UserOAuthToken

class RepositoryStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID, repository_id: UUID) -> Repository | None:
        result = await self.session.execute(
            select(Repository).where(
                Repository.id == repository_id,
                Repository.user_id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[Repository]:
        result = await self.session.execute(
            select(Repository).where(Repository.user_id == user_id)
        )

        return list(result.scalars().all()) # Retrieve everything. Notice 'scalars'; it's not 'scalar' in this case.

    async def create(self, user_id: UUID, data: RepositoryCreate) -> Repository:
        repository_orm = Repository(
            user_id=user_id,
            **data.model_dump()
        )

        self.session.add(repository_orm)
        await self.session.commit()
        await self.session.refresh(repository_orm)

        return repository_orm

    async def update(self, user_id: UUID, repository_id: UUID, data: RepositoryUpdate) -> Repository | None:
        repository = await self.get_by_id(user_id, repository_id)

        if not repository:
            return None

        for key, value in data.model_dump(exclude_unset=True).items(): # The 'exclude_unset' flag will exclude the fields those have not explicitly set.
            setattr(repository, key, value)

        await self.session.commit()
        await self.session.refresh(repository)

        return repository

    async def delete(self, user_id: UUID, repository_id: UUID) -> bool:
        repository = await self.get_by_id(user_id, repository_id)

        if not repository:
            return False

        await self.session.delete(repository) # The deletion method
        await self.session.commit()

        return True

    async def get_github_token(self, user_id: UUID) -> str | None:
        result = await self.session.execute(
            select(UserOAuthToken).where(
                UserOAuthToken.user_id == user_id,
                UserOAuthToken.provider == 'github'
            )
        )

        oauth_token = result.scalar_one_or_none()

        return oauth_token.access_token if oauth_token else None
