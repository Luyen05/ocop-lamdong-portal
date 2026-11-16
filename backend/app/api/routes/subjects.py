from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.routes.products import (
    public_product_filters,
    subject_account_active_filter,
    to_product_list_item,
)
from app.core.database import get_db
from app.models.location import TourismLocation
from app.models.product import Product
from app.models.subject import Subject
from app.schemas.error import ErrorResponse
from app.schemas.location import PublicSubjectDetail
from app.services.location_catalog import public_location_filters, to_location_list_item


router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.get(
    "/{subject_id}",
    response_model=PublicSubjectDetail,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def get_public_subject(subject_id: int, db: Session = Depends(get_db)) -> PublicSubjectDetail:
    """Từ một chủ thể truy ra mọi điểm (du lịch, cửa hàng) và sản phẩm công khai của chủ thể."""

    subject = db.scalar(
        select(Subject).where(
            Subject.id == subject_id,
            Subject.status == "approved",
            subject_account_active_filter(),
        )
    )
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SUBJECT_NOT_FOUND",
                "message": "Không tìm thấy chủ thể.",
                "details": {"subject_id": subject_id},
            },
        )
    locations = db.scalars(
        select(TourismLocation)
        .where(*public_location_filters(subject_id=subject.id))
        .options(selectinload(TourismLocation.images))
        .order_by(TourismLocation.name.asc(), TourismLocation.id.asc())
    ).all()
    products = db.scalars(
        select(Product)
        .join(Product.subject)
        .where(Product.subject_id == subject.id, *public_product_filters())
        .options(
            joinedload(Product.category),
            joinedload(Product.subject),
            selectinload(Product.images),
        )
        .order_by(Product.name.asc(), Product.id.asc())
    ).all()
    return PublicSubjectDetail(
        id=subject.id,
        name=subject.name,
        district=subject.district,
        address=subject.address,
        locations=[to_location_list_item(location) for location in locations],
        products=[to_product_list_item(product) for product in products],
    )
