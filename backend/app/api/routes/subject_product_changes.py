from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.models.product import ProductChangeRequest
from app.schemas.product_management import (
    ProductChangeRequestListResponse,
    ProductChangeRequestRead,
    ProductChangeRevision,
    ProductChangeStatus,
    ProductDeleteRequestCreate,
    ProductUpdateRequestCreate,
)
from app.services.product_workflow import (
    change_request_load_options,
    get_approved_subject,
    get_change_request,
    get_owned_product,
    to_change_request_read,
    validate_certificate_storage,
    workflow_error,
)


router = APIRouter()
ACTIVE_REQUEST_STATUSES = {"pending", "needs_revision"}


def ensure_product_accepts_request(db: Session, product_id: int, subject_id: int):
    product = get_owned_product(db, product_id, subject_id)
    if product.status != "approved":
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "APPROVED_PRODUCT_REQUIRED",
            "Chỉ sản phẩm đã duyệt mới sử dụng yêu cầu thay đổi.",
            {"current_status": product.status},
        )
    active_request_id = db.scalar(
        select(ProductChangeRequest.id).where(
            ProductChangeRequest.product_id == product.id,
            ProductChangeRequest.status.in_(ACTIVE_REQUEST_STATUSES),
        )
    )
    if active_request_id is not None:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "ACTIVE_PRODUCT_CHANGE_REQUEST_EXISTS",
            "Sản phẩm đang có một yêu cầu thay đổi chưa xử lý.",
            {"request_id": active_request_id},
        )
    return product


def save_change_request(db: Session, change_request: ProductChangeRequest) -> None:
    db.add(change_request)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_CHANGE_REQUEST_CONFLICT",
            "Sản phẩm đang có một yêu cầu thay đổi chưa xử lý.",
        ) from exc


@router.post(
    "/products/{product_id}/change-requests",
    response_model=ProductChangeRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def request_product_update(
    product_id: int,
    payload: ProductUpdateRequestCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ProductChangeRequestRead:
    subject = get_approved_subject(db, current_user)
    product = ensure_product_accepts_request(db, product_id, subject.id)
    validate_certificate_storage(product, payload.proposed_data.certificate_storage_path)
    if payload.proposed_data.cert_expires_at < date.today():
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "CERTIFICATE_EXPIRED",
            "Không thể gửi cập nhật với giấy chứng nhận đã hết hạn.",
        )
    change_request = ProductChangeRequest(
        product_id=product.id,
        subject_id=subject.id,
        request_type="update",
        proposed_data=payload.proposed_data.model_dump(mode="json"),
        reason=payload.reason,
        status="pending",
        base_version=product.version,
    )
    save_change_request(db, change_request)
    return to_change_request_read(get_change_request(db, change_request.id, subject_id=subject.id))


@router.post(
    "/products/{product_id}/deletion-requests",
    response_model=ProductChangeRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def request_product_deletion(
    product_id: int,
    payload: ProductDeleteRequestCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ProductChangeRequestRead:
    subject = get_approved_subject(db, current_user)
    product = ensure_product_accepts_request(db, product_id, subject.id)
    change_request = ProductChangeRequest(
        product_id=product.id,
        subject_id=subject.id,
        request_type="delete",
        proposed_data=None,
        reason=payload.reason,
        status="pending",
        base_version=product.version,
    )
    save_change_request(db, change_request)
    return to_change_request_read(get_change_request(db, change_request.id, subject_id=subject.id))


@router.get("/product-change-requests", response_model=ProductChangeRequestListResponse)
def list_my_product_change_requests(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request_status: ProductChangeStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> ProductChangeRequestListResponse:
    subject = get_approved_subject(db, current_user)
    filters = [ProductChangeRequest.subject_id == subject.id]
    if request_status:
        filters.append(ProductChangeRequest.status == request_status)
    total = db.scalar(select(func.count(ProductChangeRequest.id)).where(*filters)) or 0
    requests = list(
        db.scalars(
            select(ProductChangeRequest)
            .where(*filters)
            .options(*change_request_load_options())
            .order_by(ProductChangeRequest.updated_at.desc(), ProductChangeRequest.id.desc())
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


@router.get(
    "/product-change-requests/{request_id}",
    response_model=ProductChangeRequestRead,
)
def get_my_product_change_request(
    request_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ProductChangeRequestRead:
    subject = get_approved_subject(db, current_user)
    return to_change_request_read(
        get_change_request(db, request_id, subject_id=subject.id)
    )


@router.put(
    "/product-change-requests/{request_id}",
    response_model=ProductChangeRequestRead,
)
def resubmit_product_change_request(
    request_id: int,
    payload: ProductChangeRevision,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ProductChangeRequestRead:
    subject = get_approved_subject(db, current_user)
    change_request = get_change_request(
        db,
        request_id,
        subject_id=subject.id,
        lock=True,
    )
    if change_request.status != "needs_revision":
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_CHANGE_REQUEST_NOT_EDITABLE",
            "Chỉ yêu cầu cần bổ sung mới có thể chỉnh sửa và gửi lại.",
            {"current_status": change_request.status},
        )
    if change_request.request_type == "update":
        if payload.proposed_data is None:
            raise workflow_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "PROPOSED_PRODUCT_DATA_REQUIRED",
                "Cần gửi lại đầy đủ thông tin sản phẩm đề xuất.",
            )
        if payload.proposed_data.cert_expires_at < date.today():
            raise workflow_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "CERTIFICATE_EXPIRED",
                "Không thể gửi cập nhật với giấy chứng nhận đã hết hạn.",
            )
        validate_certificate_storage(
            change_request.product,
            payload.proposed_data.certificate_storage_path,
        )
        change_request.proposed_data = payload.proposed_data.model_dump(mode="json")
    if payload.reason is not None:
        change_request.reason = payload.reason.strip() or None
    if change_request.request_type == "delete" and not change_request.reason:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "DELETION_REASON_REQUIRED",
            "Yêu cầu ngừng hiển thị phải có lý do.",
        )
    change_request.status = "pending"
    change_request.submitted_at = datetime.now(timezone.utc)
    change_request.reviewed_by = None
    change_request.reviewed_at = None
    change_request.review_note = None
    save_change_request(db, change_request)
    return to_change_request_read(
        get_change_request(db, change_request.id, subject_id=subject.id)
    )


@router.post(
    "/product-change-requests/{request_id}/cancel",
    response_model=ProductChangeRequestRead,
)
def cancel_product_change_request(
    request_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ProductChangeRequestRead:
    subject = get_approved_subject(db, current_user)
    change_request = get_change_request(
        db,
        request_id,
        subject_id=subject.id,
        lock=True,
    )
    if change_request.status not in ACTIVE_REQUEST_STATUSES:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "PRODUCT_CHANGE_REQUEST_CANNOT_BE_CANCELLED",
            "Yêu cầu này không còn có thể hủy.",
            {"current_status": change_request.status},
        )
    change_request.status = "cancelled"
    db.add(change_request)
    db.commit()
    return to_change_request_read(
        get_change_request(db, change_request.id, subject_id=subject.id)
    )
