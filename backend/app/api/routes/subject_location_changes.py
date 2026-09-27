"""Chủ thể gửi yêu cầu cập nhật hoặc ngừng hiển thị điểm du lịch đã duyệt."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.core.geometry import GeoPoint
from app.models.location import TourismLocation, TourismLocationChangeRequest
from app.schemas.error import ErrorResponse
from app.schemas.location_management import (
    LocationChangeRequestListResponse,
    LocationChangeRequestRead,
    LocationChangeRevision,
    LocationChangeStatus,
    LocationDeleteRequestCreate,
    LocationUpdateRequestCreate,
    LocationWritePayload,
)
from app.services.location_workflow import (
    ACTIVE_CHANGE_REQUEST_STATUSES,
    change_request_load_options,
    ensure_inside_lam_dong,
    get_location_change_request,
    get_location_subject,
    get_owned_location,
    resolve_location_products,
    to_location_change_request_read,
    validate_location_images,
)
from app.services.product_workflow import workflow_error


router = APIRouter()


def ensure_location_accepts_request(db: Session, location_id: int, subject_id: int) -> TourismLocation:
    location = get_owned_location(db, location_id, subject_id)
    if location.status != "approved":
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "APPROVED_LOCATION_REQUIRED",
            "Chỉ điểm du lịch đã duyệt mới dùng yêu cầu thay đổi.",
            {"current_status": location.status},
        )
    active_request_id = db.scalar(
        select(TourismLocationChangeRequest.id).where(
            TourismLocationChangeRequest.location_id == location.id,
            TourismLocationChangeRequest.status.in_(ACTIVE_CHANGE_REQUEST_STATUSES),
        )
    )
    if active_request_id is not None:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "ACTIVE_LOCATION_CHANGE_REQUEST_EXISTS",
            "Điểm du lịch đang có một yêu cầu thay đổi chưa xử lý.",
            {"request_id": active_request_id},
        )
    return location


def validate_proposed_location(
    db: Session,
    payload: LocationWritePayload,
    subject_id: int,
    location_id: int,
) -> None:
    ensure_inside_lam_dong(GeoPoint(longitude=payload.longitude, latitude=payload.latitude))
    validate_location_images(db, payload.images, subject_id, location_id)
    resolve_location_products(db, payload.product_ids, subject_id)


def save_change_request(db: Session, change_request: TourismLocationChangeRequest) -> None:
    db.add(change_request)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_CHANGE_REQUEST_CONFLICT",
            "Điểm du lịch đang có một yêu cầu thay đổi chưa xử lý.",
        ) from exc
    db.expire_all()


def read_request(db: Session, request_id: int, subject_id: int) -> LocationChangeRequestRead:
    return to_location_change_request_read(
        get_location_change_request(db, request_id, subject_id=subject_id)
    )


@router.post(
    "/locations/{location_id}/change-requests",
    response_model=LocationChangeRequestRead,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
)
def request_location_update(
    location_id: int,
    payload: LocationUpdateRequestCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> LocationChangeRequestRead:
    subject = get_location_subject(db, current_user)
    location = ensure_location_accepts_request(db, location_id, subject.id)
    validate_proposed_location(db, payload.proposed_data, subject.id, location.id)
    change_request = TourismLocationChangeRequest(
        location_id=location.id,
        subject_id=subject.id,
        request_type="update",
        proposed_data=payload.proposed_data.model_dump(mode="json"),
        reason=payload.reason,
        status="pending",
        base_version=location.version,
    )
    save_change_request(db, change_request)
    return read_request(db, change_request.id, subject.id)


@router.post(
    "/locations/{location_id}/deletion-requests",
    response_model=LocationChangeRequestRead,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
)
def request_location_deletion(
    location_id: int,
    payload: LocationDeleteRequestCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> LocationChangeRequestRead:
    subject = get_location_subject(db, current_user)
    location = ensure_location_accepts_request(db, location_id, subject.id)
    change_request = TourismLocationChangeRequest(
        location_id=location.id,
        subject_id=subject.id,
        request_type="delete",
        proposed_data=None,
        reason=payload.reason,
        status="pending",
        base_version=location.version,
    )
    save_change_request(db, change_request)
    return read_request(db, change_request.id, subject.id)


@router.get("/location-change-requests", response_model=LocationChangeRequestListResponse)
def list_my_location_change_requests(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request_status: LocationChangeStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> LocationChangeRequestListResponse:
    subject = get_location_subject(db, current_user)
    filters = [TourismLocationChangeRequest.subject_id == subject.id]
    if request_status:
        filters.append(TourismLocationChangeRequest.status == request_status)
    total = db.scalar(select(func.count(TourismLocationChangeRequest.id)).where(*filters)) or 0
    requests = list(
        db.scalars(
            select(TourismLocationChangeRequest)
            .where(*filters)
            .options(*change_request_load_options())
            .order_by(
                TourismLocationChangeRequest.updated_at.desc(),
                TourismLocationChangeRequest.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return LocationChangeRequestListResponse(
        items=[to_location_change_request_read(item) for item in requests],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/location-change-requests/{request_id}", response_model=LocationChangeRequestRead)
def get_my_location_change_request(
    request_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> LocationChangeRequestRead:
    subject = get_location_subject(db, current_user)
    return read_request(db, request_id, subject.id)


@router.put("/location-change-requests/{request_id}", response_model=LocationChangeRequestRead)
def resubmit_location_change_request(
    request_id: int,
    payload: LocationChangeRevision,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> LocationChangeRequestRead:
    subject = get_location_subject(db, current_user)
    change_request = get_location_change_request(db, request_id, subject_id=subject.id, lock=True)
    if change_request.status != "needs_revision":
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_CHANGE_REQUEST_NOT_EDITABLE",
            "Chỉ yêu cầu cần bổ sung mới có thể chỉnh sửa và gửi lại.",
            {"current_status": change_request.status},
        )
    if change_request.request_type == "update":
        if payload.proposed_data is None:
            raise workflow_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "PROPOSED_LOCATION_DATA_REQUIRED",
                "Cần gửi lại đầy đủ thông tin điểm du lịch đề xuất.",
            )
        validate_proposed_location(
            db, payload.proposed_data, subject.id, change_request.location_id
        )
        change_request.proposed_data = payload.proposed_data.model_dump(mode="json")
    if payload.reason is not None:
        change_request.reason = payload.reason.strip() or None
    if change_request.request_type == "delete" and len(change_request.reason or "") < 5:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "DELETION_REASON_REQUIRED",
            "Yêu cầu ngừng hiển thị phải có lý do (tối thiểu 5 ký tự).",
        )
    change_request.status = "pending"
    change_request.submitted_at = datetime.now(timezone.utc)
    change_request.reviewed_by = None
    change_request.reviewed_at = None
    change_request.review_note = None
    save_change_request(db, change_request)
    return read_request(db, change_request.id, subject.id)


@router.post(
    "/location-change-requests/{request_id}/cancel",
    response_model=LocationChangeRequestRead,
)
def cancel_location_change_request(
    request_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> LocationChangeRequestRead:
    subject = get_location_subject(db, current_user)
    change_request = get_location_change_request(db, request_id, subject_id=subject.id, lock=True)
    if change_request.status not in ACTIVE_CHANGE_REQUEST_STATUSES:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_CHANGE_REQUEST_CANNOT_BE_CANCELLED",
            "Yêu cầu này không còn có thể hủy.",
            {"current_status": change_request.status},
        )
    change_request.status = "cancelled"
    save_change_request(db, change_request)
    return read_request(db, change_request.id, subject.id)
