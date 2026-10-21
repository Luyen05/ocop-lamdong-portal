from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.roles import RoleName


SubjectType = Literal["cooperative", "enterprise", "household", "individual"]
SubjectStatus = Literal["pending", "approved", "rejected"]


class SubjectApplicationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=255)
    type: SubjectType
    tax_code: str | None = Field(default=None, max_length=50)
    representative: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=8, max_length=20)
    email: EmailStr | None = None
    address: str = Field(min_length=5, max_length=1000)
    district: str = Field(min_length=2, max_length=100)

    @field_validator("name", "representative", "phone", "address", "district", mode="before")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @field_validator("tax_code", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class SubjectApplicationRead(SubjectApplicationPayload):
    id: int
    user_id: int
    status: SubjectStatus
    moderation_note: str | None
    created_at: datetime
    updated_at: datetime


class ApplicantRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: RoleName
    is_active: bool


class AdminSubjectApplicationRead(SubjectApplicationRead):
    applicant: ApplicantRead


class SubjectApplicationListResponse(BaseModel):
    items: list[AdminSubjectApplicationRead]
    page: int
    page_size: int
    total: int


class SubjectModerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["approved", "rejected"]
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def require_rejection_note(self) -> "SubjectModerationRequest":
        if self.status == "rejected" and not self.note:
            raise ValueError("Cần nhập lý do khi từ chối hồ sơ.")
        return self


# Thông tin định danh đã được quản trị viên xác minh, chủ thể không tự sửa.
SUBJECT_LOCKED_FIELDS = ("name", "type", "tax_code")


class SubjectProfileUpdate(BaseModel):
    """Chủ thể đã duyệt sửa thông tin liên hệ của đơn vị (cùng ràng buộc với form đăng ký chủ thể)."""

    model_config = ConfigDict(extra="forbid")

    representative: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(default=None, min_length=5, max_length=1000)
    district: str | None = Field(default=None, min_length=2, max_length=100)
    # Chỉ để trả lỗi rõ ràng (SUBJECT_IDENTITY_LOCKED) khi client gửi kèm; không bao giờ được ghi.
    name: Any = Field(default=None, description="Không sửa được; gửi kèm sẽ bị từ chối.")
    type: Any = Field(default=None, description="Không sửa được; gửi kèm sẽ bị từ chối.")
    tax_code: Any = Field(default=None, description="Không sửa được; gửi kèm sẽ bị từ chối.")

    @field_validator("representative", "phone", "address", "district", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @model_validator(mode="after")
    def validate_patch_fields(self) -> "SubjectProfileUpdate":
        editable = self.model_fields_set - set(SUBJECT_LOCKED_FIELDS)
        if not editable and not self.locked_fields:
            raise ValueError("Cần cung cấp ít nhất một trường để cập nhật.")
        for field in ("representative", "phone", "address", "district"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"Trường {field} không được để trống.")
        return self

    @property
    def locked_fields(self) -> list[str]:
        return [field for field in SUBJECT_LOCKED_FIELDS if field in self.model_fields_set]

    def editable_values(self) -> dict[str, Any]:
        fields = self.model_fields_set - set(SUBJECT_LOCKED_FIELDS)
        return {field: getattr(self, field) for field in sorted(fields)}
