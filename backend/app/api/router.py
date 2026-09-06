from fastapi import APIRouter

from app.api.routes import categories, system


api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(categories.router)
