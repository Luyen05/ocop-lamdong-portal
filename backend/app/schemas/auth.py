from datetime import datetime

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

from app.core.roles import RoleName

# Số điện thoại: chữ số, có thể có +, khoảng trắng, dấu chấm, gạch ngang, ngoặc (giống số liên hệ điểm du lịch).
PHONE_PATTERN = r"^[0-9+][0-9 ().-]{7,19}$"


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = Field(default=None, min_length=8, max_length=20, pattern=PHONE_PATTERN)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("full_name", "phone", mode="before")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class ChangePasswordRequest(BaseModel):
    """Đổi mật khẩu (cần mật khẩu hiện tại) hoặc đặt mật khẩu lần đầu cho tài khoản Google/Facebook."""

    model_config = ConfigDict(extra="forbid")

    current_password: SecretStr | None = Field(default=None, min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=8, max_length=128)


class UpdateMeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, min_length=8, max_length=20, pattern=PHONE_PATTERN)
    avatar_url: AnyHttpUrl | None = Field(default=None, max_length=500)

    @field_validator("full_name", "phone", mode="before")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("avatar_url", mode="before")
    @classmethod
    def normalize_avatar_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_patch_fields(self) -> "UpdateMeRequest":
        if not self.model_fields_set:
            raise ValueError("Cần cung cấp ít nhất một trường để cập nhật.")
        if "full_name" in self.model_fields_set and self.full_name is None:
            raise ValueError("Họ tên không được để trống.")
        return self


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    phone: str | None
    avatar_url: str | None
    is_active: bool
    role: RoleName
    # Tài khoản tạo bằng Google/Facebook chưa có mật khẩu.
    has_password: bool = True
    social_providers: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SocialProvidersResponse(BaseModel):
    providers: list[str]


class SocialAuthorizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Chuỗi ngẫu nhiên do frontend tạo và giữ lại để so khi Google/Facebook trả người dùng về.
    state: str = Field(min_length=32, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    # PKCE (bắt buộc với Google): base64url(SHA-256(code_verifier)).
    code_challenge: str | None = Field(default=None, min_length=43, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")


class SocialAuthorizeResponse(BaseModel):
    authorization_url: str


class SocialCallbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=2048)
    code_verifier: str | None = Field(default=None, min_length=43, max_length=128, pattern=r"^[A-Za-z0-9._~-]+$")


class SocialLoginResponse(TokenResponse):
    is_new_user: bool = False
