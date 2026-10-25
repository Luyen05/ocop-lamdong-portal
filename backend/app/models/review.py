from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.location import TourismLocation
    from app.models.product import Product
    from app.models.user import User


REVIEW_STATUSES = ("pending", "approved", "rejected")
ID_TYPE = BigInteger().with_variant(Integer, "sqlite")


class Review(Base):
    """Đánh giá của người dùng cho một sản phẩm OCOP hoặc một điểm du lịch (giống database/schema.sql)."""

    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="reviews_rating_check"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="reviews_status_check",
        ),
        CheckConstraint(
            "(product_id IS NOT NULL AND location_id IS NULL)"
            " OR (product_id IS NULL AND location_id IS NOT NULL)",
            name="review_exactly_one_target",
        ),
        CheckConstraint(
            "status <> 'rejected'"
            " OR (rejection_reason IS NOT NULL AND length(trim(rejection_reason)) > 0)",
            name="reviews_rejection_reason_check",
        ),
        Index("idx_reviews_product_status", "product_id", "status"),
        Index("idx_reviews_location_status", "location_id", "status"),
        Index(
            "uq_review_user_product",
            "user_id",
            "product_id",
            unique=True,
            sqlite_where=text("product_id IS NOT NULL"),
            postgresql_where=text("product_id IS NOT NULL"),
        ),
        Index(
            "uq_review_user_location",
            "user_id",
            "location_id",
            unique=True,
            sqlite_where=text("location_id IS NOT NULL"),
            postgresql_where=text("location_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("ocop_products.id", ondelete="CASCADE"),
    )
    location_id: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("tourism_locations.id", ondelete="CASCADE"),
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    reviewed_by: Mapped[int | None] = mapped_column(
        ID_TYPE,
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])
    product: Mapped[Product | None] = relationship()
    location: Mapped[TourismLocation | None] = relationship()
