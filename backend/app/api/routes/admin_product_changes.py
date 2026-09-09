from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.models.product import Product, ProductChangeRequest
from app.models.subject import Subject
from app.schemas.product_management import (
    ProductChangeRequestListResponse,
    ProductChangeRequestRead,
    ProductChangeStatus,
    ProductModerationRequest,
    ProductWritePayload,
)
from app.services.product_workflow import (
    apply_product_payload,
    change_request_load_options,
    get_change_request,
    to_change_request_read,
    validate_certificate_is_current,
    workflow_error,
)


router = APIRouter(prefix="/product-change-requests")
RequestType = Literal["update", "delete"]


@router.get("", response_model=ProductChangeRequestListResponse)
def list_product_change_requests(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request_status: ProductChangeStatus | None = Query(default=None, alias="status"),
    request_type: RequestType | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    db: Session = Depends(get_db),
) -> ProductChangeRequestListResponse:
    filters = []
    if request_status:
        filters.append(ProductChangeRequest.status == request_status)
    if request_type:
        filters.append(ProductChangeRequest.request_type == request_type)
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(or_(Product.name.ilike(keyword), Subject.name.ilike(keyword)))

    base = (
        select(ProductChangeRequest)
        .join(ProductChangeRequest.product)
        .join(Product.subject)
        .where(*filters)
    )
    total = db.scalar(
        select(func.count(ProductChangeRequest.id))
        .join(ProductChangeRequest.product)
        .join(Product.subject)
        .where(*filters)
    ) or 0
    request_order = case(
        (ProductChangeRequest.status == "pending", 0),
        (ProductChangeRequest.status == "needs_revision", 1),
        else_=2,
    )
    requests = list(
        db.scalars(
            base.options(*change_request_load_options())
            .order_by(
                request_order,
                ProductChangeRequest.submitted_at.desc(),
                ProductChangeRequest.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return ProductChangeRequestListResponse(
        items=[to_change_request_read(item) for item in requests],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{request_id}", response_model=ProductChangeRequestRead)
def get_product_change_request(
    request_id: int,
    db: Session = Depends(get_db),
) -> ProductChangeRequestRead:
    return to_change_request_read(get_change_request(db, request_id))


@router.patch("/{request_id}/moderation", response_model=ProductChangeRequestRead)
def moderate_product_change_request(
    request_id: int,
    payload: ProductModerationRequest,
    current_admin: CurrentUser,
    db: Session = Depends(get_db),
) -> ProductChangeRequestRead:
    change_request = get_change_request(db, request_id, lock=True)
    if change_request.status != "pending":
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_CHANGE_REQUEST_ALREADY_REVIEWED",
            "Yêu cầu thay đổi này không còn ở trạng thái chờ duyệt.",
            {"current_status": change_request.status},
        )

    product = db.scalar(
        select(Product)
        .where(Product.id == change_request.product_id)
        .with_for_update()
    )
    if product is None:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_FOR_CHANGE_REQUEST_NOT_FOUND",
            "Sản phẩm của yêu cầu không còn tồn tại.",
        )

    if payload.status == "approved":
        if product.status != "approved":
            raise workflow_error(
                status.HTTP_409_CONFLICT,
                "PRODUCT_NOT_PUBLIC",
                "Chỉ có thể áp dụng yêu cầu cho sản phẩm đang được duyệt hiển thị.",
                {"current_status": product.status},
            )
        if product.version != change_request.base_version:
            raise workflow_error(
                status.HTTP_409_CONFLICT,
                "PRODUCT_VERSION_CONFLICT",
                "Sản phẩm đã thay đổi sau khi yêu cầu được tạo. Chủ thể cần tạo yêu cầu mới.",
                {
                    "base_version": change_request.base_version,
                    "current_version": product.version,
                },
            )
        if change_request.request_type == "update":
            proposed_data = ProductWritePayload.model_validate(
                change_request.proposed_data
            )
            apply_product_payload(db, product, proposed_data, update_slug=False)
            validate_certificate_is_current(product)
        else:
            product.status = "archived"
            product.review_note = change_request.reason
        product.version += 1
        db.add(product)

    change_request.status = payload.status
    change_request.reviewed_by = current_admin.id
    change_request.reviewed_at = datetime.now(timezone.utc)
    change_request.review_note = payload.note
    db.add(change_request)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_UPDATE_CONFLICT",
            "Không thể áp dụng yêu cầu vì dữ liệu mới bị trùng hoặc không còn hợp lệ.",
        ) from exc
    return to_change_request_read(get_change_request(db, change_request.id))
