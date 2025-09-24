from fastapi import APIRouter
from . import users, tasks, auth

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users.router,prefix="/users")
api_router.include_router(tasks.router,prefix="/tasks")
api_router.include_router(auth.router,prefix="/auth")
