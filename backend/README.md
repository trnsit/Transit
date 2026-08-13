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

* Create the FastAPI application.
* Register API routers.
* Register global middleware.
* Register global exception handlers.
* Configure application-level behavior.

Business logic should **never** be placed directly in `main.py`.

---

# `app/core/`

Contains application-wide infrastructure and configuration.

This directory should contain functionality that is not specific to a particular business feature.

## `core/config.py`

Central configuration management.

Responsible for reading and validating environment variables such as:

* Database URL
* Secret keys
* JWT configuration
* Redis configuration
* CORS configuration
* Application environment
* External service configuration

Configuration should be accessed through a central settings object instead of reading environment variables throughout the application.

## `core/security.py`

Contains security-related functionality.

Examples:

* Password hashing
* Password verification
* JWT creation
* JWT validation
* Authentication-related security helpers
* Permission-related helpers

Authentication business logic itself belongs inside the appropriate feature module, such as `modules/auth/`.

## `core/logging.py`

Central logging configuration.

Responsible for:

* Log formatting
* Log levels
* Application logging configuration
* Structured logging configuration if introduced later

Feature modules should use the application's logging configuration rather than configuring independent loggers.

## `core/exceptions.py`

Contains application-wide custom exceptions and exception handling.

Examples:

* Resource not found
* Authentication errors
* Permission errors
* Business rule violations

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

* Current authenticated user
* Database session dependencies
* Permission checks
* Common request dependencies

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

* Define endpoints
* Receive validated request data
* Call the appropriate service
* Return responses
* Handle HTTP-specific concerns

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

* Validate business rules
* Coordinate multiple repositories
* Perform calculations
* Execute workflows
* Decide what operations should happen

The service layer should not be responsible for HTTP details.

## `repository.py`

Contains database access specific to the feature.

Examples:

* Find a user
* Create a user
* Update a project
* Query records
* Delete records

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
