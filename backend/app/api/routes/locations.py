from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.routes.products import public_product_filters, to_product_list_item
from app.core.database import get_db
from app.models.location import TourismLocation, location_ocop_products
from app.models.product import Product
from app.schemas.error import ErrorResponse
from app.schemas.location import (
    LocationDetail,
    LocationFilterOptions,
    LocationImageRead,
    LocationListResponse,
    LocationSubjectRead,
    LocationTypeOption,
)
from app.services.location_catalog import (
    LOCATION_TYPES,
    LocationTypeCode,
    public_location_filters,
    to_location_list_item,
)


router = APIRouter(prefix="/locations", tags=["Locations"])

SortOption = Literal["name", "-name", "newest", "rating"]


@router.get(
    "",
    response_model=LocationListResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse}},
)
def list_locations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    location_type: LocationTypeCode | None = Query(default=None, alias="type"),
    district: str | None = Query(default=None, min_length=1, max_length=100),
    sort: SortOption = Query(default="name"),
    db: Session = Depends(get_db),
) -> LocationListResponse:
    filters = public_location_filters(
        search=search,
        location_type=location_type,
        district=district,
    )
    total = db.scalar(select(func.count(TourismLocation.id)).where(*filters)) or 0
    sort_columns = {
        "name": (TourismLocation.name.asc(),),
        "-name": (TourismLocation.name.desc(),),
        "newest": (TourismLocation.created_at.desc(),),
        "rating": (TourismLocation.rating_avg.desc(),),
    }
    locations = db.scalars(
        select(TourismLocation)
        .where(*filters)
        .options(selectinload(TourismLocation.images))
        .order_by(*sort_columns[sort], TourismLocation.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return LocationListResponse(
        items=[to_location_list_item(location) for location in locations],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/filter-options", response_model=LocationFilterOptions)
def get_location_filter_options(db: Session = Depends(get_db)) -> LocationFilterOptions:
    filters = public_location_filters()
    used_types = set(
        db.scalars(select(TourismLocation.type).where(*filters).distinct()).all()
    )
    districts = db.scalars(
        select(TourismLocation.district)
        .where(*filters, func.trim(TourismLocation.district) != "")
        .distinct()
        .order_by(TourismLocation.district)
    ).all()
    return LocationFilterOptions(
        types=[
            LocationTypeOption(value=code, label=label)
            for code, label in LOCATION_TYPES.items()
            if code in used_types
        ],
        districts=list(districts),
    )


@router.get(
    "/{slug}",
    response_model=LocationDetail,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def get_location(slug: str, db: Session = Depends(get_db)) -> LocationDetail:
    location = db.scalar(
        select(TourismLocation)
        .where(TourismLocation.slug == slug, *public_location_filters())
        .options(
            selectinload(TourismLocation.images),
            joinedload(TourismLocation.subject),
        )
    )
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "LOCATION_NOT_FOUND",
                "message": "Không tìm thấy điểm du lịch.",
                "details": {"slug": slug},
            },
        )

    products = db.scalars(
        select(Product)
        .join(Product.subject)
        .join(location_ocop_products, location_ocop_products.c.product_id == Product.id)
        .where(location_ocop_products.c.location_id == location.id, *public_product_filters())
        .options(
            joinedload(Product.category),
            joinedload(Product.subject),
            selectinload(Product.images),
        )
        .order_by(Product.name.asc(), Product.id.asc())
    ).all()
    subject = location.subject
    return LocationDetail(
        **to_location_list_item(location).model_dump(),
        contact_phone=location.contact_phone,
        website=location.website,
        source_url=location.source_url,
        views=location.views,
        images=[
            LocationImageRead(
                id=image.id,
                image_url=image.image_url,
                is_primary=image.is_primary,
                sort_order=image.sort_order,
            )
            for image in location.images
        ],
        subject=(
            LocationSubjectRead(id=subject.id, name=subject.name, district=subject.district)
            if subject is not None and subject.status == "approved"
            else None
        ),
        products=[to_product_list_item(product) for product in products],
        updated_at=location.updated_at,
    )
