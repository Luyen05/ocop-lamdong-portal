from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.models.category import Category
from app.models.data_source import ProductSource
from app.models.product import Product
from app.models.subject import Subject
from app.schemas.error import ErrorResponse
from app.schemas.product import (
    ProductCategoryRead,
    ProductDetail,
    ProductFilterOptions,
    ProductImageRead,
    ProductListItem,
    ProductListResponse,
    ProductPublicSourceRead,
    ProductSearchSuggestions,
    ProductSubjectRead,
)


router = APIRouter(prefix="/products", tags=["Products"])

SortOption = Literal["newest", "name", "-name", "price", "-price", "rating"]


def search_expressions(search: str, db: Session):
    normalized = search.strip()
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        query = func.websearch_to_tsquery("simple", normalized)
        vector = func.to_tsvector(
            "simple",
            func.concat_ws(
                " ",
                Product.name,
                Product.description,
                Product.story,
                Product.ingredients,
                Product.usage_instructions,
            ),
        )
        return vector.op("@@")(query), func.ts_rank_cd(vector, query)

    keyword = f"%{normalized}%"
    return (
        or_(
            Product.name.ilike(keyword),
            Product.description.ilike(keyword),
            Product.story.ilike(keyword),
            Product.ingredients.ilike(keyword),
            Product.usage_instructions.ilike(keyword),
            Category.name.ilike(keyword),
            Subject.name.ilike(keyword),
            Subject.district.ilike(keyword),
        ),
        case(
            (Product.name.ilike(keyword), 5),
            (Category.name.ilike(keyword), 4),
            (Subject.name.ilike(keyword), 3),
            else_=1,
        ),
    )


@router.get("/suggestions", response_model=ProductSearchSuggestions)
def get_product_search_suggestions(
    q: str = Query(min_length=2, max_length=80),
    db: Session = Depends(get_db),
) -> ProductSearchSuggestions:
    keyword = f"%{q.strip()}%"
    product_names = db.scalars(
        select(Product.name)
        .join(Product.subject)
        .where(*public_product_filters(), Product.name.ilike(keyword))
        .distinct()
        .order_by(Product.name)
        .limit(5)
    ).all()
    category_names = db.scalars(
        select(Category.name)
        .join(Product, Product.category_id == Category.id)
        .join(Subject, Product.subject_id == Subject.id)
        .where(*public_product_filters(), Category.name.ilike(keyword))
        .distinct()
        .order_by(Category.name)
        .limit(3)
    ).all()
    return ProductSearchSuggestions(
        suggestions=list(dict.fromkeys([*product_names, *category_names]))
    )


def public_eligibility_filter():
    has_recognition_source = (
        select(ProductSource.product_id)
        .where(
            ProductSource.product_id == Product.id,
            ProductSource.evidence_role == "recognition",
            ProductSource.verification_level.in_(("A", "B1")),
        )
        .exists()
    )
    has_current_certificate = and_(
        Product.cert_code.is_not(None),
        Product.cert_code != "",
        Product.cert_issued_at.is_not(None),
        Product.cert_expires_at.is_not(None),
        Product.cert_expires_at >= date.today(),
        Product.issuing_authority.is_not(None),
        Product.issuing_authority != "",
    )
    return or_(has_recognition_source, has_current_certificate)


def public_product_filters():
    return (
        Product.status == "approved",
        Product.is_demo.is_(False),
        Subject.status == "approved",
        Product.star.is_not(None),
        Product.description.is_not(None),
        public_eligibility_filter(),
    )


def to_product_list_item(product: Product) -> ProductListItem:
    primary_image = product.images[0].image_url if product.images else None
    return ProductListItem(
        id=product.id,
        name=product.name,
        slug=product.slug,
        star=product.star,
        price=float(product.price) if product.price is not None else None,
        unit=product.unit,
        description=product.description,
        rating_avg=float(product.rating_avg),
        vietgap_code=product.vietgap_code,
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

    filters = list(public_product_filters())
    search_rank = None
    if search:
        search_filter, search_rank = search_expressions(search, db)
        filters.append(search_filter)
    if category:
        filters.append(func.lower(Category.slug) == category.strip().lower())
    if star is not None:
        filters.append(Product.star == star)
    if district:
        filters.append(func.lower(Subject.district) == func.lower(district.strip()))
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

    unavailable_price = case(
        (or_(Product.price.is_(None), Product.price <= 0), 1),
        else_=0,
    )
    sort_columns = {
        "newest": (Product.created_at.desc(),),
        "name": (Product.name.asc(),),
        "-name": (Product.name.desc(),),
        "price": (unavailable_price.asc(), Product.price.asc()),
        "-price": (unavailable_price.asc(), Product.price.desc()),
        "rating": (Product.rating_avg.desc(),),
    }
    if search_rank is not None and sort == "newest":
        sort_columns[sort] = (search_rank.desc(), Product.created_at.desc())
    statement = (
        base_statement.options(
            joinedload(Product.category),
            joinedload(Product.subject),
            selectinload(Product.images),
        )
        .order_by(*sort_columns[sort], Product.id.desc())
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


@router.get("/filter-options", response_model=ProductFilterOptions)
def get_product_filter_options(db: Session = Depends(get_db)) -> ProductFilterOptions:
    districts = list(
        db.scalars(
            select(Subject.district)
            .join(Product, Product.subject_id == Subject.id)
            .where(
                *public_product_filters(),
                Subject.district.is_not(None),
                func.trim(Subject.district) != "",
                func.lower(func.trim(Subject.district)).not_in(
                    ("chưa xác định", "không xác định")
                ),
            )
            .distinct()
            .order_by(Subject.district)
        ).all()
    )
    return ProductFilterOptions(districts=districts)


@router.get(
    "/{slug}",
    response_model=ProductDetail,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def get_product(slug: str, db: Session = Depends(get_db)) -> ProductDetail:
    product = db.scalar(
        select(Product)
        .join(Product.subject)
        .where(
            Product.slug == slug,
            *public_product_filters(),
        )
        .options(
            joinedload(Product.category),
            joinedload(Product.subject),
            selectinload(Product.images),
            selectinload(Product.source_links).joinedload(ProductSource.source),
        )
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PRODUCT_NOT_FOUND",
                "message": "Không tìm thấy sản phẩm.",
                "details": {"slug": slug},
            },
        )

    summary = to_product_list_item(product)
    return ProductDetail(
        **summary.model_dump(),
        cert_code=product.cert_code,
        cert_year=product.cert_year,
        cert_issued_at=product.cert_issued_at,
        cert_expires_at=product.cert_expires_at,
        issuing_authority=product.issuing_authority,
        story=product.story,
        ingredients=product.ingredients,
        usage_instructions=product.usage_instructions,
        views=product.views,
        images=[
            ProductImageRead(
                id=image.id,
                image_url=image.image_url,
                is_primary=image.is_primary,
                sort_order=image.sort_order,
            )
            for image in product.images
        ],
        recognition_sources=[
            ProductPublicSourceRead(
                id=link.source.id,
                title=link.source.title,
                document_number=link.source.document_number,
                issuing_body=link.source.issuing_body,
                published_at=link.source.published_at,
                source_url=link.source.source_url,
                verification_level=link.verification_level,
            )
            for link in product.source_links
            if link.evidence_role == "recognition"
            and link.verification_level in {"A", "B1"}
        ],
        updated_at=product.updated_at,
    )
