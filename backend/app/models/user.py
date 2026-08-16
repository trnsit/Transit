from datetime import datetime

from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Just to keep the 'forward import' (like importing the 'Repository' class inside the relationship in this case) valid in the IDE; not necessary.
from typing import TYPE_CHECKING # A special flag provided by Python's 'typing' module.

# Only import when the type checker is parsing the code, not while executing it.
if TYPE_CHECKING: # When the type checker/IDE analyzes the code: True, else: False.
    from app.models.repository import Repository

class User(Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Define relationship to access the two-way access between users and repositories
    repositories: Mapped[list['Repository']] = relationship( # 'list' is because it's a one-to-many relationship; the user could have many repos.
        back_populates='user' # Because the corresponding attribute on the other side is named 'user'.
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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
