"""Quản lý danh mục sản phẩm cho admin (quy tắc nhóm trưởng chốt 28/09).

Ẩn danh mục chỉ bỏ danh mục khỏi bộ lọc công khai và ô chọn khi tạo sản phẩm mới;
sản phẩm đã thuộc danh mục vẫn hiển thị. Chỉ xóa được danh mục không còn sản phẩm nào.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.slug import slugify
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import (
    AdminCategoryCreate,
    AdminCategoryListResponse,
    AdminCategoryRead,
    AdminCategoryUpdate,
)
from app.schemas.error import ErrorResponse


router = APIRouter(prefix="/categories")

CONFLICT_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
}


def category_error(status_code: int, code: str, message: str, details: dict | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


def count_products(db: Session, category_id: int) -> int:
    return db.scalar(
        select(func.count(Product.id)).where(Product.category_id == category_id)
    ) or 0


def to_admin_category_read(category: Category, product_count: int) -> AdminCategoryRead:
    return AdminCategoryRead(
        id=category.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        icon=category.icon,
        is_visible=category.is_visible,
        sort_order=category.sort_order,
        product_count=product_count,
    )


def get_category_or_404(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise category_error(
            status.HTTP_404_NOT_FOUND,
            "CATEGORY_NOT_FOUND",
            "Không tìm thấy danh mục.",
            {"category_id": category_id},
        )
    return category


def ensure_name_available(db: Session, name: str, category_id: int | None = None) -> None:
    # So khớp cả nguyên văn: lower() của SQLite (và collation "C" của PostgreSQL) không hạ chữ có dấu.
    conditions = [or_(Category.name == name, func.lower(Category.name) == name.lower())]
    if category_id is not None:
        conditions.append(Category.id != category_id)
    if db.scalar(select(Category.id).where(*conditions)) is not None:
        raise category_error(
            status.HTTP_409_CONFLICT,
            "CATEGORY_NAME_EXISTS",
            "Tên danh mục đã tồn tại.",
            {"name": name},
        )


def slug_taken(db: Session, slug: str, category_id: int | None = None) -> bool:
    conditions = [Category.slug == slug]
    if category_id is not None:
        conditions.append(Category.id != category_id)
    return db.scalar(select(Category.id).where(*conditions)) is not None


def ensure_slug_available(db: Session, slug: str, category_id: int | None = None) -> None:
    if slug_taken(db, slug, category_id):
        raise category_error(
            status.HTTP_409_CONFLICT,
            "CATEGORY_SLUG_EXISTS",
            "Đường dẫn (slug) danh mục đã tồn tại.",
            {"slug": slug},
        )


def unique_slug_from_name(db: Session, name: str) -> str:
    base = slugify(name, fallback="danh-muc")
    candidate = base
    suffix = 2
    while slug_taken(db, candidate):
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def commit_category(
    db: Session,
    message: str = "Tên hoặc đường dẫn danh mục đã tồn tại.",
) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        # Hai admin thao tác cùng lúc: ràng buộc UNIQUE/khóa ngoại của database chặn lại.
        db.rollback()
        raise category_error(status.HTTP_409_CONFLICT, "CATEGORY_CONFLICT", message) from exc


@router.get("", response_model=AdminCategoryListResponse)
def list_admin_categories(db: Session = Depends(get_db)) -> AdminCategoryListResponse:
    product_counts = (
        select(Product.category_id, func.count(Product.id).label("product_count"))
        .group_by(Product.category_id)
        .subquery()
    )
    rows = db.execute(
        select(Category, func.coalesce(product_counts.c.product_count, 0))
        .outerjoin(product_counts, product_counts.c.category_id == Category.id)
        .order_by(Category.sort_order.asc(), Category.name.asc(), Category.id.asc())
    ).all()
    return AdminCategoryListResponse(
        items=[to_admin_category_read(category, count) for category, count in rows],
        total=len(rows),
    )


@router.post(
    "",
    response_model=AdminCategoryRead,
    status_code=status.HTTP_201_CREATED,
    responses=CONFLICT_RESPONSES,
)
def create_category(
    payload: AdminCategoryCreate,
    db: Session = Depends(get_db),
) -> AdminCategoryRead:
    ensure_name_available(db, payload.name)
    if payload.slug:
        ensure_slug_available(db, payload.slug)
        slug = payload.slug
    else:
        slug = unique_slug_from_name(db, payload.name)

    category = Category(
        name=payload.name,
        slug=slug,
        description=payload.description,
        icon=payload.icon,
        is_visible=payload.is_visible,
        sort_order=payload.sort_order,
    )
    db.add(category)
    commit_category(db)
    return to_admin_category_read(category, 0)


@router.patch(
    "/{category_id}",
    response_model=AdminCategoryRead,
    responses=CONFLICT_RESPONSES,
)
def update_category(
    category_id: int,
    payload: AdminCategoryUpdate,
    db: Session = Depends(get_db),
) -> AdminCategoryRead:
    category = get_category_or_404(db, category_id)
    values = payload.model_dump(exclude_unset=True)
    if "name" in values and values["name"] != category.name:
        ensure_name_available(db, values["name"], category.id)
    if "slug" in values and values["slug"] != category.slug:
        ensure_slug_available(db, values["slug"], category.id)
    for field, value in values.items():
        setattr(category, field, value)
    db.add(category)
    commit_category(db)
    return to_admin_category_read(category, count_products(db, category.id))


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=CONFLICT_RESPONSES,
)
def delete_category(category_id: int, db: Session = Depends(get_db)) -> Response:
    category = get_category_or_404(db, category_id)
    product_count = count_products(db, category.id)
    if product_count:
        raise category_error(
            status.HTTP_409_CONFLICT,
            "CATEGORY_IN_USE",
            "Danh mục còn sản phẩm nên chưa thể xóa. Hãy ẩn danh mục hoặc chuyển sản phẩm sang danh mục khác.",
            {"product_count": product_count},
        )
    db.delete(category)
    commit_category(db, "Danh mục vừa được gán cho sản phẩm nên chưa thể xóa.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
