"""Admin duyệt yêu cầu cập nhật / ngừng hiển thị điểm du lịch đã duyệt."""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.core.geometry import GeoPoint
from app.models.location import TourismLocation, TourismLocationChangeRequest
from app.models.subject import Subject
from app.schemas.location_management import (
    LocationChangeModerationRequest,
    LocationChangeRequestListResponse,
    LocationChangeRequestRead,
    LocationChangeStatus,
    LocationWritePayload,
)
from app.services.location_workflow import (
    apply_location_write_payload,
    change_request_load_options,
    ensure_inside_lam_dong,
    get_location_change_request,
    proposed_position_check,
    to_location_change_request_read,
)
from app.services.product_workflow import workflow_error


router = APIRouter(prefix="/location-change-requests")
RequestType = Literal["update", "delete"]


def read_for_admin(db: Session, request_id: int) -> LocationChangeRequestRead:
    change_request = get_location_change_request(db, request_id)
    return to_location_change_request_read(
        change_request,
        proposed_position_check=proposed_position_check(db, change_request),
    )


@router.get("", response_model=LocationChangeRequestListResponse)
def list_location_change_requests(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request_status: LocationChangeStatus | None = Query(default=None, alias="status"),
    request_type: RequestType | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    db: Session = Depends(get_db),
) -> LocationChangeRequestListResponse:
    filters = []
    if request_status:
        filters.append(TourismLocationChangeRequest.status == request_status)
    if request_type:
        filters.append(TourismLocationChangeRequest.request_type == request_type)
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(or_(TourismLocation.name.ilike(keyword), Subject.name.ilike(keyword)))

    def base_query(*columns):
        return (
            select(*columns)
            .join(TourismLocationChangeRequest.location)
            .join(TourismLocationChangeRequest.subject)
            .where(*filters)
        )

    total = db.scalar(base_query(func.count(TourismLocationChangeRequest.id))) or 0
    request_order = case(
        (TourismLocationChangeRequest.status == "pending", 0),
        (TourismLocationChangeRequest.status == "needs_revision", 1),
        else_=2,
    )
    requests = list(
        db.scalars(
            base_query(TourismLocationChangeRequest)
            .options(*change_request_load_options())
            .order_by(
                request_order,
                TourismLocationChangeRequest.submitted_at.desc(),
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


@router.get("/{request_id}", response_model=LocationChangeRequestRead)
def get_location_change_request_for_admin(
    request_id: int,
    db: Session = Depends(get_db),
) -> LocationChangeRequestRead:
    return read_for_admin(db, request_id)


@router.patch("/{request_id}/moderation", response_model=LocationChangeRequestRead)
def moderate_location_change_request(
    request_id: int,
    payload: LocationChangeModerationRequest,
    current_admin: CurrentUser,
    db: Session = Depends(get_db),
) -> LocationChangeRequestRead:
    change_request = get_location_change_request(db, request_id, lock=True)
    if change_request.status != "pending":
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_CHANGE_REQUEST_ALREADY_REVIEWED",
            "Yêu cầu thay đổi này không còn ở trạng thái chờ duyệt.",
            {"current_status": change_request.status},
        )

    location = db.scalar(
        select(TourismLocation)
        .where(TourismLocation.id == change_request.location_id)
        .with_for_update()
    )
    if location is None:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_FOR_CHANGE_REQUEST_NOT_FOUND",
            "Điểm du lịch của yêu cầu không còn tồn tại.",
        )

    if payload.status == "approved":
        if location.status != "approved":
            raise workflow_error(
                status.HTTP_409_CONFLICT,
                "LOCATION_NOT_PUBLIC",
                "Chỉ áp dụng yêu cầu cho điểm du lịch đang hiển thị.",
                {"current_status": location.status},
            )
        if location.version != change_request.base_version:
            raise workflow_error(
                status.HTTP_409_CONFLICT,
                "LOCATION_VERSION_CONFLICT",
                "Điểm du lịch đã thay đổi sau khi yêu cầu được tạo. Chủ thể cần tạo yêu cầu mới.",
                {
                    "base_version": change_request.base_version,
                    "current_version": location.version,
                },
            )
        if change_request.request_type == "update":
            proposed = LocationWritePayload.model_validate(change_request.proposed_data)
            ensure_inside_lam_dong(GeoPoint(longitude=proposed.longitude, latitude=proposed.latitude))
            apply_location_write_payload(db, location, proposed, change_request.subject_id)
        else:
            location.status = "archived"
            location.review_note = change_request.reason
        location.reviewed_by = current_admin.id
        location.reviewed_at = datetime.now(timezone.utc)
        location.version += 1
        db.add(location)

    change_request.status = payload.status
    change_request.reviewed_by = current_admin.id
    change_request.reviewer = current_admin
    change_request.reviewed_at = datetime.now(timezone.utc)
    change_request.review_note = payload.note
    db.add(change_request)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_UPDATE_CONFLICT",
            "Không thể áp dụng yêu cầu vì dữ liệu mới bị trùng hoặc không còn hợp lệ.",
        ) from exc
    db.expire_all()
    return read_for_admin(db, change_request.id)
