from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.subject import Subject
from app.schemas.error import ErrorResponse
from app.schemas.product import (
    ProductCategoryRead,
    ProductListItem,
    ProductListResponse,
    ProductSubjectRead,
)


router = APIRouter(prefix="/products", tags=["Products"])

SortOption = Literal["newest", "name", "-name", "price", "-price", "rating"]


def to_product_list_item(product: Product) -> ProductListItem:
    primary_image = product.images[0].image_url if product.images else None
    return ProductListItem(
        id=product.id,
        name=product.name,
        slug=product.slug,
        star=product.star,
        price=float(product.price),
        unit=product.unit,
        description=product.description,
        rating_avg=float(product.rating_avg),
        primary_image_url=primary_image,
        category=ProductCategoryRead(
            id=product.category.id,
            name=product.category.name,
            slug=product.category.slug,
        ),
        subject=ProductSubjectRead(
            id=product.subject.id,
            name=product.subject.name,
            district=product.subject.district,
        ),
        created_at=product.created_at,
    )


@router.get(
    "",
    response_model=ProductListResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse}},
)
def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    category: str | None = Query(default=None, min_length=1, max_length=150),
    star: int | None = Query(default=None, ge=3, le=5),
    district: str | None = Query(default=None, min_length=1, max_length=100),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    sort: SortOption = Query(default="newest"),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_PRICE_RANGE",
                "message": "Giá tối thiểu không được lớn hơn giá tối đa.",
                "details": {"min_price": str(min_price), "max_price": str(max_price)},
            },
        )

    filters = [Product.status == "approved", Subject.status == "approved"]
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(
            or_(
                Product.name.ilike(keyword),
                Product.description.ilike(keyword),
                Subject.name.ilike(keyword),
            )
        )
    if category:
        filters.append(func.lower(Category.slug) == category.strip().lower())
    if star is not None:
        filters.append(Product.star == star)
    if district:
        filters.append(Subject.district == district.strip())
    if min_price is not None:
        filters.append(Product.price >= min_price)
    if max_price is not None:
        filters.append(Product.price <= max_price)

    base_statement = select(Product).join(Product.subject).join(Product.category).where(*filters)
    total = db.scalar(
        select(func.count(Product.id))
        .join(Product.subject)
        .join(Product.category)
        .where(*filters)
    ) or 0

    sort_columns = {
        "newest": Product.created_at.desc(),
        "name": Product.name.asc(),
        "-name": Product.name.desc(),
        "price": Product.price.asc(),
        "-price": Product.price.desc(),
        "rating": Product.rating_avg.desc(),
    }
    statement = (
        base_statement.options(
            joinedload(Product.category),
            joinedload(Product.subject),
            selectinload(Product.images),
        )
        .order_by(sort_columns[sort], Product.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    products = list(db.scalars(statement).all())

    return ProductListResponse(
        items=[to_product_list_item(product) for product in products],
        page=page,
        page_size=page_size,
        total=total,
    )
