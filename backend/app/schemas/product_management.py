from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ProductWorkflowStatus = Literal[
    "draft",
    "pending",
    "needs_revision",
    "approved",
    "rejected",
    "suspended",
    "archived",
]
ProductModerationStatus = Literal["approved", "needs_revision", "rejected"]
ProductChangeStatus = Literal[
    "pending",
    "needs_revision",
    "approved",
    "rejected",
    "cancelled",
]
VerificationLevel = Literal["A", "B1", "B2", "C"]
ProductVerificationStatus = Literal[
    "verified_official_decision",
    "verified_government_source",
    "pending_verification",
]
ProductEvidenceIssue = Literal[
    "no_recognition_source",
    "missing_decision",
    "missing_issued_at",
    "missing_expires_at",
]
EvidenceRole = Literal["recognition", "identity", "address", "enrichment"]
DataSourceType = Literal[
    "legal_document",
    "recognition_decision",
    "government_portal",
    "government_news",
    "subject_website",
    "academic_reference",
    "other",
]


def _validate_http_url(value: str) -> str:
    normalized = value.strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Đường dẫn phải bắt đầu bằng http:// hoặc https://.")
    return normalized


class ProductImagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_url: str = Field(min_length=8, max_length=500)
    storage_path: str | None = Field(default=None, min_length=10, max_length=500)
    is_primary: bool = False
    sort_order: int = Field(default=0, ge=0, le=100)

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str) -> str:
        return _validate_http_url(value)


class ProductWritePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=255)
    star: int = Field(ge=3, le=5)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    unit: str = Field(min_length=1, max_length=50)
    cert_code: str = Field(min_length=2, max_length=100)
    cert_issued_at: date
    cert_expires_at: date
    issuing_authority: str = Field(min_length=2, max_length=255)
    certificate_url: str = Field(min_length=8, max_length=500)
    vietgap_code: str | None = Field(default=None, max_length=100)
    description: str = Field(min_length=10, max_length=5000)
    story: str | None = Field(default=None, max_length=10000)
    ingredients: str | None = Field(default=None, max_length=5000)
    usage_instructions: str | None = Field(default=None, max_length=5000)
    images: list[ProductImagePayload] = Field(min_length=1, max_length=10)

    @field_validator(
        "name",
        "unit",
        "cert_code",
        "issuing_authority",
        "description",
        mode="before",
    )
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @field_validator(
        "vietgap_code",
        "story",
        "ingredients",
        "usage_instructions",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("certificate_url")
    @classmethod
    def validate_certificate_url(cls, value: str) -> str:
        return _validate_http_url(value)

    @model_validator(mode="after")
    def validate_certificate_and_images(self) -> "ProductWritePayload":
        if self.cert_expires_at <= self.cert_issued_at:
            raise ValueError("Ngày hết hạn phải sau ngày cấp chứng nhận.")
        if sum(image.is_primary for image in self.images) != 1:
            raise ValueError("Sản phẩm phải có đúng một ảnh chính.")
        image_urls = [image.image_url for image in self.images]
        if len(image_urls) != len(set(image_urls)):
            raise ValueError("Không được gửi trùng đường dẫn ảnh sản phẩm.")
        return self


class ManagedProductImageRead(ProductImagePayload):
    id: int


class ProductImageUploadResponse(BaseModel):
    image_url: str
    storage_path: str
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    size_bytes: int


class ManagedProductCategoryRead(BaseModel):
    id: int
    name: str
    slug: str


class ManagedProductSubjectRead(BaseModel):
    id: int
    name: str
    representative: str
    tax_code: str | None


class ManagedProductRead(BaseModel):
    id: int
    subject_id: int
    category_id: int
    name: str
    slug: str
    star: int
    price: Decimal
    unit: str
    cert_code: str | None
    cert_issued_at: date | None
    cert_expires_at: date | None
    issuing_authority: str | None
    certificate_url: str | None
    vietgap_code: str | None
    description: str
    story: str | None
    ingredients: str | None
    usage_instructions: str | None
    status: ProductWorkflowStatus
    submitted_at: datetime | None
    reviewed_at: datetime | None
    reviewed_by_name: str | None
    moderation_note: str | None
    version: int
    category: ManagedProductCategoryRead
    subject: ManagedProductSubjectRead
    images: list[ManagedProductImageRead]
    verification_level: VerificationLevel | None = None
    verification_status: ProductVerificationStatus = "pending_verification"
    evidence_count: int = 0
    missing_decision: bool = True
    missing_issued_at: bool = True
    created_at: datetime
    updated_at: datetime


class ManagedProductListResponse(BaseModel):
    items: list[ManagedProductRead]
    page: int
    page_size: int
    total: int


class DataSourceRead(BaseModel):
    id: int
    title: str
    document_number: str | None
    issuing_body: str | None
    source_type: str
    published_at: date | None
    source_url: str
    local_path: str | None
    sha256: str | None
    retrieved_at: date


class DataSourceWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=500)
    document_number: str | None = Field(default=None, max_length=100)
    issuing_body: str | None = Field(default=None, max_length=255)
    source_type: DataSourceType
    published_at: date | None = None
    source_url: str = Field(min_length=8, max_length=2000)
    retrieved_at: date = Field(default_factory=date.today)

    @field_validator("title", "document_number", "issuing_body", mode="before")
    @classmethod
    def normalize_source_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        return _validate_http_url(value)


class DataSourceListResponse(BaseModel):
    items: list[DataSourceRead]
    page: int
    page_size: int
    total: int


class ProductEvidenceLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: int = Field(gt=0)
    evidence_role: EvidenceRole = "recognition"
    verification_level: VerificationLevel
    original_address: str | None = Field(default=None, max_length=2000)
    verified_at: date = Field(default_factory=date.today)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("original_address", "notes", mode="before")
    @classmethod
    def normalize_link_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ProductEvidenceLinkUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verification_level: VerificationLevel
    original_address: str | None = Field(default=None, max_length=2000)
    verified_at: date
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("original_address", "notes", mode="before")
    @classmethod
    def normalize_updated_link_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ProductEvidenceSourceRead(BaseModel):
    evidence_role: EvidenceRole
    verification_level: VerificationLevel
    original_address: str | None
    verified_at: date
    notes: str | None
    source: DataSourceRead


class ProductEvidenceResponse(BaseModel):
    product_id: int
    product_name: str
    verification_level: VerificationLevel | None
    verification_status: ProductVerificationStatus
    evidence_count: int
    issues: list[ProductEvidenceIssue]
    sources: list[ProductEvidenceSourceRead]


class ProductModerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ProductModerationStatus
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def require_note_when_not_approved(self) -> "ProductModerationRequest":
        if self.status in {"needs_revision", "rejected"} and not self.note:
            raise ValueError("Cần nhập ghi chú khi yêu cầu bổ sung hoặc từ chối.")
        return self


class ProductUpdateRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposed_data: ProductWritePayload
    reason: str | None = Field(default=None, max_length=1000)


class ProductDeleteRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class ProductSnapshotRead(BaseModel):
    category_id: int
    name: str
    star: int
    price: Decimal
    unit: str
    cert_code: str | None
    cert_issued_at: date | None
    cert_expires_at: date | None
    issuing_authority: str | None
    certificate_url: str | None
    vietgap_code: str | None
    description: str
    story: str | None
    ingredients: str | None
    usage_instructions: str | None
    images: list[ProductImagePayload]


class ProductChangeRequestRead(BaseModel):
    id: int
    product_id: int
    subject_id: int
    request_type: Literal["update", "delete"]
    current_data: ProductSnapshotRead
    proposed_data: dict | None
    reason: str | None
    status: ProductChangeStatus
    base_version: int
    submitted_at: datetime
    reviewed_at: datetime | None
    reviewed_by_name: str | None
    review_note: str | None
    product_name: str
    subject_name: str
    created_at: datetime
    updated_at: datetime


class ProductChangeRequestListResponse(BaseModel):
    items: list[ProductChangeRequestRead]
    page: int
    page_size: int
    total: int


class ProductChangeRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposed_data: ProductWritePayload | None = None
    reason: str | None = Field(default=None, max_length=1000)


class ProductSuspensionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=5, max_length=2000)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value
