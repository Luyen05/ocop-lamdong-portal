"""Tính điểm trung bình và chuyển đổi dữ liệu đánh giá sản phẩm, điểm du lịch."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.location import TourismLocation
from app.models.product import Product
from app.models.review import Review
from app.schemas.review import (
    AdminReviewRead,
    MyReviewRead,
    ReviewAuthorRead,
    ReviewSummary,
    ReviewTargetRead,
)


TWO_PLACES = Decimal("0.01")


def review_load_options() -> tuple:
    return (
        joinedload(Review.product),
        joinedload(Review.location),
        joinedload(Review.user),
        joinedload(Review.reviewer),
    )


def _target_filter(*, product_id: int | None, location_id: int | None):
    if product_id is not None:
        return Review.product_id == product_id
    if location_id is not None:
        return Review.location_id == location_id
    raise ValueError("Cần product_id hoặc location_id.")


def _round_average(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def review_summary(
    db: Session,
    *,
    product_id: int | None = None,
    location_id: int | None = None,
) -> ReviewSummary:
    """Tóm tắt các đánh giá đã duyệt: trung bình, tổng số và số lượt theo từng mức sao."""

    rows = db.execute(
        select(Review.rating, func.count(Review.id))
        .where(
            _target_filter(product_id=product_id, location_id=location_id),
            Review.status == "approved",
        )
        .group_by(Review.rating)
    ).all()
    distribution = {str(star): 0 for star in range(1, 6)}
    total = 0
    weighted = 0
    for rating, count in rows:
        distribution[str(int(rating))] = int(count)
        total += int(count)
        weighted += int(rating) * int(count)
    average = _round_average(Decimal(weighted) / Decimal(total)) if total else Decimal("0.00")
    return ReviewSummary(average=float(average), count=total, distribution=distribution)


def recalculate_rating(
    db: Session,
    *,
    product_id: int | None = None,
    location_id: int | None = None,
) -> Decimal:
    """Ghi lại rating_avg của sản phẩm/điểm từ các đánh giá đã duyệt (0 khi chưa có)."""

    average = db.scalar(
        select(func.avg(Review.rating)).where(
            _target_filter(product_id=product_id, location_id=location_id),
            Review.status == "approved",
        )
    )
    rounded = _round_average(average)
    target = (
        db.get(Product, product_id)
        if product_id is not None
        else db.get(TourismLocation, location_id)
    )
    if target is not None and Decimal(target.rating_avg or 0) != rounded:
        target.rating_avg = rounded
        db.add(target)
    return rounded


def recalculate_review_target(db: Session, review: Review) -> Decimal:
    return recalculate_rating(db, product_id=review.product_id, location_id=review.location_id)


def review_target(review: Review) -> ReviewTargetRead:
    if review.product_id is not None and review.product is not None:
        return ReviewTargetRead(
            type="product",
            id=review.product.id,
            name=review.product.name,
            slug=review.product.slug,
        )
    if review.location is None:
        raise ValueError(f"Đánh giá {review.id} không gắn với sản phẩm hay điểm du lịch.")
    return ReviewTargetRead(
        type="location",
        id=review.location.id,
        name=review.location.name,
        slug=review.location.slug,
    )


def to_my_review_read(review: Review) -> MyReviewRead:
    return MyReviewRead(
        id=review.id,
        rating=review.rating,
        comment=review.comment,
        status=review.status,
        rejection_reason=review.rejection_reason,
        reviewed_at=review.reviewed_at,
        created_at=review.created_at,
        updated_at=review.updated_at,
        target=review_target(review),
    )


def to_admin_review_read(review: Review) -> AdminReviewRead:
    return AdminReviewRead(
        **to_my_review_read(review).model_dump(),
        author=ReviewAuthorRead(
            id=review.user.id,
            full_name=review.user.full_name,
            email=review.user.email,
        ),
        reviewed_by_name=review.reviewer.full_name if review.reviewer else None,
    )
