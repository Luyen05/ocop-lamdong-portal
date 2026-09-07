from fastapi import APIRouter

from app.api.routes import admin, auth, categories, products, subject_applications, system


api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(subject_applications.router)
api_router.include_router(admin.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
