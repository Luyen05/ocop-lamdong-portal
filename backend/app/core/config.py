from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "OCOP Lâm Đồng API"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://postgres:change-me@localhost:5432/lamdong_ocop"
    jwt_secret_key: SecretStr = Field(
        default=SecretStr("development-only-secret-change-me-123456"),
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=60, ge=1, le=1440)
    upload_directory: Path = BACKEND_ROOT / "uploads"
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, ge=1024)
    certificate_upload_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    news_rss_url: str = "https://ocoplamdong.gov.vn/rssChanel/tin-tuc-su-kien.rss"
    news_rss_timeout_seconds: float = Field(default=8.0, ge=1.0, le=30.0)
    news_rss_max_bytes: int = Field(default=1024 * 1024, ge=1024, le=5 * 1024 * 1024)
    news_cache_ttl_seconds: int = Field(default=900, ge=60, le=86400)
    osrm_base_url: str = "https://router.project-osrm.org"
    osrm_timeout_seconds: float = Field(default=8.0, ge=1.0, le=30.0)

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("osrm_base_url")
    @classmethod
    def validate_osrm_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("OSRM_BASE_URL phải là đường dẫn http:// hoặc https://.")
        return normalized

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
