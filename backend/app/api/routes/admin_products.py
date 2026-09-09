from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.models.product import Product
from app.models.subject import Subject
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.product_management import (
    ManagedProductListResponse,
    ManagedProductRead,
    ProductModerationRequest,
    ProductWorkflowStatus,
)
from app.services.product_workflow import (
    get_product_for_admin,
    product_load_options,
    to_managed_product_read,
    validate_certificate_is_current,
    workflow_error,
)


router = APIRouter(prefix="/products")


@router.get("", response_model=ManagedProductListResponse)
def list_products_for_moderation(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    product_status: ProductWorkflowStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    db: Session = Depends(get_db),
) -> ManagedProductListResponse:
    filters = []
    if product_status:
        filters.append(Product.status == product_status)
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(
            or_(
                Product.name.ilike(keyword),
                Product.cert_code.ilike(keyword),
                Subject.name.ilike(keyword),
            )
        )

    total = db.scalar(
        select(func.count(Product.id)).join(Product.subject).where(*filters)
    ) or 0
    status_order = case(
        (Product.status == "pending", 0),
        (Product.status == "needs_revision", 1),
        (Product.status == "draft", 2),
        else_=3,
    )
    products = list(
        db.scalars(
            select(Product)
            .join(Product.subject)
            .where(*filters)
            .options(*product_load_options())
            .order_by(status_order, Product.submitted_at.desc(), Product.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return ManagedProductListResponse(
        items=[to_managed_product_read(product) for product in products],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{product_id}", response_model=ManagedProductRead)
def get_product_for_moderation(
    product_id: int,
    db: Session = Depends(get_db),
) -> ManagedProductRead:
    return to_managed_product_read(get_product_for_admin(db, product_id))


@router.patch(
    "/{product_id}/moderation",
    response_model=ManagedProductRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
def moderate_product(
    product_id: int,
    payload: ProductModerationRequest,
    current_admin: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedProductRead:
    product = get_product_for_admin(db, product_id, lock=True)
    if product.status != "pending":
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_ALREADY_REVIEWED",
            "Sản phẩm không còn ở trạng thái chờ duyệt.",
            {"current_status": product.status},
        )

    subject = db.scalar(
        select(Subject).where(Subject.id == product.subject_id).with_for_update()
    )
    owner = (
        db.scalar(select(User).where(User.id == subject.user_id).with_for_update())
        if subject
        else None
    )
    if subject is None or subject.status != "approved" or owner is None or not owner.is_active:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_SUBJECT_INACTIVE",
            "Không thể duyệt sản phẩm vì chủ thể không còn hợp lệ hoặc đã bị khóa.",
        )
    if payload.status == "approved":
        validate_certificate_is_current(product)

    product.status = payload.status
    product.reviewed_by = current_admin.id
    product.reviewed_at = datetime.now(timezone.utc)
    product.review_note = payload.note
    if payload.status == "approved":
        product.version += 1
    db.add(product)
    db.commit()
    return to_managed_product_read(get_product_for_admin(db, product.id))
