"""Admin kiểm duyệt điểm du lịch chủ thể khai báo."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.core.geometry import GeoPoint
from app.models.location import TourismLocation
from app.models.subject import Subject
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.location_management import (
    LocationModerationRequest,
    LocationOrigin,
    LocationWorkflowStatus,
    ManagedLocationListResponse,
    ManagedLocationRead,
    SubjectLocationSource,
)
from app.services.location_catalog import LocationTypeCode
from app.services.location_workflow import (
    ensure_inside_lam_dong,
    get_location_for_admin,
    location_load_options,
    location_position_check,
    open_change_request_ids,
    to_managed_location_read,
    validate_location_submission,
)
from app.services.product_workflow import workflow_error


router = APIRouter(prefix="/locations")
REVIEW_QUEUE_STATUSES = {"pending", "needs_revision"}


def read_for_admin(db: Session, location_id: int) -> ManagedLocationRead:
    location = get_location_for_admin(db, location_id)
    return to_managed_location_read(
        location,
        position_check=location_position_check(db, location),
        open_change_request_id=open_change_request_ids(db, [location.id]).get(location.id),
    )


def format_point(point: GeoPoint | None) -> str:
    return f"{point.latitude:.6f}, {point.longitude:.6f}" if point else "chưa có"


@router.get("", response_model=ManagedLocationListResponse)
def list_locations_for_moderation(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    location_status: LocationWorkflowStatus | None = Query(default=None, alias="status"),
    origin: LocationOrigin | None = Query(default=None),
    location_type: LocationTypeCode | None = Query(default=None, alias="type"),
    location_source: SubjectLocationSource | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    db: Session = Depends(get_db),
) -> ManagedLocationListResponse:
    filters: list = []
    # Điểm nhóm nhập từ nguồn công khai không gắn chủ thể; điểm chủ thể khai báo luôn có subject_id.
    if origin == "subject":
        filters.append(TourismLocation.subject_id.is_not(None))
    elif origin == "import":
        filters.append(TourismLocation.subject_id.is_(None))
    if location_type:
        filters.append(TourismLocation.type == location_type)
    if location_source:
        filters.append(TourismLocation.location_source == location_source)
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(
            or_(
                TourismLocation.name.ilike(keyword),
                TourismLocation.address.ilike(keyword),
                TourismLocation.district.ilike(keyword),
                Subject.name.ilike(keyword),
            )
        )
    # Bản nháp là việc riêng của chủ thể nên admin không thấy, trừ khi lọc đúng trạng thái này.
    status_filters = (
        [TourismLocation.status == location_status]
        if location_status
        else [TourismLocation.status != "draft"]
    )

    def base_query(*columns):
        return select(*columns).outerjoin(TourismLocation.subject)

    total = db.scalar(
        base_query(func.count(TourismLocation.id)).where(*filters, *status_filters)
    ) or 0
    status_order = case(
        (TourismLocation.status == "pending", 0),
        (TourismLocation.status == "needs_revision", 1),
        else_=2,
    )
    locations = list(
        db.scalars(
            base_query(TourismLocation)
            .where(*filters, *status_filters)
            .options(*location_load_options())
            .order_by(
                status_order,
                TourismLocation.submitted_at.desc().nulls_last(),
                TourismLocation.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    open_requests = open_change_request_ids(db, [location.id for location in locations])
    counts = {
        status_name: count
        for status_name, count in db.execute(
            base_query(TourismLocation.status, func.count(TourismLocation.id))
            .where(*filters, TourismLocation.status != "draft")
            .group_by(TourismLocation.status)
        )
    }
    return ManagedLocationListResponse(
        items=[
            to_managed_location_read(
                location,
                # Kiểm tra vị trí tốn một truy vấn mỗi điểm nên chỉ tính cho hàng chờ duyệt.
                position_check=(
                    location_position_check(db, location)
                    if location.status in REVIEW_QUEUE_STATUSES
                    else None
                ),
                open_change_request_id=open_requests.get(location.id),
            )
            for location in locations
        ],
        page=page,
        page_size=page_size,
        total=total,
        status_counts=counts,
    )


@router.get("/{location_id}", response_model=ManagedLocationRead)
def get_location_for_moderation(
    location_id: int,
    db: Session = Depends(get_db),
) -> ManagedLocationRead:
    return read_for_admin(db, location_id)


@router.patch(
    "/{location_id}/moderation",
    response_model=ManagedLocationRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
def moderate_location(
    location_id: int,
    payload: LocationModerationRequest,
    current_admin: CurrentUser,
    db: Session = Depends(get_db),
) -> ManagedLocationRead:
    location = get_location_for_admin(db, location_id, lock=True)
    if location.status != "pending":
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_ALREADY_REVIEWED",
            "Điểm du lịch không còn ở trạng thái chờ duyệt.",
            {"current_status": location.status},
        )

    subject = (
        db.scalar(select(Subject).where(Subject.id == location.subject_id).with_for_update())
        if location.subject_id is not None
        else None
    )
    owner = (
        db.scalar(select(User).where(User.id == subject.user_id).with_for_update())
        if subject
        else None
    )
    if subject is None or subject.status != "approved" or owner is None or not owner.is_active:
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_SUBJECT_INACTIVE",
            "Không thể duyệt điểm vì chủ thể không còn hợp lệ hoặc đã bị khóa.",
        )

    note = payload.note
    if payload.latitude is not None and payload.longitude is not None:
        new_point = GeoPoint(longitude=payload.longitude, latitude=payload.latitude)
        ensure_inside_lam_dong(new_point)
        if new_point != location.geom:
            moved = (
                f"Quản trị viên đã chỉnh vị trí từ {format_point(location.geom)}"
                f" sang {format_point(new_point)}."
            )
            note = f"{note}\n{moved}" if note else moved
            location.geom = new_point
            # Tọa độ không còn là số đo GPS của chủ thể nên bỏ độ chính xác.
            location.location_accuracy_m = None

    if payload.status == "approved":
        validate_location_submission(location)

    location.status = payload.status
    location.reviewed_by = current_admin.id
    location.reviewer = current_admin
    location.reviewed_at = datetime.now(timezone.utc)
    location.review_note = note
    if payload.status == "approved":
        location.version += 1
    db.add(location)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise workflow_error(
            status.HTTP_409_CONFLICT,
            "LOCATION_MODERATION_CONFLICT",
            "Không lưu được quyết định duyệt vì dữ liệu điểm không còn hợp lệ.",
        ) from exc
    db.expire_all()
    return read_for_admin(db, location.id)
