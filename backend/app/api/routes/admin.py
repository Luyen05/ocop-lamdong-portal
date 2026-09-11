from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser, require_roles
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.data_source import DataSource, ProductSource
from app.models.product import Product, ProductChangeRequest
from app.models.subject import Subject
from app.schemas.access import AdminAccessResponse, AdminDashboardResponse
from app.schemas.error import ErrorResponse
from app.api.routes import (
    admin_data_sources,
    admin_product_changes,
    admin_products,
    admin_subject_applications,
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)


@router.get(
    "/access",
    response_model=AdminAccessResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
)
def check_admin_access(current_user: CurrentUser) -> AdminAccessResponse:
    """Xác nhận JWT hiện tại thuộc một tài khoản admin đang hoạt động."""
    return AdminAccessResponse(role=RoleName(current_user.role.name))


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(db: Session = Depends(get_db)) -> AdminDashboardResponse:
    has_decision = (
        select(ProductSource.product_id)
        .join(DataSource, DataSource.id == ProductSource.source_id)
        .where(
            ProductSource.product_id == Product.id,
            ProductSource.evidence_role == "recognition",
            DataSource.document_number.is_not(None),
            func.length(func.trim(DataSource.document_number)) > 0,
        )
        .exists()
    )

    def count_products(*conditions) -> int:
        return db.scalar(select(func.count(Product.id)).where(*conditions)) or 0

    return AdminDashboardResponse(
        total_products=count_products(),
        approved_products=count_products(Product.status == "approved"),
        pending_products=count_products(Product.status == "pending"),
        pending_subject_applications=db.scalar(
            select(func.count(Subject.id)).where(Subject.status == "pending")
        ) or 0,
        pending_change_requests=db.scalar(
            select(func.count(ProductChangeRequest.id)).where(
                ProductChangeRequest.status == "pending"
            )
        ) or 0,
        products_missing_decision=count_products(~has_decision),
    )


router.include_router(
    admin_subject_applications.router,
    prefix="/subject-applications",
)
router.include_router(admin_products.router)
router.include_router(admin_product_changes.router)
router.include_router(admin_data_sources.router)
