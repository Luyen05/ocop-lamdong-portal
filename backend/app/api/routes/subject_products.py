from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.models.product import Product
from app.schemas.error import ErrorResponse
from app.schemas.product_management import (
    ManagedProductListResponse,
    ManagedProductRead,
    ProductWorkflowStatus,
    ProductWritePayload,
)
from app.services.product_workflow import (
    apply_product_payload,
    build_unique_slug,
    get_approved_subject,
    get_owned_product,
    product_load_options,
    to_managed_product_read,
    validate_certificate_is_current,
    workflow_error,
)


router = APIRouter(prefix="/products")
EDITABLE_STATUSES = {"draft", "needs_revision", "rejected"}


def commit_product(db: Session, product: Product) -> None:
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_CONFLICT",
            "Mã chứng nhận hoặc thông tin sản phẩm đã được sử dụng.",
        ) from exc


@router.get("", response_model=ManagedProductListResponse)
def list_my_products(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    product_status: ProductWorkflowStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> ManagedProductListResponse:
    subject = get_approved_subject(db, current_user)
    filters = [Product.subject_id == subject.id]
    if product_status:
        filters.append(Product.status == product_status)

    total = db.scalar(select(func.count(Product.id)).where(*filters)) or 0
    products = list(
        db.scalars(
            select(Product)
            .where(*filters)
            .options(*product_load_options())
            .order_by(Product.updated_at.desc(), Product.id.desc())
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


@router.post(
    "",
    response_model=ManagedProductRead,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
)
def create_product_draft(
    payload: ProductWritePayload,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedProductRead:
    subject = get_approved_subject(db, current_user)
    product = Product(
        subject_id=subject.id,
        category_id=payload.category_id,
        name=payload.name,
        slug=build_unique_slug(db, payload.name),
        star=payload.star,
        price=payload.price,
        unit=payload.unit,
        description=payload.description,
        status="draft",
    )
    apply_product_payload(db, product, payload, update_slug=False)
    commit_product(db, product)
    return to_managed_product_read(get_owned_product(db, product.id, subject.id))


@router.get("/{product_id}", response_model=ManagedProductRead)
def get_my_product(
    product_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedProductRead:
    subject = get_approved_subject(db, current_user)
    return to_managed_product_read(get_owned_product(db, product_id, subject.id))


@router.put("/{product_id}", response_model=ManagedProductRead)
def update_product_draft(
    product_id: int,
    payload: ProductWritePayload,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedProductRead:
    subject = get_approved_subject(db, current_user)
    product = get_owned_product(db, product_id, subject.id)
    if product.status not in EDITABLE_STATUSES:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_NOT_EDITABLE",
            "Chỉ bản nháp hoặc hồ sơ cần chỉnh sửa mới được cập nhật trực tiếp.",
            {"current_status": product.status},
        )
    apply_product_payload(db, product, payload, update_slug=True)
    commit_product(db, product)
    return to_managed_product_read(get_owned_product(db, product.id, subject.id))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_draft(
    product_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Response:
    subject = get_approved_subject(db, current_user)
    product = get_owned_product(db, product_id, subject.id)
    if product.status not in EDITABLE_STATUSES:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_CANNOT_BE_DELETED",
            "Sản phẩm đã gửi duyệt hoặc đã công khai không thể xóa trực tiếp.",
            {"current_status": product.status},
        )
    db.delete(product)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{product_id}/submit", response_model=ManagedProductRead)
def submit_product_for_moderation(
    product_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedProductRead:
    subject = get_approved_subject(db, current_user)
    product = get_owned_product(db, product_id, subject.id)
    if product.status not in EDITABLE_STATUSES:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_CANNOT_BE_SUBMITTED",
            "Sản phẩm không ở trạng thái có thể gửi duyệt.",
            {"current_status": product.status},
        )
    validate_certificate_is_current(product)
    if not product.images or sum(image.is_primary for image in product.images) != 1:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "PRIMARY_IMAGE_REQUIRED",
            "Sản phẩm phải có đúng một ảnh chính trước khi gửi duyệt.",
        )
    product.status = "pending"
    product.submitted_at = datetime.now(timezone.utc)
    product.reviewed_by = None
    product.reviewed_at = None
    product.review_note = None
    commit_product(db, product)
    return to_managed_product_read(get_owned_product(db, product.id, subject.id))
