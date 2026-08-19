from fastapi import FastAPI

from app.core.config import settings
from app.api.routes.users import router as user_router

import app.models

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

app.include_router(user_router) # Include the user router in app
