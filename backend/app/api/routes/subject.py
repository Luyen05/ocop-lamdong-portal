from fastapi import APIRouter, Depends

from app.api.dependencies import require_roles
from app.api.routes import subject_product_changes, subject_products
from app.core.roles import RoleName


router = APIRouter(
    prefix="/subject",
    tags=["Subject"],
    dependencies=[Depends(require_roles(RoleName.SUBJECT))],
)
router.include_router(subject_products.router)
router.include_router(subject_product_changes.router)
