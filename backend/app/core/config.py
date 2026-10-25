import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]
logger = logging.getLogger(__name__)

# Giá trị mẫu trong .env.example: ai cũng biết nên không được dùng để ký JWT.
JWT_SECRET_PLACEHOLDER = "replace-with-a-random-value-at-least-32-characters"
# Mặc định chỉ để chạy kiểm thử và phát triển trên máy cá nhân.
DEV_JWT_SECRET = "development-only-secret-change-me-123456"


class Settings(BaseSettings):
    app_name: str = "OCOP Lâm Đồng API"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://postgres:change-me@localhost:5432/lamdong_ocop"
    jwt_secret_key: SecretStr = Field(
        default=SecretStr(DEV_JWT_SECRET),
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=60, ge=1, le=1440)
    upload_directory: Path = BACKEND_ROOT / "uploads"
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, ge=1024)
    certificate_upload_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    # Địa chỉ công khai của backend (ví dụ https://ocop.example.vn) dùng để tạo đường dẫn ảnh lưu cục bộ.
    # Để trống thì lấy theo địa chỉ của request (có thể sai khi chạy sau proxy hoặc trong Docker).
    public_base_url: str = ""
    # Nơi lưu ảnh sản phẩm và ảnh điểm du lịch: "local" (thư mục uploads) hoặc "cloudinary".
    image_storage: Literal["local", "cloudinary"] = "local"
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: SecretStr = SecretStr("")
    cloudinary_folder: str = Field(default="ocop", pattern=r"^[A-Za-z0-9_-]+$")
    cloudinary_timeout_seconds: float = Field(default=15.0, ge=1.0, le=60.0)
    news_rss_url: str = "https://ocoplamdong.gov.vn/rssChanel/tin-tuc-su-kien.rss"
    news_rss_timeout_seconds: float = Field(default=8.0, ge=1.0, le=30.0)
    news_rss_max_bytes: int = Field(default=1024 * 1024, ge=1024, le=5 * 1024 * 1024)
    news_cache_ttl_seconds: int = Field(default=900, ge=60, le=86400)
    osrm_base_url: str = "https://router.project-osrm.org"
    osrm_timeout_seconds: float = Field(default=8.0, ge=1.0, le=30.0)
    # Đăng nhập bằng Google/Facebook. Để trống khóa của nhà cung cấp nào thì nút của nhà cung cấp đó bị ẩn.
    # Google/Facebook trả người dùng về {FRONTEND_BASE_URL}/dang-nhap/mang-xa-hoi/<google|facebook>,
    # địa chỉ này phải được khai báo đúng trong trang quản lý ứng dụng của Google/Facebook.
    frontend_base_url: str = "http://localhost:5173"
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    facebook_app_id: str = ""
    facebook_app_secret: SecretStr = SecretStr("")
    facebook_graph_version: str = Field(default="v26.0", pattern=r"^v\d+\.\d+$")
    social_login_timeout_seconds: float = Field(default=10.0, ge=1.0, le=30.0)

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def reject_placeholder_jwt_secret(cls, value: SecretStr) -> SecretStr:
        if value.get_secret_value().strip() == JWT_SECRET_PLACEHOLDER:
            raise ValueError(
                "JWT_SECRET_KEY đang là giá trị mẫu trong .env.example. Hãy đặt một chuỗi ngẫu nhiên riêng, "
                'ví dụ tạo bằng: python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        return value

    @field_validator("osrm_base_url")
    @classmethod
    def validate_osrm_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("OSRM_BASE_URL phải là đường dẫn http:// hoặc https://.")
        return normalized

    @field_validator("public_base_url")
    @classmethod
    def validate_public_base_url(cls, value: str) -> str:
        normalized = value.strip().strip("\"'").strip().rstrip("/")
        if not normalized:
            return ""
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("PUBLIC_BASE_URL phải có dạng http(s)://tên-miền[:cổng][/đường-dẫn] hoặc để trống.")
        return normalized

    @field_validator("frontend_base_url")
    @classmethod
    def validate_frontend_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path:
            raise ValueError("FRONTEND_BASE_URL phải có dạng http(s)://tên-miền[:cổng], không có đường dẫn.")
        return normalized

    @field_validator(
        "cloudinary_cloud_name",
        "cloudinary_api_key",
        "cloudinary_api_secret",
        "google_client_id",
        "google_client_secret",
        "facebook_app_id",
        "facebook_app_secret",
        mode="before",
    )
    @classmethod
    def clean_cloudinary_value(cls, value: object) -> object:
        """Bỏ khoảng trắng và dấu ngoặc kép thừa khi dán khóa vào .env."""

        if isinstance(value, SecretStr):
            value = value.get_secret_value()
        if isinstance(value, str):
            return value.strip().strip("\"'").strip()
        return value

    @model_validator(mode="after")
    def validate_cloudinary_settings(self) -> "Settings":
        if self.image_storage == "cloudinary":
            missing = [
                name
                for name, value in (
                    ("CLOUDINARY_CLOUD_NAME", self.cloudinary_cloud_name),
                    ("CLOUDINARY_API_KEY", self.cloudinary_api_key),
                    ("CLOUDINARY_API_SECRET", self.cloudinary_api_secret.get_secret_value()),
                )
                if not value.strip()
            ]
            if missing:
                raise ValueError(f"IMAGE_STORAGE=cloudinary cần khai báo: {', '.join(missing)}.")
        return self

    @model_validator(mode="after")
    def warn_development_jwt_secret(self) -> "Settings":
        if self.jwt_secret_key.get_secret_value() == DEV_JWT_SECRET:
            logger.warning(
                "JWT_SECRET_KEY đang dùng giá trị mặc định chỉ dành cho phát triển. "
                "Đặt JWT_SECRET_KEY riêng trong .env trước khi triển khai."
            )
        return self

    @property
    def social_providers(self) -> list[str]:
        """Nhà cung cấp đăng nhập đã khai báo đủ khóa, theo thứ tự hiển thị nút."""

        providers = []
        if self.google_client_id and self.google_client_secret.get_secret_value():
            providers.append("google")
        if self.facebook_app_id and self.facebook_app_secret.get_secret_value():
            providers.append("facebook")
        return providers

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
