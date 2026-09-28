"""Chủ thể khai báo điểm du lịch: bản nháp, sửa, gửi duyệt, kiểm tra vị trí."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.core.geometry import GeoPoint
from app.models.location import TourismLocation
from app.schemas.error import ErrorResponse
from app.schemas.location_management import (
    CoordinateParseRequest,
    CoordinateParseResponse,
    LocationDraftCreate,
    LocationDraftUpdate,
    LocationPositionCheck,
    LocationWorkflowStatus,
    ManagedLocationListResponse,
    ManagedLocationRead,
)
from app.services.location_workflow import (
    DELETABLE_LOCATION_STATUSES,
    EDITABLE_LOCATION_STATUSES,
    apply_location_draft_payload,
    build_unique_location_slug,
    check_position,
    count_by_status,
    get_location_subject,
    get_owned_location,
    location_load_options,
    location_position_check,
    open_change_request_ids,
    parse_coordinate_text,
    to_managed_location_read,
    validate_location_submission,
)
from app.services.product_workflow import workflow_error


router = APIRouter(prefix="/locations")


def commit_location(db: Session, location: TourismLocation) -> None:
    db.add(location)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_CONFLICT",
            "Không lưu được điểm du lịch vì dữ liệu bị trùng hoặc không hợp lệ.",
        ) from exc
    # Phiên không tự hết hạn sau commit (expire_on_commit=False): nạp lại quan hệ khi đọc kết quả.
    db.expire_all()


def read_owned(db: Session, location_id: int, subject_id: int) -> ManagedLocationRead:
    location = get_owned_location(db, location_id, subject_id)
    return to_managed_location_read(
        location,
        position_check=location_position_check(db, location),
        open_change_request_id=open_change_request_ids(db, [location.id]).get(location.id),
    )


def ensure_editable(location: TourismLocation, code: str, message: str) -> None:
    if location.status not in EDITABLE_LOCATION_STATUSES:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            code,
            message,
            {"current_status": location.status},
        )


@router.get("", response_model=ManagedLocationListResponse)
def list_my_locations(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    location_status: LocationWorkflowStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> ManagedLocationListResponse:
    subject = get_location_subject(db, current_user)
    base_filters = [TourismLocation.subject_id == subject.id]
    filters = list(base_filters)
    if location_status:
        filters.append(TourismLocation.status == location_status)
    total = db.scalar(select(func.count(TourismLocation.id)).where(*filters)) or 0
    locations = list(
        db.scalars(
            select(TourismLocation)
            .where(*filters)
            .options(*location_load_options())
            .order_by(TourismLocation.updated_at.desc(), TourismLocation.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    open_requests = open_change_request_ids(db, [location.id for location in locations])
    return ManagedLocationListResponse(
        items=[
            to_managed_location_read(location, open_change_request_id=open_requests.get(location.id))
            for location in locations
        ],
        page=page,
        page_size=page_size,
        total=total,
        status_counts=count_by_status(db, *base_filters),
    )


@router.get("/position-check", response_model=LocationPositionCheck)
def check_location_position(
    current_user: CurrentUser,
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    exclude_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> LocationPositionCheck:
    """Kiểm tra ghim ngay khi chủ thể chọn vị trí: trong tỉnh chưa, có điểm đã duyệt nào quá gần không."""

    get_location_subject(db, current_user)
    return check_position(
        db,
        GeoPoint(longitude=longitude, latitude=latitude),
        exclude_location_id=exclude_id,
    )


@router.post(
    "/parse-coordinates",
    response_model=CoordinateParseResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse}},
)
def parse_coordinates(
    payload: CoordinateParseRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> CoordinateParseResponse:
    """Đọc tọa độ dán vào (thập phân hoặc độ-phút-giây) hay link Google Maps đầy đủ."""

    get_location_subject(db, current_user)
    point, source = parse_coordinate_text(payload.text)
    return CoordinateParseResponse(
        latitude=point.latitude,
        longitude=point.longitude,
        location_source=source,
        position_check=check_position(db, point),
    )


@router.post(
    "",
    response_model=ManagedLocationRead,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
)
def create_location_draft(
    payload: LocationDraftCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedLocationRead:
    subject = get_location_subject(db, current_user)
    location = TourismLocation(
        subject_id=subject.id,
        name=payload.name,
        slug=build_unique_location_slug(db, payload.name),
        type=payload.type,
        services=[],
        status="draft",
    )
    apply_location_draft_payload(db, location, payload, subject.id)
    commit_location(db, location)
    return read_owned(db, location.id, subject.id)


@router.get("/{location_id}", response_model=ManagedLocationRead)
def get_my_location(
    location_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedLocationRead:
    subject = get_location_subject(db, current_user)
    return read_owned(db, location_id, subject.id)


@router.patch("/{location_id}", response_model=ManagedLocationRead)
def update_location_draft(
    location_id: int,
    payload: LocationDraftUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedLocationRead:
    subject = get_location_subject(db, current_user)
    location = get_owned_location(db, location_id, subject.id, lock=True)
    ensure_editable(
        location,
        "LOCATION_NOT_EDITABLE",
        "Chỉ bản nháp hoặc điểm cần bổ sung mới được sửa trực tiếp."
        " Điểm đã duyệt cần gửi yêu cầu cập nhật.",
    )
    apply_location_draft_payload(db, location, payload, subject.id)
    commit_location(db, location)
    return read_owned(db, location.id, subject.id)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location_draft(
    location_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Response:
    subject = get_location_subject(db, current_user)
    location = get_owned_location(db, location_id, subject.id, lock=True)
    if location.status not in DELETABLE_LOCATION_STATUSES:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_CANNOT_BE_DELETED",
            "Điểm đang chờ duyệt hoặc đã công khai không thể xóa trực tiếp.",
            {"current_status": location.status},
        )
    db.delete(location)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{location_id}/submit",
    response_model=ManagedLocationRead,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
def submit_location_for_moderation(
    location_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedLocationRead:
    subject = get_location_subject(db, current_user)
    location = get_owned_location(db, location_id, subject.id, lock=True)
    ensure_editable(
        location,
        "LOCATION_CANNOT_BE_SUBMITTED",
        "Điểm du lịch không ở trạng thái có thể gửi duyệt.",
    )
    validate_location_submission(location)
    location.status = "pending"
    location.submitted_at = datetime.now(timezone.utc)
    location.reviewed_by = None
    location.reviewed_at = None
    location.review_note = None
    commit_location(db, location)
    return read_owned(db, location.id, subject.id)
