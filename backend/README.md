# PQShield Backend

The backend of **PQShield** is built with **FastAPI** and follows a modular architecture designed to remain maintainable as the application grows.

The backend is organized as a **modular monolith**. Features are separated into independent modules while remaining part of the same FastAPI application.

## Architecture

```text
backend/
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   │
│   ├── api/
│   │   ├── router.py
│   │   └── dependencies.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   │
│   ├── modules/
│   │   └── <feature>/
│   │
│   └── shared/
│       ├── pagination.py
│       └── utils.py
│
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## `app/main.py`

The main entry point of the FastAPI application.

Its responsibilities should remain minimal:

- Create the FastAPI application.
- Register API routers.
- Register global middleware.
- Register global exception handlers.
- Configure application-level behavior.

Business logic should **never** be placed directly in `main.py`.

---

# `app/core/`

Contains application-wide infrastructure and configuration.

This directory should contain functionality that is not specific to a particular business feature.

## `core/config.py`

Central configuration management.

Responsible for reading and validating environment variables such as:

- Database URL
- Secret keys
- JWT configuration
- Redis configuration
- CORS configuration
- Application environment
- External service configuration

Configuration should be accessed through a central settings object instead of reading environment variables throughout the application.

## `core/security.py`

Contains security-related functionality.

Examples:

- Password hashing
- Password verification
- JWT creation
- JWT validation
- Authentication-related security helpers
- Permission-related helpers

Authentication business logic itself belongs inside the appropriate feature module, such as `modules/auth/`.

## `core/logging.py`

Central logging configuration.

Responsible for:

- Log formatting
- Log levels
- Application logging configuration
- Structured logging configuration if introduced later

Feature modules should use the application's logging configuration rather than configuring independent loggers.

## `core/exceptions.py`

Contains application-wide custom exceptions and exception handling.

Examples:

- Resource not found
- Authentication errors
- Permission errors
- Business rule violations

Global exception handlers can also be registered from this layer.

---

# `app/api/`

Contains the API-level composition and reusable FastAPI dependencies.

## `api/router.py`

The central API router.

Individual feature modules expose their own routers.

For example:

```text
modules/
├── auth/
│   └── router.py
└── users/
    └── router.py
```

`api/router.py` combines them into the application's API.

The API can be versioned:

```text
/api/v1/...
```

For example:

```text
/api/v1/auth/login
/api/v1/users/me
```

## `api/dependencies.py`

Contains reusable FastAPI dependencies.

Examples:

- Current authenticated user
- Database session dependencies
- Permission checks
- Common request dependencies

Dependencies that are highly specific to a particular feature may instead remain inside that feature's module.

---

# `app/db/`

Contains database infrastructure.

## `db/session.py`

Responsible for database connection/session management.

This is where the application's database engine and session factory are configured.

The database layer should support proper session lifecycle management so database connections are not leaked.

## `db/base.py`

Contains the database model base/metadata configuration.

Database models from individual feature modules can be registered with the application's SQLAlchemy metadata through this layer.

Database migration configuration will also use this metadata.

---

# `app/modules/`

This is the most important part of the application's business architecture.

Each major PQShield feature should have its own module.

For example:

```text
modules/
├── auth/
├── users/
├── organizations/
├── projects/
└── ...
```

A feature module should contain everything primarily related to that feature.

A typical module looks like:

```text
auth/
├── __init__.py
├── router.py
├── schemas.py
├── models.py
├── service.py
└── repository.py
```

## `router.py`

Defines the HTTP API for the feature.

Responsibilities:

- Define endpoints
- Receive validated request data
- Call the appropriate service
- Return responses
- Handle HTTP-specific concerns

The router should not contain substantial business logic.

Example flow:

```text
HTTP Request
     ↓
router.py
     ↓
service.py
     ↓
repository.py
     ↓
database
```

## `schemas.py`

Contains Pydantic request and response schemas.

Examples:

```text
CreateUserRequest
LoginRequest
UserResponse
TokenResponse
```

Schemas describe the API contract.

They should not be confused with database models.

## `models.py`

Contains SQLAlchemy database models belonging to the feature.

For example:

```text
User
Organization
Project
```

Database models represent how information is stored.

Pydantic schemas represent how information enters and leaves the API.

## `service.py`

Contains the feature's business logic.

Examples:

- Validate business rules
- Coordinate multiple repositories
- Perform calculations
- Execute workflows
- Decide what operations should happen

The service layer should not be responsible for HTTP details.

## `repository.py`

Contains database access specific to the feature.

Examples:

- Find a user
- Create a user
- Update a project
- Query records
- Delete records

The repository abstracts database operations away from the service layer.

---

# `app/shared/`

Contains genuinely reusable functionality that does not belong to one particular feature.

## `shared/pagination.py`

Reusable pagination functionality.

For example:

```text
page
page_size
offset
limit
pagination metadata
```

## `shared/utils.py`

Contains small reusable utilities that are genuinely shared across multiple modules.

Avoid turning this into a dumping ground.

If a function belongs specifically to authentication, users, projects, etc., it should remain inside that module instead.

---

# Feature Module Rules

When adding a new PQShield feature, create a module under:

```text
app/modules/
```

For example:

```text
app/modules/projects/
├── __init__.py
├── router.py
├── schemas.py
├── models.py
├── service.py
└── repository.py
```

Then register its router in:

```text
app/api/router.py
```

The normal request flow should be:

```text
Client
  ↓
FastAPI Router
  ↓
Service
  ↓
Repository
  ↓
Database
```

Not:

```text
Client
  ↓
Router
  ↓
SQL queries + business logic + authentication + validation
```

Keep HTTP concerns, business logic, and persistence concerns separated.

---

# Dependency Direction

The preferred dependency direction is:

```text
Router
  ↓
Service
  ↓
Repository
  ↓
Database
```

Supporting infrastructure can be used by the appropriate layers:

```text
core/
  ↑
  ├── routers
  ├── services
  └── repositories
```

Avoid circular dependencies between feature modules.

If two modules need to communicate, prefer explicit service interfaces or shared domain functionality rather than importing implementation details from each other indiscriminately.

---

# API Versioning

Public APIs should be versioned from the beginning.

Example:

```text
/api/v1/auth/login
/api/v1/users/me
/api/v1/projects
```

Future breaking changes can then be introduced as:

```text
/api/v2/...
```

without immediately breaking existing clients.

---

# Environment Configuration

Environment-specific configuration should not be hardcoded.

Use:

```text
.env
```

for local development and:

```text
.env.example
```

as the documented template.

Secrets must never be committed to Git.

Example configuration categories:

```text
DATABASE_URL
SECRET_KEY
JWT_SECRET_KEY
JWT_ALGORITHM
REDIS_URL
CORS_ORIGINS
ENVIRONMENT
```

Production secrets should be provided through the deployment platform's secret/environment-variable system.

---

# Database

The application is designed to use PostgreSQL as the primary relational database.

Database schema changes should be managed through migrations rather than manually modifying production databases.

The intended database stack is:

```text
FastAPI
   ↓
SQLAlchemy
   ↓
Alembic
   ↓
PostgreSQL
```

---

# Development Principles

The backend follows these principles:

1. Keep `main.py` small.
2. Organize business functionality by feature.
3. Keep routers focused on HTTP concerns.
4. Keep business logic inside services.
5. Keep database operations inside repositories.
6. Keep database models separate from API schemas.
7. Centralize configuration.
8. Never commit secrets.
9. Avoid unnecessary abstractions.
10. Avoid premature microservices.
11. Keep modules independently understandable.
12. Prefer explicit dependencies over hidden global state.

---

# Current Architecture

PQShield currently uses a modular-monolith architecture:

```text
                    ┌─────────────────┐
                    │     Client      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    FastAPI      │
                    │    API Layer    │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
          Feature Module             Feature Module
          auth / users / ...         ...
                │                         │
                └────────────┬────────────┘
                             ▼
                       PostgreSQL
```

This structure is intentionally designed so that the application can grow without requiring an immediate transition to microservices.

If a particular feature eventually requires independent scaling, deployment, or ownership, that feature can be extracted into a separate service later.

# Authentication Module — Code Example

The following example demonstrates how the Authentication module is organized in practice.

The code is intentionally simplified. It demonstrates **where each responsibility belongs**, rather than implementing the complete production authentication system.

```text
app/
└── modules/
    └── auth/
        ├── __init__.py
        ├── router.py
        ├── schemas.py
        ├── models.py
        ├── service.py
        └── repository.py
```

---

## 1. `schemas.py` — API Data

Pydantic schemas define what data the API accepts and returns.

```python
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
```

For example, the frontend sends:

```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

FastAPI validates this data using `LoginRequest`.

If the email is invalid or required fields are missing, FastAPI can reject the request before it reaches the service layer.

---

# 2. `models.py` — Database Model

SQLAlchemy models represent data stored in PostgreSQL.

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
```

This represents a database table conceptually like:

```text
users
--------------------------------
id
email
password_hash
```

Notice that the database stores `password_hash`, **not the user's plain-text password**.

---

# 3. `repository.py` — Database Operations

The repository handles database access.

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User


class AuthRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(
        self,
        email: str,
    ) -> User | None:

        result = await self.db.execute(
            select(User).where(User.email == email)
        )

        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password_hash: str,
    ) -> User:

        user = User(
            email=email,
            password_hash=password_hash,
        )

        self.db.add(user)

        await self.db.flush()

        return user
```

The repository's responsibility is essentially:

> "How do I retrieve or store authentication-related data in the database?"

It should **not decide whether a password is valid** or whether registration is allowed.

---

# 4. `service.py` — Business Logic

The service contains the actual authentication logic.

```python
from app.modules.auth.repository import AuthRepository


class AuthService:

    def __init__(self, repository: AuthRepository):
        self.repository = repository

    async def register(
        self,
        email: str,
        password: str,
    ):

        existing_user = await self.repository.get_user_by_email(
            email
        )

        if existing_user:
            raise ValueError("User already exists")

        password_hash = hash_password(password)

        user = await self.repository.create_user(
            email=email,
            password_hash=password_hash,
        )

        return user
```

The service answers questions such as:

```text
Does the user already exist?
Is the password valid?
Should this operation be allowed?
What business operation should happen?
```

It coordinates the necessary operations but doesn't directly execute SQL queries.

---

# 5. `router.py` — HTTP Layer

The router exposes the service through HTTP endpoints.

```python
from fastapi import APIRouter, Depends, status

from app.modules.auth.schemas import RegisterRequest
from app.modules.auth.service import AuthService

router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    user = await service.register(
        email=data.email,
        password=data.password,
    )

    return {
        "id": user.id,
        "email": user.email,
    }
```

The router's responsibility is mainly:

```text
HTTP request
     ↓
Validate request
     ↓
Call service
     ↓
Return HTTP response
```

The router should **not** contain code such as:

```python
password_hash = bcrypt.hash(...)
```

or:

```python
result = await db.execute(...)
```

Those responsibilities belong elsewhere.

---

# 6. Putting Everything Together

The complete flow becomes:

```text
Frontend
   │
   │ POST /api/v1/auth/register
   │
   ▼
┌───────────────────┐
│     router.py     │
│                   │
│ RegisterRequest   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│     service.py    │
│                   │
│ Business Logic    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│   repository.py   │
│                   │
│ Database Access   │
└─────────┬─────────┘
          │
          ▼
      PostgreSQL
```

The response travels back in the opposite direction:

```text
PostgreSQL
    ↓
Repository
    ↓
Service
    ↓
Router
    ↓
Frontend
```

---

# 7. Why Not Put Everything in `router.py`?

You could technically write this:

```python
@router.post("/register")
async def register(data: RegisterRequest):

    user = await db.execute(...)

    if user:
        ...

    password_hash = bcrypt.hashpw(...)

    new_user = User(...)

    await db.commit()

    return ...
```

FastAPI will allow it.

The problem is that the router now contains:

```text
HTTP handling
+
business logic
+
password handling
+
database queries
+
database persistence
```

As the application grows, this becomes difficult to maintain and test.

Instead:

```text
router.py
    ↓
service.py
    ↓
repository.py
```

keeps each layer focused.

---

# 8. What Each Layer Knows

A useful mental model is:

| Layer           | Knows about                     |
| --------------- | ------------------------------- |
| `router.py`     | HTTP, FastAPI, request/response |
| `schemas.py`    | API data structure              |
| `service.py`    | Business rules                  |
| `repository.py` | Database queries                |
| `models.py`     | Database structure              |

For example:

```text
Router:
"Someone sent POST /register."

Service:
"Registration requires a unique email and a hashed password."

Repository:
"Here is how I find/create the user in PostgreSQL."

Model:
"This is what a User looks like in the database."

Schema:
"This is what the API expects from the frontend."
```

This separation is the main architectural principle behind the module structure.

---

# 9. Dependencies Connect the Layers

FastAPI's dependency injection can be used to construct the dependencies:

```python
async def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:

    repository = AuthRepository(db)

    return AuthService(repository)
```

Then the router only needs:

```python
@router.post("/register")
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    return await service.register(
        email=data.email,
        password=data.password,
    )
```

The dependency chain becomes:

```text
FastAPI
   │
   ▼
get_db()
   │
   ▼
AuthRepository
   │
   ▼
AuthService
   │
   ▼
router endpoint
```

This is how the different pieces are connected without manually creating everything inside every endpoint.

---

# 10. Important Principle

Not every module must contain exactly these five files.

For a very small feature, you might only need:

```text
feature/
├── router.py
└── schemas.py
```

For a complex feature, you might eventually have:

```text
feature/
├── router.py
├── schemas.py
├── models.py
├── service.py
├── repository.py
├── dependencies.py
├── permissions.py
└── exceptions.py
```

The architecture should grow according to the complexity of the feature.

The goal is **separation of responsibilities**, not creating files just for the sake of having files.

# Main API Router — Connecting Feature Modules

Each feature module has its own `router.py`, but those routers need to be connected to the main FastAPI application.

The responsibility is divided into two levels:

```text
app/
├── main.py
│
├── api/
│   └── router.py          ← Main API router
│
└── modules/
    ├── auth/
    │   └── router.py      ← Authentication routes
    │
    ├── users/
    │   └── router.py      ← User routes
    │
    └── projects/
        └── router.py      ← Project routes
```

## 1. Feature Router

For example, the authentication module defines its own router:

```python
# app/modules/auth/router.py

from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register():
    ...


@router.post("/login")
async def login():
    ...
```

The authentication module does not need to know about the other modules.

Its router only defines authentication-related endpoints.

---

## 2. Main API Router

The main API router is responsible for combining all feature routers.

```python
# app/api/router.py

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.projects.router import router as projects_router


api_router = APIRouter()


api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    projects_router,
    prefix="/projects",
    tags=["Projects"],
)
```

Now the main API router contains all feature routers.

The resulting endpoints are:

```text
POST /auth/register
POST /auth/login

GET  /users/me
GET  /users/{user_id}

GET  /projects
POST /projects
```

---

# 3. API Versioning

For PQShield, the API should be versioned from the beginning.

The main router can therefore use:

```python
# app/api/router.py

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.projects.router import router as projects_router


api_router = APIRouter(
    prefix="/api/v1",
)


api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    projects_router,
    prefix="/projects",
    tags=["Projects"],
)
```

Now the actual endpoints become:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login

GET  /api/v1/users/me
GET  /api/v1/users/{user_id}

GET  /api/v1/projects
POST /api/v1/projects
```

This is preferable because future breaking API changes can be introduced under:

```text
/api/v2/
```

without immediately replacing `/api/v1/`.

---

# 4. Connecting the Main Router to `main.py`

The final step is connecting `api_router` to the FastAPI application.

```python
# app/main.py

from fastapi import FastAPI

from app.api.router import api_router


app = FastAPI(
    title="PQShield API",
    version="1.0.0",
)


app.include_router(api_router)
```

That's all `main.py` needs to do for routing.

---

# 5. Complete Flow

The complete routing hierarchy is:

```text
                    FastAPI Application
                           │
                           ▼
                    app/main.py
                           │
                           ▼
                  app/api/router.py
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
           auth          users       projects
           router        router        router
              │            │            │
              ▼            ▼            ▼
          /auth/...     /users/...   /projects/...
```

For example, when the frontend sends:

```text
POST /api/v1/auth/login
```

FastAPI processes it approximately like this:

```text
Request
   │
   ▼
app/main.py
   │
   ▼
app/api/router.py
   │
   ▼
auth/router.py
   │
   ▼
auth/service.py
   │
   ▼
auth/repository.py
   │
   ▼
PostgreSQL
```

---

# 6. Why Have a Main API Router?

You could technically put every route directly into `main.py`:

```python
@app.post("/api/v1/auth/login")
async def login():
    ...


@app.get("/api/v1/users/me")
async def get_user():
    ...


@app.get("/api/v1/projects")
async def get_projects():
    ...
```

But as the application grows, `main.py` would become a huge collection of unrelated endpoints.

Instead:

```text
main.py
   ↓
api/router.py
   ↓
feature routers
```

keeps the application's entry point clean.

The responsibilities become:

```text
main.py
    → Create the FastAPI application

api/router.py
    → Combine application routes

module/router.py
    → Define routes for a specific feature
```

This gives PQShield a clear routing hierarchy and allows new modules to be added without turning `main.py` into a large file.
