"""Đánh giá công khai của sản phẩm OCOP và điểm du lịch; người dùng viết, sửa, xóa đánh giá của mình."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.api.routes.products import public_product_filters
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.location import TourismLocation
from app.models.product import Product
from app.models.review import Review
from app.models.subject import Subject
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.review import (
    MyReviewListResponse,
    MyReviewRead,
    PublicReviewListResponse,
    PublicReviewRead,
    ReviewCreate,
    ReviewUpdate,
)
from app.services.location_catalog import public_location_filters
from app.services.reviews import (
    recalculate_rating,
    recalculate_review_target,
    review_load_options,
    review_summary,
    to_my_review_read,
)


router = APIRouter(tags=["Reviews"])

AUTH_RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
}


def _not_found(code: str, message: str, details: dict) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": code, "message": message, "details": details},
    )


def get_public_product(db: Session, product_id: int) -> Product:
    product = db.scalar(
        select(Product)
        .join(Product.subject)
        .where(Product.id == product_id, *public_product_filters())
    )
    if product is None:
        raise _not_found(
            "PRODUCT_NOT_FOUND",
            "Không tìm thấy sản phẩm.",
            {"product_id": product_id},
        )
    return product


def get_public_location(db: Session, location_id: int) -> TourismLocation:
    location = db.scalar(
        select(TourismLocation).where(
            TourismLocation.id == location_id,
            *public_location_filters(),
        )
    )
    if location is None:
        raise _not_found(
            "LOCATION_NOT_FOUND",
            "Không tìm thấy điểm du lịch.",
            {"location_id": location_id},
        )
    return location


def list_public_reviews(
    db: Session,
    *,
    page: int,
    page_size: int,
    product_id: int | None = None,
    location_id: int | None = None,
) -> PublicReviewListResponse:
    target_filter = (
        Review.product_id == product_id if product_id is not None else Review.location_id == location_id
    )
    filters = (target_filter, Review.status == "approved")
    total = db.scalar(select(func.count(Review.id)).where(*filters)) or 0
    rows = db.execute(
        select(Review, User.full_name)
        .join(User, User.id == Review.user_id)
        .where(*filters)
        .order_by(Review.created_at.desc(), Review.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return PublicReviewListResponse(
        items=[
            PublicReviewRead(
                id=review.id,
                rating=review.rating,
                comment=review.comment,
                author_name=full_name,
                created_at=review.created_at,
                updated_at=review.updated_at,
            )
            for review, full_name in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
        summary=review_summary(db, product_id=product_id, location_id=location_id),
    )


def ensure_can_review(current_user: User, owner_user_id: int | None) -> None:
    if current_user.role.name == RoleName.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_CANNOT_REVIEW",
                "message": "Tài khoản quản trị chỉ kiểm duyệt, không viết đánh giá.",
                "details": None,
            },
        )
    if owner_user_id is not None and owner_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "OWN_TARGET_REVIEW_FORBIDDEN",
                "message": "Bạn không thể tự đánh giá sản phẩm hoặc điểm du lịch của đơn vị mình.",
                "details": None,
            },
        )


def create_review(
    db: Session,
    current_user: User,
    payload: ReviewCreate,
    *,
    product_id: int | None = None,
    location_id: int | None = None,
) -> MyReviewRead:
    target_filter = (
        Review.product_id == product_id if product_id is not None else Review.location_id == location_id
    )
    existing_id = db.scalar(
        select(Review.id).where(Review.user_id == current_user.id, target_filter)
    )
    if existing_id is not None:
        raise _already_reviewed(existing_id)

    review = Review(
        user_id=current_user.id,
        product_id=product_id,
        location_id=location_id,
        rating=payload.rating,
        comment=payload.comment,
        status="pending",
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError as exc:
        # Hai yêu cầu gửi cùng lúc: chỉ mục duy nhất trong database chặn bản thứ hai.
        db.rollback()
        existing_id = db.scalar(
            select(Review.id).where(Review.user_id == current_user.id, target_filter)
        )
        if existing_id is None:
            raise
        raise _already_reviewed(existing_id) from exc
    return to_my_review_read(load_review(db, review.id))


def _already_reviewed(review_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "REVIEW_ALREADY_EXISTS",
            "message": "Bạn đã đánh giá mục này. Hãy sửa đánh giá cũ thay vì viết mới.",
            "details": {"review_id": review_id},
        },
    )


def load_review(db: Session, review_id: int) -> Review:
    review = db.scalar(
        select(Review)
        .where(Review.id == review_id)
        .options(*review_load_options())
        .execution_options(populate_existing=True)
    )
    if review is None:
        raise _not_found(
            "REVIEW_NOT_FOUND",
            "Không tìm thấy đánh giá.",
            {"review_id": review_id},
        )
    return review


def get_own_review(db: Session, current_user: User, review_id: int) -> Review:
    review = load_review(db, review_id)
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "REVIEW_FORBIDDEN",
                "message": "Bạn chỉ có thể sửa hoặc xóa đánh giá của mình.",
                "details": None,
            },
        )
    return review


@router.get(
    "/products/{product_id}/reviews",
    response_model=PublicReviewListResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def list_product_reviews(
    product_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db),
) -> PublicReviewListResponse:
    get_public_product(db, product_id)
    return list_public_reviews(db, page=page, page_size=page_size, product_id=product_id)


@router.get(
    "/locations/{location_id}/reviews",
    response_model=PublicReviewListResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def list_location_reviews(
    location_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db),
) -> PublicReviewListResponse:
    get_public_location(db, location_id)
    return list_public_reviews(db, page=page, page_size=page_size, location_id=location_id)


@router.post(
    "/products/{product_id}/reviews",
    response_model=MyReviewRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        **AUTH_RESPONSES,
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
def create_product_review(
    product_id: int,
    payload: ReviewCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> MyReviewRead:
    product = get_public_product(db, product_id)
    owner_user_id = db.scalar(select(Subject.user_id).where(Subject.id == product.subject_id))
    ensure_can_review(current_user, owner_user_id)
    return create_review(db, current_user, payload, product_id=product.id)


@router.post(
    "/locations/{location_id}/reviews",
    response_model=MyReviewRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        **AUTH_RESPONSES,
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
def create_location_review(
    location_id: int,
    payload: ReviewCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> MyReviewRead:
    location = get_public_location(db, location_id)
    owner_user_id = (
        db.scalar(select(Subject.user_id).where(Subject.id == location.subject_id))
        if location.subject_id is not None
        else None
    )
    ensure_can_review(current_user, owner_user_id)
    return create_review(db, current_user, payload, location_id=location.id)


@router.get(
    "/reviews/me",
    response_model=MyReviewListResponse,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)
def list_my_reviews(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    product_id: int | None = Query(default=None, ge=1),
    location_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> MyReviewListResponse:
    """Mọi đánh giá của tài khoản hiện tại; lọc theo product_id/location_id để biết đã đánh giá chưa."""

    filters = [Review.user_id == current_user.id]
    if product_id is not None:
        filters.append(Review.product_id == product_id)
    if location_id is not None:
        filters.append(Review.location_id == location_id)
    total = db.scalar(select(func.count(Review.id)).where(*filters)) or 0
    reviews = db.scalars(
        select(Review)
        .where(*filters)
        .options(*review_load_options())
        .order_by(Review.updated_at.desc(), Review.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return MyReviewListResponse(
        items=[to_my_review_read(review) for review in reviews],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.patch(
    "/reviews/{review_id}",
    response_model=MyReviewRead,
    responses={**AUTH_RESPONSES, status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def update_my_review(
    review_id: int,
    payload: ReviewUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> MyReviewRead:
    review = get_own_review(db, current_user, review_id)
    if payload.rating is not None:
        review.rating = payload.rating
    if payload.comment is not None:
        review.comment = payload.comment
    # Nội dung mới phải được duyệt lại trước khi hiện công khai.
    review.status = "pending"
    review.reviewed_by = None
    review.reviewed_at = None
    review.rejection_reason = None
    db.add(review)
    db.flush()
    recalculate_review_target(db, review)
    db.commit()
    return to_my_review_read(load_review(db, review.id))


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**AUTH_RESPONSES, status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def delete_my_review(
    review_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Response:
    review = get_own_review(db, current_user, review_id)
    product_id, location_id = review.product_id, review.location_id
    db.delete(review)
    db.flush()
    recalculate_rating(db, product_id=product_id, location_id=location_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
