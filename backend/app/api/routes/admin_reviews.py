"""Admin kiểm duyệt đánh giá sản phẩm và điểm du lịch (gắn dưới /admin, chỉ role admin)."""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.models.location import TourismLocation
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.review import (
    AdminReviewListResponse,
    AdminReviewRead,
    ReviewModerationRequest,
    ReviewStatus,
)
from app.services.reviews import (
    recalculate_review_target,
    review_load_options,
    to_admin_review_read,
)


router = APIRouter(prefix="/reviews")


def _reviews_query(*filters):
    return (
        select(Review)
        .join(User, User.id == Review.user_id)
        .outerjoin(Product, Product.id == Review.product_id)
        .outerjoin(TourismLocation, TourismLocation.id == Review.location_id)
        .where(*filters)
    )


@router.get(
    "",
    response_model=AdminReviewListResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse}},
)
def list_reviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    review_status: ReviewStatus | None = Query(default=None, alias="status"),
    target: Literal["product", "location"] | None = Query(default=None),
    q: str | None = Query(default=None, max_length=150),
    db: Session = Depends(get_db),
) -> AdminReviewListResponse:
    filters = []
    if review_status:
        filters.append(Review.status == review_status)
    if target == "product":
        filters.append(Review.product_id.is_not(None))
    elif target == "location":
        filters.append(Review.location_id.is_not(None))
    if q and q.strip():
        keyword = f"%{q.strip()}%"
        filters.append(
            or_(
                Review.comment.ilike(keyword),
                User.full_name.ilike(keyword),
                User.email.ilike(keyword),
                Product.name.ilike(keyword),
                TourismLocation.name.ilike(keyword),
            )
        )

    total = db.scalar(
        _reviews_query(*filters).with_only_columns(func.count(Review.id)).order_by(None)
    ) or 0
    status_order = case(
        (Review.status == "pending", 0),
        (Review.status == "rejected", 1),
        else_=2,
    )
    reviews = db.scalars(
        _reviews_query(*filters)
        .options(*review_load_options())
        .order_by(status_order, Review.updated_at.desc(), Review.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    return AdminReviewListResponse(
        items=[to_admin_review_read(review) for review in reviews],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.patch(
    "/{review_id}/moderation",
    response_model=AdminReviewRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
def moderate_review(
    review_id: int,
    payload: ReviewModerationRequest,
    current_admin: CurrentUser,
    db: Session = Depends(get_db),
) -> AdminReviewRead:
    review = db.scalar(select(Review).where(Review.id == review_id).with_for_update())
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "REVIEW_NOT_FOUND",
                "message": "Không tìm thấy đánh giá.",
                "details": {"review_id": review_id},
            },
        )
    if payload.action == "reject" and not payload.reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "REJECTION_REASON_REQUIRED",
                "message": "Vui lòng nhập lý do từ chối để người viết biết cần sửa gì.",
                "details": None,
            },
        )
    new_status = "approved" if payload.action == "approve" else "rejected"
    if review.status == new_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "REVIEW_ALREADY_MODERATED",
                "message": (
                    "Đánh giá này đã được duyệt."
                    if new_status == "approved"
                    else "Đánh giá này đã bị từ chối."
                ),
                "details": {"current_status": review.status},
            },
        )

    review.status = new_status
    review.reviewed_by = current_admin.id
    review.reviewed_at = datetime.now(timezone.utc)
    review.rejection_reason = payload.reason if new_status == "rejected" else None
    db.add(review)
    db.flush()
    recalculate_review_target(db, review)
    db.commit()

    moderated = db.scalar(
        select(Review)
        .where(Review.id == review_id)
        .options(*review_load_options())
        .execution_options(populate_existing=True)
    )
    return to_admin_review_read(moderated)
