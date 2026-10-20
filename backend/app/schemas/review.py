from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ReviewStatus = Literal["pending", "approved", "rejected"]
ReviewTargetType = Literal["product", "location"]

COMMENT_MIN_LENGTH = 10
COMMENT_MAX_LENGTH = 1000


def _strip_text(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


class ReviewCreate(BaseModel):
    """Nội dung người dùng gửi; lưu dạng văn bản thuần, giao diện tự escape khi hiển thị."""

    model_config = ConfigDict(extra="forbid")

    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=COMMENT_MIN_LENGTH, max_length=COMMENT_MAX_LENGTH)

    @field_validator("comment", mode="before")
    @classmethod
    def normalize_comment(cls, value: object) -> object:
        return _strip_text(value)


class ReviewUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(
        default=None,
        min_length=COMMENT_MIN_LENGTH,
        max_length=COMMENT_MAX_LENGTH,
    )

    @field_validator("comment", mode="before")
    @classmethod
    def normalize_comment(cls, value: object) -> object:
        return _strip_text(value)

    @model_validator(mode="after")
    def require_change(self) -> "ReviewUpdate":
        if self.rating is None and self.comment is None:
            raise ValueError("Cần gửi số sao hoặc nội dung đánh giá.")
        return self


class ReviewModerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=COMMENT_MAX_LENGTH)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> object:
        value = _strip_text(value)
        return value or None


class PublicReviewRead(BaseModel):
    id: int
    rating: int
    comment: str
    author_name: str
    created_at: datetime
    updated_at: datetime


class ReviewSummary(BaseModel):
    average: float
    count: int
    # Khóa "1".."5": số đánh giá đã duyệt theo từng mức sao.
    distribution: dict[str, int]


class PublicReviewListResponse(BaseModel):
    items: list[PublicReviewRead]
    page: int
    page_size: int
    total: int
    summary: ReviewSummary


class ReviewTargetRead(BaseModel):
    type: ReviewTargetType
    id: int
    name: str
    slug: str


class MyReviewRead(BaseModel):
    id: int
    rating: int
    comment: str
    status: ReviewStatus
    rejection_reason: str | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    target: ReviewTargetRead


class MyReviewListResponse(BaseModel):
    items: list[MyReviewRead]
    page: int
    page_size: int
    total: int


class ReviewAuthorRead(BaseModel):
    id: int
    full_name: str
    email: str


class AdminReviewRead(MyReviewRead):
    author: ReviewAuthorRead
    reviewed_by_name: str | None


class AdminReviewListResponse(BaseModel):
    items: list[AdminReviewRead]
    page: int
    page_size: int
    total: int
