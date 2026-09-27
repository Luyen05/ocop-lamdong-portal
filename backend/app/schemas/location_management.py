"""Dữ liệu vào/ra cho chủ thể khai báo điểm du lịch và admin kiểm duyệt."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.product_management import _validate_http_url, _validate_image_url
from app.services.location_catalog import LocationTypeCode


LocationWorkflowStatus = Literal[
    "draft",
    "pending",
    "needs_revision",
    "approved",
    "rejected",
    "archived",
]
SubjectLocationSource = Literal["map_pin", "device_gps", "coordinates", "google_maps_link"]
LocationSource = Literal["admin_import", "map_pin", "device_gps", "coordinates", "google_maps_link"]
LocationModerationStatus = Literal["approved", "needs_revision", "rejected"]
LocationChangeStatus = Literal["pending", "needs_revision", "approved", "rejected", "cancelled"]
LocationOrigin = Literal["subject", "import"]

PHONE_PATTERN = r"^[0-9+][0-9 ().-]{7,19}$"
MIN_DESCRIPTION_LENGTH = 40


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    normalized = value.strip()
    return normalized or None


class LocationImagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_url: str = Field(min_length=8, max_length=500)
    storage_path: str | None = Field(default=None, min_length=10, max_length=500)
    is_primary: bool = False
    sort_order: int = Field(default=0, ge=0, le=100)
    alt_text: str | None = Field(default=None, max_length=255)

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str) -> str:
        return _validate_image_url(value)

    @field_validator("alt_text", mode="before")
    @classmethod
    def normalize_alt_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class _LocationFields(BaseModel):
    """Các trường chung; lớp con quyết định trường nào bắt buộc."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=255)
    type: LocationTypeCode | None = None
    description: str | None = Field(default=None, max_length=5000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_source: SubjectLocationSource | None = None
    location_accuracy_m: Decimal | None = Field(
        default=None, ge=0, le=100000, max_digits=8, decimal_places=2
    )
    district: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=1000)
    contact_phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    opening_hours: str | None = Field(default=None, max_length=100)
    ticket_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    services: list[str] | None = Field(default=None, max_length=20)
    website: str | None = Field(default=None, max_length=500)
    images: list[LocationImagePayload] | None = Field(default=None, max_length=10)
    product_ids: list[int] | None = Field(default=None, max_length=50)

    @field_validator(
        "name",
        "description",
        "district",
        "address",
        "contact_phone",
        "opening_hours",
        "website",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        return _validate_http_url(value) if value else None

    @field_validator("services")
    @classmethod
    def normalize_services(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        services: list[str] = []
        for item in value:
            normalized = item.strip()
            if not normalized:
                continue
            if len(normalized) > 60:
                raise ValueError("Mỗi dịch vụ tối đa 60 ký tự.")
            if normalized.casefold() not in {service.casefold() for service in services}:
                services.append(normalized)
        return services

    @field_validator("product_ids")
    @classmethod
    def unique_product_ids(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        if any(product_id <= 0 for product_id in value):
            raise ValueError("Mã sản phẩm không hợp lệ.")
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def validate_position_and_images(self) -> "_LocationFields":
        fields = self.model_fields_set
        if ("latitude" in fields) != ("longitude" in fields) or (
            (self.latitude is None) != (self.longitude is None)
        ):
            raise ValueError("Cần gửi đồng thời vĩ độ và kinh độ.")
        if self.latitude is not None and self.location_source is None:
            raise ValueError("Cần cho biết cách lấy vị trí (ghim bản đồ, GPS, tọa độ hoặc link).")
        if self.location_accuracy_m is not None and self.location_source != "device_gps":
            raise ValueError("Độ chính xác chỉ dùng khi lấy vị trí bằng GPS của thiết bị.")
        if self.images:
            if sum(image.is_primary for image in self.images) != 1:
                raise ValueError("Điểm du lịch phải có đúng một ảnh chính khi đã thêm ảnh.")
            urls = [image.image_url for image in self.images]
            if len(urls) != len(set(urls)):
                raise ValueError("Không được gửi trùng đường dẫn ảnh.")
        return self


class LocationDraftCreate(_LocationFields):
    """Tạo bản nháp: chỉ cần tên và loại hình, các phần khác lưu dần."""

    name: str = Field(min_length=2, max_length=255)
    type: LocationTypeCode


class LocationDraftUpdate(_LocationFields):
    """Sửa một phần bản nháp; trường không gửi được giữ nguyên."""

    @model_validator(mode="after")
    def forbid_clearing_identity(self) -> "LocationDraftUpdate":
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Tên điểm du lịch không được để trống.")
        if "type" in self.model_fields_set and self.type is None:
            raise ValueError("Loại hình không được để trống.")
        return self


class LocationWritePayload(_LocationFields):
    """Thông tin đầy đủ của điểm, dùng cho yêu cầu cập nhật điểm đã duyệt."""

    name: str = Field(min_length=2, max_length=255)
    type: LocationTypeCode
    description: str = Field(min_length=MIN_DESCRIPTION_LENGTH, max_length=5000)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_source: SubjectLocationSource
    district: str = Field(min_length=2, max_length=100)
    address: str = Field(min_length=5, max_length=1000)
    services: list[str] = Field(default_factory=list, max_length=20)
    images: list[LocationImagePayload] = Field(min_length=1, max_length=10)
    product_ids: list[int] = Field(default_factory=list, max_length=50)


class ManagedLocationImageRead(BaseModel):
    id: int
    image_url: str
    storage_path: str | None
    is_primary: bool
    sort_order: int
    alt_text: str | None


class LocationProductRead(BaseModel):
    id: int
    name: str
    slug: str
    status: str


class LocationOwnerRead(BaseModel):
    id: int
    name: str
    representative: str
    phone: str
    status: Literal["pending", "approved", "rejected"]
    is_active: bool


class NearestApprovedLocation(BaseModel):
    id: int
    name: str
    slug: str
    distance_m: float


class LocationPositionCheck(BaseModel):
    """Kiểm tra vị trí: chỉ khung tỉnh là điều kiện bắt buộc, trùng điểm chỉ để cảnh báo."""

    latitude: float
    longitude: float
    inside_lam_dong: bool
    nearest: NearestApprovedLocation | None
    duplicate_warning: bool
    duplicate_radius_m: int


class ManagedLocationRead(BaseModel):
    id: int
    subject_id: int | None
    name: str
    slug: str
    type: str
    type_label: str
    description: str | None
    latitude: float | None
    longitude: float | None
    location_source: LocationSource | None
    location_accuracy_m: float | None
    district: str | None
    address: str | None
    contact_phone: str | None
    opening_hours: str | None
    ticket_price: Decimal | None
    services: list[str]
    website: str | None
    status: LocationWorkflowStatus
    submitted_at: datetime | None
    reviewed_at: datetime | None
    reviewed_by_name: str | None
    review_note: str | None
    version: int
    images: list[ManagedLocationImageRead]
    products: list[LocationProductRead]
    subject: LocationOwnerRead | None
    open_change_request_id: int | None = None
    position_check: LocationPositionCheck | None = None
    created_at: datetime
    updated_at: datetime


class ManagedLocationListResponse(BaseModel):
    items: list[ManagedLocationRead]
    page: int
    page_size: int
    total: int
    status_counts: dict[str, int]


class LocationImageUploadResponse(BaseModel):
    image_url: str
    storage_path: str
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    size_bytes: int


class CoordinateParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=3, max_length=2000)


class CoordinateParseResponse(BaseModel):
    latitude: float
    longitude: float
    location_source: Literal["coordinates", "google_maps_link"]
    position_check: LocationPositionCheck


class LocationModerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: LocationModerationStatus
    note: str | None = Field(default=None, max_length=2000)
    # Admin kéo ghim về đúng chỗ; tọa độ mới được ghi kèm ghi chú duyệt.
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        return _strip_or_none(value)

    @model_validator(mode="after")
    def validate_decision(self) -> "LocationModerationRequest":
        if self.status in {"needs_revision", "rejected"} and not self.note:
            raise ValueError("Cần nhập ghi chú khi yêu cầu bổ sung hoặc từ chối.")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Cần gửi đồng thời vĩ độ và kinh độ khi chỉnh vị trí.")
        return self


class LocationChangeModerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: LocationModerationStatus
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        return _strip_or_none(value)

    @model_validator(mode="after")
    def require_note_when_not_approved(self) -> "LocationChangeModerationRequest":
        if self.status in {"needs_revision", "rejected"} and not self.note:
            raise ValueError("Cần nhập ghi chú khi yêu cầu bổ sung hoặc từ chối.")
        return self


class LocationUpdateRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposed_data: LocationWritePayload
    reason: str | None = Field(default=None, max_length=1000)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class LocationDeleteRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class LocationChangeRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposed_data: LocationWritePayload | None = None
    reason: str | None = Field(default=None, max_length=1000)


class LocationSnapshotRead(BaseModel):
    name: str
    type: str
    description: str | None
    latitude: float | None
    longitude: float | None
    location_source: LocationSource | None
    location_accuracy_m: float | None
    district: str | None
    address: str | None
    contact_phone: str | None
    opening_hours: str | None
    ticket_price: Decimal | None
    services: list[str]
    website: str | None
    images: list[LocationImagePayload]
    product_ids: list[int]


class LocationChangeRequestRead(BaseModel):
    id: int
    location_id: int
    subject_id: int
    request_type: Literal["update", "delete"]
    current_data: LocationSnapshotRead
    proposed_data: dict | None
    reason: str | None
    status: LocationChangeStatus
    base_version: int
    submitted_at: datetime
    reviewed_at: datetime | None
    reviewed_by_name: str | None
    review_note: str | None
    location_name: str
    location_slug: str
    subject_name: str
    # Kiểm tra vị trí đề xuất (chỉ có ở yêu cầu cập nhật).
    proposed_position_check: LocationPositionCheck | None = None
    created_at: datetime
    updated_at: datetime


class LocationChangeRequestListResponse(BaseModel):
    items: list[LocationChangeRequestRead]
    page: int
    page_size: int
    total: int
