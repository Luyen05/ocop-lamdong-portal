from datetime import datetime
from typing import Literal

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
