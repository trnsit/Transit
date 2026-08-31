import sys

import asyncio

if sys.platform == "win32":
    # Access dynamically to bypass IDE deprecation warnings in Python 3.14
    policy_class = getattr(asyncio, "WindowsSelectorEventLoopPolicy")
    set_policy = getattr(asyncio, "set_event_loop_policy")
    set_policy(policy_class())

from fastapi import FastAPI

from app.core.config import settings
from app.modules.accounts.routes import router as user_router
from app.modules.accounts.google_oauth_routes import router as google_oauth_router
from app.modules.accounts.github_oauth_routes import router as github_oauth_router
from app.modules.repositories.routes import router as repository_router
from app.modules.scans.routes import router as scan_router

import app.db

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

app.include_router(user_router) # Include local users router in app
app.include_router(google_oauth_router) # Include Google OAuth router
app.include_router(github_oauth_router) # Include GitHub OAuth router
app.include_router(repository_router) # Include repository router
app.include_router(scan_router) # Include scan router
