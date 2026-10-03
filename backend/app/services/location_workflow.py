"""Quy trình chủ thể khai báo điểm du lịch và admin kiểm duyệt (cùng mô hình với sản phẩm).

draft -> pending -> approved | needs_revision -> pending ... | rejected (kết thúc).
Điểm đã duyệt chỉ sửa hoặc ngừng hiển thị qua yêu cầu thay đổi; bản đang hiển thị giữ nguyên tới
khi admin duyệt yêu cầu. Ngừng hiển thị chuyển điểm sang archived.
"""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import unquote

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.geometry import GeoPoint, distance_meters
from app.models.location import LocationImage, TourismLocation, TourismLocationChangeRequest
from app.models.product import Product
from app.models.subject import Subject
from app.models.user import User
from app.schemas.location_management import (
    MIN_DESCRIPTION_LENGTH,
    LocationChangeRequestRead,
    LocationDraftCreate,
    LocationDraftUpdate,
    LocationImagePayload,
    LocationOwnerRead,
    LocationPositionCheck,
    LocationProductRead,
    LocationSnapshotRead,
    LocationWritePayload,
    ManagedLocationImageRead,
    ManagedLocationRead,
    NearestApprovedLocation,
)
from app.services.image_storage import is_subject_image_path, uploaded_file_exists
from app.services.location_catalog import location_type_label
from app.services.product_workflow import workflow_error


LOCATION_IMAGE_FOLDER = "locations"
# Trạng thái chủ thể được sửa trực tiếp và gửi (lại) duyệt. Bị từ chối là kết thúc: khai báo điểm mới.
EDITABLE_LOCATION_STATUSES = {"draft", "needs_revision"}
DELETABLE_LOCATION_STATUSES = {"draft", "needs_revision", "rejected"}
ACTIVE_CHANGE_REQUEST_STATUSES = {"pending", "needs_revision"}

# Khung bao tỉnh Lâm Đồng sau sáp nhập 2025 (gồm Đắk Nông và Bình Thuận cũ, cả đảo Phú Quý).
# Đây là hình chữ nhật bao ngoài nên dùng để chặn tọa độ nhập nhầm (đảo vĩ độ/kinh độ, sai tỉnh xa);
# thay bằng ranh giới hành chính khi nhóm có dữ liệu ranh giới chính thức.
LAM_DONG_BOUNDS = {
    "min_latitude": 10.4,
    "max_latitude": 12.9,
    "min_longitude": 107.1,
    "max_longitude": 109.0,
}
# Điểm đã duyệt nằm trong bán kính này được cảnh báo có thể trùng (không chặn gửi duyệt).
DUPLICATE_RADIUS_M = 200


def get_location_subject(db: Session, user: User) -> Subject:
    subject = db.scalar(
        select(Subject).where(Subject.user_id == user.id, Subject.status == "approved")
    )
    if subject is None:
        raise workflow_error(
            status.HTTP_403_FORBIDDEN,
            "APPROVED_SUBJECT_REQUIRED",
            "Chỉ chủ thể đã được duyệt mới có thể khai báo điểm du lịch.",
        )
    return subject


def location_load_options() -> tuple:
    return (
        joinedload(TourismLocation.subject).joinedload(Subject.user),
        joinedload(TourismLocation.reviewer),
        selectinload(TourismLocation.images),
        selectinload(TourismLocation.products),
    )


def get_owned_location(
    db: Session,
    location_id: int,
    subject_id: int,
    *,
    lock: bool = False,
) -> TourismLocation:
    statement = select(TourismLocation).where(
        TourismLocation.id == location_id,
        TourismLocation.subject_id == subject_id,
    )
    if lock:
        statement = statement.with_for_update(of=TourismLocation)
    location = db.scalar(statement.options(*location_load_options()))
    if location is None:
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "LOCATION_NOT_FOUND",
            "Không tìm thấy điểm du lịch thuộc chủ thể hiện tại.",
            {"location_id": location_id},
        )
    return location


def get_location_for_admin(db: Session, location_id: int, *, lock: bool = False) -> TourismLocation:
    statement = select(TourismLocation).where(TourismLocation.id == location_id)
    if lock:
        statement = statement.with_for_update(of=TourismLocation)
    location = db.scalar(statement.options(*location_load_options()))
    if location is None:
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "LOCATION_NOT_FOUND",
            "Không tìm thấy điểm du lịch.",
            {"location_id": location_id},
        )
    return location


def build_unique_location_slug(db: Session, name: str, location_id: int | None = None) -> str:
    normalized = unicodedata.normalize("NFKD", name.replace("đ", "d").replace("Đ", "D"))
    base = re.sub(r"[^a-z0-9]+", "-", normalized.encode("ascii", "ignore").decode().lower())
    base = base.strip("-")[:230].strip("-") or "diem-du-lich"
    candidate = base
    suffix = 2
    while db.scalar(
        select(TourismLocation.id).where(
            TourismLocation.slug == candidate,
            TourismLocation.id != location_id if location_id is not None else True,
        )
    ) is not None:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


# ---------------------------------------------------------------------------
# Vị trí: kiểm tra khung tỉnh, điểm trùng, đọc tọa độ/link Google Maps
# ---------------------------------------------------------------------------


def inside_lam_dong(point: GeoPoint) -> bool:
    return (
        LAM_DONG_BOUNDS["min_latitude"] <= point.latitude <= LAM_DONG_BOUNDS["max_latitude"]
        and LAM_DONG_BOUNDS["min_longitude"] <= point.longitude <= LAM_DONG_BOUNDS["max_longitude"]
    )


def check_position(
    db: Session,
    point: GeoPoint,
    *,
    exclude_location_id: int | None = None,
) -> LocationPositionCheck:
    distance = distance_meters(TourismLocation.geom, point.longitude, point.latitude)
    filters = [TourismLocation.status == "approved", TourismLocation.geom.is_not(None)]
    if exclude_location_id is not None:
        filters.append(TourismLocation.id != exclude_location_id)
    row = db.execute(
        select(TourismLocation.id, TourismLocation.name, TourismLocation.slug, distance.label("distance_m"))
        .where(*filters)
        .order_by(distance, TourismLocation.id)
        .limit(1)
    ).first()
    nearest = (
        NearestApprovedLocation(
            id=row.id,
            name=row.name,
            slug=row.slug,
            distance_m=round(float(row.distance_m), 1),
        )
        if row is not None
        else None
    )
    return LocationPositionCheck(
        latitude=point.latitude,
        longitude=point.longitude,
        inside_lam_dong=inside_lam_dong(point),
        nearest=nearest,
        duplicate_warning=nearest is not None and nearest.distance_m < DUPLICATE_RADIUS_M,
        duplicate_radius_m=DUPLICATE_RADIUS_M,
    )


def ensure_inside_lam_dong(point: GeoPoint) -> None:
    if not inside_lam_dong(point):
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "LOCATION_OUTSIDE_LAM_DONG",
            "Vị trí nằm ngoài tỉnh Lâm Đồng. Kiểm tra lại ghim hoặc thứ tự vĩ độ, kinh độ.",
            {"latitude": point.latitude, "longitude": point.longitude, "bounds": LAM_DONG_BOUNDS},
        )


_NUMBER = r"[-+]?\d{1,3}(?:\.\d+)?"
_PLAIN_PAIR = re.compile(rf"^\s*\(?\s*({_NUMBER})\s*[,;\s]\s*({_NUMBER})\s*\)?\s*$")
_DMS_PAIR = re.compile(
    r"(\d{1,3})\s*°\s*(\d{1,2})\s*['′]\s*(\d{1,2}(?:\.\d+)?)\s*(?:\"|″|'')?\s*([NS])"
    r"[\s,;]*"
    r"(\d{1,3})\s*°\s*(\d{1,2})\s*['′]\s*(\d{1,2}(?:\.\d+)?)\s*(?:\"|″|'')?\s*([EW])",
    re.IGNORECASE,
)
# Thứ tự ưu tiên: vị trí địa điểm (!3d...!4d...), tham số truy vấn, rồi tâm khung nhìn (@lat,lng).
_MAPS_PATTERNS = (
    re.compile(rf"!3d({_NUMBER})!4d({_NUMBER})"),
    re.compile(rf"[?&](?:q|query|ll|center|destination|daddr)=(?:loc:)?({_NUMBER}),\s*({_NUMBER})"),
    re.compile(rf"@({_NUMBER}),({_NUMBER})"),
)
_SHORT_LINK = re.compile(r"(?:maps\.app\.goo\.gl|goo\.gl/maps)/", re.IGNORECASE)


def _valid_pair(latitude: float, longitude: float) -> bool:
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def parse_coordinate_text(text: str) -> tuple[GeoPoint, str]:
    """Đọc tọa độ dán vào hoặc link Google Maps; trả về điểm và nguồn vị trí tương ứng."""

    value = unquote(text.strip())
    if _SHORT_LINK.search(value):
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "SHORT_MAPS_LINK_UNSUPPORTED",
            "Link rút gọn không chứa tọa độ. Mở link trên trình duyệt rồi sao chép đường dẫn đầy đủ,"
            " hoặc bấm giữ vào điểm trên Google Maps để sao chép tọa độ.",
        )

    if re.search(r"https?://|google\.|maps\.", value, re.IGNORECASE):
        for pattern in _MAPS_PATTERNS:
            match = pattern.search(value)
            if match:
                latitude, longitude = float(match[1]), float(match[2])
                if _valid_pair(latitude, longitude):
                    return GeoPoint(longitude=longitude, latitude=latitude), "google_maps_link"
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "MAPS_LINK_WITHOUT_COORDINATES",
            "Không tìm thấy tọa độ trong link. Hãy dùng link chia sẻ đầy đủ của Google Maps.",
        )

    dms = _DMS_PAIR.search(value)
    if dms and all(float(dms[index]) < 60 for index in (2, 3, 6, 7)):
        latitude = float(dms[1]) + float(dms[2]) / 60 + float(dms[3]) / 3600
        longitude = float(dms[5]) + float(dms[6]) / 60 + float(dms[7]) / 3600
        if dms[4].upper() == "S":
            latitude = -latitude
        if dms[8].upper() == "W":
            longitude = -longitude
        if _valid_pair(latitude, longitude):
            return GeoPoint(longitude=round(longitude, 7), latitude=round(latitude, 7)), "coordinates"

    plain = _PLAIN_PAIR.match(value)
    if plain:
        first, second = float(plain[1]), float(plain[2])
        # Người dùng đôi khi dán theo thứ tự kinh độ, vĩ độ; chỉ đổi khi số đầu không thể là vĩ độ.
        if abs(first) > 90 and abs(second) <= 90:
            first, second = second, first
        if _valid_pair(first, second):
            return GeoPoint(longitude=second, latitude=first), "coordinates"

    raise workflow_error(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "INVALID_COORDINATES",
        "Không đọc được tọa độ. Nhập dạng \"12.047000, 108.441000\" hoặc dán link Google Maps.",
    )


# ---------------------------------------------------------------------------
# Ghi dữ liệu chủ thể khai báo
# ---------------------------------------------------------------------------


def validate_location_images(
    db: Session,
    images: list[LocationImagePayload],
    subject_id: int,
    location_id: int | None,
) -> None:
    """Ảnh tải lên phải thuộc chủ thể, còn file, và không đang dùng cho điểm khác."""

    for image in images:
        if image.storage_path is None:
            continue
        if not is_subject_image_path(image.storage_path, LOCATION_IMAGE_FOLDER, subject_id):
            raise workflow_error(
                status.HTTP_403_FORBIDDEN,
                "LOCATION_IMAGE_NOT_OWNED",
                "Ảnh tải lên không thuộc chủ thể hiện tại.",
            )
        if not uploaded_file_exists(image.storage_path):
            raise workflow_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "LOCATION_IMAGE_NOT_FOUND",
                "Không tìm thấy file ảnh đã tải lên.",
            )
        if image_used_by_other_location(db, image.storage_path, subject_id, location_id):
            raise workflow_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "LOCATION_IMAGE_USED_ELSEWHERE",
                "Ảnh này đang dùng cho một điểm du lịch khác. Hãy tải ảnh riêng cho điểm này.",
                {"storage_path": image.storage_path},
            )


def image_used_by_other_location(
    db: Session,
    storage_path: str,
    subject_id: int,
    location_id: int | None,
) -> bool:
    """Ảnh đã gắn vào điểm khác hoặc nằm trong yêu cầu cập nhật đang mở của điểm khác."""

    linked = select(LocationImage.id).where(LocationImage.storage_path == storage_path)
    if location_id is not None:
        linked = linked.where(LocationImage.location_id != location_id)
    if db.scalar(linked) is not None:
        return True
    proposals = select(TourismLocationChangeRequest.proposed_data).where(
        TourismLocationChangeRequest.subject_id == subject_id,
        TourismLocationChangeRequest.request_type == "update",
        TourismLocationChangeRequest.status.in_(ACTIVE_CHANGE_REQUEST_STATUSES),
    )
    if location_id is not None:
        proposals = proposals.where(TourismLocationChangeRequest.location_id != location_id)
    return any(
        item.get("storage_path") == storage_path
        for proposal in db.scalars(proposals)
        for item in (proposal or {}).get("images", [])
    )


def resolve_location_products(db: Session, product_ids: list[int], subject_id: int) -> list[Product]:
    """Chỉ gắn sản phẩm OCOP đã duyệt của chính chủ thể."""

    if not product_ids:
        return []
    products = {
        product.id: product
        for product in db.scalars(
            select(Product).where(
                Product.id.in_(product_ids),
                Product.subject_id == subject_id,
                Product.status == "approved",
            )
        )
    }
    invalid_ids = [product_id for product_id in product_ids if product_id not in products]
    if invalid_ids:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "LOCATION_PRODUCT_INVALID",
            "Chỉ gắn được sản phẩm OCOP đã duyệt của đơn vị.",
            {"product_ids": invalid_ids},
        )
    return [products[product_id] for product_id in product_ids]


def replace_location_images(
    db: Session,
    location: TourismLocation,
    images: list[LocationImagePayload],
    subject_id: int,
) -> None:
    validate_location_images(db, images, subject_id, location.id)
    # Giữ nguồn/giấy phép của ảnh đã có khi chủ thể lưu lại danh sách ảnh (giao diện không gửi các trường này).
    attribution = {
        image.image_url: (image.source_url, image.credit, image.license) for image in location.images
    }
    if location.images:
        location.images.clear()
        # Xóa ảnh cũ trước khi thêm ảnh mới để không vướng chỉ mục duy nhất
        # (một ảnh chính mỗi điểm, đường dẫn lưu trữ không trùng) trên PostgreSQL.
        db.flush()
    for image in images:
        source_url, credit, license_name = attribution.get(image.image_url, (None, None, None))
        location.images.append(
            LocationImage(
                image_url=image.image_url,
                storage_path=image.storage_path,
                is_primary=image.is_primary,
                sort_order=image.sort_order,
                alt_text=image.alt_text or location.name,
                source_url=source_url,
                credit=credit,
                license=license_name,
            )
        )


def _apply_position(
    location: TourismLocation,
    latitude: float | None,
    longitude: float | None,
    source: str | None,
    accuracy,
) -> None:
    if latitude is None or longitude is None:
        location.geom = None
        location.location_accuracy_m = None
        return
    location.geom = GeoPoint(longitude=longitude, latitude=latitude)
    if source is not None:
        location.location_source = source
    location.location_accuracy_m = accuracy if location.location_source == "device_gps" else None


def apply_location_draft_payload(
    db: Session,
    location: TourismLocation,
    payload: LocationDraftCreate | LocationDraftUpdate,
    subject_id: int,
) -> None:
    fields = payload.model_fields_set
    simple_fields = (
        "name",
        "type",
        "description",
        "district",
        "address",
        "contact_phone",
        "opening_hours",
        "ticket_price",
        "website",
    )
    for field in simple_fields:
        if field in fields:
            setattr(location, field, getattr(payload, field))
    if "services" in fields:
        location.services = list(payload.services or [])
    if "latitude" in fields:
        _apply_position(
            location,
            payload.latitude,
            payload.longitude,
            payload.location_source,
            payload.location_accuracy_m,
        )
    elif "location_source" in fields and payload.location_source is not None and location.geom is not None:
        location.location_source = payload.location_source
        if payload.location_source != "device_gps":
            location.location_accuracy_m = None
    if "name" in fields:
        location.slug = build_unique_location_slug(db, location.name, location.id)
    if "images" in fields:
        replace_location_images(db, location, list(payload.images or []), subject_id)
    if "product_ids" in fields:
        location.products = resolve_location_products(db, list(payload.product_ids or []), subject_id)


def apply_location_write_payload(
    db: Session,
    location: TourismLocation,
    payload: LocationWritePayload,
    subject_id: int,
) -> None:
    """Áp dữ liệu đầy đủ của yêu cầu cập nhật đã duyệt; giữ nguyên slug để link cũ còn dùng được."""

    for field in (
        "name",
        "type",
        "description",
        "district",
        "address",
        "contact_phone",
        "opening_hours",
        "ticket_price",
        "website",
    ):
        setattr(location, field, getattr(payload, field))
    location.services = list(payload.services)
    _apply_position(
        location,
        payload.latitude,
        payload.longitude,
        payload.location_source,
        payload.location_accuracy_m,
    )
    replace_location_images(db, location, list(payload.images), subject_id)
    location.products = resolve_location_products(db, list(payload.product_ids), subject_id)


def validate_location_submission(location: TourismLocation) -> None:
    missing_fields: list[str] = []
    if location.geom is None or location.location_source == "admin_import":
        missing_fields.append("position")
    if not location.district:
        missing_fields.append("district")
    if not location.address:
        missing_fields.append("address")
    if not location.description or len(location.description.strip()) < MIN_DESCRIPTION_LENGTH:
        missing_fields.append("description")
    if not location.images or sum(image.is_primary for image in location.images) != 1:
        missing_fields.append("primary_image")
    if missing_fields:
        raise workflow_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "LOCATION_SUBMISSION_INCOMPLETE",
            "Hồ sơ điểm du lịch chưa đủ điều kiện gửi duyệt.",
            {"missing_fields": missing_fields},
        )
    if location.geom is not None:
        ensure_inside_lam_dong(location.geom)


# ---------------------------------------------------------------------------
# Đọc dữ liệu
# ---------------------------------------------------------------------------


def open_change_request_ids(db: Session, location_ids: list[int]) -> dict[int, int]:
    if not location_ids:
        return {}
    rows = db.execute(
        select(TourismLocationChangeRequest.location_id, TourismLocationChangeRequest.id).where(
            TourismLocationChangeRequest.location_id.in_(location_ids),
            TourismLocationChangeRequest.status.in_(ACTIVE_CHANGE_REQUEST_STATUSES),
        )
    )
    return {location_id: request_id for location_id, request_id in rows}


def count_by_status(db: Session, *filters) -> dict[str, int]:
    rows = db.execute(
        select(TourismLocation.status, func.count(TourismLocation.id))
        .where(*filters)
        .group_by(TourismLocation.status)
    )
    return {status_name: count for status_name, count in rows}


def _image_reads(location: TourismLocation) -> list[ManagedLocationImageRead]:
    return [
        ManagedLocationImageRead(
            id=image.id,
            image_url=image.image_url,
            storage_path=image.storage_path,
            is_primary=image.is_primary,
            sort_order=image.sort_order,
            alt_text=image.alt_text,
        )
        for image in location.images
    ]


def to_managed_location_read(
    location: TourismLocation,
    *,
    position_check: LocationPositionCheck | None = None,
    open_change_request_id: int | None = None,
) -> ManagedLocationRead:
    subject = location.subject
    return ManagedLocationRead(
        id=location.id,
        subject_id=location.subject_id,
        name=location.name,
        slug=location.slug,
        type=location.type,
        type_label=location_type_label(location.type),
        description=location.description,
        latitude=location.geom.latitude if location.geom else None,
        longitude=location.geom.longitude if location.geom else None,
        location_source=location.location_source if location.geom else None,
        location_accuracy_m=(
            float(location.location_accuracy_m) if location.location_accuracy_m is not None else None
        ),
        district=location.district,
        address=location.address,
        contact_phone=location.contact_phone,
        opening_hours=location.opening_hours,
        ticket_price=location.ticket_price,
        services=list(location.services or []),
        website=location.website,
        status=location.status,
        submitted_at=location.submitted_at,
        reviewed_at=location.reviewed_at,
        reviewed_by_name=location.reviewer.full_name if location.reviewer else None,
        review_note=location.review_note,
        version=location.version,
        images=_image_reads(location),
        products=[
            LocationProductRead(id=product.id, name=product.name, slug=product.slug, status=product.status)
            for product in sorted(location.products, key=lambda item: item.name)
        ],
        subject=(
            LocationOwnerRead(
                id=subject.id,
                name=subject.name,
                representative=subject.representative,
                phone=subject.phone,
                status=subject.status,
                is_active=subject.user.is_active,
            )
            if subject is not None
            else None
        ),
        open_change_request_id=open_change_request_id,
        position_check=position_check,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


def location_position_check(db: Session, location: TourismLocation) -> LocationPositionCheck | None:
    if location.geom is None:
        return None
    return check_position(db, location.geom, exclude_location_id=location.id)


# ---------------------------------------------------------------------------
# Yêu cầu thay đổi điểm đã duyệt
# ---------------------------------------------------------------------------


def change_request_load_options() -> tuple:
    return (
        joinedload(TourismLocationChangeRequest.location).joinedload(TourismLocation.subject),
        joinedload(TourismLocationChangeRequest.location).selectinload(TourismLocation.images),
        joinedload(TourismLocationChangeRequest.location).selectinload(TourismLocation.products),
        joinedload(TourismLocationChangeRequest.subject),
        joinedload(TourismLocationChangeRequest.reviewer),
    )


def get_location_change_request(
    db: Session,
    request_id: int,
    *,
    subject_id: int | None = None,
    lock: bool = False,
) -> TourismLocationChangeRequest:
    filters = [TourismLocationChangeRequest.id == request_id]
    if subject_id is not None:
        filters.append(TourismLocationChangeRequest.subject_id == subject_id)
    statement = select(TourismLocationChangeRequest).where(*filters)
    if lock:
        statement = statement.with_for_update(of=TourismLocationChangeRequest)
    change_request = db.scalar(statement.options(*change_request_load_options()))
    if change_request is None:
        raise workflow_error(
            status.HTTP_404_NOT_FOUND,
            "LOCATION_CHANGE_REQUEST_NOT_FOUND",
            "Không tìm thấy yêu cầu thay đổi điểm du lịch.",
            {"request_id": request_id},
        )
    return change_request


def location_snapshot(location: TourismLocation) -> LocationSnapshotRead:
    return LocationSnapshotRead(
        name=location.name,
        type=location.type,
        description=location.description,
        latitude=location.geom.latitude if location.geom else None,
        longitude=location.geom.longitude if location.geom else None,
        location_source=location.location_source if location.geom else None,
        location_accuracy_m=(
            float(location.location_accuracy_m) if location.location_accuracy_m is not None else None
        ),
        district=location.district,
        address=location.address,
        contact_phone=location.contact_phone,
        opening_hours=location.opening_hours,
        ticket_price=location.ticket_price,
        services=list(location.services or []),
        website=location.website,
        images=[
            LocationImagePayload(
                image_url=image.image_url,
                storage_path=image.storage_path,
                is_primary=image.is_primary,
                sort_order=image.sort_order,
                alt_text=image.alt_text,
            )
            for image in location.images
        ],
        product_ids=sorted(product.id for product in location.products),
    )


def to_location_change_request_read(
    change_request: TourismLocationChangeRequest,
    *,
    proposed_position_check: LocationPositionCheck | None = None,
) -> LocationChangeRequestRead:
    location = change_request.location
    return LocationChangeRequestRead(
        id=change_request.id,
        location_id=change_request.location_id,
        subject_id=change_request.subject_id,
        request_type=change_request.request_type,
        current_data=location_snapshot(location),
        proposed_data=change_request.proposed_data,
        reason=change_request.reason,
        status=change_request.status,
        base_version=change_request.base_version,
        submitted_at=change_request.submitted_at,
        reviewed_at=change_request.reviewed_at,
        reviewed_by_name=change_request.reviewer.full_name if change_request.reviewer else None,
        review_note=change_request.review_note,
        location_name=location.name,
        location_slug=location.slug,
        subject_name=change_request.subject.name,
        proposed_position_check=proposed_position_check,
        created_at=change_request.created_at,
        updated_at=change_request.updated_at,
    )


def proposed_position_check(
    db: Session,
    change_request: TourismLocationChangeRequest,
) -> LocationPositionCheck | None:
    data = change_request.proposed_data or {}
    if change_request.request_type != "update" or data.get("latitude") is None:
        return None
    point = GeoPoint(longitude=float(data["longitude"]), latitude=float(data["latitude"]))
    return check_position(db, point, exclude_location_id=change_request.location_id)
