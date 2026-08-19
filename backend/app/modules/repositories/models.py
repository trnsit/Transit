from datetime import datetime

from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.accounts.models import User

class Repository(Base):
    __tablename__ = 'repositories'

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id'), # ForeignKey will only give you the database-level relationship/constraint, not an ORM-level.
        nullable=False
    ) # This will only give you repository.user_id; no relationship between the tables users and repositories

    # Relationships are explicitly defined to access the table, like 'repository.user', or 'user.repositories'.
    # You define a relationship explicitly at the both sides for both-end access.

    # Create a relationship with the users table
    user: Mapped['User'] = relationship(
        back_populates='repositories' # The other-side attribute; named 'repositories there, in this case.
    )

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    external_repo_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    default_branch: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    is_private: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
