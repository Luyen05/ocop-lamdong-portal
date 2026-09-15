from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.news import News
from app.schemas.error import ErrorResponse
from app.schemas.news import NewsDetail, NewsImageRead, NewsListItem, NewsListResponse


router = APIRouter(prefix="/news", tags=["News"])


def to_news_list_item(news: News) -> NewsListItem:
    return NewsListItem(
        id=news.id,
        title=news.title,
        slug=news.slug,
        category=news.category,
        summary=news.summary,
        primary_image_url=next(
            (image.image_url for image in news.images if image.is_primary), None,
        ),
        published_at=news.published_at,
    )


@router.get(
    "",
    response_model=NewsListResponse,
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse}},
)
def list_news(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=150),
    category: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
) -> NewsListResponse:
    filters = [News.status == "published"]
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(or_(News.title.ilike(keyword), News.summary.ilike(keyword)))
    if category:
        filters.append(func.lower(News.category) == func.lower(category.strip()))

    total = db.scalar(select(func.count(News.id)).where(*filters)) or 0
    statement = (
        select(News)
        .where(*filters)
        .options(selectinload(News.images))
        .order_by(News.published_at.desc(), News.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return NewsListResponse(
        items=[to_news_list_item(news) for news in db.scalars(statement).all()],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{slug}",
    response_model=NewsDetail,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def get_news(slug: str, db: Session = Depends(get_db)) -> NewsDetail:
    news = db.scalar(
        select(News)
        .where(News.slug == slug, News.status == "published")
        .options(selectinload(News.images))
    )
    if news is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NEWS_NOT_FOUND",
                "message": "Không tìm thấy bài viết.",
                "details": {"slug": slug},
            },
        )

    return NewsDetail(
        **to_news_list_item(news).model_dump(),
        content=news.content,
        views=news.views,
        images=[
            NewsImageRead(
                id=image.id,
                image_url=image.image_url,
                is_primary=image.is_primary,
                sort_order=image.sort_order,
            )
            for image in news.images
        ],
        updated_at=news.updated_at,
    )
