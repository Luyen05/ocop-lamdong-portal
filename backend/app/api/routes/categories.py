from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryListResponse, CategoryRead
from app.schemas.error import ErrorResponse


router = APIRouter(prefix="/categories", tags=["Categories"])

SortOption = Literal["name", "-name", "id", "-id"]


@router.get("", response_model=CategoryListResponse)
def list_categories(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    sort: SortOption = Query(default="name"),
    db: Session = Depends(get_db),
) -> CategoryListResponse:
    filters = []
    if search:
        filters.append(Category.name.ilike(f"%{search.strip()}%"))

    total = db.scalar(select(func.count(Category.id)).where(*filters)) or 0

    sort_columns = {
        "name": Category.name.asc(),
        "-name": Category.name.desc(),
        "id": Category.id.asc(),
        "-id": Category.id.desc(),
    }
    statement = (
        select(Category)
        .where(*filters)
        .order_by(sort_columns[sort])
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(statement).all())

    return CategoryListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{slug}",
    response_model=CategoryRead,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def get_category(slug: str, db: Session = Depends(get_db)) -> Category:
    category = db.scalar(select(Category).where(Category.slug == slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CATEGORY_NOT_FOUND",
                "message": "Không tìm thấy danh mục.",
                "details": {"slug": slug},
            },
        )
    return category
