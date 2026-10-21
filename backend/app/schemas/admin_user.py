from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.roles import RoleName
from app.schemas.subject import SubjectStatus


class AdminUserSubjectRead(BaseModel):
    """Hồ sơ chủ thể gắn với tài khoản (nếu có)."""

    id: int
    name: str
    status: SubjectStatus


class AdminUserRead(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str | None
    role: RoleName
    is_active: bool
    created_at: datetime
    has_password: bool
    social_providers: list[str]
    subject: AdminUserSubjectRead | None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserRead]
    page: int
    page_size: int
    total: int


class AdminUserStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool
